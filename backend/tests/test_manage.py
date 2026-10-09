import json

from app.manage import load_courses, parse_filename, prune_courses, sync_courses, sync_files
from app.models import Resource, Subject, Term
from app.models.enums import ResourceType


def test_filename_parsing():
    assert parse_filename("CAT1-2024") == ("CAT-1", 2024, "CAT-1 2024")
    assert parse_filename("cat-2_2023") == ("CAT-2", 2023, "CAT-2 2023")
    assert parse_filename("CAT-2025") == ("CAT", 2025, "CAT 2025")
    assert parse_filename("cat_2025") == ("CAT", 2025, "CAT 2025")
    assert parse_filename("CAT2025") == ("CAT", 2025, "CAT 2025")
    assert parse_filename("CAT1-2025") == ("CAT-1", 2025, "CAT-1 2025")
    assert parse_filename("CAT2-2025") == ("CAT-2", 2025, "CAT-2 2025")
    assert parse_filename("FAT 2022") == ("FAT-Theory", 2022, "FAT Theory 2022")
    assert parse_filename("FAT-Theory-2025") == ("FAT-Theory", 2025, "FAT Theory 2025")
    assert parse_filename("fat_lab 2024") == ("FAT-Lab", 2024, "FAT Lab 2024")
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
    pyq = root / "CSE0106" / "pyq"
    notes = root / "CSE0106" / "notes"
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


def test_sync_files_warns_for_unrecognised_pyq(session_factory, tmp_path, monkeypatch, capsys):
    pyq = tmp_path / "CSE0106" / "pyq"
    pyq.mkdir(parents=True)
    (pyq / "midterm.pdf").write_bytes(b"%PDF")
    monkeypatch.setattr("app.manage.storage_root", lambda: tmp_path)
    monkeypatch.setattr("app.services.storage.storage_root", lambda: tmp_path)

    with session_factory() as db:
        sync_files(db)

    assert "it will appear under 'Other'" in capsys.readouterr().out


def test_prune_courses_removes_unlisted_subject_and_term(
    session_factory, tmp_path, monkeypatch
):
    from app.models.enums import ResourceType

    old_file = tmp_path / "OLD999" / "pyq" / "CAT1-2020.pdf"
    old_file.parent.mkdir(parents=True)
    old_file.write_bytes(b"%PDF")
    monkeypatch.setattr("app.manage.storage_root", lambda: tmp_path)
    monkeypatch.setattr("app.services.storage.storage_root", lambda: tmp_path)
    with session_factory() as db:
        old_subject = Subject(code="OLD999", name="Old")
        db.add(old_subject)
        db.flush()
        db.add(Term(
            name="Winter Semester 2020-21",
            season="winter",
            academic_year="2020-21",
            is_freshers=False,
            subjects=[old_subject],
        ))
        db.add(Resource(
            subject_id=old_subject.id,
            type=ResourceType.pyq,
            title="Old",
            file_path="OLD999/pyq/CAT1-2020.pdf",
        ))
        db.commit()
        prune_courses(db, load_courses(), yes=True)
        assert db.query(Subject).filter_by(code="OLD999").one_or_none() is None
        assert db.query(Term).filter_by(academic_year="2020-21").one_or_none() is None
        assert (
            db.query(Resource)
            .filter_by(file_path="OLD999/pyq/CAT1-2020.pdf")
            .one_or_none()
            is None
        )
    assert not old_file.exists()


def test_prune_courses_requires_confirmation(session_factory, monkeypatch):
    with session_factory() as db:
        db.add(Term(
            name="Winter Semester 2020-21",
            season="winter",
            academic_year="2020-21",
            is_freshers=False,
        ))
        db.commit()
        monkeypatch.setattr("builtins.input", lambda _: "no")
        try:
            prune_courses(db, load_courses())
        except SystemExit as exc:
            assert str(exc) == "Aborted."
        else:
            raise AssertionError("prune_courses did not require confirmation")


def test_file_endpoint_headers_and_missing_file(client, session_factory, tmp_path, monkeypatch):
    path = tmp_path / "CSE0106" / "pyq" / "CAT1-2024.pdf"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"%PDF-1.4")
    with session_factory() as db:
        subject = db.query(Subject).filter_by(code="CSE0106").one()
        resource = Resource(
            subject_id=subject.id,
            type=ResourceType.pyq,
            title="CAT-1 2024",
            file_path="CSE0106/pyq/CAT1-2024.pdf",
            exam="CAT-1",
            year=2024,
        )
        db.add(resource)
        db.commit()
        resource_id = resource.id
    monkeypatch.setattr(
        "app.api.routes.resources.resolve_path",
        lambda file_path: (
            path if file_path == "CSE0106/pyq/CAT1-2024.pdf" else tmp_path / "missing"
        ),
    )
    inline = client.get(f"/api/v1/resources/{resource_id}/file")
    download = client.get(f"/api/v1/resources/{resource_id}/file?download=1")
    assert inline.status_code == download.status_code == 200
    assert "cache-control" not in inline.headers
    assert inline.headers["content-disposition"] == "inline"
    assert download.headers["content-disposition"] == 'attachment; filename="CAT1-2024.pdf"'
    assert client.get("/api/v1/resources/9999/file").status_code == 404
