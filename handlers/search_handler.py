"""
handlers/search_handler.py — TransferRadar AI
Search command + inline search flow with rate limiting.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from services.transfer_service import search_transfers
from utils.formatters import format_search_results, format_news_item, format_rate_limit_warning
from utils.rate_limiter import search_limiter
from loguru import logger

# Context key for tracking users in search mode
_SEARCH_STATE_KEY = "awaiting_search"


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search [query] — search immediately or prompt for input."""
    user = update.effective_user
    if not user:
        return

    # Check rate limit
    if not await search_limiter.is_allowed(user.id):
        await update.message.reply_text(format_rate_limit_warning(), parse_mode="Markdown")
        return

    args = context.args
    if args:
        query = " ".join(args)
        await _do_search(update, context, query)
    else:
        # Prompt user to type query
        context.user_data[_SEARCH_STATE_KEY] = True
        await update.message.reply_text(
            "🔍 *Search TransferRadar*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "Type a player name, club, or keyword:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]
            ]),
        )


async def handle_search_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-text messages when user is in search mode."""
    user = update.effective_user
    if not user:
        return
    if not context.user_data.get(_SEARCH_STATE_KEY):
        return  # Not in search mode

    # Clear state
    context.user_data.pop(_SEARCH_STATE_KEY, None)

    # Rate limit
    if not await search_limiter.is_allowed(user.id):
        await update.message.reply_text(format_rate_limit_warning(), parse_mode="Markdown")
        return

    query = update.message.text.strip()
    if not query:
        return
    await _do_search(update, context, query)


async def _do_search(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str
) -> None:
    try:
        results = await search_transfers(query, limit=10)
        text = format_search_results(query, results)

        # Build buttons for each result
        buttons: list[list[InlineKeyboardButton]] = []
        for item in results[:5]:
            title_short = item.get("title", "")[:38] + "…"
            buttons.append([InlineKeyboardButton(
                title_short,
                callback_data=f"newsitem:{item['id']}:search",
            )])
        buttons.append([
            InlineKeyboardButton("🔍 New Search", callback_data="search_prompt"),
            InlineKeyboardButton("⬅️ Menu", callback_data="main_menu"),
        ])

        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception as e:
        logger.error(f"Search error for '{query}': {e}")
        await update.message.reply_text("⚠️ Search failed. Please try again.")


async def prompt_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback: prompt user to type a search query."""
    query = update.callback_query
    user = query.from_user
    context.user_data[_SEARCH_STATE_KEY] = True
    await query.edit_message_text(
        "🔍 *Search TransferRadar*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Type a player name, club, or keyword in the chat:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="main_menu")]
        ]),
    )
