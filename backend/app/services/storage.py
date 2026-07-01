import io
import mimetypes
from datetime import timedelta

import structlog
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = structlog.get_logger()


class StorageService:
    """Wrapper around MinIO (S3 compatible) for document storage."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._bucket_checked = False

    def _ensure_bucket(self) -> None:
        """Ensure the target bucket exists, create if not."""
        if self._bucket_checked:
            return

        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("Created MinIO bucket", bucket=self.bucket_name)
            self._bucket_checked = True
        except S3Error as e:
            logger.error("Failed to ensure MinIO bucket", error=str(e))
            raise

    def get_object_path(
        self, tenant_id: str, collection_id: str, document_id: str, filename: str
    ) -> str:
        """Generate isolated object path."""
        return f"{tenant_id}/{collection_id}/{document_id}/{filename}"

    def upload_file(
        self, object_name: str, data: bytes, content_type: str | None = None
    ) -> str:
        """Upload file bytes to MinIO."""
        self._ensure_bucket()
        if not content_type:
            content_type, _ = mimetypes.guess_type(object_name)
            content_type = content_type or "application/octet-stream"

        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return object_name
        except S3Error as e:
            logger.error(
                "Failed to upload file to MinIO", error=str(e), object_name=object_name
            )
            raise

    def get_presigned_url(
        self, object_name: str, expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate a secure pre-signed URL for temporary access."""
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires,
            )
            return url
        except S3Error as e:
            logger.error(
                "Failed to generate pre-signed URL",
                error=str(e),
                object_name=object_name,
            )
            raise

    def download_file(self, object_name: str) -> bytes:
        """Download file bytes from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(
                "Failed to download file from MinIO",
                error=str(e),
                object_name=object_name,
            )
            raise

    def delete_file(self, object_name: str) -> None:
        """Delete an object from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(
                "Failed to delete file from MinIO",
                error=str(e),
                object_name=object_name,
            )
            raise


storage_service = StorageService()
