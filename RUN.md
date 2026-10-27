# Running the mentoring platform

This workspace contains two things:

1. **The design deliverable** — the report sources and generated artifacts in `src/`, `database/`,
   `diagrams/`, `api-spec.yaml` and the PDF. These are unchanged.
2. **A working implementation** — a FastAPI backend in `backend/` and a React front end in
   `frontend/` that implement the 58-operation API contract and the 26 pages in the design.

The implementation follows `api-spec.yaml` exactly: `/api/v1` paths, the `{data, meta}` success
envelope and the `{error: {code, message, details, request_id}}` error envelope. The database is
created from the report's PostgreSQL 16 DDL (17 tables, 26 foreign keys, triggers and exclusion
constraints).

## Prerequisites

- Python **3.11+**
- Node.js **18+** (20+ recommended) and npm
- PostgreSQL **16** — easiest with Docker Desktop and the included `docker-compose.yml`
- Ports: **5433** (database), **8000** (API), **5173** (web app), **8080** (Adminer, optional)

The compose file maps PostgreSQL to **5433** on purpose, so it can coexist with a native
PostgreSQL install on 5432.

## Quick start

From the repository root:

```powershell
# 1. Database (PostgreSQL 16 on localhost:5433, Adminer on :8080)
docker compose up -d

# 2. Backend
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env          # already present in this workspace; edit if needed
alembic upgrade head                 # applies the exact report DDL
python -m app.cli seed-demo          # admin + catalogues + demo students/mentors
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The API is at **http://localhost:8000**; interactive docs are at
**http://localhost:8000/docs** and the raw OpenAPI document at **http://localhost:8000/openapi.json**.

On macOS or Linux, replace the venv activation with `source .venv/bin/activate` and use
`cp .env.example .env`.

### Demo accounts

`python -m app.cli seed-demo` creates these accounts (all demo passwords are
`correct-horse-battery-9` unless noted):

| Role | Account | Notes |
| --- | --- | --- |
| Administrator | `admin@example.org` / `admin-password-123` | Password comes from `ADMIN_PASSWORD` |
| Student | `asha.menon@example.org` | Complete profile; one pending request to Rohan |
| Student | `vikram.shah@example.org` | Active mentorship with Divya; one completed, rated session |
| Student | `ravi.kumar@example.org` | Active mentorship with Divya |
| Mentor | `rohan.iyer@example.org`, `meera.nair@example.org`, `karthik.rao@example.org` | Approved and eligible for requests |
| Mentor | `divya.sharma@example.org` | Approved, at capacity (2 active mentees) |
| Mentor | `sanjay.patel@example.org` | Approved but paused for new requests |
| Mentor | `lakshmi.pillai@example.org` | Pending administrator review |

The login page also has a **demo accounts** shortcut that fills the student, mentor or admin
credentials.

## What to try

- **Student** — dashboard, mentor search and recommendations, mentor profile, send/cancel a
  request, mentorship overview, book/cancel a session, session history and in-window ratings,
  profile onboarding, notifications.
- **Mentor** — dashboard, accept/decline requests, mentees and shared notes, schedule/complete/
  cancel sessions, single and weekly-recurring availability, capacity and pause settings, profile
  submission for review and notifications.
- **Administrator** — KPIs, trends and audit activity; user management; skill/interest catalogue;
  mentor review queue with checklist, approve/reject/suspend; mentorships and stale requests;
  analytics funnel, ratings, trends and CSV exports.
- **Access control** — `/403`, `/404`, `/500` and `/session-expired` pages; role guards redirect
  signed-in users to their own home area.

## Configuration

Backend configuration lives in `backend/.env` (see `.env.example`). The important values:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://mentoring:mentoring_dev_pw@localhost:5433/mentoring` | SQLAlchemy URL |
| `JWT_SECRET_KEY` | dev placeholder | **Change for anything non-local** |
| `ACCESS_TOKEN_MINUTES` | `15` | Access-token lifetime |
| `REFRESH_TOKEN_DAYS` | `7` | Refresh-token lifetime |
| `REQUEST_EXPIRY_DAYS` | `14` | Pending-request expiry (R3) |
| `COOLDOWN_DAYS` | `30` | Re-request cooldown after a declined/cancelled request |
| `FEEDBACK_WINDOW_DAYS` | `14` | How long a completed session can be rated |
| `MAX_PENDING_REQUESTS` | `3` | Concurrent pending requests per student |
| `MATCH_W_*` | `0.50 / 0.30 / 0.20` | Matching weights; must sum to 1.0 |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `EMAIL_ENABLED` | `false` | Emails are logged instead of sent when off |
| `JOBS_ENABLED` | `true` | In-process job loop (expiry and reminders) |
| `ENV` | `local` | `local` leaves the refresh cookie non-Secure |

The front end uses same-origin `/api/v1` requests and relies on the Vite dev proxy
(`frontend/vite.config.js`) for local development. For a production deployment, serve
`frontend/dist` behind a reverse proxy that forwards `/api` to the backend, set `ENV=production`,
use a strong `JWT_SECRET_KEY` and `ADMIN_PASSWORD`, and put the API behind HTTPS.

## Verification and checks

From `backend/` (the API must be running for the HTTP checks):

```powershell
.\.venv\Scripts\python scripts\check_contract.py   # every contract endpoint exists, no extras
.\.venv\Scripts\python scripts\smoke.py            # 29 read-path and permission checks
.\.venv\Scripts\python scripts\walkthrough.py      # end-to-end API workflow; mutates the database
.\.venv\Scripts\python -m app.cli run-jobs         # run expiry/reminder jobs once
```

`walkthrough.py` registers throwaway users, exercises request/session/feedback/admin flows and
changes their passwords. Run it against a disposable database, or reset the demo data afterwards.

From `frontend/`:

```powershell
npm run build      # production build in frontend/dist
npm run preview    # serve the build locally
```

From `src/` (design-data consistency, no third-party dependencies):

```powershell
python schema.py
python pages.py
python components_data.py
python matching.py
```

The design counts stay in sync across `api-spec.yaml`, `database/schema.sql` and the prose via
these checks. Database-specific checks (39 integrity assertions plus the concurrency script) are
documented in `README.md` and `database/`.

## Resetting the database

```powershell
docker compose down -v
docker compose up -d
cd backend
alembic upgrade head
python -m app.cli seed-demo
```

`seed-demo` is idempotent: it skips if `asha.menon@example.org` already exists. To use a native
PostgreSQL instance instead of Docker, create the `mentoring` database and role, then point
`DATABASE_URL` at it and run `alembic upgrade head` on an empty database.

## Layout

```
api-spec.yaml            OpenAPI 3.0.3 contract (58 operations)
database/schema.sql      exact PostgreSQL 16 DDL used by the migration
src/                     report generators and prose (design sources; do not edit generated files)
diagrams/                diagram sources and renders

backend/
  app/routers/           E01–E58 HTTP endpoints, grouped by resource
  app/services/          business rules (matching, requests, sessions, admin, analytics)
  app/models/            SQLAlchemy models matching the DDL
  app/serializers.py     response shapes from the contract
  app/core/              errors, security, rate limiting, pagination
  app/jobs/              expiry and reminder jobs
  alembic/               migration applying app/ddl/schema.sql
  scripts/               contract, smoke and walkthrough checks

frontend/
  src/pages/             public, student, mentor and administrator pages
  src/components/        shell, dialogs, editors, toasts, shared UI
  src/api.js             axios client, token refresh, paging helper, CSV download
  src/auth.jsx           session restore, role guards, home routing
  src/App.jsx            all routes
```

## Troubleshooting

- **`/health` works but the UI shows 401 on refresh** — you are not signed in; the login page
  makes one expected `/auth/refresh` call that returns 401.
- **Login returns `RATE_LIMITED`** — development limits are 10/minute for login/register and
  5/minute for forgot-password per IP. Wait a minute or restart the API (buckets are in memory).
- **`database "mentoring" does not exist`** — start the compose database and run
  `alembic upgrade head`; check `DATABASE_URL` uses port 5433.
- **`alembic upgrade head` fails on a non-empty database** — the initial migration expects the
  schema to be absent. Use a fresh database or `docker compose down -v` first.
- **Port already in use** — stop the native PostgreSQL service on 5432 (or leave it; compose uses
  5433), or change the Vite/uvicorn ports.
- **Starlette deprecation warning about `HTTP_422_UNPROCESSABLE_ENTITY`** — cosmetic, emitted by
  the installed Starlette version; responses still use 422.
