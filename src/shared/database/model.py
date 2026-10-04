from sqlmodel import SQLModel

# Import every table model here. A model only registers in SQLModel.metadata
# when its module is imported, so anything missing from this file is invisible
# to Alembic autogenerate and to relationships declared by name.

metadata = SQLModel.metadata

__all__ = ["metadata"]
