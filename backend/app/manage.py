"""Synchronise course data and local PDF files with the database."""

import argparse
import os
import re
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, field_validator
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Article, Faculty, Resource, Subject, Term
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


class ArticleFrontmatter(BaseModel):
    title: str
    category: str
    summary: str
    author: str | None = None
    order: int = 100

    @field_validator("title", "category", "summary", "author", mode="before")
    @classmethod
    def article_blank_strings_are_missing(cls, value: object) -> object:
        return None if isinstance(value, str) and not value.strip() else value


def parse_article_file(path: Path) -> tuple[str, ArticleFrontmatter, str, datetime]:
    slug = path.stem
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is None:
        raise ValueError(f"{path.name}: slug must be lowercase kebab-case")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: missing frontmatter opening fence")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError(f"{path.name}: missing frontmatter closing fence") from exc
    values: dict[str, str] = {}
    for line_number, line in enumerate(lines[1:closing], start=2):
        if not line.strip() or ":" not in line:
            raise ValueError(f"{path.name}: invalid frontmatter on line {line_number}")
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key:
            raise ValueError(f"{path.name}: frontmatter key is empty on line {line_number}")
        values[key] = value
    try:
        frontmatter = ArticleFrontmatter.model_validate(values)
    except ValueError as exc:
        raise ValueError(f"{path.name}: invalid frontmatter: {exc}") from exc
    body = "\n".join(lines[closing + 1:]).strip()
    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(
        tzinfo=None
    )
    return slug, frontmatter, body, modified_at


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
    from app.core.config import get_settings
    from app.services.storage import (
        get_s3_client,
        is_s3_backend,
        object_exists_with_size,
    )

    root = storage_root()
    settings = get_settings()
    s3 = get_s3_client() if is_s3_backend() else None
    known = {subject.code: subject for subject in db.scalars(select(Subject)).all()}
    seen: set[str] = set()
    added = updated = skipped = 0
    uploaded = unchanged = 0
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
                if s3 is not None:
                    if object_exists_with_size(
                        s3, settings.s3_bucket or "", relative, path.stat().st_size
                    ):
                        unchanged += 1
                    else:
                        s3.upload_file(str(path), settings.s3_bucket, relative)
                        uploaded += 1
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
    stale_resources = db.scalars(select(Resource).where(Resource.file_path.not_in(seen))).all()
    for resource in stale_resources:
        if s3 is not None:
            s3.delete_object(Bucket=settings.s3_bucket, Key=resource.file_path)
    removed = len(stale_resources)
    db.execute(delete(Resource).where(Resource.file_path.not_in(seen)))
    db.commit()
    result = {"added": added, "updated": updated, "removed": removed, "skipped": skipped}
    if s3 is not None:
        result.update({"uploaded": uploaded, "unchanged": unchanged})
    return result


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


def sync_advice(db: Session, directory: Path | None = None) -> dict[str, int]:
    advice_dir = directory or Path(__file__).parents[1] / "data" / "advice"
    files = sorted(advice_dir.glob("*.md")) if advice_dir.is_dir() else []
    parsed = [parse_article_file(path) for path in files]
    existing = {article.slug: article for article in db.scalars(select(Article)).all()}
    seen = {slug for slug, _, _, _ in parsed}
    added = updated = 0
    for slug, frontmatter, body, modified_at in parsed:
        article = existing.get(slug)
        values = (
            frontmatter.title,
            frontmatter.category,
            frontmatter.summary,
            body,
            frontmatter.author,
            frontmatter.order,
            modified_at,
        )
        if article is None:
            db.add(
                Article(
                    slug=slug,
                    title=frontmatter.title,
                    category=frontmatter.category,
                    summary=frontmatter.summary,
                    body=body,
                    author=frontmatter.author,
                    order=frontmatter.order,
                    updated_at=modified_at,
                )
            )
            added += 1
        elif (
            article.title,
            article.category,
            article.summary,
            article.body,
            article.author,
            article.order,
            article.updated_at,
        ) != values:
            (
                article.title,
                article.category,
                article.summary,
                article.body,
                article.author,
                article.order,
                article.updated_at,
            ) = values
            updated += 1
    removed = db.execute(delete(Article).where(Article.slug.not_in(seen))).rowcount
    db.commit()
    return {"added": added, "updated": updated, "removed": removed or 0}


def print_summary(command: str, summary: dict[str, int]) -> None:
    print(f"{command}: " + ", ".join(f"{key} {value}" for key, value in summary.items()))


def load_env_file(path: Path) -> None:
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip("\"'")


def target_description() -> tuple[str, str]:
    from app.core.config import get_settings

    settings = get_settings()
    return urlsplit(settings.database_url).hostname or "unknown", settings.s3_bucket or "(local)"


def confirm_write(yes: bool) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    remote = not settings.database_url.startswith("sqlite") or settings.storage_backend == "s3"
    if not remote or yes:
        return
    host, bucket = target_description()
    print(f"Target database host: {host}")
    print(f"Target storage bucket: {bucket}")
    if input("Type 'yes' to continue: ").strip().lower() != "yes":
        raise SystemExit("Aborted.")


def check_storage() -> int:
    from app.core.config import get_settings
    from app.services.storage import get_s3_client

    settings = get_settings()
    if settings.storage_backend != "s3":
        print("FAIL: STORAGE_BACKEND must be s3 for check-storage")
        return 1
    client = get_s3_client()
    key = f"healthcheck/notesnest-{os.getpid()}.txt"
    body = b"NotesNest storage healthcheck\n"
    failed = False
    try:
        client.put_object(Bucket=settings.s3_bucket, Key=key, Body=body, ContentType="text/plain")
        print("PASS: uploaded healthcheck object")
        client.head_object(Bucket=settings.s3_bucket, Key=key)
        print("PASS: HEAD healthcheck object")
        for label, disposition in (
            ("inline", 'inline; filename="notesnest-healthcheck.txt"'),
            ("attachment", 'attachment; filename="notesnest-healthcheck.txt"'),
        ):
            url = client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.s3_bucket,
                    "Key": key,
                    "ResponseContentType": "text/plain",
                    "ResponseContentDisposition": disposition,
                },
                ExpiresIn=settings.s3_presign_seconds,
            )
            with urllib.request.urlopen(url, timeout=30) as response:
                actual_type = response.headers.get("Content-Type", "")
                actual_disposition = response.headers.get("Content-Disposition", "")
                print(
                    f"{'PASS' if response.status == 200 else 'FAIL'}: {label} GET "
                    f"status={response.status} Content-Type={actual_type} "
                    f"Content-Disposition={actual_disposition}"
                )
                if response.status != 200 or disposition != actual_disposition:
                    print(
                        "Content-Disposition was missing or ignored; forced downloads may "
                        "not work with this provider. Report this to the owner."
                    )
                    failed = True
    except Exception as exc:
        print(f"FAIL: storage verification failed ({type(exc).__name__})")
        failed = True
    finally:
        try:
            client.delete_object(Bucket=settings.s3_bucket, Key=key)
            print("PASS: deleted healthcheck object")
        except Exception as exc:
            print(f"FAIL: could not delete healthcheck object ({type(exc).__name__})")
            failed = True
    if not failed:
        print("PASS: storage check completed")
    return int(failed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument(
        "command",
        choices=(
            "sync-courses",
            "sync-files",
            "sync-faculty",
            "sync-advice",
            "sync",
            "check-storage",
        ),
    )
    args = parser.parse_args()
    if args.env_file:
        load_env_file(args.env_file)
    from app.core.config import get_settings

    get_settings()
    confirm_write(args.yes)
    if args.command == "check-storage":
        raise SystemExit(check_storage())
    from app.db.session import get_session_factory

    with get_session_factory()() as db:
        if args.command == "sync-courses":
            print_summary(args.command, sync_courses(db))
        elif args.command == "sync-files":
            print_summary(args.command, sync_files(db))
        elif args.command == "sync-faculty":
            print_summary(args.command, sync_faculty(db))
        elif args.command == "sync-advice":
            print_summary(args.command, sync_advice(db))
        else:
            print_summary("sync-courses", sync_courses(db))
            print_summary("sync-files", sync_files(db))
            print_summary("sync-faculty", sync_faculty(db))
            print_summary("sync-advice", sync_advice(db))


if __name__ == "__main__":
    main()
