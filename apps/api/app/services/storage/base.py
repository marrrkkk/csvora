from typing import Protocol


class StorageService(Protocol):
    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        """Store bytes at a logical key and return stored key."""

    def exists(self, key: str) -> bool:
        """Check if key exists."""

    def get_object_reference(self, key: str) -> str:
        """Return key or URL-like reference for clients."""

    def get_bytes(self, key: str) -> bytes:
        """Read bytes for the provided key."""
