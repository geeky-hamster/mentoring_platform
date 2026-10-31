# Student Mentoring and Career Support Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## Overview

A full-stack mentoring platform connecting students with industry mentors for career guidance, skill development, and professional growth. Built as a **working implementation** of the design specification documented in `IITM_Mentoring_Platform_Design_Report.pdf`, this application implements all **58 REST API endpoints** and **26 UI pages** with a PostgreSQL 16 database.

### Key Features

| Category | Features |
|----------|----------|
| **Authentication** | JWT access tokens + HTTP-only refresh cookies, password reset via email, role-based access (Student/Mentor/Admin) |
| **Student Portal** | Profile onboarding, mentor discovery with smart matching, request management, session booking, feedback & ratings |
| **Mentor Portal** | Professional profile with expertise/availability, request review, session management, mentee tracking, capacity controls |
| **Admin Dashboard** | Mentor approval queue, user management (suspend/reactivate), mentorship oversight, analytics with CSV export, audit logs |
| **Matching Engine** | Score = 0.50 x Skills + 0.30 x Interests + 0.20 x Availability (renormalised when dimension missing) |
| **Real-time Notifications** | Request accepted/declined, session scheduled/cancelled, feedback requested, mentorship ended |

---

## Architecture

```
+---------------------------------------------------------------------------+
|                           PLATFORM ARCHITECTURE                           |
+---------------------------------------------------------------------------+
|                                                                           |
|   +--------------+       +--------------+       +--------------+         |
|   |   React 18   | ----> |   FastAPI    | ----> | PostgreSQL 16|         |
|   |   Frontend   |       |   Backend    |       |   Database   |         |
|   |  (Vite + TS) |       |  (Uvicorn)   |       |  (Docker)    |         |
|   +--------------+       +--------------+       +--------------+         |
|         |                    |                    |                      |
|         v                    v                    v                      |
|   +--------------+       +--------------+       +--------------+         |
|   |  Bootstrap 5 |       |  58 Endpoints|       |  17 Tables   |         |
|   |  React-BS    |       |  /api/v1     |       |  26 FKs      |         |
|   +--------------+       +--------------+       +--------------+         |
|                                                                           |
+---------------------------------------------------------------------------+
```

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React, TypeScript, Vite | 18, 5.x, 6.x |
| **UI Framework** | Bootstrap 5, React-Bootstrap | 5.3, 2.10 |
| **State/HTTP** | React Query (TanStack Query), Axios | 5.x, 1.7 |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy 2.0 | 0.115, 0.30, 2.0 |
| **Database** | PostgreSQL | 16 |
| **Auth** | JWT (HS256), bcrypt, HTTP-only cookies | - |
| **Validation** | Pydantic v2 | 2.x |
| **Migrations** | Alembic | 1.13 |
| **Testing** | Playwright (E2E), httpx (contract) | 1.47, 0.27 |

---

## Project Structure

```
IITM_Mentoring_Platform_Source/
+-- README.md                          # This file
+-- RUN.md                             # Quick start & verification guide
+-- api-spec.yaml                      # OpenAPI 3.0.3 contract (58 operations)
+-- matching_reference.py              # Reference matching algorithm
+-- database/
|   +-- schema.sql                        # PostgreSQL 16 DDL (17 tables)
|   +-- db_integrity_tests.sql            # 39 integrity checks
|   +-- db_concurrency_test.sh            # Concurrency stress test
|   +-- db_test_results.txt               # Recorded test output (39 PASS)
|   +-- db_concurrency_result.txt         # Recorded concurrency output
+-- diagrams/                          # Architecture & ER diagrams
|   +-- *.mmd, *.dot, *.png, *.json       # Mermaid, Graphviz sources & renders
+-- src/                               # Design report generators (Python)
|   +-- build.py, doc.py, kit.py          # PDF report builder
|   +-- schema.py, api.py, pages.py       # Single sources of truth
|   +-- components_data.py, matching.py   # Component graph & matching rule
|   +-- content_a.py - content_e.py       # Report prose sections
|   +-- flows.py, uml_figs.py, wire_*.py  # Diagram generators
+-- backend/                           # FastAPI Implementation
|   +-- app/
|   |   +-- main.py                       # App factory, middleware, router wiring
|   |   +-- config.py                     # Settings (env-driven)
|   |   +-- extensions.py                 # SQLAlchemy engine/session
|   |   +-- models.py                     # ORM models (17 tables)
|   |   +-- serializers.py                # API response envelopes
|   |   +-- deps.py                       # FastAPI dependencies (DB, auth, paging)
|   |   +-- core/
|   |   |   +-- errors.py                 # DomainError + error codes (32)
|   |   |   +-- security.py               # JWT, password hashing
|   |   |   +-- rate_limit.py             # In-memory rate limiting
|   |   |   +-- pagination.py             # Page/meta helpers
|   |   |   +-- transactions.py           # TransactionRoute (commit before response)
|   |   +-- routers/                      # 11 route modules (all 58 endpoints)
|   |   |   +-- auth.py                   # E01-E09: Auth & account
|   |   |   +-- catalogues.py             # E10/E11, E55-E58: Skills/Interests CRUD
|   |   |   +-- profiles.py               # E12-E15: Own profile CRUD
|   |   |   +-- mentors.py                # E16-E23: Discovery & matching
|   |   |   +-- requests.py               # E24-E29: Mentoring requests
|   |   |   +-- mentorships.py            # E30-E34: Mentorships
|   |   |   +-- sessions.py               # E35-E39: Sessions & feedback
|   |   |   +-- dashboards.py             # E40-E44: Dashboards & notifications
|   |   |   +-- admin.py                  # E45-E54: Administration
|   |   +-- services/                     # Business logic (9 services)
|   |   |   +-- auth_service.py
|   |   |   +-- catalogue_service.py
|   |   |   +-- profile_service.py
|   |   |   +-- matching_service.py       # C04/C05: Discovery & Matching
|   |   |   +-- mentoring_service.py      # C06: Requests & mentorships
|   |   |   +-- session_service.py        # C08: Availability & sessions
|   |   |   +-- feedback_service.py
|   |   |   +-- dashboard_service.py
|   |   |   +-- notification_service.py
|   |   |   +-- admin_service.py
|   |   |   +-- analytics_service.py
|   |   |   +-- audit_service.py
|   +-- scripts/
|   |   +-- check_contract.py             # Verifies 58 endpoints vs OpenAPI
|   |   +-- smoke.py                      # 29-call integration smoke test
|   +-- alembic/                          # Migration environment
|   +-- requirements.txt                  # Python dependencies
|   +-- README.md                         # Backend-specific docs
+-- frontend/                          # React Implementation
|   +-- src/
|   |   +-- App.jsx, main.jsx             # Entry & routing
|   |   +-- api.js                        # Axios client + envelope helpers
|   |   +-- auth.jsx                      # Auth context + guards
|   |   +-- components/
|   |   |   +-- shell.jsx                 # AppShell, topbar, sidebar, user menu
|   |   |   +-- ui.jsx                    # Primitives: Panel, Tabs, Chip, Badge, Loading...
|   |   |   +-- dialogs.jsx               # Modals: Booking, SlotEditor, Feedback, Reason, Confirm...
|   |   |   +-- editors.jsx               # SkillPicker, InterestPicker, RatingInput...
|   |   |   +-- tables.jsx                # DataTable with sorting/pagination
|   |   +-- pages/
|   |   |   +-- public.jsx                # Login, Register, Forgot/Reset, Error pages
|   |   |   +-- student.jsx               # 10 student pages (dashboard, directory, requests...)
|   |   |   +-- mentor.jsx                # 7 mentor pages (dashboard, requests, mentees, schedule...)
|   |   |   +-- admin.jsx                 # 5 admin pages (dashboard, users, mentors, mentorships, analytics)
|   |   +-- utils/                        # Date formatting, constants
|   +-- index.html, vite.config.ts
|   +-- package.json
|   +-- README.md                         # Frontend-specific docs
+-- postman/
    +-- Mentoring_Platform_API.postman_collection.json  # Postman collection for all 58 endpoints
```

---

## Quick Start

### Prerequisites

- **Docker Desktop** (for PostgreSQL 16)
- **Node.js** 20+ & **pnpm** (or npm/yarn)
- **Python** 3.11+ & **venv**

### 1. Start Database

```bash
# From project root
docker run -d \
  --name mentoring-platform-db \
  -e POSTGRES_USER=mentoring \
  -e POSTGRES_PASSWORD=mentoring_dev_pw \
  -e POSTGRES_DB=mentoring \
  -p 5433:5432 \
  postgres:16
```

### 2. Backend Setup

```bash
cd backend

# Create venv & install deps
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# Apply schema (creates all 17 tables)
docker exec -i mentoring-platform-db psql -U mentoring -d mentoring < ../database/schema.sql

# Seed demo data (admin, 9 demo users, catalogues)
python -m scripts.seed_admin
python -m scripts.seed_catalogues
python -m scripts.seed_demo

# Start server (port 8000)
python -m uvicorn app.main:app --port 8000 --log-level warning
```

### 3. Frontend Setup

```bash
cd frontend

# Install deps
pnpm install  # or npm install

# Start dev server (port 5173, proxies /api to localhost:8000)
pnpm run dev
```

### 4. Verify

| Check | Command |
|-------|---------|
| Health | `curl http://localhost:8000/health` |
| Contract | `cd backend && python scripts/check_contract.py` |
| Smoke Test | `cd backend && python scripts/smoke.py` |
| Frontend Build | `cd frontend && pnpm run build` |
| E2E Stories | `cd /tmp/opencode/pwtest && node story.cjs` |

---

## Demo Accounts

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Admin** | `admin@example.org` | `admin-password-123` | Full platform access |
| **Student** | `asha.menon@example.org` | `correct-horse-battery-9` | 2nd year, data engineering focus |
| **Mentor** | `rohan.iyer@example.org` | `correct-horse-battery-9` | Alumni, 8 yrs exp, accepts mentees |
| **Mentor** | `meera.nair@example.org` | `correct-horse-battery-9` | Recent grad, ML/AI, accepting |
| **Mentor** | `karthik.rao@example.org` | `correct-horse-battery-9` | Alumni, Product Mgmt, accepting |
| **Mentor** | `divya.sharma@example.org` | `correct-horse-battery-9` | At capacity (2/2), has completed session |
| **Mentor** | `sanjay.patel@example.org` | `correct-horse-battery-9` | Paused (not accepting) |
| **Mentor** | `lakshmi.pillai@example.org` | `correct-horse-battery-9` | Pending review |
| **Student** | `vikram.shah@example.org` | `correct-horse-battery-9` | Has active mentorship with Divya |
| **Student** | `ravi.kumar@example.org` | `correct-horse-battery-9` | Has active mentorship with Divya |

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Response Envelopes

**Success** (`{data, meta}`)
```json
{
  "data": { ... },
  "meta": { "page": 1, "page_size": 20, "total": 45, "total_pages": 3 }
}
```

**Error** (`{error: {code, message, details, request_id}}`)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more fields are invalid.",
    "details": [{ "field": "email", "issue": "invalid format" }],
    "request_id": "req_abc123"
  }
}
```

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register student/mentor |
| `POST` | `/auth/login` | Login -> access token + refresh cookie |
| `POST` | `/auth/refresh` | Rotate access token via cookie |
| `POST` | `/auth/logout` | Revoke refresh family |
| `POST` | `/auth/forgot-password` | Request reset link (dev: logs to console) |
| `POST` | `/auth/reset-password` | Set new password via token |
| `PATCH` | `/auth/change-password` | Change password (keeps refresh family) |
| `GET` | `/users/me` | Current user profile |

### Student Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/students/me/profile` | Own profile |
| `PATCH` | `/students/me/profile` | Update profile (skills, interests, bio) |
| `GET` | `/mentors` | Search mentors (filters: q, skill, interest, type, exp, sort) |
| `GET` | `/mentors/recommended` | Ranked recommendations (requires completed profile) |
| `GET` | `/mentors/{mentor_id}` | Public mentor profile |
| `POST` | `/mentoring-requests` | Send request to mentor |
| `GET` | `/mentoring-requests/mine` | Own requests (filter by status) |
| `DELETE` | `/mentoring-requests/{id}` | Cancel pending request |
| `GET` | `/mentorships` | Own mentorships |
| `GET` | `/mentorships/{id}` | Mentorship detail |
| `PATCH` | `/mentorships/{id}` | End mentorship (completed/ended + reason) |
| `GET` | `/mentorships/{id}/sessions` | Sessions for a mentorship |
| `POST` | `/sessions` | Book a session in mentor's slot |
| `PATCH` | `/sessions/{id}` | Cancel session (student) |
| `POST` | `/feedback` | Submit session feedback (1-5 stars) |
| `GET` | `/notifications` | Notifications (tabs: All/Unread) |
| `POST` | `/notifications/{id}/read` | Mark as read |
| `POST` | `/notifications/read-all` | Mark all as read |

### Mentor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/mentors/me/profile` | Own profile (all tabs) |
| `PATCH` | `/mentors/me/profile` | Update profile (submit_for_review flag) |
| `GET` | `/mentors/me/dashboard` | Dashboard stats |
| `GET` | `/mentoring-requests/mine` | Incoming requests (tabs: Pending/Accepted/Declined) |
| `GET` | `/mentoring-requests/{id}` | Request detail with student summary |
| `POST` | `/mentoring-requests/{id}/accept` | Accept -> creates mentorship |
| `POST` | `/mentoring-requests/{id}/decline` | Decline with reason |
| `GET` | `/mentorships` | Own mentorships (tabs: Active/Closed) |
| `GET` | `/mentorships/{id}` | Mentorship detail with sessions |
| `PATCH` | `/mentorships/{id}` | Close mentorship (completed/ended) |
| `GET` | `/sessions` | All sessions across mentorships |
| `PATCH` | `/sessions/{id}` | Complete/cancel/edit session |
| `POST` | `/feedback` | Submit mentor feedback |
| `GET` | `/mentors/me/availability` | Own slots (filter: from, to, is_available) |
| `POST` | `/mentors/me/availability` | Add slots (single or weekly recurrence) |
| `PATCH` | `/mentors/me/availability/{id}` | Edit slot |
| `DELETE` | `/mentors/me/availability/{id}` | Delete unbooked slot |
| `GET` | `/notifications` | Mentor notifications |

### Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/dashboard` | KPIs, stale requests, recent audit |
| `GET` | `/admin/users` | User management (search, filter, paginate) |
| `PATCH` | `/admin/users/{id}/status` | Suspend/deactivate/reactivate |
| `GET` | `/admin/mentors` | Mentor review queue (filter: status) |
| `GET` | `/admin/mentors/{id}` | Mentor application detail |
| `POST` | `/admin/mentors/{id}/approval` | Approve/reject/suspend with note |
| `GET` | `/admin/mentorships` | All mentorships (filter: status) |
| `GET` | `/admin/mentorships/{id}` | Mentorship detail (offcanvas) |
| `PATCH` | `/admin/mentorships/{id}` | End mentorship (ended + reason) |
| `GET` | `/admin/mentoring-requests` | All requests (filter: status, older_than_days) |
| `GET` | `/admin/analytics/overview` | KPIs (requires `from`, `to`) |
| `GET` | `/admin/analytics/trends` | Time series (metric, interval, from, to) |
| `GET` | `/admin/analytics/export` | CSV export (report, from, to) |
| `GET` | `/admin/audit-logs` | Paginated audit trail |
| `GET` | `/admin/skills` | Skills catalogue (search, include_inactive, with_usage) |
| `POST` | `/admin/skills` | Add skill |
| `PATCH` | `/admin/skills/{id}` | Edit skill |
| `POST` | `/admin/skills/{id}/retire` | Retire skill |
| `POST` | `/admin/skills/{id}/reactivate` | Reactivate skill |
| `GET` | `/admin/career-interests` | Interests catalogue |
| `POST` | `/admin/career-interests` | Add interest |
| `PATCH` | `/admin/career-interests/{id}` | Edit interest |
| `POST` | `/admin/career-interests/{id}/retire` | Retire interest |
| `POST` | `/admin/career-interests/{id}/reactivate` | Reactivate interest |

### Catalogue (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/skills` | Skills list (search, category) |
| `GET` | `/career-interests` | Interests list |

---

## Database Schema

> **Deep documentation:** [`docs/database/DATABASE-SPEC.md`](docs/database/DATABASE-SPEC.md) describes all 17 tables column-by-column, with lifecycles, join keys and invariants. [`docs/database/DFD.md`](docs/database/DFD.md) contains the level 0–2 data flow diagrams and a 99-flow catalogue; [`docs/database/CHARTS.md`](docs/database/CHARTS.md) defines 20 charts with runnable SQL.

### ER Diagram

<p align="center">
  <a href="docs/database/diagrams/erd.png">
    <img src="docs/database/diagrams/erd.png" alt="Entity-relationship diagram: 17 tables with primary and foreign keys" width="100%">
  </a>
</p>

The diagram above is rendered from [`docs/database/diagrams/erd.mmd`](docs/database/diagrams/erd.mmd) and matches [`database/schema.sql`](database/schema.sql) exactly. For a column-by-column description of every table — including lifecycles, join keys and invariants — see [`docs/database/DATABASE-SPEC.md`](docs/database/DATABASE-SPEC.md).

> **Join-key warning:** `mentoring_requests.student_id` and `.mentor_id` store **`users.user_id`**, not `student_profile_id` / `mentor_profile_id`. Joining to the profile tables on those columns returns zero rows. The canonical joins are in `DATABASE-SPEC.md` §5.

### Data Flow Diagrams

**Level 0 — context**

<p align="center">
  <a href="docs/database/diagrams/dfd-level0.png">
    <img src="docs/database/diagrams/dfd-level0.png" alt="Level 0 data flow diagram: students, mentors, administrators and the scheduler around the platform" width="100%">
  </a>
</p>

**Level 1 — one diagram per process.** Each process is drawn separately with all of its external entities and data stores, so every arrow has one meaning. All fifteen rendered diagrams (ERD, context, P1–P11, two level-2 decompositions) are indexed in [`docs/database/diagrams/README.md`](docs/database/diagrams/README.md).

| Process | Diagram | Writes |
| --- | --- | --- |
| **P1** Identity and access | [`dfd-p01-identity.png`](docs/database/diagrams/dfd-p01-identity.png) | D1, D16, D17 |
| **P2** Profile management | [`dfd-p02-profiles.png`](docs/database/diagrams/dfd-p02-profiles.png) | D2, D3, D6–D9, D16 |
| **P3** Catalogue administration | [`dfd-p03-catalogue.png`](docs/database/diagrams/dfd-p03-catalogue.png) | D4, D5, D16 |
| **P4** Discovery and matching | [`dfd-p04-discovery.png`](docs/database/diagrams/dfd-p04-discovery.png) | read-only |
| **P5** Request lifecycle | [`dfd-p05-requests.png`](docs/database/diagrams/dfd-p05-requests.png) | D10, D15, D16 |
| **P6** Mentorship management | [`dfd-p06-mentorship.png`](docs/database/diagrams/dfd-p06-mentorship.png) | D11, D15, D16 |
| **P7** Availability and scheduling | [`dfd-p07-scheduling.png`](docs/database/diagrams/dfd-p07-scheduling.png) | D12, D13, D15, D16 |
| **P8** Feedback | [`dfd-p08-feedback.png`](docs/database/diagrams/dfd-p08-feedback.png) | D14, D16 |
| **P9** Notification management | [`dfd-p09-notifications.png`](docs/database/diagrams/dfd-p09-notifications.png) | D15 |
| **P10** Administration and reporting | [`dfd-p10-admin.png`](docs/database/diagrams/dfd-p10-admin.png) | D1, D3–D5, D10, D11, D15, D16 |
| **P11** Scheduled maintenance | [`dfd-p11-maintenance.png`](docs/database/diagrams/dfd-p11-maintenance.png) | D10, D15 |

The branching detail for the two processes with real decision trees is decomposed further:

| Process | Level-2 diagram |
| --- | --- |
| Request creation, acceptance, decline, expiry | [`dfd-level2-requests.png`](docs/database/diagrams/dfd-level2-requests.png) |
| Slot publication, booking, cancellation, completion | [`dfd-level2-scheduling.png`](docs/database/diagrams/dfd-level2-scheduling.png) |

Every arrow is labelled with a flow ID from the catalogue; the payload, trigger and frequency of each are documented in [`docs/database/DFD.md`](docs/database/DFD.md) §7.

### Tables Summary (17 tables)

| # | Table | Purpose | Key Constraints |
|---|-------|---------|-----------------|
| 1 | `users` | Core identity & auth | PK `user_id`, UK `email`, `role` in {student,mentor,admin} |
| 2 | `student_profiles` | Student onboarding data | PK `student_profile_id`, FK `user_id` (1:1), `profile_completed` boolean |
| 3 | `mentor_profiles` | Mentor professional data | PK `mentor_profile_id`, FK `user_id` (1:1), `profile_status` in {draft,pending_review,approved,rejected,suspended} |
| 4 | `skills` | Skill catalogue | PK `skill_id`, UK `skill_name`, `is_active` |
| 5 | `career_interests` | Interest catalogue | PK `interest_id`, UK `interest_name`, `is_active` |
| 6 | `student_skills` | Student <-> Skills (N:M) | PK (`student_profile_id`,`skill_id`), `proficiency_level` in {beginner,intermediate,advanced,expert}, `is_focus` |
| 7 | `student_interests` | Student <-> Interests (N:M) | PK (`student_profile_id`,`interest_id`) |
| 8 | `mentor_expertise` | Mentor <-> Skills (N:M) | PK (`mentor_profile_id`,`skill_id`), `expertise_level` |
| 9 | `mentor_interests` | Mentor <-> Interests (N:M) | PK (`mentor_profile_id`,`interest_id`) |
| 10 | `availability_slots` | Mentor bookable windows | PK `slot_id`, FK `mentor_id`, EXCLUDE overlap constraint, `duration <= 4h` |
| 11 | `mentoring_requests` | Student -> Mentor requests | PK `request_id`, FKs `student_id`,`mentor_id`, `status` in {pending,accepted,declined,cancelled,expired}, 14-day expiry |
| 12 | `mentorships` | Active/closed relationships | PK `mentorship_id`, FK `request_id`, `status` in {active,completed,ended} |
| 13 | `sessions` | Booked meetings | PK `session_id`, FKs `mentorship_id`,`slot_id`, `status` in {scheduled,completed,cancelled}, `meeting_mode` in {online,phone,in_person} |
| 14 | `feedback` | Session ratings (1-5) | PK `feedback_id`, UK (`session_id`,`submitted_by`), FK `session_id` |
| 15 | `notifications` | In-app notifications | PK `notification_id`, FK `user_id` CASCADE, `notification_type` in 12 enum values |
| 16 | `audit_logs` | Append-only action trail | PK `audit_id`, FK `actor_user_id` SET NULL, `details` JSONB |
| 17 | `refresh_tokens` | Rotating refresh-token families | PK `token_id`, UK `token_hash`, `family_id`, `revoked_reason` in 5 values |

---

## Configuration

### Backend (`backend/.env`)

```bash
# Database
DATABASE_URL=postgresql+psycopg://mentoring:mentoring_dev_pw@localhost:5433/mentoring

# Security
SECRET_KEY=your-256-bit-secret-key-here
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=30
REFRESH_COOKIE_PATH=/api/v1/auth
REFRESH_COOKIE_SECURE=false  # true in production

# CORS
CORS_ORIGINS=http://localhost:5173

# Rate Limits (per IP)
RATE_LIMIT_LOGIN=10/minute
RATE_LIMIT_REGISTER=10/minute
RATE_LIMIT_FORGOT=5/minute
RATE_LIMIT_REQUEST=10/minute

# Matching Weights (must sum to 1.0)
MATCH_W_SKILLS=0.50
MATCH_W_INTERESTS=0.30
MATCH_W_AVAILABILITY=0.20

# Session Limits
SESSION_MAX_HOURS=4
MAX_PAGE_SIZE=50

# Jobs
JOBS_ENABLED=true
REMINDER_JOB_INTERVAL_MINUTES=10
```

### Frontend (`frontend/.env`)

```bash
VITE_API_BASE=http://localhost:8000/api/v1
VITE_APP_TITLE=IITM Mentoring Platform
```

---

## Testing

### Contract Verification

```bash
cd backend
python scripts/check_contract.py
# Output: "contract endpoints: 58   app openapi operations: 58  MATCH: every contract endpoint is implemented, no extras."
```

### Smoke Test (29 integration calls)

```bash
cd backend
python scripts/smoke.py
# Tests: health, auth flows, all CRUD, admin endpoints, analytics, CSV export, RBAC
```

### Database Integrity

```bash
# Apply schema first
docker exec -i mentoring-platform-db psql -U mentoring -d mentoring < database/schema.sql

# Run 39 integrity checks
docker exec -i mentoring-platform-db psql -U mentoring -d mentoring < database/db_integrity_tests.sql
# Expected: 39 PASS

# Concurrency test (requires psql)
PSQL="psql -U mentoring -d mentoring" ./database/db_concurrency_test.sh mentoring
```

### Frontend Build & Lint

```bash
cd frontend
pnpm run build      # Production build
pnpm run lint       # ESLint
pnpm run preview    # Preview production build
```

### E2E Story Tests (Playwright)

```bash
# Requires running backend (8000) + frontend (5173)
cd /tmp/opencode/pwtest
node story.cjs
# 76 checks across all 34 user stories
```

---

## Postman Collection

Import the complete API test collection:

### File: `postman/Mentoring_Platform_API.postman_collection.json`

This collection contains **all 58 endpoints** organized by tag with:
- Pre-request scripts for auth token management
- Environment variables for `baseUrl`, `accessToken`, `refreshToken`
- Test scripts for response validation
- Example requests with realistic payloads
- Auto-token refresh on 401

### Quick Import

1. Open Postman -> **Import** -> **File** -> Select `postman/Mentoring_Platform_API.postman_collection.json`
2. Create environment `Mentoring Platform Local` with:
   - `baseUrl` = `http://localhost:8000/api/v1`
   - `accessToken` = *(auto-populated after login)*
   - `refreshToken` = *(auto-populated via cookie)*
3. Run **Login** request first -> tokens auto-saved -> all other requests work

### Collection Structure

```
Mentoring Platform API
+-- Authentication (9)
|   +-- Register Student
|   +-- Register Mentor
|   +-- Login
|   +-- Refresh Token
|   +-- Logout
|   +-- Forgot Password
|   +-- Reset Password
|   +-- Change Password
|   +-- Get Current User
+-- Student (15)
|   +-- Get Own Profile
|   +-- Update Profile
|   +-- Search Mentors
|   +-- Get Recommended Mentors
|   +-- Get Mentor Public Profile
|   +-- Send Mentoring Request
|   +-- List My Requests
|   +-- Cancel Request
|   +-- List My Mentorships
|   +-- Get Mentorship Detail
|   +-- End Mentorship
|   +-- List Mentorship Sessions
|   +-- Book Session
|   +-- Cancel Session
|   +-- Submit Feedback
+-- Mentor (18)
|   +-- Get Own Profile
|   +-- Update Profile (Draft)
|   +-- Submit for Review
|   +-- Get Dashboard
|   +-- List Incoming Requests
|   +-- Get Request Detail
|   +-- Accept Request
|   +-- Decline Request
|   +-- List Mentorships
|   +-- Get Mentorship Detail
|   +-- Close Mentorship
|   +-- List All Sessions
|   +-- Complete Session
|   +-- Cancel Session
|   +-- Edit Session
|   +-- Submit Feedback
|   +-- List Availability
|   +-- Add Slots (Single/Recurrence)
|   +-- Edit Slot
|   +-- Delete Slot
+-- Admin (16)
|   +-- Get Dashboard
|   +-- List Users
|   +-- Update User Status
|   +-- List Mentor Applications
|   +-- Get Mentor Application Detail
|   +-- Approve/Reject/Suspend Mentor
|   +-- List All Mentorships
|   +-- Get Mentorship Detail
|   +-- End Mentorship (Admin)
|   +-- List All Requests
|   +-- Analytics Overview
|   +-- Analytics Trends
|   +-- Export CSV
|   +-- Audit Logs
|   +-- Skills Catalogue CRUD (4)
|   +-- Interests Catalogue CRUD (4)
+-- Catalogues (2)
    +-- List Skills
    +-- List Career Interests
```

---

## Design Deliverables (Unchanged)

This workspace preserves the **original design deliverable** exactly as specified:

| Artifact | Source | Description |
|----------|--------|-------------|
| `api-spec.yaml` | `src/api.py` | OpenAPI 3.0.3 contract (58 ops) |
| `database/schema.sql` | `src/schema.py` | PostgreSQL 16 DDL (17 tables) |
| `matching_reference.py` | `src/matching.py` | Reference matching algorithm |
| `diagrams/*.png` | `src/*.py` + Mermaid/Graphviz | ER, Architecture, Component, Nav-map |
| Report PDF | `src/build.py` | Generated design report |

**Regeneration Commands** (from `src/`):
```bash
python schema.py        # -> database/schema.sql
python api.py           # -> api-spec.yaml (crashes writing to /home/claude/report_build/)
python pages.py         # Page specs, stories, workflow
python components_data.py  # Component graph C01-C12
python matching.py      # Matching self-tests
python wire_test.py     # Wireframe contact sheet
python make_er.py       # ER diagram (Graphviz)
python make_dot.py      # Architecture/Component/Nav diagrams
```

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **IIT Madras** - For the mentoring platform design challenge
- **FastAPI Team** - For the exceptional async framework
- **React Team** - For the component model
- **PostgreSQL** - For robust relational foundation
- **OpenAPI Initiative** - For the contract-first standard

---

<div align="center">

**Built for the IITM Mentoring Platform Design Challenge**

*Design Report v1.0 | Implementation v1.0 | 27 October 2026*

</div>