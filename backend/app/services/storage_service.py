from pathlib import Path

import boto3
from botocore.config import Config as BotoConfig

from app.core.config import settings

_EXTENSION_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _content_type_for(key: str) -> str:
    return _EXTENSION_CONTENT_TYPES.get(Path(key).suffix.lower(), "application/octet-stream")


def _r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=BotoConfig(signature_version="s3v4"),
        region_name="auto",
    )


def save_file(key: str, data: bytes) -> None:
    """Save a file under `key`, to R2 if configured, otherwise to local disk."""
    if settings.r2_configured:
        _r2_client().put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=_content_type_for(key),
        )
        return

    path = Path(settings.UPLOAD_DIR) / key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
