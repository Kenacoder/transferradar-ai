"""
handlers/callback_handler.py — TransferRadar AI
Central dispatcher for ALL inline button callbacks.
Implements rate limiting and routes to the correct handler function.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from loguru import logger
from utils.rate_limiter import action_limiter
from utils.formatters import format_main_menu, format_about, format_rate_limit_warning, format_news_item


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Master callback dispatcher — all inline button presses route through here."""
    query = update.callback_query
    user = query.from_user

    data = query.data or ""

    # Acknowledge the callback immediately — but NOT for sub/unsub_club
    # since those need their own query.answer() with show_alert=True
    if not data.startswith(("sub_club:", "unsub_club:")):
        try:
            await query.answer()
        except Exception:
            pass

    # Per-user rate limiting
    if not await action_limiter.is_allowed(user.id):
        try:
            await query.answer(
                text="🛑 Too many requests. Please slow down!",
                show_alert=True,
            )
        except Exception:
            pass
        return

    logger.debug(f"📲 Callback [{user.id}]: {data}")

    try:
        # ── Main menu ───────────────────────────────────────────────────────────
        if data == "main_menu":
            from handlers.start_handler import get_main_menu_keyboard
            await query.edit_message_text(
                text=format_main_menu(),
                parse_mode="Markdown",
                reply_markup=get_main_menu_keyboard(),
            )

        # ── About ───────────────────────────────────────────────────────────────
        elif data == "about":
            await query.edit_message_text(
                text=format_about(),
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")]
                ]),
            )

        # ── Trending ────────────────────────────────────────────────────────────
        elif data == "trending":
            from handlers.trending_handler import show_trending
            await show_trending(update, context)

        # ── Breaking news ───────────────────────────────────────────────────────
        elif data == "breaking":
            from services.transfer_service import get_breaking_news
            items = await get_breaking_news(limit=5)
            if not items:
                await query.edit_message_text(
                    "⚡ *Breaking News*\n━━━━━━━━━━━━━━━━━━━\n"
                    "📭 No breaking news at the moment. Check back soon!",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Refresh", callback_data="breaking"),
                         InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")]
                    ]),
                )
                return

            # Show first item with navigation context
            item = items[0]
            text = "⚡ *BREAKING NEWS*\n━━━━━━━━━━━━━━━━━━━\n" + format_news_item(item)
            url = item.get("url", "")
            nav_buttons = []
            if len(items) > 1:
                nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"newsitem:{items[1]['id']}:breaking"))
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Full Story", url=url) if url else InlineKeyboardButton("🔗 No link", callback_data="noop")] + nav_buttons,
                [InlineKeyboardButton("🔄 Refresh", callback_data="breaking"),
                 InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")],
            ])
            await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=keyboard)

        # ── Leagues ─────────────────────────────────────────────────────────────
        elif data == "leagues":
            from handlers.leagues_handler import show_leagues
            await show_leagues(update, context)

        # ── league:<id> ─────────────────────────────────────────────────────────
        elif data.startswith("league:"):
            league_id = data.split(":", 1)[1]
            from handlers.leagues_handler import show_clubs
            await show_clubs(update, context, league_id)

        # ── club:<id> ───────────────────────────────────────────────────────────
        elif data.startswith("club:"):
            club_id = data.split(":", 1)[1]
            from handlers.leagues_handler import show_club_news
            await show_club_news(update, context, club_id, page=0)

        # ── clubpage:<club_id>:<page> ────────────────────────────────────────
        elif data.startswith("clubpage:"):
            _, club_id, page_str = data.split(":", 2)
            from handlers.leagues_handler import show_club_news
            await show_club_news(update, context, club_id, page=int(page_str))

        # ── newsitem:<id>:<back> ─────────────────────────────────────────────
        elif data.startswith("newsitem:"):
            parts = data.split(":")
            news_id = int(parts[1])
            back_club = parts[2] if len(parts) > 2 else "search"
            from handlers.leagues_handler import show_news_item
            await show_news_item(update, context, news_id, back_club)

        # ── Search prompt ───────────────────────────────────────────────────────
        elif data == "search_prompt":
            from handlers.search_handler import prompt_search
            await prompt_search(update, context)

        # ── My clubs ────────────────────────────────────────────────────────────
        elif data == "my_clubs":
            from handlers.alerts_handler import show_my_clubs
            await show_my_clubs(update, context)

        # ── Alerts ──────────────────────────────────────────────────────────────
        elif data == "alerts":
            from handlers.alerts_handler import show_alerts_settings
            await show_alerts_settings(update, context)

        elif data == "alerts_enable":
            from handlers.alerts_handler import toggle_alerts_on
            await toggle_alerts_on(update, context)

        elif data == "alerts_disable":
            from handlers.alerts_handler import toggle_alerts_off
            await toggle_alerts_off(update, context)

        # ── Subscribe / Unsubscribe ─────────────────────────────────────────────
        elif data.startswith("sub:"):
            club_id = data.split(":", 1)[1]
            from handlers.alerts_handler import handle_subscribe
            await handle_subscribe(update, context, club_id)

        elif data.startswith("unsub:"):
            club_id = data.split(":", 1)[1]
            from handlers.alerts_handler import handle_unsubscribe
            await handle_unsubscribe(update, context, club_id)

        elif data.startswith("sub_club:"):
            _, club_id, page_str = data.split(":", 2)
            page = int(page_str)
            # Subscribe silently — don't use handle_subscribe as it calls query.answer()
            # which conflicts with the answer() already called at the top of this handler
            from services.transfer_service import subscribe, is_subscribed
            from config import CLUBS as C
            club_name = C.get(club_id, {}).get("name", club_id)
            try:
                already = await is_subscribed(user.id, club_id)
                if not already:
                    await subscribe(user.id, club_id)
                    try:
                        await query.answer(f"🔔 Subscribed to {club_name}!", show_alert=True)
                    except Exception:
                        pass
                else:
                    try:
                        await query.answer(f"✅ Already subscribed to {club_name}!", show_alert=True)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Subscribe error for {club_id}: {e}")
            # Always refresh the club news page to show updated favorites state
            from handlers.leagues_handler import show_club_news
            await show_club_news(update, context, club_id, page)

        elif data.startswith("unsub_club:"):
            _, club_id, page_str = data.split(":", 2)
            page = int(page_str)
            from services.transfer_service import unsubscribe
            from config import CLUBS as C
            club_name = C.get(club_id, {}).get("name", club_id)
            try:
                success = await unsubscribe(user.id, club_id)
                if success:
                    try:
                        await query.answer(f"🔕 Removed {club_name} from Favorites", show_alert=True)
                    except Exception:
                        pass
                else:
                    try:
                        await query.answer("⚠️ Could not unsubscribe.", show_alert=True)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Unsubscribe error for {club_id}: {e}")
            # Always refresh the club news page
            from handlers.leagues_handler import show_club_news
            await show_club_news(update, context, club_id, page)

        # ── No-op (placeholder buttons) ─────────────────────────────────────────
        elif data == "noop":
            pass

        else:
            logger.warning(f"Unhandled callback: {data}")

    except Exception as e:
        logger.error(f"Callback handler error [{data}]: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                text="⚠️ Something went wrong. Please try again.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Menu", callback_data="main_menu")]
                ]),
            )
        except Exception:
            pass
