SHELL := /bin/sh

.PHONY: dev api worker web docs-sync test migrate down

dev:
	docker compose up -d --build

api:
	docker compose up -d api

worker:
	docker compose up -d worker

web:
	npm --prefix apps/web run dev

docs-sync:
	py -3 scripts/openapi_sync.py

test:
	docker compose run --rm -e TEST_BASE_URL=http://api:8000 api sh -c "alembic upgrade head && pytest -q"

migrate:
	docker compose run --rm api alembic upgrade head

down:
	docker compose down
