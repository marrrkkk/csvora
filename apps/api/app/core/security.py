import bcrypt
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.api_key import APIKey


def hash_api_key(raw_key: str) -> str:
    hashed = bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def build_key_prefix(raw_key: str) -> str:
    return raw_key[:8]


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    try:
        return bcrypt.checkpw(raw_key.encode("utf-8"), key_hash.encode("utf-8"))
    except ValueError:
        return False


def authenticate_api_key(db: Session, raw_key: str) -> APIKey | None:
    now = datetime.now(timezone.utc)
    prefix = build_key_prefix(raw_key)
    rows = db.execute(
        select(APIKey).where(
            APIKey.is_active.is_(True),
            APIKey.key_prefix == prefix,
            APIKey.revoked_at.is_(None),
        ).order_by(APIKey.created_at.desc())
    ).scalars().all()

    # Backward compatibility for pre-prefix keys.
    if not rows:
        rows = db.execute(
            select(APIKey).where(
                APIKey.is_active.is_(True),
                APIKey.key_prefix.is_(None),
                APIKey.revoked_at.is_(None),
            ).order_by(APIKey.created_at.desc())
        ).scalars().all()

    for row in rows:
        if row.expires_at and row.expires_at <= now:
            continue
        if verify_api_key(raw_key, row.key_hash):
            return row
    return None


def touch_api_key_usage(db: Session, api_key: APIKey) -> None:
    api_key.last_used_at = datetime.now(timezone.utc)
    db.add(api_key)
    db.commit()
