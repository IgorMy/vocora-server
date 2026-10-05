import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from pydantic import JsonValue

from src.shared.audit.log import current_audit_request_id
from src.shared.audit.model import AuditRequest
from src.shared.audit.repository import AuditRequestRepository
from src.shared.audit.schema import AuditRequestUpdate
from src.shared.database.engine import get_session_factory
from src.shared.version import DOCS_URL, OPENAPI_URL, REDOC_URL

logger = logging.getLogger(__name__)

EXCLUDED_PATH_PREFIXES = (
    # Docker and monitors hit these constantly; auditing them would flood the table
    "/health",
    # API docs (Swagger UI, ReDoc) and the OpenAPI schema they load
    DOCS_URL,
    REDOC_URL,
    OPENAPI_URL,
    # Browsers request it on their own when opening any page
    "/favicon.ico",
)


async def _create_audit_request(audit_request: AuditRequest) -> uuid.UUID | None:
    try:
        async with get_session_factory()() as session:
            _ = await AuditRequestRepository(session).create(audit_request)
    except Exception:
        # Auditing must never break the request it audits
        logger.exception("Could not create audit request")
        return None
    return audit_request.id


async def _update_audit_request(
    audit_request_id: uuid.UUID | None, data: AuditRequestUpdate
) -> None:
    if audit_request_id is None:
        return
    try:
        async with get_session_factory()() as session:
            await AuditRequestRepository(session).update(audit_request_id, data)
    except Exception:
        # Auditing must never break the request it audits
        logger.exception("Could not update audit request %s", audit_request_id)


async def audit_request_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if request.url.path.startswith(EXCLUDED_PATH_PREFIXES):
        return await call_next(request)

    started_at = time.perf_counter()

    def elapsed_ms() -> int:
        return round((time.perf_counter() - started_at) * 1000)

    # getlist keeps every value of repeated params (?tag=a&tag=b)
    query_params: dict[str, JsonValue] = {
        key: [*request.query_params.getlist(key)] for key in request.query_params
    }

    audit_request_id = await _create_audit_request(
        AuditRequest(
            method=request.method,
            path=request.url.path,
            query_params=query_params or None,
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    )
    request.state.audit_request_id = audit_request_id
    _ = current_audit_request_id.set(audit_request_id)

    try:
        response = await call_next(request)
    except Exception as exc:
        # Unhandled exceptions never come back as a response here: the Exception
        # handler that turns them into the JSON 500 lives in ServerErrorMiddleware,
        # outside this middleware. Record the 500 and re-raise so it still runs.
        await _update_audit_request(
            audit_request_id,
            AuditRequestUpdate(
                status_code=500,
                duration_ms=elapsed_ms(),
                error={"type": type(exc).__name__, "detail": str(exc)},
            ),
        )
        raise

    # Any other status (2xx, or errors like 401, 409, 422) arrives as a normal response
    await _update_audit_request(
        audit_request_id,
        AuditRequestUpdate(status_code=response.status_code, duration_ms=elapsed_ms()),
    )
    return response
