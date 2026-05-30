"""
services/scraper_service.py — TransferRadar AI
Multi-source async web scraper as backup to RSS feeds.
Targets structured football news pages using aiohttp + BeautifulSoup.
"""

import asyncio
import hashlib
import re
from typing import Optional

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger

from utils.retry import async_retry

# Scrape targets: (name, url, article_selector, title_selector, summary_selector)
SCRAPE_TARGETS = [
    {
        "name": "Transfermarkt",
        "url": "https://www.transfermarkt.com/transfers/neuestetransfers/transfers",
        "item_sel": "table.items tbody tr",
        "title_sel": "td.hauptlink a",
        "summary_sel": None,
    },
    {
        "name": "90min",
        "url": "https://www.90min.com/transfer-news",
        "item_sel": "article",
        "title_sel": "h3",
        "summary_sel": "p",
    },
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _make_hash(title: str, source: str) -> str:
    payload = f"{title.strip().lower()}::{source.lower()}"
    return hashlib.sha256(payload.encode()).hexdigest()


@async_retry(retries=2, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
async def _scrape_target(
    session: aiohttp.ClientSession, target: dict
) -> list[dict]:
    """Scrape a single target page and extract article stubs."""
    name = target["name"]
    url = target["url"]
    timeout = aiohttp.ClientTimeout(total=25)
    try:
        async with session.get(url, timeout=timeout, ssl=False) as resp:
            if resp.status != 200:
                logger.warning(f"⚠️ Scraper [{name}]: HTTP {resp.status}")
                return []
            html = await resp.text(errors="replace")

        soup = BeautifulSoup(html, "lxml")
        items_raw = soup.select(target["item_sel"])
        results: list[dict] = []

        for el in items_raw[:15]:
            title_el = el.select_one(target["title_sel"]) if target["title_sel"] else None
            title = title_el.get_text(strip=True) if title_el else ""
            if not title or len(title) < 10:
                continue

            summary = ""
            if target.get("summary_sel"):
                summary_el = el.select_one(target["summary_sel"])
                summary = summary_el.get_text(strip=True)[:300] if summary_el else ""

            link_el = el.select_one("a[href]")
            link = ""
            if link_el:
                href = link_el.get("href", "")
                link = href if href.startswith("http") else f"https://{name.lower()}.com{href}"

            results.append({
                "title": title,
                "summary": summary,
                "source": name,
                "url": link or url,
                "player_name": None,
                "club_name": None,
                "league": None,
                "hash": _make_hash(title, name),
                "reliability_score": 0,
                "reliability_label": None,
                "is_confirmed": 0,
            })

        logger.debug(f"🕷️ [{name}] Scraped {len(results)} articles")
        return results

    except Exception as e:
        logger.warning(f"⚠️ Scraper error [{name}]: {e}")
        return []


async def scrape_all() -> list[dict]:
    """Run all scrapers concurrently and return deduplicated results."""
    connector = aiohttp.TCPConnector(limit=5, ssl=False)
    seen: set[str] = set()
    all_items: list[dict] = []

    async with aiohttp.ClientSession(connector=connector, headers=HEADERS) as session:
        tasks = [_scrape_target(session, t) for t in SCRAPE_TARGETS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            continue
        for item in result:
            h = item.get("hash", "")
            if h and h not in seen:
                seen.add(h)
                all_items.append(item)

    logger.info(f"✅ Scraping complete: {len(all_items)} unique items")
    return all_items
