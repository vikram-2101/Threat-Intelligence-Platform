import asyncio
import functools
import structlog
from typing import Any, Callable

logger = structlog.get_logger()

def with_retry(max_retries: int = 3, backoff_multipliers: list[int] = [2, 4, 8], timeout: int = 10):
    """
    Decorator for enrichment tasks to provide retries with exponential backoff and timeout.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    # Apply timeout to the async call
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except (asyncio.TimeoutError, Exception) as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_multipliers[attempt]
                        logger.warning(
                            "enricher_retry",
                            enricher=args[0].__class__.__name__,
                            attempt=attempt + 1,
                            wait_time=wait_time,
                            error=str(e)
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            "enricher_failed_after_retries",
                            enricher=args[0].__class__.__name__,
                            attempts=max_retries + 1,
                            error=str(e)
                        )
            raise last_exception
        return wrapper
    return decorator
