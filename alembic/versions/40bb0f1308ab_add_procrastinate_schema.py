"""add procrastinate schema

Revision ID: 40bb0f1308ab
Revises: f30f9975791d
Create Date: 2026-10-06 17:58:02.478055

"""

from collections.abc import Sequence

from procrastinate.schema import SchemaManager

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "40bb0f1308ab"
down_revision: str | Sequence[str] | None = "f30f9975791d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Tables, types and functions of the job queue, from the SQL shipped with
    # procrastinate. When upgrading procrastinate, its new SQL migrations
    # (procrastinate/sql/migrations) must be added as Alembic migrations.
    # exec_driver_sql skips SQLAlchemy's parsing of ":", but psycopg still reads
    # "%" as a placeholder, so it is escaped (as procrastinate's apply_schema does).
    _ = op.get_bind().exec_driver_sql(SchemaManager.get_schema().replace("%", "%%"))


def downgrade() -> None:
    """Downgrade schema."""
    _ = op.get_bind().exec_driver_sql(
        r"""
        DROP TABLE IF EXISTS procrastinate_periodic_defers, procrastinate_events,
            procrastinate_jobs, procrastinate_workers CASCADE;
        DROP TYPE IF EXISTS procrastinate_job_event_type, procrastinate_job_status,
            procrastinate_job_to_defer_v1 CASCADE;
        DO $$
        DECLARE fn regprocedure;
        BEGIN
            FOR fn IN
                SELECT oid::regprocedure FROM pg_proc WHERE proname LIKE 'procrastinate\_%%'
            LOOP
                EXECUTE 'DROP FUNCTION IF EXISTS ' || fn || ' CASCADE';
            END LOOP;
        END $$;
        """
    )
