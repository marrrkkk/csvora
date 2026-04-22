from pathlib import Path


class LocalStorageService:
    def __init__(self, root_dir: str) -> None:
        self.root_path = Path(root_dir).resolve()
        self.root_path.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        target_path = self._key_to_path(key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)
        return key

    def exists(self, key: str) -> bool:
        return self._key_to_path(key).exists()

    def get_object_reference(self, key: str) -> str:
        return key

    def get_bytes(self, key: str) -> bytes:
        return self._key_to_path(key).read_bytes()

    def _key_to_path(self, key: str) -> Path:
        safe_key = key.lstrip("/")
        candidate = (self.root_path / safe_key).resolve()
        if candidate != self.root_path and self.root_path not in candidate.parents:
            raise ValueError("Invalid storage key path")
        return candidate
