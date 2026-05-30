"""
handlers/alerts_handler.py — TransferRadar AI
Subscription / alerts management: subscribe to clubs, toggle notifications.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

from config import CLUBS, LEAGUES
from database import db
from services.transfer_service import subscribe, unsubscribe, get_subscriptions, is_subscribed
from utils.formatters import format_my_clubs
from loguru import logger


# ─── My Clubs keyboard ────────────────────────────────────────────────────────
def _my_clubs_keyboard(subs: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for sub in subs:
        club_data = CLUBS.get(sub.get("club_id", ""), {})
        name = club_data.get("name", sub.get("club_id", "?"))
        emoji = club_data.get("emoji", "🏟️")
        rows.append([
            InlineKeyboardButton(
                f"{emoji} {name}",
                callback_data=f"club:{sub['club_id']}",
            ),
            InlineKeyboardButton(
                "❌ Unsub",
                callback_data=f"unsub:{sub['club_id']}",
            ),
        ])
    rows.append([
        InlineKeyboardButton("🏆 Browse Leagues", callback_data="leagues"),
        InlineKeyboardButton("⬅️ Menu", callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(rows)


# ─── Alerts settings keyboard ─────────────────────────────────────────────────
def _alerts_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    toggle_label = "🔕 Disable Alerts" if notifications_enabled else "🔔 Enable Alerts"
    toggle_data = "alerts_disable" if notifications_enabled else "alerts_enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_label, callback_data=toggle_data)],
        [InlineKeyboardButton("⭐ My Clubs", callback_data="my_clubs")],
        [InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")],
    ])


# ─── Commands ─────────────────────────────────────────────────────────────────
async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alerts — show alert settings."""
    user = update.effective_user
    if not user:
        return
    user_data = await db.get_user(user.id)
    notifications_enabled = bool(user_data.get("notifications_enabled", 1)) if user_data else True
    await update.message.reply_text(
        "🔔 *Alert Settings*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Notifications: {'✅ ON' if notifications_enabled else '❌ OFF'}\n\n"
        "Subscribe to clubs from the Leagues menu to receive alerts "
        "when new transfer news drops.",
        parse_mode="Markdown",
        reply_markup=_alerts_keyboard(notifications_enabled),
    )


async def my_clubs_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myclubs — show user's subscribed clubs."""
    user = update.effective_user
    if not user:
        return
    subs = await get_subscriptions(user.id)
    await update.message.reply_text(
        text=format_my_clubs(subs),
        parse_mode="Markdown",
        reply_markup=_my_clubs_keyboard(subs),
    )


# ─── Callback handlers (called from callback_handler.py) ──────────────────────
async def show_my_clubs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    subs = await get_subscriptions(user.id)
    await query.edit_message_text(
        text=format_my_clubs(subs),
        parse_mode="Markdown",
        reply_markup=_my_clubs_keyboard(subs),
    )


async def show_alerts_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    user_data = await db.get_user(user.id)
    notifications_enabled = bool(user_data.get("notifications_enabled", 1)) if user_data else True
    await query.edit_message_text(
        "🔔 *Alert Settings*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Notifications: {'✅ ON' if notifications_enabled else '❌ OFF'}\n\n"
        "Subscribe to clubs from the Leagues menu to receive real-time transfer alerts.",
        parse_mode="Markdown",
        reply_markup=_alerts_keyboard(notifications_enabled),
    )


async def handle_subscribe(
    update: Update, context: ContextTypes.DEFAULT_TYPE, club_id: str
) -> None:
    query = update.callback_query
    user = query.from_user
    already = await is_subscribed(user.id, club_id)
    if already:
        club_name = CLUBS.get(club_id, {}).get("name", club_id)
        await query.answer(f"✅ Already subscribed to {club_name}!", show_alert=True)
        return
    success = await subscribe(user.id, club_id)
    club_name = CLUBS.get(club_id, {}).get("name", club_id)
    if success:
        await query.answer(f"🔔 Subscribed to {club_name}!", show_alert=True)
    else:
        await query.answer("⚠️ Could not subscribe. Try again.", show_alert=True)


async def handle_unsubscribe(
    update: Update, context: ContextTypes.DEFAULT_TYPE, club_id: str
) -> None:
    query = update.callback_query
    user = query.from_user
    success = await unsubscribe(user.id, club_id)
    club_name = CLUBS.get(club_id, {}).get("name", club_id)
    if success:
        await query.answer(f"🔕 Unsubscribed from {club_name}", show_alert=True)
    else:
        await query.answer("⚠️ Could not unsubscribe.", show_alert=True)
    # Refresh my_clubs view
    subs = await get_subscriptions(user.id)
    await query.edit_message_text(
        text=format_my_clubs(subs),
        parse_mode="Markdown",
        reply_markup=_my_clubs_keyboard(subs),
    )


async def toggle_alerts_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    await db.toggle_notifications(user.id, enabled=True)
    await query.answer("🔔 Alerts enabled!", show_alert=True)
    await show_alerts_settings(update, context)


async def toggle_alerts_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    await db.toggle_notifications(user.id, enabled=False)
    await query.answer("🔕 Alerts disabled", show_alert=True)
    await show_alerts_settings(update, context)
