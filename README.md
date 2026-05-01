# Fight The Future

Fight The Future is a classroom coding game platform built with Django.  
Students progress through a story-driven sequence of data and coding challenges, each with a personal 6-digit code.  
Progression is validated through collaboration rules and submitted via a central podium.

The app is designed for live workshop delivery with a facilitator dashboard, deterministic per-player stage code generation, downloadable stage datasets, and end-of-session feedback collection.

## What This System Does

- Runs a live multiplayer classroom session ("run")
- Lets students join with a username and complete staged coding tasks
- Generates per-player puzzle data and codes for each stage
- Enforces stage progression and collaboration sizes at the podium
- Supports facilitator controls (start/pause/reset users/run state)
- Captures structured feedback when players complete the final stage

## Game Model

- Stages: `4` total (`STAGE_COUNT = 4`)
- Progression: players move from stage `1` to stage `5` (`5` means completed)
- Collaboration requirements by stage:
  - Stage 1: solo
  - Stage 2: pair
  - Stage 3: group of 4
  - Stage 4: group of 8
- Dynamic fallback: if a player is truly stranded at a stage, solo progression can be allowed to avoid deadlock.

## Key User Flows

### Player flow

1. Join the current run at `/join`
2. Read intro/orientation and open personal terminal at `/play/<user_id>`
3. Download stage dataset from `/play/<user_id>/dataset/<stage>`
4. Solve challenge in external tools (R/Python/etc.)
5. Submit required code sum at `/podium`
6. Progress to next stage when a valid matching collaboration group is found

### Facilitator flow

1. Authenticate at `/teacher` using passcode
2. Start/pause/resume/archive/reset run
3. Create test users
4. Set/clear collaboration cap
5. Suspend/reactivate users
6. Monitor progression and stage codes

## Architecture Overview

- Framework: Django 5
- App module: `game`
- Runtime config: `config/settings.py`
- Stage definitions/content: `game/stages.yaml` + `game/stage_content.py`
- Core progression and matching logic: `game/services.py`
- Request handlers and dataset generation: `game/views.py`
- Templates: `templates/game/*.html`
- Tests: `game/tests/test_views.py`, `game/tests/test_services.py`

## Data Model Summary

Main entities:

- `Run`: one classroom session, with active/paused/archived state
- `Player`: participant, stage pointer, orientation state, suspension state
- `StageCode`: per-player per-stage 6-digit solution code
- `PodiumSubmission`: submitted group sum and resolution outcome
- `SubmissionCandidate`: potential groups for ambiguous submissions
- `PlayerFeedback`: post-completion likert + open response data

## Endpoints

- `/` - home redirect
- `/join` - join current run
- `/play/<user_id>` - player terminal and stage UI
- `/play/<user_id>/dataset/<stage>` - stage dataset download
- `/podium` - code sum submissions and ambiguity resolution
- `/teacher` - facilitator controls (passcode protected)

## Configuration

Environment variables are read in `config/settings.py`.

Common values:

- `DEBUG` - `1/0`, `true/false`
- `SECRET_KEY` - Django secret key
- `ALLOWED_HOSTS` - comma-separated host list
- `TEACHER_PASSCODE` - teacher login code
- `SQLITE_PATH` - SQLite file path (used when Postgres env vars are absent)

Postgres mode activates when `POSTGRES_DB` is set:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## Local Development

### Docker Compose

```bash
cp .env.example .env
docker compose up --build
docker compose run --rm web python manage.py migrate
```

App URL: `http://localhost:8009`

### Native Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Testing

Run all tests:

```bash
python manage.py test
```

Targeted suites:

```bash
python manage.py test game.tests.test_views game.tests.test_services
```

## Deployment

This repo includes:

- `requirements.txt`
- `Procfile`
- `render.yaml` (Starter + persistent disk + SQLite path)

For full deployment instructions, see:

- [Render Deployment Guide](./render.md)

## Notes for Operators

- Stage content and narrative are configured in `game/stages.yaml`.
- Podium matching behavior depends on current run state and configured collaboration cap.
- Stage 4 dataset generation includes `sanity_check.csv` (ground truth coordinates for `001.png` and `002.png`).
- Static assets are served with WhiteNoise and generated with `collectstatic`.
