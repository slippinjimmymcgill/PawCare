import abc
import logging
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings
from app.schemas.attachment import AttachmentUploadResponse

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

ALLOWED_MIME_TYPES = set(ALLOWED_EXTENSIONS.values())


class BaseStorageProvider(abc.ABC):
    """Abstract interface for object and local file storage providers."""

    @abc.abstractmethod
    def save(self, filename: str, content: bytes, mime_type: str) -> str:
        """Save file content and return its accessible URL."""

    @abc.abstractmethod
    def get_file_path(self, filename: str) -> Path | None:
        """Get the local filesystem path if available, or None for cloud providers."""

    @abc.abstractmethod
    def delete(self, filename: str) -> bool:
        """Delete file from storage."""


class LocalStorageProvider(BaseStorageProvider):
    """Local filesystem storage provider for dev, test, and self-hosted deployments."""

    def __init__(self, base_dir: str | Path | None = None) -> None:
        settings = get_settings()
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_safe_path(self, filename: str) -> Path:
        if "/" in filename or "\\" in filename or ".." in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename: path traversal not allowed",
            )
        target = (self.base_dir / filename).resolve()
        if not str(target).startswith(str(self.base_dir)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename path traversal detected",
            )
        return target

    def save(self, filename: str, content: bytes, mime_type: str) -> str:
        target_path = self._get_safe_path(filename)
        target_path.write_bytes(content)
        return f"/api/v1/records/attachments/{filename}"

    def get_file_path(self, filename: str) -> Path | None:
        target_path = self._get_safe_path(filename)
        if target_path.exists() and target_path.is_file():
            return target_path
        return None

    def delete(self, filename: str) -> bool:
        target_path = self._get_safe_path(filename)
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False


class S3StorageProvider(BaseStorageProvider):
    """S3-compatible object storage provider (AWS S3, Cloudflare R2, MinIO)."""

    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.OBJECT_STORAGE_BUCKET
        self.key = settings.OBJECT_STORAGE_KEY
        self.secret = settings.OBJECT_STORAGE_SECRET
        self.region = settings.OBJECT_STORAGE_REGION
        self.endpoint_url = settings.OBJECT_STORAGE_ENDPOINT_URL or None

        self._fallback = LocalStorageProvider()

        if not (self.bucket and self.key and self.secret):
            logger.warning(
                "S3StorageProvider configured but missing bucket/credentials. Falling back to local storage."
            )
            self._client = None
            return

        try:
            import boto3  # type: ignore

            self._client = boto3.client(
                "s3",
                aws_access_key_id=self.key,
                aws_secret_access_key=self.secret,
                region_name=self.region,
                endpoint_url=self.endpoint_url,
            )
        except ImportError:
            logger.warning(
                "boto3 is not installed. S3StorageProvider falling back to local storage."
            )
            self._client = None

    def save(self, filename: str, content: bytes, mime_type: str) -> str:
        if not self._client:
            return self._fallback.save(filename, content, mime_type)

        self._client.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=content,
            ContentType=mime_type,
        )

        if self.endpoint_url:
            return f"{self.endpoint_url.rstrip('/')}/{self.bucket}/{filename}"
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{filename}"

    def get_file_path(self, filename: str) -> Path | None:
        if not self._client:
            return self._fallback.get_file_path(filename)
        return None

    def delete(self, filename: str) -> bool:
        if not self._client:
            return self._fallback.delete(filename)

        try:
            self._client.delete_object(Bucket=self.bucket, Key=filename)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to delete object from S3: %s", exc)
            return False


class StorageService:
    """High-level storage service managing validation and persistence of attachments."""

    def __init__(self, provider: BaseStorageProvider | None = None) -> None:
        if provider is not None:
            self.provider = provider
        else:
            settings = get_settings()
            provider_type = (settings.OBJECT_STORAGE_PROVIDER or "local").lower().strip()
            if provider_type in {"s3", "aws", "r2"}:
                self.provider = S3StorageProvider()
            else:
                self.provider = LocalStorageProvider()

    async def validate_and_save(self, file: UploadFile) -> AttachmentUploadResponse:
        settings = get_settings()
        original_name = file.filename or "attachment"
        suffix = Path(original_name).suffix.lower()

        # Validate file extension
        if suffix not in ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(ALLOWED_EXTENSIONS.keys())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file extension '{suffix}'. Allowed formats: {allowed_list}",
            )

        # Content type determination
        expected_mime = ALLOWED_EXTENSIONS[suffix]
        actual_mime = file.content_type or expected_mime

        if actual_mime not in ALLOWED_MIME_TYPES and actual_mime != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type '{actual_mime}'. Allowed: PDF, JPEG, PNG, WEBP",
            )

        # Read content and enforce max size
        content = await file.read()
        size_bytes = len(content)

        if size_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)",
            )

        if size_bytes > settings.MAX_ATTACHMENT_SIZE_BYTES:
            max_mb = settings.MAX_ATTACHMENT_SIZE_BYTES / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB",
            )

        # Generate unique identifier for storage
        unique_filename = f"{uuid.uuid4().hex}{suffix}"
        resolved_mime = expected_mime if actual_mime == "application/octet-stream" else actual_mime

        # Save to provider
        url = self.provider.save(unique_filename, content, resolved_mime)

        return AttachmentUploadResponse(
            filename=unique_filename,
            original_filename=original_name,
            url=url,
            mime_type=resolved_mime,
            size_bytes=size_bytes,
        )

    def get_file_path(self, filename: str) -> Path | None:
        return self.provider.get_file_path(filename)

    def delete(self, filename: str) -> bool:
        return self.provider.delete(filename)


_default_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _default_storage_service
    if _default_storage_service is None:
        _default_storage_service = StorageService()
    return _default_storage_service
