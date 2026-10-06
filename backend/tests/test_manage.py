import json

from app.manage import parse_filename, sync_courses, sync_files
from app.models import Resource, Subject
from app.models.enums import ResourceType


def test_filename_parsing():
    assert parse_filename("CAT1-2024") == ("CAT-1", 2024, "CAT-1 2024")
    assert parse_filename("cat-2_2023") == ("CAT-2", 2023, "CAT-2 2023")
    assert parse_filename("FAT 2022") == ("FAT", 2022, "FAT 2022")
    assert parse_filename("midterm") == (None, None, "Midterm")


def test_sync_courses_unknown_subject_is_clear(session_factory, tmp_path):
    path = tmp_path / "courses.json"
    path.write_text(json.dumps({
        "subjects": [{"code": "KNOWN", "name": "Known"}],
        "terms": [{
            "season": "fall",
            "academic_year": "2026-27",
            "is_freshers": False,
            "subjects": ["MISSING"],
        }],
    }))
    with session_factory() as db:
        try:
            sync_courses(db, path)
        except ValueError as exc:
            assert "MISSING" in str(exc)
        else:
            raise AssertionError("sync_courses accepted an unknown subject code")


def test_sync_files_is_idempotent_and_removes_missing(session_factory, tmp_path, monkeypatch):
    root = tmp_path / "storage"
    pyq = root / "SAMPLE101" / "pyq"
    notes = root / "SAMPLE101" / "notes"
    pyq.mkdir(parents=True)
    notes.mkdir()
    (pyq / "CAT1-2024.pdf").write_bytes(b"%PDF")
    (pyq / "cat-2_2023.pdf").write_bytes(b"%PDF")
    (pyq / "FAT 2022.pdf").write_bytes(b"%PDF")
    (pyq / "unmatched_name.pdf").write_bytes(b"%PDF")
    (notes / "lecture_notes.pdf").write_bytes(b"%PDF")
    (root / "UNKNOWN" / "pyq").mkdir(parents=True)
    (root / "UNKNOWN" / "pyq" / "FAT-2020.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr("app.manage.storage_root", lambda: root)

    with session_factory() as db:
        first = sync_files(db)
        second = sync_files(db)
        assert first == {"added": 5, "updated": 0, "removed": 0, "skipped": 1}
        assert second == {"added": 0, "updated": 0, "removed": 0, "skipped": 1}
        resources = db.query(Resource).order_by(Resource.title).all()
        assert [resource.type for resource in resources].count(ResourceType.note) == 1
        (notes / "lecture_notes.pdf").unlink()
        result = sync_files(db)
        assert result["removed"] == 1


def test_file_endpoint_headers_and_missing_file(client, session_factory, tmp_path, monkeypatch):
    path = tmp_path / "SAMPLE101" / "pyq" / "CAT1-2024.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.4")
    with session_factory() as db:
        subject = db.query(Subject).filter_by(code="SAMPLE101").one()
        resource = Resource(
            subject_id=subject.id,
            type=ResourceType.pyq,
            title="CAT-1 2024",
            file_path="SAMPLE101/pyq/CAT1-2024.pdf",
            exam="CAT-1",
            year=2024,
        )
        db.add(resource)
        db.commit()
        resource_id = resource.id
    monkeypatch.setattr(
        "app.api.routes.resources.resolve_path",
        lambda file_path: (
            path if file_path == "SAMPLE101/pyq/CAT1-2024.pdf" else tmp_path / "missing"
        ),
    )
    inline = client.get(f"/api/v1/resources/{resource_id}/file")
    download = client.get(f"/api/v1/resources/{resource_id}/file?download=1")
    assert inline.status_code == download.status_code == 200
    assert inline.headers["content-disposition"] == "inline"
    assert download.headers["content-disposition"] == 'attachment; filename="CAT1-2024.pdf"'
    assert client.get("/api/v1/resources/9999/file").status_code == 404
