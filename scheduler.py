"""
scheduler.py — TransferRadar AI
APScheduler AsyncIOScheduler with all 8 required background jobs.
All jobs have try/except, loguru logging, and 60-second timeouts.
"""

import asyncio
from datetime import datetime, timezone

import aiohttp
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from config import (
    SCRAPE_INTERVAL_MINUTES,
    TRENDING_UPDATE_INTERVAL_HOURS,
    SELF_PING_INTERVAL_MINUTES,
    FAKE_DETECT_INTERVAL_HOURS,
    JOB_TIMEOUT_SECONDS,
    RENDER_URL,
    ROUNDUP_TIMES,
    CLEAN_NEWS_DAYS,
)
from database import db

# Module-level scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")

# Will be set in run_scheduler() once the bot application is available
_bot_app = None


def set_bot_app(app) -> None:
    """Inject the PTB Application so scheduler jobs can send messages."""
    global _bot_app
    _bot_app = app


# ─── Job 1: Scrape all sources ─────────────────────────────────────────────────
async def scrape_all_sources() -> None:
    start = datetime.now(timezone.utc)
    logger.info("⏰ Job: scrape_all_sources — START")
    try:
        async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
            from services.rss_service import fetch_all_feeds
            from services.scraper_service import scrape_all
            from services.transfer_service import ingest_items

            rss_items, scraped_items = await asyncio.gather(
                fetch_all_feeds(), scrape_all(), return_exceptions=True
            )

            all_items: list[dict] = []
            if not isinstance(rss_items, Exception):
                all_items.extend(rss_items)
            if not isinstance(scraped_items, Exception):
                all_items.extend(scraped_items)

            inserted = await ingest_items(all_items)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            logger.info(
                f"✅ Job: scrape_all_sources — {inserted} new items in {elapsed:.1f}s"
            )
    except asyncio.TimeoutError:
        logger.error("❌ Job: scrape_all_sources — TIMEOUT")
    except Exception as e:
        logger.error(f"❌ Job: scrape_all_sources — ERROR: {e}")


# ─── Job 2: Update trending ────────────────────────────────────────────────────
async def update_trending() -> None:
    logger.info("⏰ Job: update_trending — START")
    try:
        async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
            from services.trending_service import update_trending as _update
            items = await db.get_latest_news(limit=100)
            await _update(items)
            logger.info("✅ Job: update_trending — DONE")
    except asyncio.TimeoutError:
        logger.error("❌ Job: update_trending — TIMEOUT")
    except Exception as e:
        logger.error(f"❌ Job: update_trending — ERROR: {e}")


# ─── Job 3 & 5: Morning / Evening broadcast ────────────────────────────────────
async def _broadcast_roundup(period: str) -> None:
    logger.info(f"⏰ Job: {period}_roundup — START")
    try:
        async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
            if _bot_app is None:
                logger.warning(f"Bot app not set, skipping {period} roundup")
                return

            items = await db.get_latest_news(limit=5)
            if not items:
                return

            from utils.formatters import format_morning_roundup, format_evening_recap
            if period == "morning":
                text = format_morning_roundup(items)
            else:
                text = format_evening_recap(items)

            users = await db.get_active_users()
            sent = 0
            for user in users:
                try:
                    await _bot_app.bot.send_message(
                        chat_id=user["user_id"],
                        text=text,
                        parse_mode="Markdown",
                    )
                    sent += 1
                    await asyncio.sleep(0.05)  # Telegram rate limit
                except Exception as e:
                    logger.warning(f"Could not send {period} roundup to {user['user_id']}: {e}")

            logger.info(f"✅ Job: {period}_roundup — sent to {sent} users")
    except asyncio.TimeoutError:
        logger.error(f"❌ Job: {period}_roundup — TIMEOUT")
    except Exception as e:
        logger.error(f"❌ Job: {period}_roundup — ERROR: {e}")


async def send_morning_roundup() -> None:
    await _broadcast_roundup("morning")


async def send_afternoon_breaking() -> None:
    """Send highest-reliability news at 13:00 UTC."""
    logger.info("⏰ Job: afternoon_breaking — START")
    try:
        async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
            if _bot_app is None:
                return
            from services.transfer_service import get_breaking_news
            items = await get_breaking_news(limit=3)
            if not items:
                return
            from utils.formatters import format_news_item
            texts = ["⚡ *AFTERNOON TRANSFER BULLETIN*\n━━━━━━━━━━━━━━━━━━━"]
            for item in items:
                texts.append(format_news_item(item))
            message = "\n\n".join(texts)

            users = await db.get_active_users()
            for user in users:
                try:
                    await _bot_app.bot.send_message(
                        chat_id=user["user_id"], text=message, parse_mode="Markdown"
                    )
                    await asyncio.sleep(0.05)
                except Exception:
                    pass
            logger.info("✅ Job: afternoon_breaking — DONE")
    except asyncio.TimeoutError:
        logger.error("❌ Job: afternoon_breaking — TIMEOUT")
    except Exception as e:
        logger.error(f"❌ Job: afternoon_breaking — ERROR: {e}")


async def send_evening_recap() -> None:
    await _broadcast_roundup("evening")


# ─── Job 6: Clean old news ─────────────────────────────────────────────────────
async def clean_old_news() -> None:
    logger.info("⏰ Job: clean_old_news — START")
    try:
        async with asyncio.timeout(30):
            deleted = await db.clean_old_news()
            logger.info(f"✅ Job: clean_old_news — deleted {deleted} old records")
    except Exception as e:
        logger.error(f"❌ Job: clean_old_news — ERROR: {e}")


# ─── Job 7: Self-ping keep-alive ───────────────────────────────────────────────
async def self_ping_keep_alive() -> None:
    logger.debug("⏰ Job: self_ping — pinging Render keep-alive URL")
    try:
        async with asyncio.timeout(15):
            async with aiohttp.ClientSession() as session:
                async with session.get(RENDER_URL, ssl=False) as resp:
                    status = resp.status
                    logger.debug(f"✅ Job: self_ping — HTTP {status}")
    except Exception as e:
        logger.warning(f"⚠️ Job: self_ping — {e}")


# ─── Job 8: Run fake detection batch ──────────────────────────────────────────
async def run_fake_detection_batch() -> None:
    logger.info("⏰ Job: fake_detection_batch — START")
    try:
        async with asyncio.timeout(JOB_TIMEOUT_SECONDS):
            items = await db.get_unanalyzed_news(limit=20)
            if not items:
                logger.info("✅ Job: fake_detection_batch — nothing to analyze")
                return

            from services.fake_detector import score_news_item
            analyzed = 0
            for item in items:
                try:
                    result = await score_news_item(
                        item["title"], item["source"] or "", item["summary"] or ""
                    )
                    await db.update_news_analysis(
                        news_id=item["id"],
                        score=result.get("reliability_score", 0),
                        label=result.get("reliability_label", "UNKNOWN"),
                        is_confirmed=result.get("reliability_label") == "CONFIRMED",
                    )
                    analyzed += 1
                    await asyncio.sleep(0.5)  # Rate limit Gemini API
                except Exception as e:
                    logger.warning(f"Fake detection failed for item {item['id']}: {e}")

            logger.info(f"✅ Job: fake_detection_batch — analyzed {analyzed}/{len(items)} items")
    except asyncio.TimeoutError:
        logger.error("❌ Job: fake_detection_batch — TIMEOUT")
    except Exception as e:
        logger.error(f"❌ Job: fake_detection_batch — ERROR: {e}")


# ─── Scheduler setup ───────────────────────────────────────────────────────────
def setup_scheduler() -> AsyncIOScheduler:
    """Register all 8 jobs and return the configured scheduler."""
    r = ROUNDUP_TIMES

    scheduler.add_job(
        scrape_all_sources, IntervalTrigger(minutes=SCRAPE_INTERVAL_MINUTES),
        id="scrape_all", replace_existing=True, max_instances=1,
    )
    scheduler.add_job(
        update_trending, IntervalTrigger(hours=TRENDING_UPDATE_INTERVAL_HOURS),
        id="update_trending", replace_existing=True, max_instances=1,
    )
    scheduler.add_job(
        send_morning_roundup,
        CronTrigger(hour=r["morning"]["hour"], minute=r["morning"]["minute"]),
        id="morning_roundup", replace_existing=True,
    )
    scheduler.add_job(
        send_afternoon_breaking,
        CronTrigger(hour=r["afternoon"]["hour"], minute=r["afternoon"]["minute"]),
        id="afternoon_breaking", replace_existing=True,
    )
    scheduler.add_job(
        send_evening_recap,
        CronTrigger(hour=r["evening"]["hour"], minute=r["evening"]["minute"]),
        id="evening_recap", replace_existing=True,
    )
    scheduler.add_job(
        clean_old_news,
        CronTrigger(hour=r["cleanup"]["hour"], minute=r["cleanup"]["minute"]),
        id="clean_news", replace_existing=True,
    )
    scheduler.add_job(
        self_ping_keep_alive, IntervalTrigger(minutes=SELF_PING_INTERVAL_MINUTES),
        id="self_ping", replace_existing=True, max_instances=1,
    )
    scheduler.add_job(
        run_fake_detection_batch, IntervalTrigger(hours=FAKE_DETECT_INTERVAL_HOURS),
        id="fake_detect", replace_existing=True, max_instances=1,
    )

    logger.info("📅 All 8 scheduler jobs registered")
    return scheduler


async def run_scheduler() -> None:
    """Start the scheduler and keep it alive."""
    setup_scheduler()
    scheduler.start()
    logger.info("🚀 Scheduler started")
    # Keep the coroutine alive
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        scheduler.shutdown(wait=False)
        logger.info("🛑 Scheduler shut down")
