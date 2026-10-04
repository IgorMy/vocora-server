COMPOSE := docker compose -f docker/compose.yaml --env-file .env

.PHONY: database migrate

# Start only the PostgreSQL service in the background and wait until it is healthy
database:
	$(COMPOSE) up -d --wait --build database

# Apply pending database migrations
migrate: database
	uv run alembic upgrade head
