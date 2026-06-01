"""
services/trending_service.py — TransferRadar AI
Trending algorithm: scores topics based on mention frequency + source diversity + recency.
"""

import asyncio
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from config import CLUBS
from database import db

# Build known entity set for fast matching
_KNOWN_NAMES: list[str] = [v["name"] for v in CLUBS.values()]


def _extract_topics(items: list[dict]) -> list[str]:
    """
    Extract trending topics (player/club name combos) from a list of news items.
    """
    topics: list[str] = []
    for item in items:
        player = item.get("player_name")
        club = item.get("club_name")
        if player and club:
            topics.append(f"{player} → {club}")
        elif player:
            topics.append(player)
        elif club:
            topics.append(club)
        else:
            # Fallback: extract from title using club names
            title = item.get("title", "")
            for name in _KNOWN_NAMES:
                if name.lower() in title.lower():
                    topics.append(name)
                    break
    return topics


def _compute_trend_score(
    mention_count: int, source_count: int, recency_hours: float
) -> float:
    """
    Trend score = mentions × source_diversity_bonus / recency_decay
    """
    source_bonus = 1.0 + (source_count * 0.25)
    recency_decay = max(1.0, recency_hours * 0.5)
    return round((mention_count * source_bonus) / recency_decay, 4)


async def update_trending(items: list[dict]) -> None:
    """
    Recompute trending topics from freshly scraped news items
    and persist them to the database.
    """
    topics = _extract_topics(items)
    if not topics:
        logger.info("📊 Trending: no topics extracted")
        return

    # Count mentions per topic
    mention_map: dict[str, int] = defaultdict(int)
    source_map: dict[str, set] = defaultdict(set)

    for item, topic in zip(items, topics):
        mention_map[topic] += 1
        source_map[topic].add(item.get("source", "unknown"))

    # Upsert each trending topic
    for topic, count in mention_map.items():
        score = _compute_trend_score(count, len(source_map[topic]), recency_hours=1.0)
        await db.upsert_trending(topic, score)

    # Clean yesterday's stale entries
    await db.clean_old_trending()
    logger.info(f"🔥 Trending updated: {len(mention_map)} topics")


async def get_trending_topics(limit: int = 10) -> list[dict]:
    """Return top trending topics from DB."""
    topics = await db.get_trending(limit=limit)
    if not topics:
        latest = await db.get_latest_news(limit=100)
        if latest:
            await update_trending(latest)
            topics = await db.get_trending(limit=limit)
    return topics
