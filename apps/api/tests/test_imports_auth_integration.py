import uuid
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core.security import build_key_prefix, hash_api_key
from app.db.session import SessionLocal
from app.main import create_app
from app.models.api_key import APIKey


def test_imports_requires_api_key() -> None:
    with TestClient(create_app()) as c:
        assert c.post("/api/v1/imports", json={}).status_code == 401


def test_imports_rejects_invalid_api_key() -> None:
    with TestClient(create_app()) as c:
        r = c.post("/api/v1/imports", json={}, headers={"X-API-Key": "invalid-key"})
        assert r.status_code == 403


def test_revoked_and_expired_keys_rejected() -> None:
    db = SessionLocal()
    revoked_raw = "revoked-key-1234"
    expired_raw = "expired-key-1234"
    try:
        db.add(
            APIKey(
                id=uuid.uuid4(),
                key_prefix=build_key_prefix(revoked_raw),
                key_hash=hash_api_key(revoked_raw),
                name="revoked",
                is_active=True,
                revoked_at=datetime.now(timezone.utc),
            )
        )
        db.add(
            APIKey(
                id=uuid.uuid4(),
                key_prefix=build_key_prefix(expired_raw),
                key_hash=hash_api_key(expired_raw),
                name="expired",
                is_active=True,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            )
        )
        db.commit()
    finally:
        db.close()

    with TestClient(create_app()) as c:
        assert c.post("/api/v1/imports", json={}, headers={"X-API-Key": revoked_raw}).status_code == 403
        assert c.post("/api/v1/imports", json={}, headers={"X-API-Key": expired_raw}).status_code == 403


def test_health_and_metrics_accessible_without_api_key() -> None:
    with TestClient(create_app()) as c:
        assert c.get("/health").status_code == 200
        assert c.get("/api/v1/health").status_code == 200
        assert c.get("/api/v1/metrics").status_code == 200
