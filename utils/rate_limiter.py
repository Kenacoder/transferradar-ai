"""
utils/rate_limiter.py — TransferRadar AI
Per-user rate limiting for button presses and search queries.
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque

from config import (
    RATE_LIMIT_ACTIONS,
    RATE_LIMIT_WINDOW_SECONDS,
    SEARCH_RATE_LIMIT,
    SEARCH_RATE_WINDOW_SECONDS,
)


class RateLimiter:
    """Sliding-window rate limiter per user."""

    def __init__(self, max_calls: int, window_seconds: int):
        self._max_calls = max_calls
        self._window = window_seconds
        self._history: dict[int, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_allowed(self, user_id: int) -> bool:
        async with self._lock:
            now = time.monotonic()
            q = self._history[user_id]
            # Remove timestamps outside window
            while q and now - q[0] > self._window:
                q.popleft()
            if len(q) >= self._max_calls:
                return False
            q.append(now)
            return True

    async def remaining(self, user_id: int) -> int:
        async with self._lock:
            now = time.monotonic()
            q = self._history[user_id]
            while q and now - q[0] > self._window:
                q.popleft()
            return max(0, self._max_calls - len(q))


# Module-level singletons
action_limiter = RateLimiter(RATE_LIMIT_ACTIONS, RATE_LIMIT_WINDOW_SECONDS)
search_limiter = RateLimiter(SEARCH_RATE_LIMIT, SEARCH_RATE_WINDOW_SECONDS)
