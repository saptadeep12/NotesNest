import json

from app.manage import sync_faculty
from app.models import Faculty


def test_sync_faculty_mirrors_file_and_is_idempotent(session_factory, tmp_path):
    path = tmp_path / "faculty.json"
    path.write_text(
        json.dumps(
            {
                "faculty": [
                    {"name": "Zed", "email": "zed@example.edu"},
                    {"name": "Ada", "department": "Computing"},
                ]
            }
        )
    )
    with session_factory() as db:
        assert sync_faculty(db, path)["added"] == 2
        assert sync_faculty(db, path) == {
            "added": 0,
            "updated": 0,
            "removed": 0,
            "skipped": 0,
        }
        path.write_text(json.dumps({"faculty": [{"name": "Ada"}]}))
        result = sync_faculty(db, path)
        assert result["removed"] == 2
        assert [person.name for person in db.query(Faculty).all()] == ["Ada"]


def test_sync_faculty_missing_file_is_skipped(session_factory, tmp_path, capsys):
    with session_factory() as db:
        result = sync_faculty(db, tmp_path / "missing.json")
    assert result["skipped"] == 1
    assert "copy data/faculty.example.json to data/faculty.json" in capsys.readouterr().out


def test_sync_faculty_requires_name(session_factory, tmp_path):
    path = tmp_path / "faculty.json"
    path.write_text(json.dumps({"faculty": [{"designation": "Professor"}]}))
    with session_factory() as db:
        try:
            sync_faculty(db, path)
        except ValueError as exc:
            assert "name" in str(exc)
        else:
            raise AssertionError("sync_faculty accepted an entry without a name")


def test_list_faculty_is_case_insensitive_and_includes_all_fields(client, session_factory):
    with session_factory() as db:
        db.add_all(
            [
                Faculty(
                    name="zoe",
                    designation="Lecturer",
                    department="Physics",
                    email="zoe@example.edu",
                    cabin="B-2",
                ),
                Faculty(name="Ada", department="Computing"),
            ]
        )
        db.commit()
    response = client.get("/api/v1/faculty")
    assert response.status_code == 200
    assert [person["name"] for person in response.json()] == ["Ada", "zoe"]
    assert response.json()[1]["email"] == "zoe@example.edu"
    assert response.json()[0]["designation"] is None
