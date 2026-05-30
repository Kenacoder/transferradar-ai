"""
handlers/start_handler.py — TransferRadar AI
/start command handler — registers the user and displays the main menu.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from database import db
from utils.formatters import format_main_menu, format_about
from utils.rate_limiter import action_limiter
from loguru import logger


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔥 Trending Now", callback_data="trending"),
            InlineKeyboardButton("⚡ Breaking News", callback_data="breaking"),
        ],
        [
            InlineKeyboardButton("🏆 Leagues", callback_data="leagues"),
            InlineKeyboardButton("🔍 Search", callback_data="search_prompt"),
        ],
        [
            InlineKeyboardButton("⭐ My Clubs", callback_data="my_clubs"),
            InlineKeyboardButton("🔔 Alerts", callback_data="alerts"),
        ],
        [
            InlineKeyboardButton("ℹ️ About", callback_data="about"),
        ],
    ])


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — register user and show main menu."""
    user = update.effective_user
    if not user:
        return

    try:
        await db.upsert_user(
            user_id=user.id,
            username=user.username or "",
            first_name=user.first_name or "",
        )
        logger.info(f"👤 User registered/updated: {user.id} (@{user.username})")
    except Exception as e:
        logger.error(f"DB upsert error for user {user.id}: {e}")

    await update.message.reply_text(
        text=format_main_menu(),
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about — show bot information."""
    await update.message.reply_text(
        text=format_about(),
        parse_mode="Markdown",
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu — show main menu inline."""
    await update.message.reply_text(
        text=format_main_menu(),
        parse_mode="Markdown",
        reply_markup=_main_menu_keyboard(),
    )


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Public accessor for main menu keyboard (used by callback_handler)."""
    return _main_menu_keyboard()
