import uuid
from datetime import datetime, timedelta, timezone

from app.core.security import authenticate_api_key, build_key_prefix, hash_api_key, verify_api_key
from app.db.session import SessionLocal
from app.models.api_key import APIKey


def test_api_key_hash_round_trip() -> None:
    raw = "hello-world"
    key_hash = hash_api_key(raw)
    assert verify_api_key(raw, key_hash) is True


def test_api_key_verify_invalid_hash_is_false() -> None:
    assert verify_api_key("hello", "not-a-bcrypt-hash") is False


def test_build_key_prefix() -> None:
    assert build_key_prefix("abcdefgh1234") == "abcdefgh"


def test_authenticate_api_key_respects_expiry_and_revocation() -> None:
    raw = "security-test-key"
    db = SessionLocal()
    try:
        active = APIKey(
            id=uuid.uuid4(),
            key_prefix=build_key_prefix(raw),
            key_hash=hash_api_key(raw),
            name="active",
            is_active=True,
        )
        expired = APIKey(
            id=uuid.uuid4(),
            key_prefix=build_key_prefix(raw),
            key_hash=hash_api_key(raw),
            name="expired",
            is_active=True,
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        revoked = APIKey(
            id=uuid.uuid4(),
            key_prefix=build_key_prefix(raw),
            key_hash=hash_api_key(raw),
            name="revoked",
            is_active=True,
            revoked_at=datetime.now(timezone.utc),
        )
        db.add_all([active, expired, revoked])
        db.commit()

        found = authenticate_api_key(db, raw)
        assert found is not None
        assert found.id == active.id
    finally:
        db.close()

