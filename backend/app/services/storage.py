from pathlib import Path

from app.core.config import get_settings


def storage_root() -> Path:
    return Path(get_settings().storage_dir).resolve()


def resolve_path(file_path: str) -> Path:
    root = storage_root()
    candidate = (root / file_path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("File path escapes the storage directory")
    return candidate
