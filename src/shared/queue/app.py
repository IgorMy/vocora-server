import procrastinate

from src.shared.config import settings

queue_app = procrastinate.App(
    connector=procrastinate.PsycopgConnector(
        # Same database as the app; psycopg wants a plain libpq URL, without "+psycopg"
        conninfo=settings.database_url.set(drivername="postgresql").render_as_string(
            hide_password=False
        ),
    ),
    # Modules with tasks, imported by the worker so it knows every task it may run
    import_paths=["src.recording.task"],
)
