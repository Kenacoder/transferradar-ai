"""
utils/retry.py — TransferRadar AI
Exponential backoff retry decorator for async HTTP calls and API requests.
"""

import asyncio
import functools
from typing import Any, Callable, Tuple, Type

from loguru import logger

from config import MAX_RETRIES, RETRY_BASE_DELAY


def async_retry(
    retries: int = MAX_RETRIES,
    base_delay: float = RETRY_BASE_DELAY,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator: retries the wrapped async function up to `retries` times
    with exponential backoff (base_delay * 2^attempt).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception = RuntimeError("No attempts made")
            for attempt in range(retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"⚠️ {func.__name__} failed (attempt {attempt+1}/{retries+1}): "
                            f"{exc}. Retrying in {delay:.1f}s…"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"❌ {func.__name__} failed after {retries+1} attempts: {exc}"
                        )
            raise last_exc
        return wrapper
    return decorator
