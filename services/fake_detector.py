"""
services/fake_detector.py — TransferRadar AI
AI + rule-based credibility scoring engine for transfer rumours.
Falls back gracefully to rule-based scoring if Gemini is unavailable.
"""

from typing import Optional
from loguru import logger

from config import (
    TRUSTED_SOURCES,
    UNTRUSTED_MARKERS,
    POSITIVE_KEYWORDS,
)


# ─── Rule-based scorer ─────────────────────────────────────────────────────────
def rule_based_score(title: str, source: str, summary: str) -> dict:
    """
    Compute a credibility score using keyword heuristics.
    Returns a dict matching the Gemini response schema.
    """
    score = 50  # neutral baseline
    text = f"{title} {source} {summary}".lower()

    # Trusted source bonuses
    for keyword, bonus in TRUSTED_SOURCES.items():
        if keyword in text:
            score += bonus

    # Positive signal keywords
    for keyword, bonus in POSITIVE_KEYWORDS.items():
        if keyword in text:
            score += bonus

    # Negative markers
    for keyword, penalty in UNTRUSTED_MARKERS.items():
        if keyword in text:
            score += penalty  # penalty is already negative

    score = max(0, min(100, score))

    if score >= 85:
        label = "CONFIRMED"
    elif score >= 70:
        label = "HIGHLY RELIABLE"
    elif score >= 50:
        label = "POSSIBLE"
    elif score >= 30:
        label = "LOW RELIABILITY"
    else:
        label = "FAKE RUMOR"

    return {
        "reliability_score": score,
        "reliability_label": label,
        "confidence_reason": "Rule-based heuristic scoring",
        "journalist_trust": "UNKNOWN",
        "verdict": f"Score: {score}/100 — {label}",
        "player_name": None,
        "club_name": None,
    }


# ─── Combined scorer (AI + rule-based fallback) ────────────────────────────────
async def score_news_item(title: str, source: str, summary: str) -> dict:
    """
    Attempt Gemini AI scoring first. Fall back to rule-based if unavailable.
    Returns a normalised dict with reliability_score (0-100) and reliability_label.
    """
    try:
        from services.gemini_service import analyze_rumor
        result = await analyze_rumor(title, source, summary)
        if result and "reliability_score" in result:
            # Clamp score to valid range
            result["reliability_score"] = max(0, min(100, int(result["reliability_score"])))
            logger.debug(
                f"🤖 Gemini scored '{title[:50]}': "
                f"{result['reliability_score']}% — {result.get('reliability_label')}"
            )
            return result
    except Exception as e:
        logger.warning(f"Gemini scoring unavailable, using rule-based: {e}")

    # Fallback
    result = rule_based_score(title, source, summary)
    logger.debug(
        f"📏 Rule-based scored '{title[:50]}': "
        f"{result['reliability_score']}% — {result['reliability_label']}"
    )
    return result
