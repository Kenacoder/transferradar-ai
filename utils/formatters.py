"""
utils/formatters.py — TransferRadar AI
Telegram message formatting helpers. Builds all bot message templates.
"""

from datetime import datetime, timezone
from typing import Optional

from config import BOT_NAME, BOT_VERSION, BOT_DESCRIPTION, LEAGUES, CLUBS


def _time_ago(dt_str: Optional[str]) -> str:
    """Convert a scraped_at timestamp string to a human-readable 'X ago' string."""
    if not dt_str:
        return "recently"
    try:
        if isinstance(dt_str, str):
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            dt = dt_str
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        diff = datetime.now(timezone.utc) - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            return f"{seconds // 60}m ago"
        elif seconds < 86400:
            return f"{seconds // 3600}h ago"
        else:
            return f"{seconds // 86400}d ago"
    except Exception:
        return "recently"


def _reliability_bar(score: int) -> str:
    """Build a 10-char progress bar from a 0-100 score."""
    filled = round(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _reliability_emoji(label: Optional[str]) -> str:
    mapping = {
        "CONFIRMED": "✅",
        "HIGHLY RELIABLE": "🟢",
        "POSSIBLE": "🟡",
        "LOW RELIABILITY": "🟠",
        "FAKE RUMOR": "🔴",
    }
    return mapping.get(label or "", "⚪")


# ─── Main Menu ─────────────────────────────────────────────────────────────────
def format_main_menu() -> str:
    return (
        f"⚽ *{BOT_NAME}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Your 24/7 football transfer intelligence platform.\n\n"
        "🔍 *What would you like to explore?*\n"
        "Use the buttons below to navigate:"
    )


# ─── News Item ─────────────────────────────────────────────────────────────────
def format_news_item(item: dict) -> str:
    score = item.get("reliability_score", 0)
    label = item.get("reliability_label", "UNKNOWN")
    rel_emoji = _reliability_emoji(label)
    bar = _reliability_bar(score)
    time_str = _time_ago(item.get("scraped_at"))

    player = item.get("player_name") or "Unknown Player"
    club = item.get("club_name") or "Unknown Club"
    source = item.get("source") or "Unknown Source"
    title = item.get("title") or ""
    summary = item.get("summary") or title

    is_confirmed = item.get("is_confirmed", 0)
    header = "🚨 *BREAKING*" if is_confirmed else "📡 *TRANSFER NEWS*"

    return (
        f"{header}\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *{player}* → 🏟️ *{club}*\n"
        f"📰 Source: _{source}_\n"
        f"⏰ _{time_str}_\n\n"
        f"📝 {summary}\n\n"
        f"🎯 Reliability: `{bar}` {score}%\n"
        f"{rel_emoji} Status: *{label}*"
    )


# ─── Trending ──────────────────────────────────────────────────────────────────
def format_trending(items: list[dict]) -> str:
    if not items:
        return (
            "🔥 *TRENDING TRANSFERS TODAY*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "📭 No trending topics yet. Check back soon!"
        )
    number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣",
                     "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    lines = ["🔥 *TRENDING TRANSFERS TODAY*", "━━━━━━━━━━━━━━━━━━━"]
    for i, item in enumerate(items[:10]):
        num = number_emojis[i] if i < len(number_emojis) else f"{i+1}."
        topic = item.get("topic", "Unknown")
        mentions = item.get("mention_count", 0)
        lines.append(f"{num} {topic} _({mentions} mentions)_")
    return "\n".join(lines)


# ─── League Menu ───────────────────────────────────────────────────────────────
def format_league_menu() -> str:
    return (
        "🏆 *Select a League*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Choose a league to browse clubs and latest transfer news:"
    )


# ─── Club List ─────────────────────────────────────────────────────────────────
def format_club_list(league_id: str) -> str:
    league = LEAGUES.get(league_id, {})
    emoji = league.get("emoji", "🏟️")
    name = league.get("name", league_id)
    return (
        f"{emoji} *{name} Clubs*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Select a club to view the latest transfer rumours:"
    )


# ─── Club News Header ──────────────────────────────────────────────────────────
def format_club_header(club_id: str, counts: dict) -> str:
    club = CLUBS.get(club_id, {})
    emoji = club.get("emoji", "🏟️")
    name = club.get("name", club_id)
    total = counts.get("total", 0)
    confirmed = counts.get("confirmed", 0)
    return (
        f"{emoji} *{name}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📰 Total Rumours: *{total}*\n"
        f"✅ Confirmed Deals: *{confirmed}*\n\n"
        "Latest transfer news:"
    )


# ─── Search Results ────────────────────────────────────────────────────────────
def format_search_results(query: str, results: list[dict]) -> str:
    if not results:
        return (
            f"🔍 *Search: _{query}_*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "😔 No results found. Try a different player or club name."
        )
    lines = [
        f"🔍 *Search: _{query}_*",
        "━━━━━━━━━━━━━━━━━━━",
        f"Found *{len(results)}* result(s):\n",
    ]
    for i, item in enumerate(results[:5], 1):
        rel_emoji = _reliability_emoji(item.get("reliability_label"))
        time_str = _time_ago(item.get("scraped_at"))
        lines.append(
            f"*{i}.* {rel_emoji} {item.get('title', 'No title')}\n"
            f"   📰 _{item.get('source', '?')}_ · ⏰ _{time_str}_"
        )
    return "\n".join(lines)


# ─── My Clubs / Subscriptions ──────────────────────────────────────────────────
def format_my_clubs(subs: list[dict]) -> str:
    if not subs:
        return (
            "⭐ *My Clubs*\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "You haven't subscribed to any clubs yet.\n\n"
            "Browse leagues to subscribe and get instant alerts!"
        )
    lines = ["⭐ *My Clubs*", "━━━━━━━━━━━━━━━━━━━", "Your subscribed clubs:\n"]
    for sub in subs:
        club_data = CLUBS.get(sub.get("club_id", ""), {})
        emoji = club_data.get("emoji", "🏟️")
        name = club_data.get("name", sub.get("club_id", "Unknown"))
        lines.append(f"{emoji} *{name}*")
    return "\n".join(lines)


# ─── Alert message ─────────────────────────────────────────────────────────────
def format_alert(item: dict) -> str:
    return (
        "🔔 *NEW TRANSFER ALERT*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        + format_news_item(item)
    )


# ─── Morning roundup ───────────────────────────────────────────────────────────
def format_morning_roundup(items: list[dict]) -> str:
    header = (
        "☀️ *MORNING TRANSFER ROUNDUP*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"Top stories this morning:\n\n"
    )
    if not items:
        return header + "📭 No major transfer news overnight. Stay tuned!"
    parts = [header]
    for item in items[:5]:
        rel_emoji = _reliability_emoji(item.get("reliability_label"))
        parts.append(
            f"{rel_emoji} *{item.get('title', 'No title')}*\n"
            f"   _{item.get('source', '?')} · {_time_ago(item.get('scraped_at'))}_\n"
        )
    return "\n".join(parts)


# ─── Evening recap ─────────────────────────────────────────────────────────────
def format_evening_recap(items: list[dict]) -> str:
    header = (
        "🌙 *EVENING TRANSFER RECAP*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Today's biggest transfer stories:\n\n"
    )
    if not items:
        return header + "📭 A quiet day on the transfer front."
    parts = [header]
    for item in items[:5]:
        rel_emoji = _reliability_emoji(item.get("reliability_label"))
        parts.append(
            f"{rel_emoji} *{item.get('title', 'No title')}*\n"
            f"   _{item.get('source', '?')}_\n"
        )
    return "\n".join(parts)


# ─── About ─────────────────────────────────────────────────────────────────────
def format_about() -> str:
    return (
        f"ℹ️ *About {BOT_NAME}*\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"{BOT_DESCRIPTION}\n\n"
        f"🤖 Version: `{BOT_VERSION}`\n"
        "📡 Sources: BBC Sport, Sky Sports, Goal.com, ESPN FC, Guardian, and more\n"
        "🧠 AI: Google Gemini 1.5 Flash\n"
        "⚡ Update frequency: Every 30 minutes\n\n"
        "🛠️ Commands:\n"
        "`/start` — Main menu\n"
        "`/search <query>` — Search transfers\n"
        "`/trending` — Trending now\n"
        "`/alerts` — Manage alerts\n"
        "`/myclubs` — My subscriptions\n"
        "`/about` — About this bot"
    )


# ─── Error message ─────────────────────────────────────────────────────────────
def format_error(details: str = "") -> str:
    msg = "⚠️ *Something went wrong.* Please try again in a moment."
    if details:
        msg += f"\n\n_Error: {details}_"
    return msg


# ─── Rate limit warning ────────────────────────────────────────────────────────
def format_rate_limit_warning() -> str:
    return (
        "🛑 *Slow down!*\n"
        "You're pressing buttons too quickly.\n"
        "Please wait a moment and try again. 😊"
    )
