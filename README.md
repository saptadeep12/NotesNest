# NotesNest

NotesNest is a read-only study companion for BSc students: browse semesters
and subjects, view or download PYQs and notes, find faculty contact details,
and read practical advice articles.

## Features

- Semester and subject browsing
- Client-side subject filtering by code or name
- PYQ and notes tabs with View and Download actions
- Searchable faculty directory
- Markdown advice articles with category filters
- Owner-managed content files and idempotent sync commands

## Tech stack

- **Frontend:** Next.js 14, React, TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic
- **Local database:** SQLite
- **Production database:** Neon Postgres
- **Production PDF storage:** Private Cloudflare R2 bucket
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

Open http://localhost:3000. See [deployment.md](docs/deployment.md) for the
Vercel, Neon, and R2 setup. The backend migrations are run from the owner's
machine against Neon, not during deployment.

## Adding content

| Content | Location | Format | Sync command |
| --- | --- | --- | --- |
| Courses and terms | `backend/data/courses.json` | JSON | `python -m app.manage sync-courses` |
| PDFs | `backend/storage/<CODE>/pyq` or `notes` | PDF | `python -m app.manage sync-files` |
| Faculty | `backend/data/faculty.json` | JSON; copy the example first | `python -m app.manage sync-faculty` |
| Advice | `backend/data/advice/*.md` | Markdown with frontmatter | `python -m app.manage sync-advice` |

Run `python -m app.manage sync` to run every sync in order. For production,
use `python -m app.manage --env-file .env.production sync`; remote write
commands ask for confirmation unless `--yes` is supplied. Content API caching
means a published change may take up to about five minutes to appear.

Advice frontmatter requires `title`, `category`, and `summary`. `author` and
integer `order` are optional. Advice filenames must be lowercase kebab-case;
the filename stem becomes the article slug. Real faculty JSON and PDFs are
gitignored on purpose.

## Project structure

```text
backend/
  app/{api,core,db,models,schemas,services}/
  data/{courses.json,advice/,faculty.example.json}
  alembic/
  tests/
frontend/
  src/{app,components,lib}/
docs/
  architecture.md
  deployment.md
```

## Screenshots

Screenshots are added by the owner:

- `docs/screenshots/home.png`
- `docs/screenshots/subject.png`
- `docs/screenshots/faculty.png`
- `docs/screenshots/advice.png`

## Roadmap

- [x] Project scaffold
- [x] Database models and migrations
- [x] PDF resources
- [x] Faculty directory
- [x] Advice articles
- [x] Subject filter
- [x] Vercel-ready production configuration
- [ ] AI features (RAG over notes and PYQs)

See the [architecture guide](docs/architecture.md) for the verified system
design and API reference.

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
