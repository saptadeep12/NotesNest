# Contributing to NotesNest

Thanks for helping out! NotesNest is a small, read-only app that helps students find question papers, faculty info and advice. Contributions of all sizes are welcome.

If you find NotesNest useful, please give the repo a ⭐. It helps the project reach more students and grow.

## Before you start

1. Browse the [open issues](../../issues). Issues labelled `good first issue` are the best place to begin.
2. Got a new idea? Open an issue first and describe it. Please don't send a large PR out of nowhere.

## Picking an issue

- **One issue at a time.** Finish (or drop) your current issue before taking another, so more people get a chance to contribute.
- **Comment before you start** (e.g. "I'd like to work on this") so others know it's taken.
- **If someone has already commented**, don't start working right away. Reply and ask if they are still working on it, or if they're open to you contributing.
- **No reply?** Give it a few days, then ping a maintainer before picking it up.
- **Changed your mind?** Leave a quick comment so someone else can take the issue.

## Project layout

- `backend/`: FastAPI + SQLAlchemy + Alembic (read-only API)
- `frontend/`: Next.js web app
- `backend/README.md`: full map of the backend (data model, API, commands)

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m app.manage sync
uvicorn app.main:app --reload
```

- API runs at `http://localhost:8000`, interactive docs at `/docs`.
- Defaults use SQLite and a local `storage/` folder, so no setup or secrets are needed.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- App runs at `http://localhost:3000`.
- Point it at your local backend (check `frontend/.env.example` for the variable name).

## Branches and commits

- Fork the repo, then branch off `main`.
- Branch names: `type/short-description`
  - `feat/dark-mode-toggle`
  - `fix/navbar-overflow-mobile`
  - `docs/update-setup-steps`
  - `chore/update-deps`
- Commit messages: short, present tense, imperative.
  - Good: `Add loading skeletons to papers page`
  - Avoid: `fixed stuff`, `changes`
- Keep PRs focused: one issue per PR.

## Before opening a PR

Run these and make sure they pass.

**Backend**
```bash
cd backend
ruff check .
pytest
```

**Frontend**
```bash
cd frontend
npm run lint
npm run build
```

## Pull request checklist

- [ ] Linked the issue (`Closes #123`)
- [ ] Lint and tests pass locally
- [ ] Tested on mobile width (360px) and desktop
- [ ] Added screenshots or a short screen recording for UI changes (before/after)
- [ ] Added or updated tests for backend changes
- [ ] Updated docs (`backend/README.md`) if you changed an endpoint, model or command
- [ ] No unrelated changes or formatting-only churn

## Hard rules

- **No secrets.** Never commit `.env`, `.env.production`, database URLs or bucket keys. If you accidentally leak one, tell a maintainer immediately so it can be rotated.
- **No PDFs, `storage/` files or `faculty.json`** in PRs. They are gitignored on purpose. For testing, use your own dummy files locally.
- **Do not run `sync` against production.** Content changes are handled by the maintainer only.
- **Do not add `pyproject.toml` to `backend/`.** It breaks the Vercel build. Keep config in `ruff.toml` and `pytest.ini`.
- If you change a database model, include the generated Alembic migration and mention it in the PR.

## Code style

- **Python:** follow `ruff.toml`. Routes stay thin, file access only goes through `app/services/storage.py`.
- **Frontend:** keep components small and reusable, prefer accessible HTML (semantic tags, labels, focus states), and respect `prefers-reduced-motion` for animations.
- Match the surrounding code style rather than introducing new patterns.

## Getting help

Stuck? Comment on your issue or open a draft PR and ask. No question is too small.

## Code of conduct

Be kind and respectful. Constructive feedback only. Harassment or discrimination isn't tolerated.

## Enjoying NotesNest?

If it helped you, please ⭐ star the repo. It's a small thing that helps the project grow and reach more students. Thank you!
