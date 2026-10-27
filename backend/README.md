# Backend — Student Mentoring and Career Support Platform

FastAPI implementation of the 58-operation contract in `../api-spec.yaml`, backed by PostgreSQL 16
and the exact DDL in `../database/schema.sql`.

## Stack

- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy 2 (typed ORM), psycopg 3, Alembic
- PostgreSQL 16
- PyJWT access tokens + rotating refresh tokens stored in the database
- Argon2 password hashing

## Layout

```
app/
  main.py              application factory, CORS, per-request transaction middleware, /health
  config.py            environment configuration and rule parameters
  cli.py               seed-admin, seed-catalogues, seed-demo, run-jobs
  deps.py              auth/role dependencies, pagination, request metadata
  serializers.py       model -> exact contract response shapes
  routers/             auth, profiles, catalogues, mentors, requests, mentorships,
                       sessions, dashboards, admin (E01-E58)
  services/            business rules: matching, mentoring, sessions, feedback, admin,
                       analytics, notifications, audit
  models/              SQLAlchemy models mirroring the 17 contract tables
  core/                errors, security, rate limiting, pagination
  jobs/runner.py       request expiry and 24-hour session reminders
  ddl/schema.sql       copy of the report DDL, applied by the initial migration

alembic/versions/0001_initial.py   applies app/ddl/schema.sql verbatim
scripts/                           contract, smoke and walkthrough checks
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
python -m app.cli seed-demo
python -m uvicorn app.main:app --reload --port 8000
```

`seed-demo` runs `seed-admin`, `seed-catalogues` and the demo dataset. Demo passwords are
`correct-horse-battery-9`; the administrator is `admin@example.org` / `admin-password-123` (from
`ADMIN_EMAIL` / `ADMIN_PASSWORD`). See `../RUN.md` for the full account list and configuration
table.

## Request lifecycle

Every request runs inside a database session owned by the `db_transaction` HTTP middleware in
`main.py`:

- status `< 400` → commit before the response is sent
- error status or raised exception → rollback

This is deliberate: FastAPI's yield-dependency cleanup runs after the response, which would let a
client act on data that is not committed yet.

Responses follow the contract exactly:

```json
{ "data": ..., "meta": { "page": 1, "page_size": 10, "total": 42, "total_pages": 5 } }
```

```json
{ "error": { "code": "INVALID_STATE_TRANSITION", "message": "...", "details": [], "request_id": "..." } }
```

List endpoints accept `page` and `page_size` (default 10, maximum 50). JSON field names are
snake_case throughout. Times are ISO-8601 UTC.

## Authentication and authorization

- `POST /auth/login` returns a short-lived access token in the body and sets an HttpOnly refresh
  cookie scoped to `/api/v1/auth`. The cookie is `Secure` when `ENV != "local"`.
- Refresh tokens rotate and reuse is detected (`REFRESH_REUSED`); changing the password keeps the
  current refresh family but revokes all others.
- Role guards are enforced server-side; the front end only mirrors them.
- Sensitive actions (mentor decisions, account status, catalogue changes, exports) are written to
  the `audit_log` table.
- Development rate limits: login/register 10/min, forgot-password 5/min, mentoring requests 10/min
  per IP. Buckets are in memory, so a server restart clears them.

## Domain rules at a glance

- **Requests** — one pending request per student/mentor pair, at most 3 pending per student,
  14-day expiry, 30-day cooldown after a decline/cancel. Accepting creates the mentorship and
  rejects other pending requests from the same student.
- **Matching** — `0.50 × skills + 0.30 × career interests + 0.20 × availability`, with
  deterministic tie-breaking and human-readable reasons. Weights are validated at startup.
- **Sessions** — students book open slots; mentors may also book custom times. Overlaps are
  rejected by the service and by a database exclusion constraint. Only mentors complete sessions,
  and only after the start time. Cancellation notifies the other participant.
- **Feedback** — one rating per participant per completed session, within `FEEDBACK_WINDOW_DAYS`.
  Rating aggregates drive mentor ranking and analytics.
- **Mentors** — profile submission requires title, organisation, experience, bio and at least one
  expertise. Admin decisions are `approve|reject|suspend`; suspension hides the mentor and cancels
  pending requests. Capacity and paused state are enforced when accepting requests.
- **Privacy** — analytics returns aggregates; feedback groups smaller than five are suppressed
  (`"<5"`); exports never include free-text feedback.

## Jobs

`JOBS_ENABLED=true` starts an in-process loop that runs every few minutes. It expires overdue
requests and creates one reminder per participant for sessions starting within 24 hours. Run it
once with:

```powershell
.\.venv\Scripts\python -m app.cli run-jobs
```

## Checks

With the API running on port 8000:

```powershell
.\.venv\Scripts\python scripts\check_contract.py
.\.venv\Scripts\python scripts\smoke.py
.\.venv\Scripts\python scripts\walkthrough.py
```

- `check_contract.py` compares the contract's operation set with the app's OpenAPI document and
  fails on missing or extra operations.
- `smoke.py` performs 29 read-path, authentication and authorization checks.
- `walkthrough.py` exercises the mutating workflows end to end: registration, profiles, approval,
  matching, requests, availability, booking, completion, feedback, notifications, password change
  and refresh-token reuse. It creates throwaway users and **mutates the database** — use a
  disposable database or reseed afterwards.

There is no pytest suite; these scripts are the backend's regression checks.

## Notes and gotchas

- The initial Alembic migration applies the report DDL verbatim. It expects an empty database.
- Uvicorn logs a Starlette deprecation warning about `HTTP_422_UNPROCESSABLE_ENTITY`; it is
  cosmetic and the API still returns 422 for validation errors.
- `/health` is outside `/api/v1` and outside the OpenAPI schema.
- The OpenAPI document is intentionally generated from FastAPI, not copied from
  `api-spec.yaml`; `check_contract.py` is the gate that keeps the operation set aligned.
- The refresh cookie path is `/api/v1/auth` so password change and logout requests carry it; the
  front end restores a session by calling `POST /auth/refresh` on load.
