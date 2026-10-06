from sqlmodel import SQLModel

from src.recording.model import Recording
from src.shared.audit_change.model import AuditChange
from src.shared.audit_request.model import AuditRequest

# Import every table model here. A model only registers in SQLModel.metadata
# when its module is imported, so anything missing from this file is invisible
# to Alembic autogenerate and to relationships declared by name.

metadata = SQLModel.metadata


__all__ = ["AuditChange", "AuditRequest", "Recording", "metadata"]
