from fastapi import Request
from fastapi.responses import JSONResponse

from src.shared.schema.response import ErrorResponse


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # pyright: ignore[reportUnusedParameter]
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail=str(exc)).model_dump(),
    )
