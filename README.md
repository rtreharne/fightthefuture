# Fight The Future

Rebuilt classroom game system with 5-stage progression and collaboration code submission.

## Stack

- Django 5
- PostgreSQL (Docker Compose)

## Endpoints

- `/join` - join current run with username
- `/play/<user_id>` - player stage dashboard
- `/podium` - submit solution code sums and resolve ambiguities
- `/teacher` - facilitator controls (passcode protected)

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Then run migrations in a separate shell:

```bash
docker compose run --rm web python manage.py migrate
```

App: http://localhost:8000

## Local dev (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Run tests

```bash
python manage.py test
```

## Deploy on Render (Starter + SQLite disk)

This repository includes a baseline `render.yaml` for a low-cost deployment:

- `Starter` web service
- Persistent disk mounted at `/var/data`
- SQLite database path: `/var/data/db.sqlite3`
- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start command: `python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

### Steps

1. Push this repo to GitHub (`main` branch recommended).
2. In Render, create a new Web Service from that repo.
3. Confirm it picks up `render.yaml` (or copy the same commands manually).
4. Deploy and open the generated `*.onrender.com` URL.
5. Validate endpoints: `/join`, `/podium`, `/teacher`.
6. Later, add `fightthefuture.uniwebdev.co.uk` as a custom domain and include it in `ALLOWED_HOSTS`.
