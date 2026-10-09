# NotesNest

NotesNest is a read-only study companion for BSc students: browse semesters
and subjects, view or download PYQs and notes, find faculty contact details,
and read practical advice articles.

## Features

- Semester and subject browsing
- Client-side subject filtering by code or name
- PYQ and notes tabs with View and Download actions
- Searchable, expandable faculty directory
- Markdown advice articles with category filters
- Owner-managed content files and idempotent sync commands

## Tech stack

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic
- **Database:** SQLite locally; models remain portable to PostgreSQL
- **Tooling:** Ruff, pytest, ESLint, TypeScript

## Quick start

The supported local workflow does not use Docker. Docker files exist for
future experimentation, but local non-Docker setup is the supported path.

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.manage sync
uvicorn app.main:app --reload
```

### Frontend

In a second terminal, while the backend is running on port 8000:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Create `frontend/.env.local` only when changing
the API URL from the default `http://localhost:8000`.

## Adding content

| Content | Location | Format | Sync command |
| --- | --- | --- | --- |
| Courses and terms | `backend/data/courses.json` | JSON | `python -m app.manage sync-courses` |
| PDFs | `backend/storage/<CODE>/pyq/` | PDF filenames such as `CAT-2025.pdf` (single CAT), `CAT1-2025.pdf`, `CAT2-2025.pdf`, `FAT-Theory-2025.pdf`, or `FAT-Lab-2025.pdf` | `python -m app.manage sync-files` |
| Faculty | `backend/data/faculty.json` | JSON; copy the example first | `python -m app.manage sync-faculty` |
| Advice | `backend/data/advice/*.md` | Markdown with frontmatter | `python -m app.manage sync-advice` |

Run `python -m app.manage sync` to run every sync in order. In S3 mode,
`sync-files` stores a SHA-256 metadata value with each upload and compares
content hashes on later runs, so replacing a PDF with another file of the same
size is detected. Use `python -m app.manage sync-files --force` (or
`sync --force`) to re-upload every PDF. The real faculty JSON and PDF files are
gitignored on purpose.

### Publishing new content

Add or replace PDFs under `backend/storage/<CODE>/pyq/`, then run
`python -m app.manage sync-files`. New files are uploaded, changed files are
uploaded again, and identical files are reported as unchanged. Older remote
objects without SHA-256 metadata are uploaded once to add the metadata.

On a subject page, CAT and FAT tabs are always shown. FAT papers are split into
Theory and Lab sections; Notes and Other appear only when they contain files.
Unrecognised PYQ filenames appear under Other. To remove old placeholder terms
or retired subjects, use `python -m app.manage sync-courses --prune` (or
`sync --prune`). Pruning permanently deletes unlisted terms, subjects,
resources, and stored files; review the printed plan and confirm with `yes`, or
use `--yes` deliberately.

Advice frontmatter requires `title`, `category`, and `summary`. `author` and
integer `order` are optional. Advice filenames must be lowercase kebab-case;
the filename stem becomes the article slug.

## Project structure

```text
backend/
  app/
    api/          # FastAPI routes
    core/         # Settings
    db/           # Database base and sessions
    models/       # SQLAlchemy models
    schemas/      # Pydantic schemas
    services/     # Storage helpers
  data/           # Course, faculty, and advice source files
  alembic/        # Database migrations
  tests/
frontend/
  src/
    app/           # App Router pages
    components/    # Shared UI
    lib/           # API helper and types
docs/
  architecture.md
```

## Screenshots

Screenshots are added by the owner:

- `docs/screenshots/home.png`
- `docs/screenshots/subject.png`
- `docs/screenshots/faculty.png`
- `docs/screenshots/advice.png`

## Deployment

The deployed architecture uses Vercel for both projects, Neon Postgres for the
database, and private Backblaze B2 storage for PDFs through signed URLs. See
the [deployment guide](docs/deployment.md). Before the first content sync,
run `python -m app.manage --env-file .env.production check-storage`.

## Roadmap

- [x] Project scaffold
- [x] Database models and migrations
- [x] PDF resources
- [x] Faculty directory
- [x] Advice articles
- [x] Subject filter
- [ ] AI features (RAG over notes and PYQs)
- [x] Deployment preparation for Vercel, Neon, and Backblaze B2

See the [architecture guide](docs/architecture.md) for the verified system
design, API reference, and content workflow.

## Validation

```powershell
cd backend
ruff check .
pytest
cd ..\frontend
npm run lint
npm run typecheck
npm run build
```
