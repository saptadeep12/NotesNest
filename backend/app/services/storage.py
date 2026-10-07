from collections.abc import Callable
from pathlib import Path
from typing import Any

import boto3
from botocore.exceptions import ClientError
from fastapi.responses import FileResponse, RedirectResponse

from app.core.config import get_settings


def storage_root() -> Path:
    return Path(get_settings().storage_dir).resolve()


def resolve_path(file_path: str) -> Path:
    root = storage_root()
    candidate = (root / file_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("File path escapes the storage directory")
    return candidate


def is_s3_backend() -> bool:
    return get_settings().storage_backend == "s3"


def get_s3_client() -> Any:
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=boto3.session.Config(signature_version="s3v4"),
    )


def safe_filename(file_path: str) -> str:
    name = Path(file_path).name
    ascii_name = name.encode("ascii", "ignore").decode("ascii").strip()
    return ascii_name or "resource.pdf"


def get_file_response(
    file_path: str,
    download: bool = False,
    resolver: Callable[[str], Path] | None = None,
) -> FileResponse | RedirectResponse:
    filename = safe_filename(file_path)
    disposition = (
        f'attachment; filename="{filename}"' if download else f'inline; filename="{filename}"'
    )
    if is_s3_backend():
        settings = get_settings()
        url = get_s3_client().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": file_path,
                "ResponseContentType": "application/pdf",
                "ResponseContentDisposition": disposition,
            },
            ExpiresIn=settings.s3_presign_seconds,
        )
        return RedirectResponse(url, status_code=307, headers={"Cache-Control": "no-store"})

    path = (resolver or resolve_path)(file_path)
    if not path.is_file():
        raise FileNotFoundError(file_path)
    return FileResponse(
        path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": disposition if download else "inline",
        },
    )


def object_exists_with_size(client: Any, bucket: str, key: str, size: int) -> bool:
    try:
        return client.head_object(Bucket=bucket, Key=key).get("ContentLength") == size
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise
