# NotesNest

A web app for BSc students: previous year papers (PYQs), notes, faculty details and advice from seniors, organised by semester and subject.

## Stack
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS
- **Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic
- **Database:** SQLite locally (models remain portable to PostgreSQL)
- **Tooling:** Docker Compose, GitHub Actions, Ruff, pytest, ESLint

## Run locally (no Docker)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.manage sync
uvicorn app.main:app --reload
```
The API docs are available at http://localhost:8000/docs. In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
The backend must be running on port 8000. Create `frontend/.env.local` only if
you need to use a different API URL.

## Adding content
Course and term metadata lives in `backend/data/courses.json`. Add subjects by
course code, then list their codes under each term. Only fall and winter terms
are supported. Store PDFs under `backend/storage/<COURSE_CODE>/pyq/` or
`backend/storage/<COURSE_CODE>/notes/`. PYQ filenames can use `CAT1-2024`,
`cat-2_2023`, or `FAT 2022`; notes use their filename as the title. Re-run
`python -m app.manage sync` after changing the JSON or adding/removing files.

Faculty data lives in `backend/data/faculty.json`. Copy
`backend/data/faculty.example.json` to create it, edit the entries, then run
`python -m app.manage sync` or `python -m app.manage sync-faculty`. The real
faculty JSON and storage PDFs are gitignored on purpose.

## Tests and linting
```bash
cd backend && ruff check . && pytest
cd frontend && npm run lint && npm run typecheck
```

## Structure
```
backend/app/{api,core,db,models,schemas,services}
frontend/src/{app,lib}
docs/
```

## Roadmap
- [x] Project scaffold
- [x] Models and migrations
- [ ] Resources (PYQs, notes) improvements
- [ ] Faculty directory and advice board
- [ ] Search
- [ ] AI features (RAG over notes and PYQs)
