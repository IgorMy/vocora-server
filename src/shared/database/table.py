import re

from sqlalchemy.orm import declared_attr
from sqlmodel import SQLModel


class TableModel(SQLModel):
    """Base for table models: names the table after the class in snake_case (AuditRequest -> audit_request)."""

    @declared_attr  # pyright: ignore[reportArgumentType]
    def __tablename__(cls) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
