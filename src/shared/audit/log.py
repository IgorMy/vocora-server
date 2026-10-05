import datetime
import logging
import uuid
from contextvars import ContextVar

from pydantic import JsonValue

from src.shared.audit.model import LogEntry, LogLevel
from src.shared.audit.repository import AuditRequestRepository
from src.shared.database.engine import get_session_factory

logger = logging.getLogger(__name__)

# Set by the audit middleware for the duration of each audited request
current_audit_request_id: ContextVar[uuid.UUID | None] = ContextVar(
    "current_audit_request_id", default=None
)


async def audit_log(
    level: LogLevel, event: str, extra: dict[str, JsonValue] | None = None
) -> None:
    """
    Logs to stdout and appends the entry to the logs of the current request's audit.
    Outside an audited request (or if the audit could not be created) it only logs to stdout.
    """
    logger.log(logging.getLevelNamesMapping()[level], "%s %s", event, extra or "")

    audit_request_id = current_audit_request_id.get()
    if audit_request_id is None:
        return

    entry = LogEntry(
        timestamp=datetime.datetime.now(tz=datetime.UTC),
        level=level,
        event=event,
        extra=extra,
    )
    try:
        async with get_session_factory()() as session:
            await AuditRequestRepository(session).add_log(audit_request_id, entry)
    except Exception:
        # Auditing must never break the request it audits
        logger.exception("Could not add log to audit request %s", audit_request_id)
