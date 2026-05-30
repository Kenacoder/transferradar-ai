"""
services/gemini_service.py — TransferRadar AI
Google Gemini 1.5 Flash integration for AI analysis and summarization.
"""

import asyncio
import json
import re
from typing import Optional

import google.generativeai as genai
from loguru import logger

from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_MAX_TOKENS
from utils.retry import async_retry

# Configure Gemini on module load
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

_FAKE_DETECT_PROMPT = """You are a football transfer news credibility analyst.
Analyze this transfer rumor and return JSON only.

Rumor: {title}
Source: {source}
Content: {summary}

Return this exact JSON:
{{
  "reliability_score": <integer 0-100>,
  "reliability_label": "<CONFIRMED|HIGHLY RELIABLE|POSSIBLE|LOW RELIABILITY|FAKE RUMOR>",
  "confidence_reason": "<brief explanation>",
  "journalist_trust": "<HIGH|MEDIUM|LOW|UNKNOWN>",
  "verdict": "<one sentence summary>"
}}

Scoring guide:
- Fabrizio Romano = +30 points
- Sky Sports = +25 points
- BBC = +20 points
- David Ornstein = +25 points
- "Here We Go" phrase = +15 points
- "loan" or "bid submitted" = +10 points
- "medical" or "signed" = +12 points
- Anonymous source = -20 points
- Twitter rumor account = -30 points
- Unverified = -15 points

Return ONLY valid JSON. No markdown, no explanation."""

_SUMMARIZE_PROMPT = """Summarize this football transfer news for a Telegram message.
Keep it to 2-3 concise sentences. Include: player, clubs involved, fee if known, contract length if known.
End with the most important fact.

Title: {title}
Content: {content}
Source: {source}

Return only the summary text. No headers, no bullet points."""


@async_retry(retries=3, exceptions=(Exception,))
async def analyze_rumor(title: str, source: str, summary: str) -> dict:
    """
    Send transfer rumor to Gemini for credibility analysis.
    Returns a dict with reliability_score, label, reason, and verdict.
    Falls back to empty dict on failure (caller uses rule-based scoring).
    """
    prompt = _FAKE_DETECT_PROMPT.format(
        title=title, source=source, summary=summary or title
    )
    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=GEMINI_MAX_TOKENS,
                temperature=0.1,
            ),
        )
        raw = response.text.strip()
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
        data = json.loads(raw)
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Gemini returned invalid JSON: {e}")
        return {}
    except Exception as e:
        logger.error(f"Gemini analyze_rumor error: {e}")
        raise


@async_retry(retries=2, exceptions=(Exception,))
async def summarize_article(title: str, content: str, source: str) -> str:
    """
    Use Gemini to generate a short Telegram-ready summary of an article.
    Falls back to the first 300 characters of content if Gemini fails.
    """
    prompt = _SUMMARIZE_PROMPT.format(
        title=title, content=content[:2000], source=source
    )
    try:
        response = await asyncio.to_thread(
            model.generate_content,
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=200,
                temperature=0.3,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini summarize_article error: {e}")
        raise
