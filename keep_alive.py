"""
keep_alive.py — TransferRadar AI
FastAPI health-check server for Render.com keep-alive pings.
"""

import asyncio
from datetime import datetime, timezone

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger

from config import HOST, PORT, BOT_NAME, BOT_VERSION

app = FastAPI(title=f"{BOT_NAME} Keep-Alive", docs_url=None, redoc_url=None)
_start_time: datetime = datetime.now(tz=timezone.utc)


@app.get("/", response_class=JSONResponse)
async def root() -> dict:
    uptime = (datetime.now(tz=timezone.utc) - _start_time).total_seconds()
    return {
        "status": "alive",
        "bot": BOT_NAME,
        "version": BOT_VERSION,
        "uptime_seconds": round(uptime, 1),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }


@app.get("/health", response_class=JSONResponse)
async def health() -> dict:
    return {"status": "healthy", "service": BOT_NAME}


async def run_web_server() -> None:
    config = uvicorn.Config(
        app=app, host=HOST, port=PORT,
        log_level="warning", access_log=False, loop="asyncio",
    )
    server = uvicorn.Server(config)
    logger.info(f"🌐 Keep-alive server starting on {HOST}:{PORT}")
    await server.serve()
