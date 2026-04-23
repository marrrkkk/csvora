# Run migrations and test suite
docker compose run --rm -e TEST_BASE_URL=http://api:8000 api sh -c "alembic upgrade head && pytest -q"
