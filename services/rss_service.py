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

from utils.extractor import extract_club, extract_player, compute_rule_based_score


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
            
            # Smart immediate local extraction
            club_name, league = extract_club(f"{title} {summary}")
            player_name = extract_player(title)
            
            # Immediately calculate default rule-based score so it's never 0%
            score_data = compute_rule_based_score(title, name, summary)
            
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
                "reliability_score": score_data["reliability_score"],
                "reliability_label": score_data["reliability_label"],
                "is_confirmed": score_data["is_confirmed"],
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
