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
