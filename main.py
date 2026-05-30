"""
main.py — TransferRadar AI
Entry point: launches Telegram bot + FastAPI keep-alive server + APScheduler
concurrently via asyncio.gather().
"""

import asyncio
import os
import sys

from loguru import logger
from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_TOKEN, CLUBS, BOT_NAME
from database import db
from keep_alive import run_web_server
from scheduler import run_scheduler, set_bot_app

# ─── Loguru configuration ──────────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stdout,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>"
    ),
    level="INFO",
    colorize=True,
)
logger.add(
    "logs/transferradar.log",
    rotation="10 MB",
    retention="7 days",
    compression="gz",
    level="DEBUG",
    enqueue=True,
)

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)


# ─── Bot setup ─────────────────────────────────────────────────────────────────
def build_application() -> Application:
    """Build and configure the PTB Application with all handlers registered."""
    from handlers.start_handler import start_command, about_command, menu_command
    from handlers.trending_handler import trending_command
    from handlers.search_handler import search_command, handle_search_text
    from handlers.alerts_handler import alerts_command, my_clubs_command
    from handlers.callback_handler import handle_callback

    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .concurrent_updates(True)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("trending", trending_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("alerts", alerts_command))
    app.add_handler(CommandHandler("myclubs", my_clubs_command))
    app.add_handler(CommandHandler("about", about_command))

    # Inline keyboard callbacks
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Free-text message handler (for search flow)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search_text)
    )

    return app


async def set_bot_commands(app: Application) -> None:
    """Register bot command list visible in Telegram's menu."""
    commands = [
        BotCommand("start", "Main menu"),
        BotCommand("trending", "Trending transfer news"),
        BotCommand("search", "Search player or club"),
        BotCommand("myclubs", "My subscribed clubs"),
        BotCommand("alerts", "Manage transfer alerts"),
        BotCommand("about", "About TransferRadar AI"),
        BotCommand("menu", "Show main menu"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("✅ Bot commands registered")


async def run_bot(app: Application) -> None:
    """Initialise the bot, seed the database, and start polling."""
    # Connect DB
    await db.connect()

    # Seed club master data
    await db.seed_clubs(CLUBS)

    # Set bot commands
    await set_bot_commands(app)

    # Inject app reference into scheduler (for broadcasts)
    set_bot_app(app)

    logger.info(f"🤖 {BOT_NAME} starting polling…")

    # Use run_polling in a thread-compatible async way
    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )

    logger.info(f"✅ {BOT_NAME} is LIVE and polling")

    # Keep alive until cancelled
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("🛑 Bot polling stopping…")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await db.close()
        logger.info("🔒 Bot shut down cleanly")


# ─── Main entrypoint ───────────────────────────────────────────────────────────
async def main() -> None:
    if not TELEGRAM_TOKEN:
        logger.critical("❌ TELEGRAM_TOKEN is not set. Exiting.")
        sys.exit(1)

    app = build_application()

    logger.info("🚀 Launching TransferRadar AI — bot + web server + scheduler")

    try:
        await asyncio.gather(
            run_bot(app),
            run_web_server(),
            run_scheduler(),
        )
    except KeyboardInterrupt:
        logger.info("👋 Received interrupt — shutting down gracefully")
    except Exception as e:
        logger.critical(f"💥 Fatal error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
