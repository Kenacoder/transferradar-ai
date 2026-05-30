"""
config.py — TransferRadar AI
All constants, league/club data, RSS feeds, and global configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Credentials ───────────────────────────────────────────────────────────────
TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
RENDER_URL: str = os.getenv("RENDER_URL", "http://localhost:8080")

# ─── Server ────────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8080"))
HOST: str = "0.0.0.0"

# ─── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = "data/transferradar.db"

# ─── Scheduler timings ────────────────────────────────────────────────────────
SCRAPE_INTERVAL_MINUTES: int = 30
TRENDING_UPDATE_INTERVAL_HOURS: int = 1
SELF_PING_INTERVAL_MINUTES: int = 10
FAKE_DETECT_INTERVAL_HOURS: int = 2
CLEAN_NEWS_DAYS: int = 7

# ─── Rate limiting ─────────────────────────────────────────────────────────────
RATE_LIMIT_ACTIONS: int = 10          # max button presses
RATE_LIMIT_WINDOW_SECONDS: int = 10   # per this many seconds
SEARCH_RATE_LIMIT: int = 5            # max searches
SEARCH_RATE_WINDOW_SECONDS: int = 60  # per this many seconds

# ─── Cache ─────────────────────────────────────────────────────────────────────
CACHE_MAX_SIZE: int = 256
CACHE_TTL_SECONDS: int = 300  # 5 minutes

# ─── Retry ─────────────────────────────────────────────────────────────────────
MAX_RETRIES: int = 3
RETRY_BASE_DELAY: float = 1.0  # seconds

# ─── Job timeouts ──────────────────────────────────────────────────────────────
JOB_TIMEOUT_SECONDS: int = 600

# ─── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-pro"
GEMINI_MAX_TOKENS: int = 512

# ─── RSS Feeds ─────────────────────────────────────────────────────────────────
RSS_FEEDS: dict[str, str] = {
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "Sky Sports": "https://www.skysports.com/rss/12040",
    "Goal.com": "https://www.goal.com/feeds/en/news",
    "ESPN FC": "https://www.espn.com/espn/rss/soccer/news",
    "The Guardian Football": "https://www.theguardian.com/football/rss",
    "Football Italia": "https://www.football-italia.net/rss.xml",
    "Transfermarkt News": "https://www.transfermarkt.com/rss/transfer-news/ajax",
    "UEFA News": "https://www.uefa.com/rssfeed/news/",
    "AS.com": "https://en.as.com/rss/news/",
    "Marca": "https://e00-marca.uecdn.es/rss/futbol/primera-division.xml",
}

# ─── Leagues ───────────────────────────────────────────────────────────────────
LEAGUES: dict[str, dict] = {
    "premier_league": {
        "name": "Premier League",
        "emoji": "🏴",
        "country": "England",
    },
    "la_liga": {
        "name": "La Liga",
        "emoji": "🇪🇸",
        "country": "Spain",
    },
    "serie_a": {
        "name": "Serie A",
        "emoji": "🇮🇹",
        "country": "Italy",
    },
    "bundesliga": {
        "name": "Bundesliga",
        "emoji": "🇩🇪",
        "country": "Germany",
    },
    "ligue_1": {
        "name": "Ligue 1",
        "emoji": "🇫🇷",
        "country": "France",
    },
}

# ─── Clubs ─────────────────────────────────────────────────────────────────────
CLUBS: dict[str, dict] = {
    # Premier League
    "man_city": {"name": "Manchester City", "league": "premier_league", "emoji": "🔵", "twitter": "ManCity"},
    "man_utd": {"name": "Manchester United", "league": "premier_league", "emoji": "🔴", "twitter": "ManUtd"},
    "arsenal": {"name": "Arsenal", "league": "premier_league", "emoji": "❤️", "twitter": "Arsenal"},
    "chelsea": {"name": "Chelsea", "league": "premier_league", "emoji": "💙", "twitter": "ChelseaFC"},
    "liverpool": {"name": "Liverpool", "league": "premier_league", "emoji": "🔴", "twitter": "LFC"},
    "tottenham": {"name": "Tottenham Hotspur", "league": "premier_league", "emoji": "⚪", "twitter": "SpursOfficial"},
    "newcastle": {"name": "Newcastle United", "league": "premier_league", "emoji": "⚫", "twitter": "NUFC"},
    "aston_villa": {"name": "Aston Villa", "league": "premier_league", "emoji": "🟣", "twitter": "AVFCOfficial"},
    "brighton": {"name": "Brighton & Hove Albion", "league": "premier_league", "emoji": "💙", "twitter": "OfficialBHAFC"},
    "west_ham": {"name": "West Ham United", "league": "premier_league", "emoji": "🫧", "twitter": "WestHam"},
    # La Liga
    "real_madrid": {"name": "Real Madrid", "league": "la_liga", "emoji": "⚪", "twitter": "realmadrid"},
    "barcelona": {"name": "FC Barcelona", "league": "la_liga", "emoji": "🔵🔴", "twitter": "FCBarcelona"},
    "atletico_madrid": {"name": "Atlético Madrid", "league": "la_liga", "emoji": "🔴⚪", "twitter": "atletienglish"},
    "sevilla": {"name": "Sevilla FC", "league": "la_liga", "emoji": "⚪🔴", "twitter": "SevillaFC_ENG"},
    "real_sociedad": {"name": "Real Sociedad", "league": "la_liga", "emoji": "🔵⚪", "twitter": "RealSociedad"},
    "villarreal": {"name": "Villarreal CF", "league": "la_liga", "emoji": "🟡", "twitter": "VillarrealCFen"},
    "real_betis": {"name": "Real Betis", "league": "la_liga", "emoji": "🟢⚪", "twitter": "RealBetis_en"},
    "athletic_bilbao": {"name": "Athletic Club", "league": "la_liga", "emoji": "🔴⚪", "twitter": "Athletic_en"},
    "valencia": {"name": "Valencia CF", "league": "la_liga", "emoji": "🦇", "twitter": "valenciacf_en"},
    "osasuna": {"name": "CA Osasuna", "league": "la_liga", "emoji": "🔴", "twitter": "CAOsasuna"},
    # Serie A
    "juventus": {"name": "Juventus", "league": "serie_a", "emoji": "⚫⚪", "twitter": "juventusfcen"},
    "inter_milan": {"name": "Inter Milan", "league": "serie_a", "emoji": "🔵⚫", "twitter": "Inter_en"},
    "ac_milan": {"name": "AC Milan", "league": "serie_a", "emoji": "🔴⚫", "twitter": "ACMilan"},
    "napoli": {"name": "SSC Napoli", "league": "serie_a", "emoji": "🔵", "twitter": "en_sscnapoli"},
    "roma": {"name": "AS Roma", "league": "serie_a", "emoji": "🟡🔴", "twitter": "ASRomaEN"},
    "lazio": {"name": "SS Lazio", "league": "serie_a", "emoji": "🔵⚪", "twitter": "OfficialSSLazio"},
    "fiorentina": {"name": "ACF Fiorentina", "league": "serie_a", "emoji": "💜", "twitter": "ACFFiorentinaEN"},
    "atalanta": {"name": "Atalanta BC", "league": "serie_a", "emoji": "⚫🔵", "twitter": "Atalanta_BC"},
    "torino": {"name": "Torino FC", "league": "serie_a", "emoji": "🟤", "twitter": "TorinoFC_1906"},
    "bologna": {"name": "Bologna FC", "league": "serie_a", "emoji": "🔵🔴", "twitter": "BolognaFC1909en"},
    # Bundesliga
    "bayern": {"name": "Bayern Munich", "league": "bundesliga", "emoji": "🔴", "twitter": "FCBayernEN"},
    "dortmund": {"name": "Borussia Dortmund", "league": "bundesliga", "emoji": "🟡⚫", "twitter": "BVB"},
    "rb_leipzig": {"name": "RB Leipzig", "league": "bundesliga", "emoji": "🔴⚪", "twitter": "RBLeipzig_EN"},
    "leverkusen": {"name": "Bayer Leverkusen", "league": "bundesliga", "emoji": "🔴⚫", "twitter": "bayer04_en"},
    "frankfurt": {"name": "Eintracht Frankfurt", "league": "bundesliga", "emoji": "⚫🔴", "twitter": "eintracht"},
    "wolfsburg": {"name": "VfL Wolfsburg", "league": "bundesliga", "emoji": "🟢⚪", "twitter": "VfLWolfsburg_EN"},
    "m_gladbach": {"name": "Borussia Mönchengladbach", "league": "bundesliga", "emoji": "⚪🟢", "twitter": "borussia_en"},
    "union_berlin": {"name": "1. FC Union Berlin", "league": "bundesliga", "emoji": "🔴", "twitter": "fcunion_en"},
    "freiburg": {"name": "SC Freiburg", "league": "bundesliga", "emoji": "🔴⚫", "twitter": "scfreiburg"},
    "hoffenheim": {"name": "TSG Hoffenheim", "league": "bundesliga", "emoji": "🔵", "twitter": "tsghoffenheim"},
    # Ligue 1
    "psg": {"name": "Paris Saint-Germain", "league": "ligue_1", "emoji": "🔵🔴", "twitter": "PSG_English"},
    "marseille": {"name": "Olympique Marseille", "league": "ligue_1", "emoji": "🔵⚪", "twitter": "OM_English"},
    "lyon": {"name": "Olympique Lyonnais", "league": "ligue_1", "emoji": "🔴⚪", "twitter": "OL"},
    "monaco": {"name": "AS Monaco", "league": "ligue_1", "emoji": "🔴⚪", "twitter": "AS_Monaco"},
    "lille": {"name": "LOSC Lille", "league": "ligue_1", "emoji": "🔴⚫", "twitter": "LOSC_EN"},
    "rennes": {"name": "Stade Rennais FC", "league": "ligue_1", "emoji": "🔴⚫", "twitter": "staderennais"},
    "lens": {"name": "RC Lens", "league": "ligue_1", "emoji": "🟡🔴", "twitter": "RCLens"},
    "nice": {"name": "OGC Nice", "league": "ligue_1", "emoji": "🔴⚫", "twitter": "ogcnice"},
    "strasbourg": {"name": "RC Strasbourg", "league": "ligue_1", "emoji": "🔵⚪", "twitter": "rcstrasbourg"},
    "montpellier": {"name": "Montpellier HSC", "league": "ligue_1", "emoji": "🟠⚫", "twitter": "MontpellierHSC"},
}

# ─── Trusted journalists / sources (for fake detection scoring) ───────────────
TRUSTED_SOURCES: dict[str, int] = {
    "fabrizio romano": 30,
    "sky sports": 25,
    "bbc": 20,
    "bbc sport": 20,
    "the guardian": 18,
    "espn": 15,
    "goal.com": 12,
    "football italia": 10,
    "marca": 10,
    "as.com": 10,
    "david ornstein": 25,
    "florian plettenberg": 20,
    "here we go": 15,
}

UNTRUSTED_MARKERS: dict[str, int] = {
    "anonymous source": -20,
    "twitter rumor": -30,
    "unverified": -15,
    "according to fans": -25,
    "exclusive leak": -10,
}

POSITIVE_KEYWORDS: dict[str, int] = {
    "here we go": 15,
    "loan": 10,
    "bid submitted": 10,
    "medical": 10,
    "signed": 12,
    "confirmed": 12,
    "official": 12,
    "agreement reached": 10,
    "personal terms": 8,
    "fee agreed": 10,
}

# ─── Reliability labels ────────────────────────────────────────────────────────
RELIABILITY_LABELS: list[str] = [
    "FAKE RUMOR",
    "LOW RELIABILITY",
    "POSSIBLE",
    "HIGHLY RELIABLE",
    "CONFIRMED",
]

# ─── Bot metadata ──────────────────────────────────────────────────────────────
BOT_NAME: str = "TransferRadar AI"
BOT_VERSION: str = "1.0.0"
BOT_DESCRIPTION: str = (
    "Your 24/7 football transfer intelligence platform. "
    "Powered by AI to deliver real-time transfer news, rumour analysis, "
    "and credibility scoring across the top 5 European leagues."
)

# ─── Morning/Afternoon/Evening roundup times (UTC) ────────────────────────────
ROUNDUP_TIMES: dict[str, dict] = {
    "morning": {"hour": 8, "minute": 0},
    "afternoon": {"hour": 13, "minute": 0},
    "evening": {"hour": 19, "minute": 0},
    "cleanup": {"hour": 2, "minute": 0},
}

# ─── Pagination ────────────────────────────────────────────────────────────────
PAGE_SIZE: int = 5  # news items per page
