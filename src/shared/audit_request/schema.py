from pydantic import BaseModel, JsonValue


class AuditRequestUpdate(BaseModel):
    status_code: int | None = None
    duration_ms: int | None = None
    error: dict[str, JsonValue] | None = None
