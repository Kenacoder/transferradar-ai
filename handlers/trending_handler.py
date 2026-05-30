"""
handlers/trending_handler.py — TransferRadar AI
/trending command and trending inline view handler.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from services.trending_service import get_trending_topics
from utils.formatters import format_trending
from loguru import logger


def _trending_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="trending"),
            InlineKeyboardButton("⬅️ Menu", callback_data="main_menu"),
        ]
    ])


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /trending command."""
    try:
        items = await get_trending_topics(limit=10)
        text = format_trending(items)
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        text = "⚠️ Could not load trending topics. Please try again."

    await update.message.reply_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=_trending_keyboard(),
    )


async def show_trending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trending via callback (edit existing message)."""
    query = update.callback_query
    try:
        items = await get_trending_topics(limit=10)
        text = format_trending(items)
    except Exception as e:
        logger.error(f"Error fetching trending: {e}")
        text = "⚠️ Could not load trending topics. Please try again."

    await query.edit_message_text(
        text=text,
        parse_mode="Markdown",
        reply_markup=_trending_keyboard(),
    )


def get_trending_keyboard() -> InlineKeyboardMarkup:
    return _trending_keyboard()
