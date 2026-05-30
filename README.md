# TransferRadar AI ⚽

> **Your 24/7 football transfer intelligence platform** — powered by Google Gemini AI, deployed on Render.com free tier with zero downtime.

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![PTB](https://img.shields.io/badge/python--telegram--bot-21.5-green)](https://python-telegram-bot.org)
[![Gemini](https://img.shields.io/badge/Gemini-1.5--Flash-orange)](https://ai.google.dev)
[![Render](https://img.shields.io/badge/Deploy-Render.com-purple)](https://render.com)

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📡 **10 RSS Sources** | BBC Sport, Sky Sports, Goal.com, ESPN, Guardian, and more |
| 🤖 **AI Credibility Scoring** | Gemini 1.5 Flash scores every rumour 0–100 |
| 🔥 **Trending Algorithm** | Tracks mention frequency + source diversity |
| ⭐ **Club Subscriptions** | Subscribe to any club for instant alerts |
| 🏆 **5 Top Leagues** | Premier League, La Liga, Serie A, Bundesliga, Ligue 1 |
| 🔍 **Full-Text Search** | Search any player, club, or keyword |
| ⏰ **8 Scheduled Jobs** | Auto-scrape, broadcasts, cleanup, self-ping |
| 🌐 **24/7 on Free Tier** | Self-pinging keep-alive system beats Render spin-down |

---

## 📁 Project Structure

```
transfer_radar2/
├── main.py                     # Entry point (bot + web + scheduler)
├── config.py                   # All constants, leagues, clubs, RSS feeds
├── keep_alive.py               # FastAPI keep-alive server
├── database.py                 # aiosqlite async DB (6 tables)
├── scheduler.py                # 8 APScheduler jobs
├── requirements.txt
├── render.yaml
├── Procfile
├── runtime.txt
├── .env.example
│
├── services/
│   ├── gemini_service.py       # Gemini 1.5 Flash integration
│   ├── scraper_service.py      # Async web scraper
│   ├── rss_service.py          # RSS feed aggregator
│   ├── fake_detector.py        # AI + rule-based scoring
│   ├── transfer_service.py     # Data access layer
│   └── trending_service.py     # Trending algorithm
│
├── handlers/
│   ├── start_handler.py        # /start + main menu
│   ├── leagues_handler.py      # League/club navigation
│   ├── search_handler.py       # Search system
│   ├── alerts_handler.py       # Subscription management
│   ├── trending_handler.py     # Trending display
│   └── callback_handler.py     # All inline button routing
│
└── utils/
    ├── formatters.py           # Message builders
    ├── cache.py                # LRU in-memory cache
    ├── rate_limiter.py         # Per-user rate limiting
    └── retry.py                # Exponential backoff
```

---

## ⚙️ Local Setup

### 1. Clone & Install

```bash
git clone https://github.com/your-username/transferradar-ai.git
cd transferradar-ai
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
RENDER_URL=http://localhost:8080    # change after Render deploy
```

### 3. Get Your API Keys

**Telegram Bot Token:**
1. Open Telegram → search `@BotFather`
2. Send `/newbot` and follow prompts
3. Copy the token

**Gemini API Key:**
1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API Key**
3. Copy the key

### 4. Run Locally

```bash
python main.py
```

You'll see:
```
INFO  | keep_alive:run_web_server — 🌐 Keep-alive server starting on 0.0.0.0:8080
INFO  | main:run_bot — 🤖 TransferRadar AI starting polling…
INFO  | scheduler:run_scheduler — 🚀 Scheduler started
INFO  | main:run_bot — ✅ TransferRadar AI is LIVE and polling
```

---

## ☁️ Deploy to Render.com (Free — 24/7)

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial TransferRadar AI deploy"
git remote add origin https://github.com/your-username/transferradar-ai.git
git push -u origin main
```

> **Important:** Add `.env` to `.gitignore` — never commit real secrets!

```bash
echo ".env" >> .gitignore
echo "data/" >> .gitignore
echo "logs/" >> .gitignore
```

### Step 2: Create Render Web Service

1. Go to [render.com](https://render.com) → **New → Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name:** `transferradar-ai`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Plan:** Free

### Step 3: Set Environment Variables

In Render dashboard → **Environment** tab, add:

| Key | Value |
|---|---|
| `TELEGRAM_TOKEN` | Your bot token |
| `GEMINI_API_KEY` | Your Gemini key |
| `RENDER_URL` | `https://your-app-name.onrender.com` |
| `PORT` | `8080` |

### Step 4: Deploy

Click **Deploy**. Wait for **"Live"** status (~3-5 minutes).

### Step 5: Set Up UptimeRobot (External Pinger — Free)

This is your backup keep-alive in case Render's own scheduler restarts:

1. Go to [uptimerobot.com](https://uptimerobot.com) → Create free account
2. **New Monitor:**
   - Type: `HTTP(s)`
   - Friendly Name: `TransferRadar AI`
   - URL: `https://your-app-name.onrender.com/health`
   - Monitoring Interval: `5 minutes`
3. Save

**Combined with the bot's internal self-ping every 10 minutes, this ensures 24/7 uptime.**

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Main menu |
| `/trending` | View trending transfers right now |
| `/search <query>` | Search player or club transfers |
| `/myclubs` | View and manage club subscriptions |
| `/alerts` | Toggle notification settings |
| `/about` | Bot info and sources |
| `/menu` | Show main menu again |

---

## 📊 Scheduler Jobs

| Job | Frequency | Purpose |
|---|---|---|
| `scrape_all_sources` | Every 30 min | RSS + web scraping |
| `update_trending` | Every 1 hour | Recompute trending topics |
| `send_morning_roundup` | Daily 08:00 UTC | Broadcast top stories |
| `send_afternoon_breaking` | Daily 13:00 UTC | Broadcast breaking news |
| `send_evening_recap` | Daily 19:00 UTC | Broadcast evening recap |
| `clean_old_news` | Daily 02:00 UTC | Delete news older than 7 days |
| `self_ping_keep_alive` | Every 10 min | Prevent Render spin-down |
| `run_fake_detection_batch` | Every 2 hours | AI-score unanalyzed items |

---

## 🛡️ Reliability Scoring

Every transfer rumour gets a score from 0–100:

| Label | Score | Meaning |
|---|---|---|
| ✅ CONFIRMED | 85–100 | Official announcement |
| 🟢 HIGHLY RELIABLE | 70–84 | Trusted journalist confirmed |
| 🟡 POSSIBLE | 50–69 | Credible source, plausible |
| 🟠 LOW RELIABILITY | 30–49 | Unverified or weak source |
| 🔴 FAKE RUMOR | 0–29 | Anonymous / Twitter rumour |

**Source trust weights (Gemini + rule-based):**
- Fabrizio Romano: +30
- Sky Sports / David Ornstein: +25
- BBC Sport: +20
- "Here We Go" phrase: +15
- Anonymous source: −20
- Twitter rumour account: −30

---

## 🔧 Architecture

```
asyncio.gather()
    ├── run_bot()          → PTB polling (Telegram updates)
    ├── run_web_server()   → FastAPI on :8080 (keep-alive)
    └── run_scheduler()    → APScheduler (8 background jobs)
            │
            ├── RSS feeds (10 sources) ─┐
            ├── Web scraper             ├─→ DB (aiosqlite)
            ├── Gemini AI scoring       │        │
            └── Trending algorithm ────┘    LRU Cache
                                                 │
                                           Telegram handlers
```

---

## 📦 Tech Stack

- **Python 3.11** — async-first
- **python-telegram-bot 21.5** — PTB async framework
- **Google Gemini 1.5 Flash** — AI credibility analysis
- **APScheduler 3.10** — AsyncIOScheduler background jobs
- **aiosqlite 0.20** — Async SQLite database
- **aiohttp 3.9** — Async HTTP client
- **FastAPI 0.111 + uvicorn** — Keep-alive web server
- **feedparser 6.0** — RSS ingestion
- **BeautifulSoup4 + lxml** — HTML parsing
- **loguru 0.7** — Structured logging

---

## 📝 License

MIT — free to use, modify, and deploy.

---

*Built with ❤️ for football fans everywhere. Not affiliated with any club, league, or media organisation.*
