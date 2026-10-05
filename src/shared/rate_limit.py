import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from limits import parse
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.exception import rate_limit_response

# Per-endpoint limits, applied with @limiter.limit(...) on each route
limiter = Limiter(key_func=get_remote_address)

# Global limit per client across all endpoints. It runs as a middleware, before auth
# and body parsing. slowapi's own SlowAPIMiddleware can't do this here: it skips any
# endpoint added through include_router, because it can't resolve it.
GLOBAL_LIMIT = parse("60/minute")
_global_limiter = MovingWindowRateLimiter(MemoryStorage())


async def global_rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    key = get_remote_address(request)
    if not _global_limiter.hit(GLOBAL_LIMIT, "global", key):
        reset_time = _global_limiter.get_window_stats(
            GLOBAL_LIMIT, "global", key
        ).reset_time
        return rate_limit_response(
            detail="60 per 1 minute",
            retry_after=max(1, round(reset_time - time.time())),
        )
    return await call_next(request)
