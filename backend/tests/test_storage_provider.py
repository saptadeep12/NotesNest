from types import SimpleNamespace

from app.core.config import Settings
from app.services import storage


def test_boto_client_config_has_checksums_retries_and_optional_path_style(monkeypatch):
    captured = {}

    def fake_client(*args, **kwargs):
        captured.update(kwargs)
        return object()

    settings = SimpleNamespace(
        s3_endpoint_url="https://s3.example",
        s3_access_key_id="key",
        s3_secret_access_key="secret",
        s3_region="test",
        s3_force_path_style=False,
    )
    monkeypatch.setattr(storage, "get_settings", lambda: settings)
    monkeypatch.setattr(storage.boto3, "client", fake_client)
    storage.get_s3_client()
    config = captured["config"]
    assert config.request_checksum_calculation == "when_required"
    assert config.response_checksum_validation == "when_required"
    assert config.retries == {"max_attempts": 5, "mode": "standard"}
    assert config.s3 is None

    settings.s3_force_path_style = True
    storage.get_s3_client()
    assert captured["config"].s3["addressing_style"] == "path"


def test_settings_does_not_read_aws_environment(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "unexpected")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "unexpected")
    settings = Settings()
    assert settings.s3_access_key_id is None
    assert settings.s3_secret_access_key is None


def test_check_storage_happy_path(monkeypatch, capsys):
    from app.manage import check_storage

    class Response:
        status = 200

        def __init__(self, disposition):
            self.headers = {
                "Content-Type": "text/plain",
                "Content-Disposition": disposition,
            }

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class Client:
        def put_object(self, **_kwargs):
            return None

        def head_object(self, **_kwargs):
            return {}

        def generate_presigned_url(self, _operation, Params, ExpiresIn):
            return Params["ResponseContentDisposition"]

        def delete_object(self, **_kwargs):
            return None

    settings = SimpleNamespace(
        storage_backend="s3", s3_bucket="bucket", s3_presign_seconds=300
    )
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.storage.get_s3_client", lambda: Client())
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda url, **_kwargs: Response(url),
    )
    assert check_storage() == 0
    assert "PASS: storage check completed" in capsys.readouterr().out


def test_check_storage_failing_override(monkeypatch, capsys):
    from app.manage import check_storage

    class Response:
        status = 200
        headers = {"Content-Type": "text/plain", "Content-Disposition": "inline"}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class Client:
        def put_object(self, **_kwargs):
            return None

        def head_object(self, **_kwargs):
            return {}

        def generate_presigned_url(self, _operation, Params, ExpiresIn):
            return "https://signed.example"

        def delete_object(self, **_kwargs):
            return None

    settings = SimpleNamespace(
        storage_backend="s3", s3_bucket="bucket", s3_presign_seconds=300
    )
    monkeypatch.setattr("app.core.config.get_settings", lambda: settings)
    monkeypatch.setattr("app.services.storage.get_s3_client", lambda: Client())
    monkeypatch.setattr("urllib.request.urlopen", lambda *_args, **_kwargs: Response())
    assert check_storage() == 1
    assert "forced downloads may not work" in capsys.readouterr().out
