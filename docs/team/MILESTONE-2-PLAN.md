# Milestone 2 — Team Execution Plan

**Frontend Build (≈80%) · Database Design · Wireframes**
**Sprint window: 3 days (Thu 29 Oct – Sat 31 Oct 2026)**
**Team of five: Frontend · Backend · Code Reviewer · Tester · Scrum/PM**

---

## How to use this document

This is the working plan the team follows *and* the story the repository tells. Every task below maps to a branch, a pull request, and a board column, so GitHub itself becomes the progress report — no separate slide deck needed at review time.

Replace the role handles (`FE-DEV`, `BE-DEV`, `CODE-REVIEWER`, `QA`, `SCRUM-PM`) with real names and GitHub usernames before Day 1. Everything else — page IDs, routes, table names, component names — is copied from the Milestone 1 design baseline so the plan stays traceable:

| Baseline artifact | Where it lives | Used in M2 for |
| --- | --- | --- |
| 26 page specs (P01–P26) | `src/pages.py` → design report §4 | Frontend build order, ownership matrix |
| Shared UI components (12) | `src/pages.py` → `SHARED` | Component kit scope |
| Role navigation model | `src/pages.py` → `SIDEBAR` | AppShell implementation |
| 17-table schema | `database/schema.sql` | DB deliverable, ERD, data dictionary |
| Endpoint contract (58 ops) | `api-spec.yaml` | Mock handlers, page wiring |
| Wireframe source | `src/wire_test.py` renderer | Wireframe exports in `docs/wireframes/` |

**Rule of thumb:** if a task is not written down here with an owner and a PR, it is not in the milestone.

---

## 1. Objective and scope

### Goal

By end of Day 3, `main` contains a runnable frontend implementing **at least 80% of the specified pages** against mock data, a **validated 17-table database design**, and a complete **wireframe set** — all landed through reviewed pull requests.

### Scope

| In scope (M2) | Out of scope (M3) |
| --- | --- |
| React app shell, routing, design system | Real authentication against live API |
| 21+ of 26 pages with realistic mock data | Real CRUD wiring, transactions, rate limits |
| Component kit (12 shared components → 14 primitives) | Email flows, password reset delivery |
| WYSIWYG wireframes for every page | Production deployment, observability |
| Final `schema.sql`, ERD, data dictionary, seed data | Migrations tooling (Alembic baseline comes in M3) |
| API contract draft (OpenAPI skeleton, reused as MSW mocks) | Backend service implementation |

### Success metrics (measured, not asserted)

| Metric | Target |
| --- | --- |
| Pages implemented with mocks | ≥ 21 / 26 (P0 + P1 lists below) |
| PRs merged with ≥ 1 review | 100% |
| CI green on `main` | 100% of merges |
| Component tests passing | ≥ 25 |
| Schema applied to a clean Postgres 16 | 0 errors; 8 integrity assertions pass |
| Lighthouse performance (login + dashboard) | ≥ 90 |
| Wireframes exported | 26 / 26 |

### Definition of "80%"

A page counts as done only when it satisfies **all** of:

1. Route registered and reachable by its specified role.
2. Layout matches the approved wireframe (spacing, hierarchy, single primary action).
3. Loading / empty / error states implemented (skeletons, `EmptyState`, `ErrorState`).
4. Wired to MSW mocks returning the real envelope shape (`{data, meta}` / `{error:{...}}`).
5. Responsive at 360 px, 768 px, 1280 px.
6. Reviewed and merged; no `TODO` left in the page file.

---

## 2. Team, roles and responsibilities

| Handle | Role | Primary ownership | Also contributes |
| --- | --- | --- | --- |
| `FE-DEV` | Frontend developer | `frontend/src/**` — shell, pages, kit | Reviews DB PRs for query-shape realism |
| `BE-DEV` | Backend developer | `database/**`, `docs/api-contract.yaml`, MSW handlers | Reviews FE data-fetching code |
| `CODE-REVIEWER` | Reviewer / second developer | Review queue, refactors, `docs/adr/**`, CI config | Builds the two hardest pages (P19, P26) |
| `QA` | Tester | `frontend/src/**/*.test.jsx`, `database/tests/**`, bug reports | Wireframe audit, accessibility sweep |
| `SCRUM-PM` | Scrum master / PM | Board, issues, standups, `docs/reports/**`, demo script | Wireframes, seed data, README updates |

### RACI for M2 deliverables

| Deliverable | FE-DEV | BE-DEV | CODE-REVIEWER | QA | SCRUM-PM |
| --- | --- | --- | --- | --- | --- |
| Design tokens & kit | **R** | C | **A** | C | I |
| App shell & routing | **R** | I | **A** | C | I |
| 21+ pages | **R** | C | **A** | C | I |
| `schema.sql` + ERD | C | **R** | **A** | C | I |
| Data dictionary | I | **R** | C | C | **A** |
| Seed data | I | **R** | C | C | **A** |
| Wireframes | C | I | C | C | **R/A** |
| Test suites | C | C | C | **R/A** | I |
| CI pipeline | C | C | **R/A** | C | I |
| Milestone report & demo | I | I | C | C | **R/A** |

`R` = responsible, `A` = accountable/approver, `C` = consulted, `I` = informed.

### Working agreements

1. **Two approvals are never required** — one reviewer approval + green CI is enough to merge.
2. **No direct pushes to `main`**, including the PM. Even a typo fix goes through a PR.
3. **PR size budget: ≤ 400 changed lines.** Larger work is split or stacked.
4. **A PR is opened as Draft within the first hour** of work starting, so the board reflects reality.
5. **Review SLA: 2 hours** during the sprint window; reviewer comments are answered with a commit, not a paragraph.
6. **The author merges** their own PR after approval (squash merge), then deletes the branch.
7. **AI-assisted work is disclosed** in the PR body ("Generated with <tool>, reviewed and adapted by @handle") — honest and increasingly standard practice.

---

## 3. Repository and GitHub workflow

### 3.1 Repository structure (target for M2)

```
mentoring-platform/
├── .github/
│   ├── CODEOWNERS
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml
│   │   ├── page_task.yml
│   │   └── db_task.yml
│   └── workflows/
│       ├── frontend-ci.yml
│       └── database-ci.yml
├── frontend/
│   ├── src/
│   │   ├── app/            # router.jsx, providers.jsx
│   │   ├── api/            # client.js, endpoints.js
│   │   ├── components/
│   │   │   ├── ui/         # Button, Input, Select, Badge, Card, Dialog, Drawer, Toast,
│   │   │   │               # DataTable, Pagination, Tabs, EmptyState, ErrorState, Skeleton
│   │   │   └── shared/     # AppShell, StatusBadge, FilterBar, ReasonDialog, ConfirmDialog,
│   │   │                   # FeedbackDialog, BookingDialog, SlotEditorDialog, RequestDrawer
│   │   ├── features/
│   │   │   ├── auth/       # P01–P04
│   │   │   ├── student/    # P05–P14
│   │   │   ├── mentor/     # P15–P21
│   │   │   └── admin/      # P22–P26
│   │   ├── mocks/          # MSW handlers + fixtures (owned by BE-DEV)
│   │   ├── styles/         # tokens.css, base.css
│   │   └── main.jsx
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── database/
│   ├── schema.sql          # final 17-table DDL
│   ├── seed.sql
│   ├── tests/integrity.sql
│   └── data-dictionary.md
├── docs/
│   ├── wireframes/         # P01-login.png … P26-analytics.png
│   ├── api-contract.yaml   # OpenAPI skeleton (paths + envelopes)
│   ├── adr/                # ADR-001…ADR-005
│   ├── reports/            # day-1.md, day-2.md, milestone-2.md
│   └── team/MILESTONE-2-PLAN.md
└── README.md
```

### 3.2 Branch strategy

Trunk-based with short-lived branches. Nothing lives longer than one day.

| Prefix | Use | Example |
| --- | --- | --- |
| `feat/ui/` | Page or component work | `feat/ui/app-shell` |
| `feat/db/` | Schema, seed, data dictionary | `feat/db/requests-and-sessions` |
| `test/` | Test suites | `test/kit-render-tests` |
| `docs/` | Docs, ADRs, wireframes | `docs/wireframes-student-flow` |
| `chore/` | Tooling, CI, deps | `chore/ci-frontend-build` |
| `fix/ui/` | Review feedback fixes | `fix/ui/sidebar-collapse` |

### 3.3 Day-1 repo setup (run once, by SCRUM-PM + CODE-REVIEWER)

```bash
# 1. Initialize and push
git init
git add -A
git commit -m "chore(repo): import Milestone 1 design baseline"
git branch -M main
git remote add origin git@github.com:<org>/<repo>.git
git push -u origin main

# 2. Develop branch is NOT used — trunk-based. Create labels instead.
gh label create "area:frontend" --color 1D76DB
gh label create "area:database" --color 0E8A16
gh label create "area:ci"       --color 5319E7
gh label create "type:feature"  --color A2EEEF
gh label create "type:bug"      --color D73A4A
gh label create "type:test"     --color FBCA04
gh label create "type:docs"     --color 0075CA
gh label create "priority:p0"   --color B60205
gh label create "priority:p1"   --color D93F0B
gh label create "priority:p2"   --color FBCA04

# 3. Milestone
gh api repos/:owner/:repo/milestones -f title="Milestone 2 — Frontend + DB" \
  -f due_on="2026-10-31T23:59:59Z"
```

**Branch protection on `main`:**

| Setting | Value |
| --- | --- |
| Require pull request before merging | ✅ |
| Require approvals | 1 |
| Dismiss stale approvals on new commits | ✅ |
| Require status checks | `frontend-ci`, `database-ci` |
| Require conversation resolution | ✅ |
| Restrict pushes | admins only (for emergency revert) |
| Allow squash merging only | ✅ |
| Auto-delete head branches | ✅ |

### 3.4 Project board

Columns: **Backlog → Ready → In progress → In review → QA → Done**

Automation rules:

- Issue assigned → *In progress*
- PR opened referencing issue → *In review*
- PR merged → issue closes → *Done*
- `priority:p0` issues pinned to the top of *Ready*

Every page gets one issue from the `page_task.yml` template; every DB area gets one from `db_task.yml`. Issue titles are stable and referenced in commits:

```
[P07] Mentor discovery and search
[DB-03] Requests, mentorships, sessions
```

### 3.5 Commit convention

Conventional Commits, scoped by area:

| Type | When | Example |
| --- | --- | --- |
| `feat` | New page/component/table | `feat(ui/student): mentor discovery with filters` |
| `fix` | Bug or review feedback | `fix(ui): stack filter bar below 768px` |
| `refactor` | No behaviour change | `refactor(ui): extract PageHeader` |
| `test` | Tests only | `test(ui): kit render + a11y smoke` |
| `docs` | Docs/ADRs | `docs(adr): record request-form-as-modal` |
| `chore` | Tooling | `chore(ci): cache npm and pip` |
| `style` | Formatting only | `style(ui): apply prettier` |

Rules: imperative mood, ≤ 72 characters, body explains *why* not *what*, reference the issue (`Refs #14`, `Closes #14`).

### 3.6 PR template (`.github/PULL_REQUEST_TEMPLATE.md`)

```markdown
## What

<!-- One paragraph. What changed and why. -->

## Issue

Closes #

## Screenshots

<!-- Before / after or the three breakpoints. Required for UI PRs. -->

| 360px | 768px | 1280px |
| --- | --- | --- |
|  |  |  |

## Checklist

- [ ] Matches the approved wireframe (link)
- [ ] Loading, empty and error states implemented
- [ ] Keyboard navigable; focus visible
- [ ] No console errors or warnings
- [ ] `npm run lint && npm run build && npm test` pass locally
- [ ] Screenshots attached (UI) / DDL applied to clean DB (DB)
- [ ] AI assistance disclosed below

## AI assistance

<!-- Tool, scope, and what was manually changed. Write "None" if not applicable. -->
```

### 3.7 Review rules (enforced by CODEOWNERS + habit)

| Area | Required reviewer |
| --- | --- |
| `frontend/src/components/**`, `frontend/src/styles/**` | CODE-REVIEWER |
| `frontend/src/features/**` | CODE-REVIEWER or FE-DEV |
| `database/**` | CODE-REVIEWER |
| `.github/**` | CODE-REVIEWER |
| `docs/**` | SCRUM-PM |

Reviewer checklist (also pasted as the first comment on every PR by a bot or the PM):

- [ ] Scope matches the linked issue; nothing extra smuggled in
- [ ] Naming follows the conventions table (below)
- [ ] No duplicated styling — tokens/classes reused, not re-invented
- [ ] Data shapes match `api-contract.yaml` (no invented fields)
- [ ] Tests cover the happy path and one failure path
- [ ] No secrets, no `console.log`, no commented-out code

### 3.8 Naming conventions (single source of truth for humans *and* agents)

| Thing | Convention | Example |
| --- | --- | --- |
| Page component | `PascalCase` + `Page` suffix | `MentorDiscoveryPage.jsx` |
| Shared component | `PascalCase` | `StatusBadge.jsx` |
| Hook | `use` + camelCase | `useMentors.js` |
| Mock handler | `camelCase` + `Handlers` | `mentorHandlers.js` |
| CSS token | `--color-*`, `--space-*`, `--radius-*`, `--text-*` | `--space-4` |
| DB table | `snake_case`, plural | `mentoring_requests` |
| DB column | `snake_case`, singular | `responded_at` |
| DB constraint | `ck_<table>_<rule>`, `uq_<table>_<cols>`, `ix_<table>_<cols>` | `ck_requests_expiry` |
| Branch | see §3.2 | `feat/ui/mentor-discovery` |
| Issue | `[P07] Title` / `[DB-03] Title` | `[P07] Mentor discovery and search` |

---

## 4. Design direction — the minimalist overhaul

### 4.1 What we are fixing

The current frontend accumulated clutter as features were added page-by-page. The audit below drives the redesign; each row becomes a review check.

| Problem | Symptom in the old UI | M2 rule |
| --- | --- | --- |
| Competing actions | 3–4 equally weighted buttons per card | **One primary action per view**; everything else is secondary/ghost or in an overflow menu |
| Dense sidebars | 6–7 nav items plus badges plus labels | Icon + label, max 6 items, active state only |
| Badge soup | Statuses expressed as colour chips everywhere | `StatusBadge` used once per row; text always present |
| Inconsistent spacing | Ad-hoc margins (7px, 13px, 22px) | 4-pt scale only: 4 / 8 / 12 / 16 / 24 / 32 / 48 |
| Duplicated filters | Filter bar repeated on 5 pages with different layouts | One `FilterBar` component, same position on every list page |
| Modal stacking | Dialog opening a dialog | Never stack dialogs; detail views are pages or drawers |
| Over-labelled forms | Every field has a hint *and* a placeholder | Label + one hint max; placeholders are examples only |
| Heavy tables | 9-column tables on 360 px screens | `DataTable` collapses to cards below 768 px |
| Colour-only meaning | Red/green dots without text | Colour is never the only signal (a11y) |
| Redundant headings | Page title repeated in the topbar and the card | One `PageHeader` per page |

### 4.2 Ten principles

1. **Whitespace is a feature.** If two elements are related, group them; if not, separate by at least `--space-6`.
2. **One primary action.** A page has exactly one filled button.
3. **Progressive disclosure.** Lists show 4 facts; everything else lives on the detail page or drawer.
4. **Predictable placement.** Page header (title + action) → filters → content → pagination. Always.
5. **Neutral by default, colour for meaning.** 90% of the UI is grayscale; accent is reserved for the primary action and focus.
6. **Type does the hierarchy work.** Two weights (400/600), three sizes per screen.
7. **Every state is designed.** Loading, empty, error, and success are first-class, not afterthoughts.
8. **Keyboard is a first-class citizen.** Visible focus rings, logical tab order, Escape closes overlays.
9. **Mobile is the constraint, not the afterthought.** Design at 360 px first.
10. **No new dependency without an ADR.** The kit is ours; we do not import a second design system.

### 4.3 Design tokens (`frontend/src/styles/tokens.css`)

```css
:root {
  /* colour — neutral first */
  --color-bg:            #F8FAFC;
  --color-surface:       #FFFFFF;
  --color-border:        #E2E8F0;
  --color-text:          #0F172A;
  --color-text-muted:    #64748B;
  --color-accent:        #2563EB;
  --color-accent-hover:  #1D4ED8;
  --color-success:       #16A34A;
  --color-warning:       #D97706;
  --color-danger:        #DC2626;
  --color-focus:         #2563EB;

  /* spacing — 4pt scale */
  --space-1: 4px;  --space-2: 8px;   --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px;  --space-12: 48px;

  /* radius */
  --radius-sm: 6px;   /* badges, inputs */
  --radius-md: 8px;   /* buttons */
  --radius-lg: 12px;  /* cards, dialogs */

  /* type */
  --font-sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px;
  --text-lg: 16px; --text-xl: 20px; --text-2xl: 24px;

  /* layout */
  --topbar-h: 56px;
  --sidebar-w: 240px;
  --content-max: 1200px;
  --form-max: 560px;

  /* elevation — two levels only */
  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.06);
  --shadow-md: 0 8px 24px rgb(15 23 42 / 0.08);
}
```

### 4.4 Layout specification

```
┌──────────────────────────────────────────────────────────────┐
│ Topbar 56px: logo · breadcrumb        · bell(3) · avatar ▾  │
├──────────────┬───────────────────────────────────────────────┤
│ Sidebar      │  Content (max 1200px, padding 24/32)         │
│ 240px        │                                               │
│              │  ┌ PageHeader ─────────────────────────────┐  │
│  Dashboard   │  │ H1 Title                 [Primary CTA]  │  │
│  Find mentors│  └─────────────────────────────────────────┘  │
│  My requests │                                               │
│  Mentorship  │  ┌ FilterBar ──────────────────────────────┐  │
│  Notifications│  │ search · select · select · reset        │  │
│  Profile     │  └─────────────────────────────────────────┘  │
│              │                                               │
│              │  Cards / DataTable  (gap: --space-4)         │
│              │                                               │
│              │  Pagination (right-aligned)                  │
└──────────────┴───────────────────────────────────────────────┘
```

Breakpoints: `sm 640` · `md 768` · `lg 1024` · `xl 1280`.
Below `lg`: sidebar becomes a slide-over opened from a hamburger; content padding drops to `--space-4`.

### 4.5 Wireframe: P07 Mentor discovery (before → after)

**Before** — filters in a card, a filter chip row, a sort dropdown, a results count, three different card actions:

```
[ Search mentors............... ] [Skill ▾] [Interest ▾] [Available ▾] [Apply] [Reset]
Chips: Python x | Data Science x | Clear all
Showing 1–12 of 48          Sort: [Relevance ▾]
┌───────────────────────────────┐
│ [avatar] Rohan Iyer   ★4.8    │
│ Senior Data Engineer @ TechCorp│
│ Python SQL AWS Docker ...      │
│ [View] [Request] [Save] [···] │
└───────────────────────────────┘
```

**After** — one filter bar, one action per card, facts capped at four:

```
Find a mentor                                            [ Recommended | All ]
[ Search by name, skill or company.............. ] [ Filters (2) ]
────────────────────────────────────────────────────────────────────────────
┌──────────────────────────────────────────────────────────────────────────┐
│  Rohan Iyer                                    ● Available                │
│  Senior Data Engineer · TechCorp · 8 yrs                                 │
│  Python · SQL · AWS · Docker                                             │
│  ★ 4.8 (12)        3 mentees · replies in ~1 day          [View profile →]│
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.6 Wireframe: P22 Admin dashboard (before → after)

**Before**: 6 KPI tiles, 3 charts, a queue table, a recent-activity feed, and two duplicated "Review" buttons — all above the fold.

**After**: four KPIs, one queue, one chart. The feed moves behind a tab.

```
Programme overview                              [ Export report ]
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ 124        │ │ 18         │ │ 42         │ │ 7          │
│ Students   │ │ Mentors    │ │ Mentorships│ │ Pending    │
└────────────┘ └────────────┘ └────────────┘ └────────────┘

Needs attention                                     [ View all → ]
┌──────────────────────────────────────────────────────────────────────────┐
│ Mentor application   Lakshmi Pillai      submitted 2 days ago   [Review] │
│ Stale request        Asha → Rohan        12 days pending       [View]    │
│ Request              Vikram → Divya      awaiting mentor       [View]    │
└──────────────────────────────────────────────────────────────────────────┘

[ Participation (30 days) ]  [ Sessions ]  [ Reviews ]     ← tabs, one chart visible
```

### 4.7 Component kit

Twelve primitives live in `components/ui/`; nine composites in `components/shared/`.

| Primitive | API sketch | Notes |
| --- | --- | --- |
| `Button` | `variant="primary\|secondary\|ghost\|danger"`, `size`, `loading`, `icon` | `loading` disables + spinner |
| `Input` / `Textarea` | `label`, `hint`, `error`, `required` | Error text replaces hint; `aria-invalid` |
| `Select` | `label`, `options`, `placeholder` | Native select styled; no custom listbox in M2 |
| `Badge` / `StatusBadge` | `status="pending"` | Status → colour + text map in one file |
| `Card` | `as`, `padding`, `interactive` | `interactive` adds hover + focus ring |
| `DataTable` | `columns`, `rows`, `empty`, `loading` | Renders cards under `md` |
| `Pagination` | `page`, `pageSize`, `total`, `onChange` | Matches contract `meta` |
| `Tabs` | `items`, `value`, `onChange` | Roving tabindex |
| `Dialog` | `open`, `onClose`, `title`, `footer` | Focus trap, Escape, `aria-modal` |
| `Drawer` | `open`, `onClose`, `side="right"` | Used by `RequestDrawer` |
| `Toast` | `toast.success/error(msg)` | Auto-dismiss 5 s, `role="status"` |
| `Skeleton` | `rows`, `height` | No layout shift (reserved height) |
| `EmptyState` | `icon`, `title`, `body`, `action` | Exactly one action |
| `ErrorState` | `title`, `body`, `onRetry`, `requestId` | Shows request ID for support |

Composites map 1:1 to the design baseline: `AppShell`, `FilterBar`, `ReasonDialog`, `ConfirmDialog`, `FeedbackDialog`, `BookingDialog`, `SlotEditorDialog`, `RequestDrawer`.

### 4.8 Architecture decisions recorded during M2

| ADR | Decision | Rationale |
| --- | --- | --- |
| ADR-001 | P09 request form becomes a modal on P08 | Removes a navigation hop; the form is 4 fields |
| ADR-002 | P14 and P21 share one `NotificationsPage` | Identical behaviour; only the endpoint differs |
| ADR-003 | MSW for API mocking, not ad-hoc fixtures | Pages call the real axios client; shapes validated early |
| ADR-004 | Tailwind + CSS custom properties for tokens | Velocity without losing a single token source |
| ADR-005 | No component library (MUI/Chakra) in M2 | The kit is ~14 components; a library would add weight and opinions |

Each ADR is a one-page markdown file in `docs/adr/`, merged with the PR that implements it.

---

## 5. Database design track (BE-DEV, reviewed by CODE-REVIEWER)

### Deliverables

| Artifact | Path | Done when |
| --- | --- | --- |
| Final DDL | `database/schema.sql` | Applies to clean Postgres 16 with zero errors |
| ERD (export) | `docs/wireframes/erd.png` | All 17 tables, all FKs, cardinalities |
| Data dictionary | `database/data-dictionary.md` | Every table: purpose, columns, types, constraints |
| Seed data | `database/seed.sql` | 1 admin, 3 students, 6 mentors, 3 requests, 2 mentorships |
| Integrity tests | `database/tests/integrity.sql` | 8 assertions (below) |
| ERD source | `docs/erd.dbml` | dbdiagram.io source kept in sync with DDL |

### The 17 tables (grouped)

| Group | Tables |
| --- | --- |
| Identity | `users`, `refresh_tokens`, `audit_logs` |
| Profiles | `student_profiles`, `mentor_profiles` |
| Catalogue | `skills`, `career_interests`, `student_skills`, `student_interests`, `mentor_expertise`, `mentor_interests` |
| Matching & relationships | `mentoring_requests`, `mentorships` |
| Scheduling | `availability_slots`, `sessions` |
| Feedback | `feedback` |
| Notifications | `notifications` |

### ERD (core relationships)

```mermaid
erDiagram
    users ||--o| student_profiles : has
    users ||--o| mentor_profiles : has
    users ||--o{ mentoring_requests : sends
    users ||--o{ mentoring_requests : receives
    mentoring_requests ||--o| mentorships : becomes
    users ||--o{ availability_slots : publishes
    mentorships ||--o{ sessions : contains
    sessions ||--o{ feedback : receives
    skills ||--o{ student_skills : tagged
    skills ||--o{ mentor_expertise : tagged
    career_interests ||--o{ student_interests : tagged
    career_interests ||--o{ mentor_interests : tagged
    users ||--o{ notifications : receives
    users ||--o{ refresh_tokens : owns
    users ||--o{ audit_logs : acts
```

### Conventions

- UUID primary keys (`gen_random_uuid()`), `created_at`/`updated_at` `timestamptz` everywhere.
- `updated_at` maintained by trigger, not application code.
- Enumerations as `CHECK` constraints (not Postgres enums) so values are visible in the DDL.
- Business invariants in the database: one pending request per student–mentor pair, one active mentorship per pair, `expires_at > created_at`, slot `end_time > start_time`.
- Partial indexes for hot paths: `ix_mentor_discoverable (profile_status, is_available)`, GIN full-text on mentor profiles.
- Delete behaviour explicit: `ON DELETE CASCADE` for child rows, `RESTRICT` for referenced users.

### Integrity assertions (`database/tests/integrity.sql`)

1. No user with `role='mentor'` lacks a `mentor_profiles` row.
2. No user with `role='student'` lacks a `student_profiles` row.
3. Rejecting a second pending request for the same pair raises a unique violation.
4. Rejecting a second active mentorship for the same pair raises a unique violation.
5. A session whose `scheduled_end <= scheduled_start` is rejected.
6. `feedback.rating` outside 1–5 is rejected.
7. A `mentorships` row whose request is not `accepted` is rejected.
8. Deleting a user cascades to profiles, requests, sessions and tokens (verified inside a rolled-back transaction).

### How QA validates it

```bash
docker run -d --name m2-pg -e POSTGRES_PASSWORD=test -p 55432:5432 postgres:16
psql "postgresql://postgres:test@localhost:55432/postgres" -v ON_ERROR_STOP=1 -f database/schema.sql
psql "postgresql://postgres:test@localhost:55432/postgres" -v ON_ERROR_STOP=1 -f database/tests/integrity.sql
psql "postgresql://postgres:test@localhost:55432/postgres" -f database/seed.sql
psql "postgresql://postgres:test@localhost:55432/postgres" -c "SELECT count(*) FROM users;"  # expect 10
```

CI runs exactly this in the `database-ci` workflow against a `postgres:16` service container.

---

## 6. Frontend track

### 6.1 Page priority and ownership

`P0` = must ship in M2; `P1` = should ship; `P2` = stretch (may slip to M3 without affecting the 80% claim).

| ID | Page | Role | Priority | Owner | Day |
| --- | --- | --- | --- | --- | --- |
| P01 | Login | Public | P0 | FE-DEV | 2 |
| P02 | Registration | Public | P0 | FE-DEV | 2 |
| P03 | Forgot / reset password | Public | P1 | FE-DEV | 3 |
| P04 | Access denied / error | Any | P0 | QA | 2 |
| P05 | Student onboarding | Student | P0 | FE-DEV | 2 |
| P06 | Student dashboard | Student | P0 | FE-DEV | 2 |
| P07 | Mentor discovery | Student | P0 | FE-DEV | 2 |
| P08 | Mentor details | Student | P0 | FE-DEV | 2 |
| P09 | Send request (modal, ADR-001) | Student | P1 | FE-DEV | 3 |
| P10 | My requests | Student | P0 | FE-DEV | 2 |
| P11 | Mentorship details | Student | P1 | FE-DEV | 3 |
| P12 | Session history & feedback | Student | P1 | CODE-REVIEWER | 3 |
| P13 | Edit student profile | Student | P0 | FE-DEV | 3 |
| P14 | Notifications (shared, ADR-002) | Student/Mentor | P2 | FE-DEV | 3 |
| P15 | Mentor dashboard | Mentor | P0 | CODE-REVIEWER | 2 |
| P16 | Incoming requests | Mentor | P0 | CODE-REVIEWER | 2 |
| P17 | Request details | Mentor | P1 | CODE-REVIEWER | 3 |
| P18 | My mentees | Mentor | P1 | CODE-REVIEWER | 3 |
| P19 | Session & availability | Mentor | P0 | CODE-REVIEWER | 3 |
| P20 | Mentor profile editing | Mentor | P0 | FE-DEV | 3 |
| P21 | Notifications (mentor) | Mentor | P2 | FE-DEV | 3 |
| P22 | Admin dashboard | Admin | P0 | CODE-REVIEWER | 2 |
| P23 | User management | Admin | P0 | CODE-REVIEWER | 3 |
| P24 | Mentor approval | Admin | P0 | CODE-REVIEWER | 3 |
| P25 | Mentorship management | Admin | P2 | CODE-REVIEWER | 3 |
| P26 | Analytics & reports | Admin | P2 | CODE-REVIEWER | 3 |

Counts: P0 = 16, P1 = 6, P2 = 4. Shipping P0 + P1 = **22 / 26 (85%)**, above the 80% bar with one page of buffer.

### 6.2 Data strategy

- **MSW is the only mock layer.** `src/mocks/browser.js` starts in dev when `VITE_USE_MOCKS=true`.
- Fixtures are generated from `docs/api-contract.yaml` examples, not hand-invented (BE-DEV owns them).
- Every page calls `src/api/endpoints.js`; switching to the real API in M3 means flipping one env var, not rewriting pages.
- Dates in fixtures are relative (`new Date(Date.now() - 12*864e5)`) so screenshots never go stale.
- Error fixtures are first-class: each list page has a `?error=1` dev toggle to preview `ErrorState`.

### 6.3 Frontend CI (`frontend-ci.yml`)

```yaml
name: frontend-ci
on:
  pull_request:
    paths: ["frontend/**"]
jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm run build
      - run: npm test -- --run
```

---

## 7. QA track

### 7.1 What QA owns in M2

| Artifact | Location | Notes |
| --- | --- | --- |
| Component tests | `frontend/src/components/**/*.test.jsx` | Vitest + Testing Library |
| Page smoke tests | `frontend/src/features/**/*.test.jsx` | Renders route, asserts heading + one interaction |
| Schema tests | `database/tests/integrity.sql` | Co-owned with BE-DEV |
| Wireframe audit | `docs/reports/wireframe-audit.md` | Page-by-page checklist result |
| Bug reports | GitHub issues (`bug_report.yml`) | One issue per defect, severity label |

### 7.2 Test plan (minimum)

| Layer | Count target | Examples |
| --- | --- | --- |
| Primitives | 14 | Button loading state, Input error wiring, Dialog focus trap |
| Composites | 8 | AppShell renders role sidebar, StatusBadge text for each status |
| Pages | 12 | Login validation, discovery filter resets page, requests empty state |
| A11y smoke | 10 pages | `axe-core` via `vitest-axe`, zero serious violations |
| Schema | 8 assertions | See §5 |

### 7.3 Wireframe audit checklist (per page)

- [ ] Title matches the page spec exactly
- [ ] Single primary action, visually dominant
- [ ] All spec elements present (cross-check `src/pages.py`)
- [ ] Empty, loading and error states shown in the audit doc
- [ ] 360 px layout has no horizontal scroll
- [ ] Focus order follows visual order
- [ ] Status conveyed by text, not colour alone
- [ ] No element from the "clutter to remove" list reappears

### 7.4 Bug severity

| Label | Meaning | SLA |
| --- | --- | --- |
| `sev:blocker` | Page unusable / data loss risk | Fix before next standup |
| `sev:major` | Wrong data, broken flow, a11y failure | Same day |
| `sev:minor` | Visual misalignment, copy issue | Before milestone review |
| `sev:nice` | Polish idea | Backlog, M3 |

---

## 8. Scrum / PM track

### 8.1 Rituals

| Ritual | When | Duration | Output |
| --- | --- | --- | --- |
| Sprint kickoff | Day 1, 09:00 | 30 min | Board populated, owners confirmed, ADRs assigned |
| Daily standup | 09:15 and 17:30 | 10 min | `docs/reports/day-N.md` updated |
| Review queue sweep | 13:00 | 15 min | PRs older than 2 h flagged |
| Milestone review | Day 3, 17:00 | 45 min | Demo script executed, `milestone-2.md` published |
| Retro | Day 3, 18:00 | 30 min | 3 keep / 3 drop / 3 try, committed to `docs/reports/retro-2.md` |

### 8.2 Standup format (async-friendly, pasted in the issue thread)

```markdown
**Day 2 — 09:15**
- FE-DEV: shipped P06 + P07 (PR #12 merged). Today: P08, P10. Blocked on: none.
- BE-DEV: schema.sql complete, 6/8 integrity assertions green. Today: fix expiry constraint, seed.sql. Blocked on: reviewer for PR #14.
- CODE-REVIEWER: reviewed 3 PRs, requested changes on #13. Today: P15 + P16. Blocked on: none.
- QA: kit tests at 17/25. Today: P04 + dialog tests. Blocked on: P19 not merged yet.
- PM: wireframes 26/26 exported. Today: audit P01–P10, update board.
```

### 8.3 Board hygiene rules

- Every card in *In progress* has an assignee and a branch link.
- A card may not sit in *In review* for more than 4 hours without a review comment.
- Blocked cards get the `status:blocked` label and are raised at standup, not in DMs.
- *Done* means merged to `main`, not "works on my machine".

### 8.4 Milestone review script (Day 3)

1. **30 s** — the one-sentence pitch and the M2 goal.
2. **3 min** — board walkthrough: 24 issues, 21 closed, 3 carried.
3. **8 min** — live demo: login → student discovery → request → mentor accept → schedule → admin review.
4. **3 min** — database: ERD, schema apply, integrity tests green.
5. **2 min** — test report and coverage numbers.
6. **4 min** — what slipped, why, and the M3 plan.

### 8.5 Metrics captured at close

| Metric | How |
| --- | --- |
| Commits / PRs / reviews | GitHub Insights |
| Cycle time (issue open → merge) | Project board timestamps |
| Pages complete | Issue count in *Done* with `area:frontend` |
| Test count and pass rate | CI output |
| Schema assertions | CI output |

---

## 9. The three-day plan

```mermaid
gantt
    title Milestone 2 — 3-day sprint
    dateFormat YYYY-MM-DD
    axisFormat %a %d %b

    section Foundations (Day 1)
    Repo, labels, board, CI           :d1a, 2026-10-29, 1d
    Tokens + kit primitives           :d1b, 2026-10-29, 1d
    ER model + DDL draft              :d1c, 2026-10-29, 1d
    Wireframes P01-P26                :d1d, 2026-10-29, 1d

    section Build (Day 2)
    AppShell + auth + student flow    :d2a, 2026-10-30, 1d
    Mentor flow (dashboard, requests) :d2b, 2026-10-30, 1d
    schema.sql final + seed.sql       :d2c, 2026-10-30, 1d
    Kit + page tests                  :d2d, 2026-10-30, 1d

    section Close (Day 3)
    Remaining pages + polish          :d3a, 2026-10-31, 1d
    Data dictionary + integrity tests :d3b, 2026-10-31, 1d
    Audit, fixes, demo rehearsal      :d3c, 2026-10-31, 1d
    Milestone review + report         :d3d, 2026-10-31, 1d
```

### Day 1 — Foundations (Thu 29 Oct)

| Time | Session | Owner | Output | PR |
| --- | --- | --- | --- | --- |
| 09:00 | Kickoff: scope, board, owners | SCRUM-PM | 24 issues, board columns | — |
| 09:30 | Repo hardening: protection, CODEOWNERS, templates, labels | CODE-REVIEWER | `.github/**` | #1 |
| 09:30 | Vite scaffold, ESLint/Prettier, Tailwind, router skeleton | FE-DEV | `frontend/` boots | #2 |
| 10:30 | CI workflows (frontend + database) | CODE-REVIEWER | Both checks green on a dummy PR | #1 |
| 10:30 | Design tokens + base reset | FE-DEV | `tokens.css`, `base.css` | #3 |
| 11:00 | ER model in dbdiagram, 17 tables, cardinalities | BE-DEV | `docs/erd.dbml` + PNG | #4 |
| 11:00 | Wireframes P01–P13 (Figma/Excalidraw → PNG) | SCRUM-PM | `docs/wireframes/` first half | #5 |
| 13:00 | Kit primitives: Button, Input, Select, Badge, Card | FE-DEV | `components/ui/*` | #6 |
| 13:00 | DDL draft: identity + profiles + catalogue | BE-DEV | `schema.sql` part 1 | #7 |
| 14:30 | AppShell: topbar, role sidebars, responsive drawer | FE-DEV | `components/shared/AppShell.jsx` | #8 |
| 14:30 | Wireframes P14–P26 | SCRUM-PM | second half | #9 |
| 16:00 | Review sweep: PRs #1–#9 | CODE-REVIEWER | Approvals / change requests | — |
| 17:30 | Standup + demo tokens, shell sketch, ERD | SCRUM-PM | `docs/reports/day-1.md` | — |

**Day 1 exit criteria:** `main` has a running app shell, a token system, a CI pipeline that blocks bad PRs, an ERD with all 17 tables, and 26 wireframes.

### Day 2 — Build the core (Fri 30 Oct)

| Time | Session | Owner | Output | PR |
| --- | --- | --- | --- | --- |
| 09:15 | Standup | SCRUM-PM | `day-2.md` | — |
| 09:30 | Auth pages P01, P02, P04 + form validation | FE-DEV | `features/auth/*` | #10 |
| 09:30 | DDL: requests, mentorships, sessions, feedback, notifications | BE-DEV | `schema.sql` complete | #11 |
| 09:30 | Kit composites: DataTable, Pagination, Tabs, Dialog, Drawer, Toast | CODE-REVIEWER | `components/ui/*` | #12 |
| 11:00 | Student flow P05, P06, P07, P08, P10 | FE-DEV | `features/student/*` | #13 |
| 11:00 | MSW handlers for 58 operations (happy path + 3 error codes each) | BE-DEV | `src/mocks/**` | #14 |
| 13:00 | Mentor flow P15, P16 | CODE-REVIEWER | `features/mentor/*` | #15 |
| 13:00 | Kit + shell tests (17 tests) | QA | `*.test.jsx` | #16 |
| 14:30 | Student flow review fixes + P13 profile | FE-DEV | merged | #17 |
| 14:30 | `seed.sql` + integrity assertions 1–4 | BE-DEV | `database/**` | #18 |
| 16:00 | Wireframe audit P01–P13 | QA | `wireframe-audit.md` part 1 | #19 |
| 17:30 | Standup + demo student flow against mocks | SCRUM-PM | `day-2.md` | — |

**Day 2 exit criteria:** a student can log in, onboard, discover a mentor, view details and track requests — entirely against mocks. Schema is complete; seeds load.

### Day 3 — Coverage and close (Sat 31 Oct)

| Time | Session | Owner | Output | PR |
| --- | --- | --- | --- | --- |
| 09:15 | Standup + scope check (drop P2 items if behind) | SCRUM-PM | decision logged | — |
| 09:30 | Mentor P17, P18, P19 (schedule is the hard one) | CODE-REVIEWER | `features/mentor/*` | #20 |
| 09:30 | Student P11, P12, P03, P09 modal | FE-DEV | `features/student/*` | #21 |
| 09:30 | Integrity assertions 5–8 + data dictionary | BE-DEV | `database/**`, `docs` | #22 |
| 11:00 | Admin P22, P23, P24 (+ P25/P26 if green) | CODE-REVIEWER | `features/admin/*` | #23 |
| 11:00 | Page tests + a11y sweep (target 25 tests) | QA | `*.test.jsx` | #24 |
| 13:00 | Consistency pass: tokens, spacing, button hierarchy | CODE-REVIEWER | refactor PR | #25 |
| 13:00 | Wireframe audit P14–P26, bug triage | QA | audit complete | #26 |
| 14:30 | Fix `sev:blocker` / `sev:major` only | All | merged | — |
| 15:30 | README update: screenshots, run instructions, M2 status | SCRUM-PM | `README.md` | #27 |
| 16:00 | Demo rehearsal | SCRUM-PM | run-of-show notes | — |
| 17:00 | Milestone review | All | `docs/reports/milestone-2.md` | — |
| 18:00 | Retro + M3 backlog draft | SCRUM-PM | `retro-2.md` | — |

**Day 3 exit criteria:** ≥21 pages merged, schema validated, CI green, demo rehearsed, report published, tag `v0.2.0-m2` created.

---

## 10. What the GitHub history should look like

This is the authenticity layer: small commits, early drafts, real review iterations, squash merges. The timeline below is a *template* — actual times will differ, but the shape should match.

### Day 1 (excerpt)

| Time | Event | Detail |
| --- | --- | --- |
| 09:41 | PR #1 opened | `chore(repo): branch protection, templates, labels, CODEOWNERS` |
| 09:58 | PR #2 opened (draft) | `chore(frontend): scaffold vite + react + tailwind + eslint` |
| 10:22 | Commit on #2 | `chore(frontend): pin node 20, add engines field` |
| 10:47 | PR #3 opened | `feat(ui): design tokens and base styles` |
| 11:05 | Review on #3 | "`--space-5` slipped in — scale is 1/2/3/4/6/8/12. Otherwise clean." |
| 11:18 | Commit on #3 | `fix(ui): remove non-scale spacing token` → approved → squash-merged |
| 11:30 | PR #4 opened | `feat(db): ER model for 17 tables` |
| 12:02 | Review on #4 | "`mentor_interests` is missing from the diagram even though the table exists." |
| 12:20 | Commit on #4 | `fix(db): add mentor_interests to ERD and cardinalities` |
| 13:15 | PR #8 opened (draft) | `feat(ui): app shell with role sidebars` |
| 15:40 | PR #8 ready for review | screenshots at 3 breakpoints attached |
| 16:12 | Review on #8 | "Sidebar collapses at 1024 but the hamburger appears at 900 — align to `lg`." |
| 16:45 | Commit on #8 | `fix(ui): show sidebar toggle below lg only` |
| 17:05 | PR #8 merged | squash → `main` |

### Day 2 (excerpt)

| Time | Event | Detail |
| --- | --- | --- |
| 09:52 | PR #11 opened | `feat(db): requests, mentorships, sessions, feedback` |
| 10:31 | Review on #11 (changes requested) | "Two issues: `uq_pending_request` should be partial (`WHERE status='pending'`), and `expires_at` needs a CHECK against `created_at`." |
| 11:04 | Commit on #11 | `fix(db): partial unique index for pending requests` |
| 11:20 | Commit on #11 | `fix(db): add ck_requests_expiry` |
| 11:41 | PR #11 approved + merged | — |
| 12:15 | PR #14 opened (draft) | `feat(mocks): MSW handlers for auth and mentors` |
| 14:03 | Comment on #14 | "Login 429 fixture missing — QA needs it for the rate-limit banner." |
| 14:38 | Commit on #14 | `test(mocks): add rate-limited login fixture` |
| 16:22 | PR #13 merged | student flow, 6 pages |

### Day 3 (excerpt)

| Time | Event | Detail |
| --- | --- | --- |
| 10:12 | Issue #31 opened (`sev:major`) | "P19: booking dialog shows slots in UTC instead of local time" |
| 10:40 | PR #32 opened | `fix(ui): render slot times in the mentor's timezone` |
| 11:05 | Review on #32 | approved with a nit about the `Intl` fallback |
| 11:20 | Merged | issue auto-closed |
| 15:47 | Tag created | `v0.2.0-m2` on `main` |
| 16:05 | Release published | auto-generated notes grouped by label |

### Example PR description (realistic, not perfect)

```markdown
## What

Implements P07 (mentor discovery) and P08 (mentor details) against MSW mocks.
Discovery uses one `FilterBar` (search + skill + availability) with URL-synced
state so refreshes and back/forward keep filters. Details page shows four facts
above the fold and everything else under tabs.

## Issue

Closes #14

## Screenshots

| 360px | 768px | 1280px |
| --- | --- | --- |
| attached | attached | attached |

## Notes for reviewer

- Recommendation and search share one endpoint call; `mode=recommended` is a
  query param rather than a separate route — matches the contract.
- I did not implement the "save mentor" action: it is not in the API contract
  and would need a new table. Flagging rather than inventing.

## AI assistance

Scaffolded the card layout with Claude, then rewrote the filter state to use
`useSearchParams` and added the empty/error states manually.
```

### Example review thread (the kind that makes a repo look real)

> **CODE-REVIEWER** · requested changes
> The empty state says "No mentors found" but gives no way out. Every empty state needs one action — in this case "Clear filters". Also `MentorCard` re-implements `Card` instead of composing it; let's not fork the primitive on day 2.

> **FE-DEV** · pushed 2 commits
> Good catch on both. Empty state now resets filters. `MentorCard` composes `Card` with `interactive` — the only local styles are the meta row grid.

> **CODE-REVIEWER** · approved
> LGTM. Nice touch syncing filters to the URL.

---

## 11. AI prompt playbook

The goal is **consistency across five people using different tools**. Three mechanisms make that work:

1. **One constitution block** pasted at the start of every session.
2. **One task template per role**, with the spec snippet attached.
3. **One rule:** generated code is a draft; the person who commits it owns it.

### 11.1 The project constitution (paste first, every time)

```text
You are contributing to a React 18 + Vite + Tailwind frontend for an IITM
mentoring platform. Follow these rules exactly. Do not deviate, do not add
libraries, do not invent data fields.

STACK
- React 18, Vite, react-router-dom v6, axios, Tailwind CSS.
- Tests: Vitest + @testing-library/react. No Enzyme, no Jest config.
- No component library (no MUI, Chakra, shadcn, Ant). Use our kit.

STRUCTURE
- Pages: src/features/<role>/<PageName>Page.jsx
- Primitives: src/components/ui/<Name>.jsx
- Composites: src/components/shared/<Name>.jsx
- API calls: src/api/endpoints.js only. Never call axios directly in a page.
- Mocks: src/mocks/ (MSW). Never hardcode fixture data inside a component.

DESIGN SYSTEM (non-negotiable)
- Spacing: 4/8/12/16/24/32/48 only. No arbitrary values.
- Colours: tokens only (--color-*). Neutral UI; accent reserved for the
  single primary action and focus rings.
- Radius: 6 badges/inputs, 8 buttons, 12 cards/dialogs.
- Type: 12/13/14/16/20/24. Weights 400 and 600 only.
- One primary button per view. Everything else secondary or ghost.
- Every list page: PageHeader -> FilterBar -> content -> Pagination.
- Every async view implements loading (Skeleton), empty (EmptyState with one
  action) and error (ErrorState with retry + request id).

DATA CONTRACT
- Success envelope: { "data": ..., "meta": { "page", "page_size", "total" } }
- Error envelope: { "error": { "code", "message", "details", "request_id" } }
- Never invent endpoint paths or fields. If something is missing, stop and say
  so instead of guessing.

CODE QUALITY
- Functional components, hooks only. No class components.
- PropTypes are not used; keep props explicit and documented with JSDoc.
- No console.log, no commented-out code, no TODO without an issue number.
- Accessible by default: labels bound to inputs, aria-invalid on errors,
  focus-visible rings, Escape closes overlays, colour never the only signal.

OUTPUT FORMAT
- List every file you create or modify, with its full path.
- Then output the complete file contents, one fenced block per file.
- Then a short "How to verify" section with exact commands.
```

### 11.2 Frontend page prompt (FE-DEV)

```text
Using the project constitution above, implement page {PAGE_ID} — {PAGE_TITLE}
at route {ROUTE} for the {ROLE} role.

PAGE SPEC (from the design baseline, do not add features):
{ELEMENTS_AND_ACTIONS_FROM_src/pages.py}

WIREFRAME: docs/wireframes/{PAGE_ID}-{slug}.png
ENDPOINTS USED: {E## list} — mock handlers already exist in src/mocks.

REQUIREMENTS
1. Compose existing primitives (Button, Input, Card, DataTable, ...). If a
   primitive is missing, stop and list what is needed instead of building it.
2. URL-synced list state (page, page_size, q, filters) via useSearchParams.
3. Loading, empty and error states. Empty state has exactly one action.
4. Responsive: verify 360 / 768 / 1280. DataTable collapses to cards < 768.
5. One test file covering: renders, primary interaction, empty state.

DELIVER
- Files created/modified with paths.
- The page component, its hook (if any), and the test.
- "How to verify" commands.
```

### 11.3 Frontend component prompt (FE-DEV / CODE-REVIEWER)

```text
Using the project constitution above, build the primitive {NAME}.

API (exact):
{PROPS_TABLE}

BEHAVIOUR
- {states and interactions}
- Keyboard: {keys}
- ARIA: {roles and attributes}

CONSTRAINTS
- Tailwind classes only from the token scale; no arbitrary values.
- No new dependencies.
- Export a single named component plus a `variants` map if needed.
- Include a test file with one test per state.

Show the component, the test, and any change needed in the kit index.
```

### 11.4 Database prompt (BE-DEV)

```text
Using the project constitution above (data contract section applies), produce
DDL for the {GROUP} tables of a PostgreSQL 16 schema.

TABLES AND COLUMNS
{COLUMN_LIST_WITH_TYPES_AND_CONSTRAINTS}

RULES
- UUID primary keys with gen_random_uuid(); timestamptz timestamps.
- CHECK constraints for enumerations; name them ck_<table>_<rule>.
- Partial unique indexes where the invariant is conditional
  (e.g. one pending request per student-mentor pair).
- Explicit ON DELETE behaviour on every FK.
- updated_at maintained by a trigger function, defined once.
- Comments (COMMENT ON) for every table: one line of purpose.

DELIVER
1. The DDL, idempotent enough to re-run in CI on a clean database.
2. The matching dbdiagram.io DBML snippet.
3. Three seed rows per table that satisfy every constraint.
4. A list of integrity assertions QA should encode.
```

### 11.5 Test prompt (QA)

```text
Using the project constitution above, write tests for {FILE_OR_PAGE}.

COVER
1. Happy path: renders with mock data, asserts the visible facts.
2. Empty state: asserts the message and the single action.
3. Error state: asserts the error code is surfaced and retry calls the API.
4. One accessibility assertion (axe, no serious violations).

RULES
- Vitest + Testing Library. Query by role and accessible name, never by class.
- Mock at the network boundary with MSW, not by stubbing hooks.
- No snapshot tests.
- Each test name reads as a sentence: "shows a retry action when the request fails".

DELIVER the test file and a one-line note on any component change required to
make it testable (prefer changing the component over weakening the test).
```

### 11.6 Review prompt (CODE-REVIEWER)

```text
Review this diff as a senior reviewer on a 3-day milestone.

CONTEXT: {PR_TITLE} — {ONE_LINE_INTENT}. Linked issue: #{N}.
CONVENTIONS: {paste §3.8 naming table + §4.2 principles}

CHECK, in this order:
1. Scope: does the diff do only what the issue asks?
2. Contract: do data shapes match docs/api-contract.yaml? Any invented field?
3. Design system: tokens only, one primary action, spacing scale, states present.
4. Accessibility: labels, focus, keyboard, colour-only meaning.
5. Tests: would they fail if the behaviour broke?
6. Duplication: is anything re-implementing an existing primitive?

OUTPUT
- Blocking comments, each with file:line and a concrete fix.
- Non-blocking nits, clearly separated.
- A verdict: approve / request changes.
Do not rewrite the code; point at it.
```

### 11.7 PM prompt (SCRUM-PM)

```text
You are the scrum master for a 5-person, 3-day milestone. Using the board state
below, produce:
1. A standup summary in the team's format (role: shipped / today / blocked).
2. A risk list: anything in "In review" > 4 h, any P0 not started, any PR
   without a reviewer.
3. A milestone burndown line: issues closed vs. total, per day.

BOARD STATE
{paste issue list with status, assignee, labels, PR link}

RULES
- No praise, no filler. Facts and owners only.
- Blockers must name a person and a next action.
- If the numbers say we will miss 80%, say so and propose what to cut.
```

### 11.8 Consistency guardrails

| Risk | Guardrail |
| --- | --- |
| Five people generate five button styles | Kit primitives merged on Day 1; pages may not define their own buttons |
| Agents invent API fields | Contract file is attached to every prompt; reviewers check against it |
| Spacing drift | Tailwind config restricts spacing to the scale; arbitrary values fail lint |
| Duplicate components | PR checklist asks "does this already exist in `components/`?" |
| Copy tone drift | All strings live in the page component; reviewer checks against the spec title |
| Silent AI errors | Author must state what they changed from the generated draft |
| Review bottleneck | Reviewer is also a builder, so review happens in fixed 13:00 sweeps, not ad hoc |

---

## 12. Definition of Done — Milestone 2

### Frontend

- [ ] 21+ pages implemented and reachable by role
- [ ] AppShell with three role sidebars, responsive below `lg`
- [ ] 14 primitives + 8 composites merged with tests
- [ ] All async views have loading / empty / error states
- [ ] Keyboard navigation and visible focus on every interactive element
- [ ] No horizontal scroll at 360 px on any P0/P1 page
- [ ] `npm run lint`, `npm run build`, `npm test` green
- [ ] Lighthouse ≥ 90 on P01 and P06

### Database

- [ ] `schema.sql` applies cleanly to Postgres 16
- [ ] All 17 tables, FKs, checks, indexes present and documented
- [ ] ERD exported and committed
- [ ] Data dictionary complete (every column described)
- [ ] `seed.sql` loads; 10 users, 3 requests, 2 mentorships
- [ ] 8 integrity assertions pass in CI

### Process

- [ ] 100% of merges through reviewed PRs
- [ ] Every issue closed by a PR (`Closes #N`)
- [ ] Board reflects reality at close (no stale *In progress*)
- [ ] `docs/reports/milestone-2.md` published with metrics
- [ ] Tag `v0.2.0-m2` created
- [ ] Retro notes committed

### Demo

- [ ] Script rehearsed end-to-end without a dead link
- [ ] Mock data looks like a real programme (names, dates, capacities)
- [ ] Every screen in the script has its empty state ready in case of failure

---

## 13. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Reviewer becomes the bottleneck | High | High | Fixed review sweeps at 13:00; reviewer builds only two pages |
| Design drift between pages | Medium | High | Kit frozen on Day 1; no page-local primitives |
| P19 scheduling is underestimated | Medium | Medium | Reviewer owns it and starts Day 3 at 09:30; timezone logic mocked first |
| Schema churn breaks mocks | Medium | Medium | Mocks generated from the contract, not the DDL; contract frozen Day 1 |
| AI-generated code that "looks right" but isn't | Medium | High | Tests required per page; reviewer checks contract and states |
| Scope creep (P2 pages) | High | Low | P2 only after 15:30 on Day 3, and only if CI is green |
| Windows/macOS line-ending noise | Low | Low | `.gitattributes` with `* text=auto eol=lf` |

---

## 14. Handoff to Milestone 3

Carried forward deliberately:

| Item | Why it waits |
| --- | --- |
| Real API wiring | Backend services land in M3; pages already call `endpoints.js` |
| Alembic baseline | Schema must be stable first; baseline generated from final DDL |
| P25, P26 (and any slipped P2) | Analytics needs real aggregates; mentorship admin needs live data |
| E2E suite (Playwright) | Needs both halves running; story list drafted in M2 |
| Auth hardening (refresh rotation, rate limits) | Backend concern; contract already specifies behaviour |
| Deployment | M4; M2 stays local + CI |

M3 entry criteria: `main` green, schema tagged, contract frozen, 21+ pages merged.

---

## Appendix A — Issue templates

### `page_task.yml`

```yaml
name: Page task
description: One page from the design baseline
labels: ["area:frontend", "type:feature"]
body:
  - type: input
    id: page_id
    attributes: { label: Page ID, placeholder: P07 }
  - type: input
    id: route
    attributes: { label: Route, placeholder: /student/mentors }
  - type: textarea
    id: spec
    attributes: { label: Spec summary, description: Elements and actions from src/pages.py }
  - type: input
    id: wireframe
    attributes: { label: Wireframe link }
  - type: checkboxes
    id: dod
    attributes:
      label: Done when
      options:
        - { label: Matches wireframe at 360/768/1280 }
        - { label: Loading, empty and error states }
        - { label: Page test passes }
        - { label: Reviewed and merged }
```

### `db_task.yml`

```yaml
name: Database task
description: Schema area, seed, or integrity work
labels: ["area:database", "type:feature"]
body:
  - type: input
    id: area
    attributes: { label: Area, placeholder: "Requests, mentorships, sessions" }
  - type: textarea
    id: tables
    attributes: { label: Tables and constraints }
  - type: checkboxes
    id: dod
    attributes:
      label: Done when
      options:
        - { label: Applies cleanly to Postgres 16 }
        - { label: Integrity assertion added }
        - { label: Data dictionary updated }
        - { label: Reviewed and merged }
```

### `bug_report.yml`

```yaml
name: Bug report
description: Something behaves differently from the spec
labels: ["type:bug"]
body:
  - type: input
    id: page
    attributes: { label: Page / route }
  - type: dropdown
    id: severity
    attributes:
      label: Severity
      options: ["sev:blocker", "sev:major", "sev:minor", "sev:nice"]
  - type: textarea
    id: steps
    attributes: { label: Steps to reproduce }
  - type: textarea
    id: expected
    attributes: { label: Expected vs actual }
  - type: input
    id: env
    attributes: { label: Browser / viewport }
```

---

## Appendix B — Daily report template

```markdown
# Day N — <date>

## Shipped
| PR | Title | Owner | Reviewers |
| --- | --- | --- | --- |

## In review at close
| PR | Title | Waiting on | Age |
| --- | --- | --- | --- |

## Blocked
| Issue | Blocker | Owner | Next action |
| --- | --- | --- | --- |

## Numbers
- Issues closed today: N / total
- PRs merged: N (avg review time: Nh)
- Pages complete: N / 21 target
- Tests: N passing / N total

## Tomorrow's first three
1.
2.
3.
```

---

## Appendix C — Wireframe export checklist (SCRUM-PM)

For every page P01–P26:

- [ ] Desktop frame 1280 px wide
- [ ] Mobile frame 360 px wide
- [ ] Title = exact page title from the baseline
- [ ] One primary action highlighted
- [ ] Empty state drawn (not described)
- [ ] Error state drawn
- [ ] File named `P07-mentor-discovery.png`
- [ ] Linked from the page issue
- [ ] Reviewed by FE-DEV before the build starts

---

*Owner: SCRUM-PM · Reviewers: all five · Last updated: Day 0 of the sprint.*
