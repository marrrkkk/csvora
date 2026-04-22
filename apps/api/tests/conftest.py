import os
import uuid
from pathlib import Path

import pytest
from httpx import Client

from app.core.security import build_key_prefix, hash_api_key
from app.db.session import SessionLocal
from app.models.api_key import APIKey


@pytest.fixture(scope="session")
def base_url() -> str:
    return os.environ.get("TEST_BASE_URL", "http://api:8000")


@pytest.fixture(scope="session")
def api_key_raw() -> str:
    # deterministic but not sensitive: only for local dev containers
    return os.environ.get("TEST_API_KEY_RAW", "test-local-api-key")


@pytest.fixture(scope="session")
def api_key_id(api_key_raw: str) -> str:
    db = SessionLocal()
    try:
        key_id = uuid.uuid4()
        db.add(
            APIKey(
                id=key_id,
                key_prefix=build_key_prefix(api_key_raw),
                key_hash=hash_api_key(api_key_raw),
                name="pytest",
                is_active=True,
            )
        )
        db.commit()
        return str(key_id)
    finally:
        db.close()


@pytest.fixture()
def client(base_url: str, api_key_raw: str, api_key_id: str) -> Client:
    return Client(base_url=base_url, headers={"X-API-Key": api_key_raw})


@pytest.fixture()
def client_inprocess(api_key_raw: str, api_key_id: str):
    """In-process FastAPI + eager Celery (same DB as SessionLocal). Use for tests that need latest routes."""
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.workers.celery_app import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    app = create_app()
    with TestClient(app, headers={"X-API-Key": api_key_raw}) as c:
        yield c


@pytest.fixture(scope="session")
def second_api_key_raw(api_key_raw: str) -> str:
    return f"{api_key_raw}-secondary"


@pytest.fixture(scope="session")
def second_api_key_id(second_api_key_raw: str) -> str:
    db = SessionLocal()
    try:
        key_id = uuid.uuid4()
        db.add(
            APIKey(
                id=key_id,
                key_prefix=build_key_prefix(second_api_key_raw),
                key_hash=hash_api_key(second_api_key_raw),
                name="pytest-secondary",
                is_active=True,
            )
        )
        db.commit()
        return str(key_id)
    finally:
        db.close()


@pytest.fixture()
def second_client(base_url: str, second_api_key_raw: str, second_api_key_id: str) -> Client:
    return Client(base_url=base_url, headers={"X-API-Key": second_api_key_raw})


@pytest.fixture()
def second_client_inprocess(second_api_key_raw: str, second_api_key_id: str):
    from fastapi.testclient import TestClient

    from app.main import create_app
    from app.workers.celery_app import celery_app

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = False
    app = create_app()
    with TestClient(app, headers={"X-API-Key": second_api_key_raw}) as c:
        yield c


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"

