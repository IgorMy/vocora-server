from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.shared.schema.response import ErrorResponse


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # pyright: ignore[reportUnusedParameter]
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )


def rate_limit_response(detail: str, retry_after: int | None) -> JSONResponse:
    """429 response shared by the per-endpoint and the global rate limits."""
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(detail=f"Too many requests: {detail}").model_dump(),
        headers={"Retry-After": str(retry_after)} if retry_after else None,
    )


async def rate_limit_exceeded_handler(
    request: Request,  # pyright: ignore[reportUnusedParameter]
    exc: Exception,
) -> JSONResponse:
    # Typed as Exception because that is what add_exception_handler accepts;
    # it is only registered for RateLimitExceeded
    assert isinstance(exc, RateLimitExceeded)
    return rate_limit_response(
        detail=exc.detail,
        retry_after=exc.limit.limit.get_expiry() if exc.limit else None,
    )
