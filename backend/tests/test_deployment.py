from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.responses import RedirectResponse

from app.core.config import Settings
from app.services import storage


def test_postgres_url_normalization():
    assert (
        Settings(database_url="postgres://user:pass@db.example/app").database_url
        == "postgresql+psycopg://user:pass@db.example/app"
    )
    assert (
        Settings(database_url="postgresql://user:pass@db.example/app").database_url
        == "postgresql+psycopg://user:pass@db.example/app"
    )


def test_s3_settings_require_credentials():
    with pytest.raises(ValueError, match="S3_BUCKET"):
        Settings(storage_backend="s3")


def test_s3_file_response_sets_disposition(monkeypatch):
    calls: list[dict[str, object]] = []
    settings = SimpleNamespace(
        storage_backend="s3",
        s3_bucket="notes",
        s3_presign_seconds=300,
    )

    class FakeClient:
        def generate_presigned_url(self, operation, *, Params, ExpiresIn):
            calls.append({"operation": operation, "params": Params, "expires": ExpiresIn})
            return "https://r2.example/signed"

    monkeypatch.setattr(storage, "get_settings", lambda: settings)
    monkeypatch.setattr(storage, "get_s3_client", lambda: FakeClient())

    response = storage.get_file_response("CSE0106/pyq/CAT1-2024.pdf")
    assert isinstance(response, RedirectResponse)
    assert response.status_code == 307
    assert response.headers["cache-control"] == "no-store"
    assert calls[0]["params"]["Key"] == "CSE0106/pyq/CAT1-2024.pdf"
    assert calls[0]["params"]["ResponseContentDisposition"] == (
        'inline; filename="CAT1-2024.pdf"'
    )

    storage.get_file_response("CSE0106/pyq/CAT1-2024.pdf", download=True)
    assert calls[1]["params"]["ResponseContentDisposition"] == (
        'attachment; filename="CAT1-2024.pdf"'
    )


def test_s3_sync_files_uploads_and_removes(tmp_path, monkeypatch, session_factory):
    from app.manage import sync_files
    from app.models import Resource, Subject
    from app.models.enums import ResourceType

    pdf = tmp_path / "CSE0106" / "pyq" / "CAT1-2024.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"pdf")

    class FakeClient:
        def __init__(self):
            self.objects: dict[str, int] = {"CSE0106/pyq/old.pdf": 10}
            self.uploaded: list[str] = []
            self.deleted: list[str] = []

        def head_object(self, *, Bucket, Key):
            if Key not in self.objects:
                from botocore.exceptions import ClientError

                raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
            return {"ContentLength": self.objects[Key]}

        def upload_file(self, filename, bucket, key):
            self.uploaded.append(key)
            self.objects[key] = Path(filename).stat().st_size

        def delete_object(self, *, Bucket, Key):
            self.deleted.append(Key)
            self.objects.pop(Key, None)

    fake = FakeClient()
    monkeypatch.setattr("app.manage.storage_root", lambda: tmp_path)
    monkeypatch.setattr("app.services.storage.is_s3_backend", lambda: True)
    monkeypatch.setattr("app.services.storage.get_s3_client", lambda: fake)
    monkeypatch.setattr(
        "app.core.config.get_settings",
        lambda: SimpleNamespace(s3_bucket="notes"),
    )

    with session_factory() as db:
        subject = db.query(Subject).filter_by(code="CSE0106").one()
        db.add(
            Resource(
                subject_id=subject.id,
                type=ResourceType.pyq,
                title="Old",
                file_path="CSE0106/pyq/old.pdf",
            )
        )
        db.commit()
        result = sync_files(db)

    assert result["uploaded"] == 1
    assert result["removed"] == 1
    assert fake.uploaded == ["CSE0106/pyq/CAT1-2024.pdf"]
    assert fake.deleted == ["CSE0106/pyq/old.pdf"]


def test_api_cache_headers(client):
    assert client.get("/api/v1/terms").headers["cache-control"] == (
        "public, max-age=0, s-maxage=300, stale-while-revalidate=600"
    )
    assert "cache-control" not in client.get("/api/v1/health").headers


def test_api_vary_origin_for_missing_allowed_and_disallowed_origins(client):
    no_origin = client.get("/api/v1/terms")
    assert "access-control-allow-origin" not in no_origin.headers
    assert no_origin.headers["vary"].lower().split(", ").count("origin") == 1

    allowed = client.get(
        "/api/v1/terms",
        headers={"Origin": "http://localhost:3000"},
    )
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert allowed.headers["vary"].lower().split(", ").count("origin") == 1

    disallowed = client.get(
        "/api/v1/terms",
        headers={"Origin": "https://not-allowed.example"},
    )
    assert "access-control-allow-origin" not in disallowed.headers
    assert disallowed.headers["vary"].lower().split(", ").count("origin") == 1


def test_confirmation_guard_requires_yes(monkeypatch):
    from app.manage import confirm_write

    settings = SimpleNamespace(
        database_url="postgresql+psycopg://user@db.example/app",
        s3_bucket="notes",
        storage_backend="s3",
    )
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("builtins.input", lambda _: "no")
    with pytest.raises(SystemExit, match="Aborted"):
        confirm_write(False)
