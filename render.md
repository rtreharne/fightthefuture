# Render Deployment Guide

This guide deploys Fight The Future to Render using a low-cost, stable setup:

- Web service plan: `Starter`
- Database: SQLite on persistent disk (`/var/data/db.sqlite3`)
- Domain strategy: deploy to `*.onrender.com` first, custom domain later

## 1) Prerequisites

- Render account
- GitHub repository with this project pushed (recommended branch: `main`)
- Repo includes:
  - `requirements.txt`
  - `render.yaml`
  - `Procfile`

## 2) Create Service on Render

Recommended path (Blueprint):

1. Render Dashboard -> `New` -> `Blueprint`
2. Connect/select your GitHub repo
3. Render reads `render.yaml`
4. Confirm and apply

The blueprint config sets:

- Runtime: Python
- Plan: `starter`
- Region: `frankfurt`
- Build command:
  - `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command:
  - `python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- Disk:
  - Mount path: `/var/data`
  - Size: `1 GB`

## 3) Environment Variables

Ensure these are present in Render service settings:

- `DEBUG=false`
- `SQLITE_PATH=/var/data/db.sqlite3`
- `SECRET_KEY=<strong random value>`
- `TEACHER_PASSCODE=<your passcode>`
- `ALLOWED_HOSTS=<comma-separated list>`

Recommended initial `ALLOWED_HOSTS`:

- `localhost,127.0.0.1,<your-service>.onrender.com`

Notes:

- The app also appends `RENDER_EXTERNAL_HOSTNAME` at runtime when available.
- If you later add a custom domain, add it explicitly to `ALLOWED_HOSTS`.

## 4) First Deploy Validation

After deploy completes, open your Render URL and verify:

- `/join`
- `/play/<user_id>`
- `/podium`
- `/teacher`

Functional checks:

1. Join a player and confirm stage page loads.
2. Download a stage dataset.
3. Submit a valid/invalid podium code and confirm response behavior.
4. Confirm teacher login works.

## 5) Persistence Validation (Critical)

Because this deployment uses SQLite on disk:

1. Create data (e.g., join a test player).
2. Trigger a manual deploy/restart.
3. Confirm the same data still exists.

If data disappears, check:

- Disk is attached to the web service
- Mount path is exactly `/var/data`
- `SQLITE_PATH` is exactly `/var/data/db.sqlite3`

## 6) Add Custom Domain Later

When ready:

1. In Render service -> `Settings` -> `Custom Domains`, add:
   - `fightthefuture.uniwebdev.co.uk`
2. In Cloudflare DNS, add/update CNAME to the Render target shown in UI.
3. Update `ALLOWED_HOSTS` env var to include:
   - `<your-service>.onrender.com`
   - `fightthefuture.uniwebdev.co.uk`
4. Redeploy and re-test app flows over HTTPS.

## 7) Cost and Operational Notes

- `Starter` web service bills monthly, prorated by runtime usage.
- Persistent disk is billed per GB/month.
- Disk-backed services do not get zero-downtime deploy behavior.
- SQLite is acceptable for this workshop workload, but for higher concurrency switch to managed Postgres.

## 8) Troubleshooting

### Error: `No module named 'yaml'`
- Ensure `PyYAML` is in `requirements.txt`.

### Error: `Error loading psycopg2 or psycopg module`
- If Postgres env vars are set, Django expects a Postgres driver.
- Ensure `psycopg2-binary` is in `requirements.txt`, or unset Postgres env vars if using SQLite mode.

### Static files missing
- Ensure build command includes `collectstatic`.
- Confirm WhiteNoise middleware and static storage settings are enabled.

### 400 Bad Request / Host header
- Add the actual hostname to `ALLOWED_HOSTS`.

