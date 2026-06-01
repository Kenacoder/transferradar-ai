"""
utils/extractor.py — TransferRadar AI
Robust entity extraction (players, clubs) and immediate rule-based scoring helpers.
Used to ensure data is instantly populated on ingestion before AI runs.
"""

import re
from typing import Optional, tuple

from config import CLUBS, LEAGUES, TRUSTED_SOURCES, UNTRUSTED_MARKERS, POSITIVE_KEYWORDS

# Build known lists for entity matching
_CLUB_NAMES: list[str] = [v["name"].lower() for v in CLUBS.values()]
_CLUB_ID_MAP: dict[str, str] = {
    v["name"].lower(): k for k, v in CLUBS.items()
}

_TRANSFER_VERBS = [
    "signs", "joins", "moves", "transfers", "agrees", "completes",
    "seals", "set to join", "close to", "nears", "heading to", "eyes",
    "targets", "linked with", "pursues", "negotiates", "bids for", "swoops for"
]

# Words that should never be treated as player names
_STOP_WORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "summer", "winter", "transfer",
    "news", "report", "deal", "agreement", "fc", "cf", "ssc", "as", "ac", "psg",
    "real", "madrid", "barcelona", "united", "city", "chelsea", "arsenal", "liverpool",
    "tottenham", "hotspur", "bayern", "munich", "dortmund", "juventus", "inter",
    "milan", "napoli", "roma", "lazio", "paris", "saint", "germain", "breaking",
    "exclusive", "rumor", "rumour", "update", "latest", "done", "signing", "bid",
    "medical", "contract", "agree", "champions", "league", "premier", "serie",
    "la", "liga", "bundesliga", "ligue", "world", "cup", "england", "spain",
    "italy", "germany", "france", "portugal", "netherlands", "argentina", "brazil"
}

def extract_club(text: str) -> tuple[Optional[str], Optional[str]]:
    """
    Scan text to find a matching club name.
    Returns (club_name, league) if found.
    """
    if not text:
        return None, None
    
    lower = text.lower()
    for club_name in _CLUB_NAMES:
        if club_name in lower:
            club_id = _CLUB_ID_MAP.get(club_name)
            if club_id:
                league_id = CLUBS[club_id]["league"]
                league_name = LEAGUES.get(league_id, {}).get("name", league_id)
                return CLUBS[club_id]["name"], league_name
    return None, None

def extract_player(title: str) -> Optional[str]:
    """
    Smart player extraction heuristic.
    1. Looks for capitalized words before or after transfer verbs.
    2. Fallback: extracts the first 2-word capitalized sequence that doesn't contain stop words/club names.
    """
    if not title:
        return None

    # Step 1: Try the verb heuristic
    for verb in _TRANSFER_VERBS:
        idx = title.lower().find(verb)
        if idx > 2:
            candidate = title[:idx].strip()
            words = candidate.split()
            name_words = [w for w in words[-3:] if w and w[0].isupper() and w.lower() not in _STOP_WORDS]
            if 1 <= len(name_words) <= 3:
                return " ".join(name_words)
        
        # If verb is in the middle, check after the verb too
        if idx != -1 and idx + len(verb) < len(title) - 5:
            candidate = title[idx + len(verb):].strip()
            words = candidate.split()
            name_words = [w for w in words[:3] if w and w[0].isupper() and w.lower() not in _STOP_WORDS]
            if 1 <= len(name_words) <= 3:
                return " ".join(name_words)

    # Step 2: Fallback - look for first consecutive capitalized words sequence of length 2
    # This matches patterns like "Mikel Merino", "Federico Chiesa", "Dominic Solanke"
    # Find all words
    words = re.findall(r"\b[A-Za-zÀ-ÿ\-]+\b", title)
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        if w1[0].isupper() and w2[0].isupper():
            w1_l, w2_l = w1.lower(), w2.lower()
            if w1_l not in _STOP_WORDS and w2_l not in _STOP_WORDS:
                # Make sure it's not a known club name
                full_seq = f"{w1_l} {w2_l}"
                is_club = False
                for club in _CLUB_NAMES:
                    if w1_l in club or w2_l in club:
                        is_club = True
                        break
                if not is_club:
                    return f"{w1} {w2}"
                    
    # Step 3: Single capitalized word fallback if it's distinctive
    for w in words:
        if w[0].isupper() and len(w) > 3:
            w_l = w.lower()
            if w_l not in _STOP_WORDS:
                is_club = False
                for club in _CLUB_NAMES:
                    if w_l in club:
                        is_club = True
                        break
                if not is_club:
                    return w

    return None

def compute_rule_based_score(title: str, source: str, summary: str) -> dict:
    """
    Compute a credibility score using keyword heuristics.
    """
    score = 50  # neutral baseline
    text = f"{title} {source} {summary or ''}".lower()

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
            score += penalty

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
        "is_confirmed": 1 if label == "CONFIRMED" else 0
    }
