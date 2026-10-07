# Deployment guide

This guide follows Vercel's FastAPI/Python runtime model: the backend project
has root directory `backend`, exposes the `app` object from `app/main.py`, and
runs as a Vercel Function. The frontend is a separate Next.js project with root
directory `frontend`.

## 1. Create Neon Postgres

Create a Neon project and database, then copy its pooled connection string.
Use it as `DATABASE_URL`. The application accepts Neon `postgresql://` and
`postgres://` URLs and normalizes them to the installed psycopg 3 driver.
Keep the SSL options supplied by Neon in the connection string.

From the owner's machine, after setting that URL in a private env file:

```powershell
cd backend
alembic upgrade head
```

Migrations are intentionally not run during Vercel deployment.

## 2. Create private Cloudflare R2 storage

Create a private R2 bucket and an API token scoped to that bucket with object
read/write permission. Record the bucket name and the S3 endpoint URL:
`https://<account-id>.r2.cloudflarestorage.com`.

Use the R2 S3-compatible values for `S3_BUCKET`, `S3_ENDPOINT_URL`,
`S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, and `S3_REGION=auto`.

## 3. Create the backend Vercel project

Import the repository as a new Vercel project and set its root directory to
`backend`. The Python runtime detects `app/main.py` and its top-level `app`
FastAPI object. No custom build command is required.

Set these backend environment variables:

| Variable | Value |
| --- | --- |
| `APP_ENV` | `production` |
| `DATABASE_URL` | Neon pooled connection string |
| `CORS_ORIGINS` | Frontend Vercel URL; comma-separated if needed |
| `STORAGE_BACKEND` | `s3` |
| `S3_BUCKET` | Private R2 bucket name |
| `S3_ENDPOINT_URL` | R2 S3 endpoint |
| `S3_ACCESS_KEY_ID` | R2 token access key |
| `S3_SECRET_ACCESS_KEY` | R2 token secret |
| `S3_REGION` | `auto` |
| `S3_PRESIGN_SECONDS` | `300` |
| `SECRET_KEY` | A generated secret value |

## 4. Create the frontend Vercel project

Create a second Vercel project from the same repository and set its root
directory to `frontend`. Set:

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Deployed backend URL |

The frontend does not need any other production setting.

## 5. Set CORS

Update the backend `CORS_ORIGINS` value to the exact deployed frontend origin,
for example `https://notesnest.example`. Multiple origins are comma-separated.
Redeploy the backend after changing it.

## 6. Publish the initial content

On the owner's machine, create `.env.production` with the production database,
R2, and CORS values. Do not commit it. Then run:

```powershell
cd backend
python -m app.manage --env-file .env.production sync
```

Because this targets a remote database and R2, the command prints the database
host and bucket and asks for `yes`. Add `--yes` only when the target has been
checked.

## 7. Smoke-test checklist

- Open the frontend and choose a semester.
- Open a subject and view a PDF in a new tab.
- Download a PDF and confirm the attachment filename.
- Open Faculty and expand a card.
- Open Advice and a full article.
- Open an unknown subject, article, and resource URL to confirm 404 handling.

## Publishing new content

Edit the course JSON, faculty JSON, advice Markdown, or local PDF folders, then
run the production sync command again:

```powershell
cd backend
python -m app.manage --env-file .env.production sync
```

Successful API GET responses are cached at the edge for five minutes with
stale-while-revalidate, so allow up to about five minutes for published
metadata to appear. PDF URLs are short-lived presigned redirects.

## Troubleshooting

- **CORS errors:** Check that `CORS_ORIGINS` contains the exact frontend origin,
  without a trailing path, and redeploy the backend.
- **Database connection errors:** Confirm the Neon pooled URL, credentials,
  SSL parameters, and that the database is reachable. Run `alembic upgrade head`
  locally against the same URL.
- **Missing PDFs:** Check the R2 bucket/key and run `sync-files` with the
  production env file. Confirm the R2 token can read and write that bucket.

## Assumptions

Vercel's current Python runtime documentation says supported entrypoints such
as `app/main.py` with a top-level `app` object are auto-detected. The backend
also includes `vercel.json` with function bundle exclusions for local-only
content. Dashboard labels and exact Neon/R2 UI steps may change, so only the
stable project/root-directory and environment-variable concepts are specified.
