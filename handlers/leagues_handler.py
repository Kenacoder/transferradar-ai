"""
handlers/leagues_handler.py — TransferRadar AI
League and club navigation — browse leagues → clubs → club news.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import LEAGUES, CLUBS
from services.transfer_service import get_club_news, get_club_stats
from utils.formatters import (
    format_league_menu,
    format_club_list,
    format_club_header,
    format_news_item,
)
from loguru import logger


# ─── League selection keyboard ─────────────────────────────────────────────────
def _league_keyboard() -> InlineKeyboardMarkup:
    rows = []
    league_ids = list(LEAGUES.keys())
    for i in range(0, len(league_ids), 2):
        row = []
        for lid in league_ids[i:i+2]:
            league = LEAGUES[lid]
            row.append(InlineKeyboardButton(
                f"{league['emoji']} {league['name']}",
                callback_data=f"league:{lid}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(rows)


# ─── Club selection keyboard for a league ─────────────────────────────────────
def _club_keyboard(league_id: str) -> InlineKeyboardMarkup:
    clubs_in_league = [
        (cid, cdata)
        for cid, cdata in CLUBS.items()
        if cdata["league"] == league_id
    ]
    rows = []
    for i in range(0, len(clubs_in_league), 2):
        row = []
        for cid, cdata in clubs_in_league[i:i+2]:
            row.append(InlineKeyboardButton(
                f"{cdata['emoji']} {cdata['name']}",
                callback_data=f"club:{cid}",
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton("⬅️ Back to Leagues", callback_data="leagues")])
    return InlineKeyboardMarkup(rows)


# ─── News list keyboard for a club ────────────────────────────────────────────
def _club_news_keyboard(club_id: str, news_items: list[dict], page: int = 0) -> InlineKeyboardMarkup:
    rows = []
    for item in news_items:
        title_short = item.get("title", "")[:35] + "…"
        rows.append([InlineKeyboardButton(
            title_short,
            callback_data=f"newsitem:{item['id']}:{club_id}",
        )])
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"clubpage:{club_id}:{page-1}"))
    if len(news_items) == 5:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"clubpage:{club_id}:{page+1}"))
    if nav_row:
        rows.append(nav_row)
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"league:{CLUBS[club_id]['league']}")])
    return InlineKeyboardMarkup(rows)


# ─── Handler functions ─────────────────────────────────────────────────────────
async def show_leagues(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.edit_message_text(
        text=format_league_menu(),
        parse_mode="Markdown",
        reply_markup=_league_keyboard(),
    )


async def show_clubs(update: Update, context: ContextTypes.DEFAULT_TYPE, league_id: str) -> None:
    query = update.callback_query
    await query.edit_message_text(
        text=format_club_list(league_id),
        parse_mode="Markdown",
        reply_markup=_club_keyboard(league_id),
    )


async def show_club_news(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    club_id: str,
    page: int = 0,
) -> None:
    query = update.callback_query
    try:
        from config import PAGE_SIZE
        news_items = await get_club_news(club_id, limit=PAGE_SIZE * (page + 1))
        # Slice for current page
        paged = news_items[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
        counts = await get_club_stats(club_id)
        header = format_club_header(club_id, counts)
        keyboard = _club_news_keyboard(club_id, paged, page)
        await query.edit_message_text(
            text=header,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"show_club_news error for {club_id}: {e}")
        await query.edit_message_text(
            text="⚠️ Could not load club news. Please try again.",
        )


async def show_news_item(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    news_id: int,
    back_club_id: str,
) -> None:
    query = update.callback_query
    try:
        from services.transfer_service import get_news_item
        item = await get_news_item(news_id)
        if not item:
            await query.edit_message_text("⚠️ News item not found.")
            return

        text = format_news_item(item)
        url = item.get("url", "")
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔗 Read Full Story", url=url) if url else
                InlineKeyboardButton("🔗 No link", callback_data="noop"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"newsitem:{news_id}:{back_club_id}"),
            ],
            [
                InlineKeyboardButton("⬅️ Back", callback_data=f"club:{back_club_id}"),
                InlineKeyboardButton("🏠 Menu", callback_data="main_menu"),
            ],
        ])
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
    except Exception as e:
        logger.error(f"show_news_item error {news_id}: {e}")
        await query.edit_message_text("⚠️ Could not load this news item.")
