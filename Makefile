COMPOSE := docker compose -f docker/compose.yaml --env-file .env

.PHONY: database migrate local_dev worker download_model up

# Start only the PostgreSQL service in the background and wait until it is healthy
database:
	$(COMPOSE) up -d --wait --build database

# Apply pending database migrations
migrate: database
	uv run alembic upgrade head

# Run the API locally with auto-reload, on API_PORT from .env, after migrating the database
local_dev: migrate
	uv run --env-file .env sh -c 'fastapi dev --port "$$API_PORT"'

# Run the queue worker that processes recordings, after migrating the database
worker: migrate
	uv run python -m src.worker

# Download the transcription model set in WHISPER_MODEL into WHISPER_MODEL_DIR
download_model:
	uv run python -m src.shared.transcription.download

# Build and start the whole app in Docker (database, migrations, api and worker)
up:
	$(COMPOSE) up -d --wait --build
