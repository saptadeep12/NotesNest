# Deployment

NotesNest uses Neon Postgres for the database, Vercel for the frontend and
backend, and Backblaze B2 as the primary PDF store through its S3-compatible
API. The application remains provider-neutral through the `S3_*` settings.

## Neon Postgres

Create a Neon project near the Vercel region and the students. Copy both
connection strings. Use the pooled string for Vercel and the direct, unpooled
string for migrations:

```powershell
cd backend
$env:DATABASE_URL = "<NEON_DIRECT_CONNECTION_STRING>"
.\.venv\Scripts\alembic.exe upgrade head
Remove-Item Env:DATABASE_URL
```

## Backblaze B2

Create a private B2 bucket. From the bucket details, note the S3 endpoint and
region, such as `https://s3.us-west-004.backblazeb2.com`. Create an Application
Key restricted to that bucket with read and write access. Save the `keyID` and
`applicationKey` immediately; do not use the master key.

Create `backend/.env.production` locally:

```text
APP_ENV=production
DATABASE_URL=<NEON_POOLED_CONNECTION_STRING>
STORAGE_BACKEND=s3
S3_BUCKET=<bucket name>
S3_ENDPOINT_URL=https://s3.<region>.backblazeb2.com
S3_REGION=<region from the endpoint>
S3_ACCESS_KEY_ID=<keyID>
S3_SECRET_ACCESS_KEY=<applicationKey>
S3_PRESIGN_SECONDS=300
S3_FORCE_PATH_STYLE=false
```

Verify the bucket before syncing:

```powershell
python -m app.manage --env-file .env.production check-storage
```

B2 provides 10 GB of storage free. Downloads are free up to 3x the average
monthly stored data; a small PDF library should normally remain within that
allowance, but monitor actual usage.

## Other S3-compatible providers

| Provider | Endpoint/region | Status |
| --- | --- | --- |
| Cloudflare R2 | `https://<account-id>.r2.cloudflarestorage.com`, region `auto` | Same settings; not tested against the real service |
| AWS S3 | Provider endpoint and AWS region | Same settings; not tested against the real service |
| Neon Object Storage | Provider endpoint; `S3_FORCE_PATH_STYLE=true` | Available only in some Neon regions; egress shares the Free-plan transfer allowance and can suspend Postgres if exceeded; not tested |

No provider has been tested against the real service yet. The
`check-storage` command is the verification step for the owner.

## Vercel

Create separate projects with root directories `backend` and `frontend`.
The backend uses the pooled Neon URL and the B2 `S3_*` variables. The frontend
uses `NEXT_PUBLIC_API_URL` set to the backend URL. Keep `DOCKER_BUILD` unset on
Vercel so standalone output is not enabled.
