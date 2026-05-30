"""
check_imports.py — TransferRadar AI
Quick import validation script. Run AFTER pip install -r requirements.txt.
Verifies all third-party packages and internal modules load correctly.
"""
import sys

failures = []

def check(label, fn):
    try:
        fn()
        print(f"  ✅ {label}")
    except Exception as e:
        print(f"  ❌ {label}: {e}")
        failures.append(label)

print("\n── Third-party packages ──────────────────────────────")
check("python-telegram-bot",    lambda: __import__("telegram"))
check("google-generativeai",    lambda: __import__("google.generativeai"))
check("aiohttp",                lambda: __import__("aiohttp"))
check("httpx",                  lambda: __import__("httpx"))
check("beautifulsoup4",         lambda: __import__("bs4"))
check("lxml",                   lambda: __import__("lxml"))
check("feedparser",             lambda: __import__("feedparser"))
check("APScheduler",            lambda: __import__("apscheduler"))
check("aiosqlite",              lambda: __import__("aiosqlite"))
check("python-dotenv",          lambda: __import__("dotenv"))
check("loguru",                 lambda: __import__("loguru"))
check("fastapi",                lambda: __import__("fastapi"))
check("uvicorn",                lambda: __import__("uvicorn"))
check("gunicorn",               lambda: __import__("gunicorn"))

print("\n── Internal modules ──────────────────────────────────")
check("config",                 lambda: __import__("config"))
check("database",               lambda: __import__("database"))
check("keep_alive",             lambda: __import__("keep_alive"))
check("scheduler",              lambda: __import__("scheduler"))
check("utils.cache",            lambda: __import__("utils.cache"))
check("utils.rate_limiter",     lambda: __import__("utils.rate_limiter"))
check("utils.retry",            lambda: __import__("utils.retry"))
check("utils.formatters",       lambda: __import__("utils.formatters"))
check("services.fake_detector", lambda: __import__("services.fake_detector"))
check("services.rss_service",   lambda: __import__("services.rss_service"))
check("services.scraper_service",lambda: __import__("services.scraper_service"))
check("services.transfer_service",lambda: __import__("services.transfer_service"))
check("services.trending_service",lambda: __import__("services.trending_service"))
check("handlers.start_handler", lambda: __import__("handlers.start_handler"))
check("handlers.trending_handler",lambda: __import__("handlers.trending_handler"))
check("handlers.leagues_handler",lambda: __import__("handlers.leagues_handler"))
check("handlers.search_handler",lambda: __import__("handlers.search_handler"))
check("handlers.alerts_handler",lambda: __import__("handlers.alerts_handler"))
check("handlers.callback_handler",lambda: __import__("handlers.callback_handler"))

print("\n" + "─" * 54)
if failures:
    print(f"❌ {len(failures)} failure(s): {', '.join(failures)}")
    sys.exit(1)
else:
    print(f"✅ All imports OK — TransferRadar AI is ready to run!")
