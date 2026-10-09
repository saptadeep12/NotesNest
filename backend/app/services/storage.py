from collections.abc import Callable
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config
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
    s3_options: dict[str, str] = {}
    if settings.s3_force_path_style:
        s3_options["addressing_style"] = "path"
    config = Config(
        signature_version="s3v4",
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
        retries={"max_attempts": 5, "mode": "standard"},
        s3=s3_options or None,
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
        config=config,
    )


def safe_filename(file_path: str) -> str:
    name = Path(file_path).name
    return name.encode("ascii", "ignore").decode("ascii").strip() or "resource.pdf"


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
        headers={"Content-Disposition": disposition if download else "inline"},
    )


def object_exists_with_size(client: Any, bucket: str, key: str, size: int) -> bool:
    try:
        return client.head_object(Bucket=bucket, Key=key).get("ContentLength") == size
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise


def delete_stored_file(file_path: str, client: Any | None = None) -> None:
    if is_s3_backend():
        settings = get_settings()
        (client or get_s3_client()).delete_object(
            Bucket=settings.s3_bucket,
            Key=file_path,
        )
        return
    path = resolve_path(file_path)
    if path.is_file():
        path.unlink()
