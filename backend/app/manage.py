"""Synchronise course data and local PDF files with the database."""

import argparse
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Faculty, Resource, Subject, Term
from app.models.enums import ResourceType
from app.services.storage import storage_root


class CourseSubject(BaseModel):
    code: str
    name: str


class CourseTerm(BaseModel):
    season: Literal["fall", "winter"]
    academic_year: str
    is_freshers: bool
    subjects: list[str]


class CourseData(BaseModel):
    subjects: list[CourseSubject]
    terms: list[CourseTerm]


class FacultyEntry(BaseModel):
    name: str
    designation: str | None = None
    department: str | None = None
    email: str | None = None
    cabin: str | None = None

    @field_validator("name", "designation", "department", "email", "cabin", mode="before")
    @classmethod
    def blank_strings_are_missing(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


class FacultyData(BaseModel):
    faculty: list[FacultyEntry]


def load_courses(path: Path | None = None) -> CourseData:
    source = path or Path(__file__).parents[1] / "data" / "courses.json"
    return CourseData.model_validate_json(source.read_text(encoding="utf-8"))


def sync_courses(db: Session, path: Path | None = None) -> dict[str, int]:
    data = load_courses(path)
    subjects_by_code: dict[str, Subject] = {}
    added = updated = 0
    for item in data.subjects:
        subject = db.scalar(select(Subject).where(Subject.code == item.code))
        if subject is None:
            subject = Subject(code=item.code, name=item.name)
            db.add(subject)
            added += 1
        elif subject.name != item.name:
            subject.name = item.name
            updated += 1
        subjects_by_code[item.code] = subject
    db.flush()

    for item in data.terms:
        missing = [code for code in item.subjects if code not in subjects_by_code]
        if missing:
            raise ValueError(
                f"Term {item.season} {item.academic_year} references unknown subject code(s): "
                + ", ".join(missing)
            )
        term = db.scalar(
            select(Term).where(
                Term.season == item.season,
                Term.academic_year == item.academic_year,
                Term.is_freshers == item.is_freshers,
            )
        )
        name = f"{item.season.capitalize()} Semester {item.academic_year}"
        if item.is_freshers:
            name += " Freshers"
        subjects = [subjects_by_code[code] for code in item.subjects]
        if term is None:
            db.add(Term(name=name, season=item.season, academic_year=item.academic_year,
                        is_freshers=item.is_freshers, subjects=subjects))
            added += 1
        elif term.name != name or {s.code for s in term.subjects} != set(item.subjects):
            term.name = name
            term.subjects = subjects
            updated += 1
    db.commit()
    return {"added": added, "updated": updated, "removed": 0, "skipped": 0}


_PYQ_RE = re.compile(r"(cat-?1|cat-?2|fat)[-_ ]?(\d{4})", re.IGNORECASE)


def prettify_stem(stem: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[-_]+", " ", stem)).strip().title()


def parse_filename(stem: str) -> tuple[str | None, int | None, str]:
    match = _PYQ_RE.search(stem)
    if match is None:
        return None, None, prettify_stem(stem)
    exam = match.group(1).upper().replace("CAT1", "CAT-1").replace("CAT2", "CAT-2")
    year = int(match.group(2))
    return exam, year, f"{exam} {year}"


def sync_files(db: Session) -> dict[str, int]:
    root = storage_root()
    known = {subject.code: subject for subject in db.scalars(select(Subject)).all()}
    seen: set[str] = set()
    added = updated = skipped = 0
    if root.is_dir():
        course_dirs = root.iterdir()
    else:
        course_dirs = ()
    for course_dir in course_dirs:
        if not course_dir.is_dir():
            continue
        subject = known.get(course_dir.name)
        if subject is None:
            print(f"Skipped unknown course folder: {course_dir.name}")
            skipped += 1
            continue
        for folder, resource_type in (("pyq", ResourceType.pyq), ("notes", ResourceType.note)):
            resource_dir = course_dir / folder
            if not resource_dir.is_dir():
                continue
            for path in resource_dir.rglob("*"):
                if not path.is_file() or path.suffix.lower() != ".pdf":
                    continue
                relative = path.relative_to(root).as_posix()
                seen.add(relative)
                exam, year, title = (
                    parse_filename(path.stem)
                    if resource_type == ResourceType.pyq
                    else (None, None, prettify_stem(path.stem))
                )
                resource = db.scalar(select(Resource).where(Resource.file_path == relative))
                values = (title, exam, year, subject.id, resource_type)
                if resource is None:
                    db.add(Resource(subject_id=subject.id, type=resource_type, title=title,
                                    file_path=relative, exam=exam, year=year))
                    added += 1
                elif (
                    resource.title,
                    resource.exam,
                    resource.year,
                    resource.subject_id,
                    resource.type,
                ) != values:
                    resource.title, resource.exam, resource.year = title, exam, year
                    resource.subject_id, resource.type = subject.id, resource_type
                    updated += 1
    removed = db.execute(delete(Resource).where(Resource.file_path.not_in(seen))).rowcount
    db.commit()
    return {"added": added, "updated": updated, "removed": removed or 0, "skipped": skipped}


def sync_faculty(db: Session, path: Path | None = None) -> dict[str, int]:
    source = path or Path(__file__).parents[1] / "data" / "faculty.json"
    if not source.exists():
        print("Faculty file missing; copy data/faculty.example.json to data/faculty.json")
        return {"added": 0, "updated": 0, "removed": 0, "skipped": 1}
    data = FacultyData.model_validate_json(source.read_text(encoding="utf-8"))
    existing = db.scalars(select(Faculty).order_by(Faculty.id)).all()
    desired = [
        (entry.name, entry.designation, entry.department, entry.email, entry.cabin)
        for entry in data.faculty
    ]
    current = [
        (person.name, person.designation, person.department, person.email, person.cabin)
        for person in existing
    ]
    if current == desired:
        return {"added": 0, "updated": 0, "removed": 0, "skipped": 0}
    db.execute(delete(Faculty))
    db.add_all(
        [
            Faculty(
                name=name,
                designation=designation,
                department=department,
                email=email,
                cabin=cabin,
            )
            for name, designation, department, email, cabin in desired
        ]
    )
    db.commit()
    removed = len(existing)
    return {
        "added": len(desired),
        "updated": 0,
        "removed": removed,
        "skipped": 0,
    }


def print_summary(command: str, summary: dict[str, int]) -> None:
    print(f"{command}: " + ", ".join(f"{key} {value}" for key, value in summary.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("sync-courses", "sync-files", "sync-faculty", "sync")
    )
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "sync-courses":
            print_summary(args.command, sync_courses(db))
        elif args.command == "sync-files":
            print_summary(args.command, sync_files(db))
        elif args.command == "sync-faculty":
            print_summary(args.command, sync_faculty(db))
        else:
            print_summary("sync-courses", sync_courses(db))
            print_summary("sync-files", sync_files(db))
            print_summary("sync-faculty", sync_faculty(db))


if __name__ == "__main__":
    main()
