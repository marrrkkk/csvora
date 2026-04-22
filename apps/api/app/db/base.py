from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


# Import models so Alembic can discover metadata.
from app import models  # noqa: E402,F401
