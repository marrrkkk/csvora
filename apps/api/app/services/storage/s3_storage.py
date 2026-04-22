import boto3
from botocore.client import BaseClient


class S3StorageService:
    def __init__(
        self,
        endpoint_url: str | None,
        access_key_id: str | None,
        secret_access_key: str | None,
        region_name: str,
        bucket_name: str,
        use_ssl: bool,
    ) -> None:
        self.bucket_name = bucket_name
        self.client: BaseClient = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name,
            use_ssl=use_ssl,
        )

    def put_bytes(self, key: str, data: bytes, content_type: str | None = None) -> str:
        kwargs: dict[str, str] = {}
        if content_type:
            kwargs["ContentType"] = content_type
        self.client.put_object(Bucket=self.bucket_name, Key=key, Body=data, **kwargs)
        return key

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except Exception:
            return False

    def get_object_reference(self, key: str) -> str:
        return key

    def get_bytes(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()
