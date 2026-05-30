"""
database.py — TransferRadar AI
Async SQLite manager using aiosqlite. Handles all 6 tables and CRUD operations.
"""

import asyncio
import hashlib
import os
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite
from loguru import logger

from config import DB_PATH, CLEAN_NEWS_DAYS

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# ─── Schema ────────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    language TEXT DEFAULT 'en',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    notifications_enabled BOOLEAN DEFAULT 1,
    alert_frequency TEXT DEFAULT 'all'
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    club_id TEXT,
    league_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT,
    source TEXT,
    url TEXT UNIQUE,
    player_name TEXT,
    club_name TEXT,
    league TEXT,
    reliability_score INTEGER DEFAULT 0,
    reliability_label TEXT,
    is_confirmed BOOLEAN DEFAULT 0,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hash TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS clubs (
    club_id TEXT PRIMARY KEY,
    name TEXT,
    league TEXT,
    emoji TEXT,
    twitter_handle TEXT
);

CREATE TABLE IF NOT EXISTS trending (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT UNIQUE,
    mention_count INTEGER DEFAULT 1,
    source_count INTEGER DEFAULT 1,
    trend_score REAL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    news_id INTEGER,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_news_scraped ON news(scraped_at);
CREATE INDEX IF NOT EXISTS idx_news_league ON news(league);
CREATE INDEX IF NOT EXISTS idx_news_club ON news(club_name);
CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_alerts_user ON alerts_log(user_id);
"""


# ─── Database Manager ──────────────────────────────────────────────────────────
class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
        await self._conn.execute("PRAGMA synchronous=NORMAL")
        await self._conn.executescript(SCHEMA_SQL)
        await self._conn.commit()
        logger.info(f"✅ Database connected: {self.db_path}")

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("🔒 Database connection closed")

    # ── Users ──────────────────────────────────────────────────────────────────
    async def upsert_user(self, user_id: int, username: str, first_name: str) -> None:
        async with self._lock:
            await self._conn.execute(
                """INSERT INTO users (user_id, username, first_name)
                   VALUES (?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                       username=excluded.username,
                       first_name=excluded.first_name,
                       is_active=1""",
                (user_id, username, first_name),
            )
            await self._conn.commit()

    async def get_user(self, user_id: int) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_active_users(self) -> list[dict]:
        async with self._conn.execute(
            "SELECT * FROM users WHERE is_active=1 AND notifications_enabled=1"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def toggle_notifications(self, user_id: int, enabled: bool) -> None:
        async with self._lock:
            await self._conn.execute(
                "UPDATE users SET notifications_enabled=? WHERE user_id=?",
                (1 if enabled else 0, user_id),
            )
            await self._conn.commit()

    # ── Subscriptions ──────────────────────────────────────────────────────────
    async def subscribe_club(self, user_id: int, club_id: str, league_id: str) -> bool:
        try:
            async with self._lock:
                await self._conn.execute(
                    "INSERT INTO subscriptions (user_id, club_id, league_id) VALUES (?,?,?)",
                    (user_id, club_id, league_id),
                )
                await self._conn.commit()
            return True
        except aiosqlite.IntegrityError:
            return False

    async def unsubscribe_club(self, user_id: int, club_id: str) -> bool:
        async with self._lock:
            cur = await self._conn.execute(
                "DELETE FROM subscriptions WHERE user_id=? AND club_id=?",
                (user_id, club_id),
            )
            await self._conn.commit()
            return cur.rowcount > 0

    async def get_user_subscriptions(self, user_id: int) -> list[dict]:
        async with self._conn.execute(
            "SELECT * FROM subscriptions WHERE user_id=?", (user_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def is_subscribed(self, user_id: int, club_id: str) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM subscriptions WHERE user_id=? AND club_id=?",
            (user_id, club_id),
        ) as cur:
            return await cur.fetchone() is not None

    async def get_subscribers_for_club(self, club_id: str) -> list[int]:
        async with self._conn.execute(
            """SELECT u.user_id FROM users u
               JOIN subscriptions s ON u.user_id=s.user_id
               WHERE s.club_id=? AND u.is_active=1 AND u.notifications_enabled=1""",
            (club_id,),
        ) as cur:
            rows = await cur.fetchall()
            return [r["user_id"] for r in rows]

    # ── News ───────────────────────────────────────────────────────────────────
    async def insert_news(self, item: dict) -> Optional[int]:
        try:
            async with self._lock:
                cur = await self._conn.execute(
                    """INSERT INTO news
                       (title, summary, source, url, player_name, club_name,
                        league, reliability_score, reliability_label, is_confirmed, hash)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        item.get("title"),
                        item.get("summary"),
                        item.get("source"),
                        item.get("url"),
                        item.get("player_name"),
                        item.get("club_name"),
                        item.get("league"),
                        item.get("reliability_score", 0),
                        item.get("reliability_label"),
                        item.get("is_confirmed", 0),
                        item.get("hash"),
                    ),
                )
                await self._conn.commit()
                return cur.lastrowid
        except aiosqlite.IntegrityError:
            return None  # Duplicate

    async def update_news_analysis(
        self, news_id: int, score: int, label: str, is_confirmed: bool
    ) -> None:
        async with self._lock:
            await self._conn.execute(
                """UPDATE news SET reliability_score=?, reliability_label=?,
                   is_confirmed=? WHERE id=?""",
                (score, label, 1 if is_confirmed else 0, news_id),
            )
            await self._conn.commit()

    async def get_latest_news(
        self, limit: int = 10, league: Optional[str] = None, club: Optional[str] = None
    ) -> list[dict]:
        sql = "SELECT * FROM news WHERE 1=1"
        params: list[Any] = []
        if league:
            sql += " AND league=?"
            params.append(league)
        if club:
            sql += " AND club_name LIKE ?"
            params.append(f"%{club}%")
        sql += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)
        async with self._conn.execute(sql, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_unanalyzed_news(self, limit: int = 20) -> list[dict]:
        async with self._conn.execute(
            """SELECT * FROM news WHERE reliability_score=0
               ORDER BY scraped_at DESC LIMIT ?""",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_news_by_id(self, news_id: int) -> Optional[dict]:
        async with self._conn.execute(
            "SELECT * FROM news WHERE id=?", (news_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def search_news(self, query: str, limit: int = 10) -> list[dict]:
        pattern = f"%{query}%"
        async with self._conn.execute(
            """SELECT * FROM news WHERE title LIKE ? OR player_name LIKE ?
               OR club_name LIKE ? OR summary LIKE ?
               ORDER BY scraped_at DESC LIMIT ?""",
            (pattern, pattern, pattern, pattern, limit),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_news_count_for_club(self, club_name: str) -> dict:
        async with self._conn.execute(
            "SELECT COUNT(*) as total FROM news WHERE club_name LIKE ?",
            (f"%{club_name}%",),
        ) as cur:
            total_row = await cur.fetchone()
        async with self._conn.execute(
            "SELECT COUNT(*) as confirmed FROM news WHERE club_name LIKE ? AND is_confirmed=1",
            (f"%{club_name}%",),
        ) as cur:
            conf_row = await cur.fetchone()
        return {
            "total": total_row["total"] if total_row else 0,
            "confirmed": conf_row["confirmed"] if conf_row else 0,
        }

    async def clean_old_news(self) -> int:
        async with self._lock:
            cur = await self._conn.execute(
                f"DELETE FROM news WHERE scraped_at < datetime('now', '-{CLEAN_NEWS_DAYS} days')"
            )
            await self._conn.commit()
            return cur.rowcount

    # ── Trending ───────────────────────────────────────────────────────────────
    async def upsert_trending(self, topic: str, score: float) -> None:
        async with self._lock:
            await self._conn.execute(
                """INSERT INTO trending (topic, mention_count, source_count, trend_score, last_updated)
                   VALUES (?, 1, 1, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(topic) DO UPDATE SET
                       mention_count=mention_count+1,
                       trend_score=excluded.trend_score,
                       last_updated=CURRENT_TIMESTAMP""",
                (topic, score),
            )
            await self._conn.commit()

    async def get_trending(self, limit: int = 10) -> list[dict]:
        async with self._conn.execute(
            """SELECT * FROM trending
               ORDER BY trend_score DESC, mention_count DESC
               LIMIT ?""",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def clean_old_trending(self) -> None:
        async with self._lock:
            await self._conn.execute(
                "DELETE FROM trending WHERE last_updated < datetime('now', '-1 day')"
            )
            await self._conn.commit()

    # ── Alerts log ─────────────────────────────────────────────────────────────
    async def log_alert(self, user_id: int, news_id: int) -> None:
        async with self._lock:
            await self._conn.execute(
                "INSERT INTO alerts_log (user_id, news_id) VALUES (?,?)",
                (user_id, news_id),
            )
            await self._conn.commit()

    async def was_alert_sent(self, user_id: int, news_id: int) -> bool:
        async with self._conn.execute(
            "SELECT 1 FROM alerts_log WHERE user_id=? AND news_id=?",
            (user_id, news_id),
        ) as cur:
            return await cur.fetchone() is not None

    # ── Clubs ──────────────────────────────────────────────────────────────────
    async def seed_clubs(self, clubs_data: dict) -> None:
        async with self._lock:
            for club_id, data in clubs_data.items():
                await self._conn.execute(
                    """INSERT INTO clubs (club_id, name, league, emoji, twitter_handle)
                       VALUES (?,?,?,?,?)
                       ON CONFLICT(club_id) DO NOTHING""",
                    (
                        club_id,
                        data["name"],
                        data["league"],
                        data["emoji"],
                        data.get("twitter", ""),
                    ),
                )
            await self._conn.commit()


# ─── Module-level singleton ────────────────────────────────────────────────────
db = Database()
