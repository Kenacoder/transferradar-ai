"""
services/rss_service.py — TransferRadar AI
Async RSS feed aggregator with deduplication, HTML cleaning, and entity extraction.
"""

import asyncio
import hashlib
import html
import re
from typing import Optional

import aiohttp
import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from config import RSS_FEEDS, CLUBS
from utils.retry import async_retry

# Build a flat set of club names for entity matching
_CLUB_NAMES: list[str] = [v["name"].lower() for v in CLUBS.values()]
_CLUB_ID_MAP: dict[str, str] = {
    v["name"].lower(): k for k, v in CLUBS.items()
}

# Common player-role keywords to help detect player names (NER heuristic)
_TRANSFER_VERBS = [
    "signs", "joins", "moves", "transfers", "agrees", "completes",
    "seals", "set to join", "close to", "nears", "heading to",
]


def _clean_html(raw: str) -> str:
    """Strip HTML tags and decode entities from a string."""
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    text = soup.get_text(separator=" ")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]  # cap summary length


def _make_hash(title: str, source: str) -> str:
    """SHA-256 hash for deduplication based on title + source."""
    payload = f"{title.strip().lower()}::{source.lower()}"
    return hashlib.sha256(payload.encode()).hexdigest()


def _extract_club(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Return (club_name, league) by scanning text for known club names.
    Returns the first match found.
    """
    lower = text.lower()
    for club_name in _CLUB_NAMES:
        if club_name in lower:
            club_id = _CLUB_ID_MAP.get(club_name)
            if club_id:
                from config import CLUBS as C, LEAGUES
                league_id = C[club_id]["league"]
                league_name = LEAGUES.get(league_id, {}).get("name", league_id)
                return C[club_id]["name"], league_name
    return None, None


def _extract_player(title: str) -> Optional[str]:
    """
    Simple heuristic: look for a capitalised two-word name before a transfer verb.
    E.g. "Kylian Mbappé signs for Real Madrid" → "Kylian Mbappé"
    """
    for verb in _TRANSFER_VERBS:
        idx = title.lower().find(verb)
        if idx > 2:
            candidate = title[:idx].strip()
            # Take the last 1-3 capitalised words as likely player name
            words = candidate.split()
            name_words = [w for w in words[-3:] if w and w[0].isupper()]
            if 1 <= len(name_words) <= 3:
                return " ".join(name_words)
    return None


@async_retry(retries=2, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
async def _fetch_feed(
    session: aiohttp.ClientSession, name: str, url: str
) -> list[dict]:
    """Fetch and parse a single RSS feed. Returns a list of raw item dicts."""
    timeout = aiohttp.ClientTimeout(total=20)
    try:
        async with session.get(url, timeout=timeout, ssl=False) as resp:
            content = await resp.read()
        feed = feedparser.parse(content)
        items = []
        for entry in feed.entries[:20]:  # cap at 20 per feed
            title = _clean_html(getattr(entry, "title", ""))
            summary = _clean_html(
                getattr(entry, "summary", "")
                or getattr(entry, "description", "")
            )
            url_link = getattr(entry, "link", "")
            if not title or not url_link:
                continue
            club_name, league = _extract_club(f"{title} {summary}")
            player_name = _extract_player(title)
            news_hash = _make_hash(title, name)
            items.append({
                "title": title,
                "summary": summary,
                "source": name,
                "url": url_link,
                "player_name": player_name,
                "club_name": club_name,
                "league": league,
                "hash": news_hash,
                "reliability_score": 0,
                "reliability_label": None,
                "is_confirmed": 0,
            })
        logger.debug(f"📡 [{name}] Fetched {len(items)} items")
        return items
    except Exception as e:
        logger.warning(f"⚠️ RSS fetch failed [{name}]: {e}")
        return []


async def fetch_all_feeds() -> list[dict]:
    """
    Fetch all RSS feeds concurrently and return a deduplicated list of items.
    """
    connector = aiohttp.TCPConnector(limit=10, ssl=False)
    headers = {"User-Agent": "TransferRadarBot/1.0 (+https://transferradar.ai)"}
    seen_hashes: set[str] = set()
    results: list[dict] = []

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [
            _fetch_feed(session, name, url)
            for name, url in RSS_FEEDS.items()
        ]
        feeds = await asyncio.gather(*tasks, return_exceptions=True)

    for feed_items in feeds:
        if isinstance(feed_items, Exception):
            continue
        for item in feed_items:
            h = item.get("hash", "")
            if h and h not in seen_hashes:
                seen_hashes.add(h)
                results.append(item)

    logger.info(f"✅ RSS aggregation complete: {len(results)} unique items")
    return results
