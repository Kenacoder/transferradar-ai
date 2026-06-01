"""
services/transfer_service.py — TransferRadar AI
Data access layer: orchestrates DB queries and cache lookups for handlers.
"""

from typing import Optional

from loguru import logger

from config import CLUBS, LEAGUES, PAGE_SIZE
from database import db
from utils.cache import cache


# ─── Latest news (cached) ──────────────────────────────────────────────────────
async def get_latest_news(
    limit: int = PAGE_SIZE,
    league: Optional[str] = None,
    club: Optional[str] = None,
) -> list[dict]:
    cache_key = f"news:{league}:{club}:{limit}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    items = await db.get_latest_news(limit=limit, league=league, club=club)
    await cache.set(cache_key, items)
    return items


# ─── Club-specific news ────────────────────────────────────────────────────────
async def get_club_news(club_id: str, limit: int = PAGE_SIZE) -> list[dict]:
    club_data = CLUBS.get(club_id)
    if not club_data:
        return []
    return await get_latest_news(limit=limit, club=club_data["name"])


# ─── Club stats ────────────────────────────────────────────────────────────────
async def get_club_stats(club_id: str) -> dict:
    cache_key = f"club_stats:{club_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    club_data = CLUBS.get(club_id)
    if not club_data:
        return {"total": 0, "confirmed": 0}
    counts = await db.get_news_count_for_club(club_data["name"])
    await cache.set(cache_key, counts)
    return counts


# ─── League clubs list ─────────────────────────────────────────────────────────
def get_clubs_for_league(league_id: str) -> list[tuple[str, dict]]:
    """Return (club_id, club_data) pairs for a given league."""
    return [
        (cid, cdata)
        for cid, cdata in CLUBS.items()
        if cdata["league"] == league_id
    ]


# ─── Search ────────────────────────────────────────────────────────────────────
async def search_transfers(query: str, limit: int = 10) -> list[dict]:
    if len(query) < 2:
        return []
    cache_key = f"search:{query.lower()}:{limit}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    results = await db.search_news(query, limit=limit)
    await cache.set(cache_key, results)
    return results


# ─── Single news item ──────────────────────────────────────────────────────────
async def get_news_item(news_id: int) -> Optional[dict]:
    cache_key = f"news_item:{news_id}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    item = await db.get_news_by_id(news_id)
    if item:
        await cache.set(cache_key, item)
    return item


# ─── Breaking news (high-reliability recent items) ────────────────────────────
async def get_breaking_news(limit: int = 5) -> list[dict]:
    cache_key = f"breaking:{limit}"
    cached = await cache.get(cache_key)
    if cached is not None:
        return cached
    all_items = await db.get_latest_news(limit=50)
    breaking = [
        i for i in all_items
        if (i.get("reliability_score") or 0) >= 70 or i.get("is_confirmed") == 1
    ]
    if not breaking and all_items:
        breaking = all_items[:limit]
    else:
        breaking = breaking[:limit]
    await cache.set(cache_key, breaking)
    return breaking


# ─── Ingest pipeline: save + trigger analysis ─────────────────────────────────
async def ingest_items(items: list[dict]) -> int:
    """
    Save new items to DB. Returns count of newly inserted items.
    """
    inserted = 0
    for item in items:
        news_id = await db.insert_news(item)
        if news_id:
            inserted += 1
    logger.info(f"💾 Ingested {inserted}/{len(items)} new items")
    return inserted


# ─── Subscription helpers ──────────────────────────────────────────────────────
async def subscribe(user_id: int, club_id: str) -> bool:
    club_data = CLUBS.get(club_id)
    if not club_data:
        return False
    league_id = club_data["league"]
    return await db.subscribe_club(user_id, club_id, league_id)


async def unsubscribe(user_id: int, club_id: str) -> bool:
    return await db.unsubscribe_club(user_id, club_id)


async def get_subscriptions(user_id: int) -> list[dict]:
    return await db.get_user_subscriptions(user_id)


async def is_subscribed(user_id: int, club_id: str) -> bool:
    return await db.is_subscribed(user_id, club_id)
