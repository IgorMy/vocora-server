COMPOSE := docker compose -f docker/compose.yaml --env-file .env

.PHONY: database

# Start only the PostgreSQL service in the background
database:
	$(COMPOSE) up -d --build database
