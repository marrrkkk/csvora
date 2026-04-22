from app.core.config import Settings
from app.services.storage.base import StorageService
from app.services.storage.local_storage import LocalStorageService
from app.services.storage.s3_storage import S3StorageService


def build_storage_service(settings: Settings) -> StorageService:
    if settings.storage_backend == "s3":
        return S3StorageService(
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            bucket_name=settings.s3_bucket_name,
            use_ssl=settings.s3_use_ssl,
        )
    return LocalStorageService(root_dir=settings.local_storage_root)
