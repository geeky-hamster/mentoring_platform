# Front end — Student Mentoring and Career Support Platform

React implementation of the 26 pages in the design report, talking to the FastAPI backend at
`/api/v1`.

## Stack

- React 18 + Vite 6
- React Router 6
- Bootstrap 5 + React Bootstrap
- Axios (JWT access token in memory, refresh cookie handled by the browser)

Navy `#1F3A5F` and teal `#2A7F8E` are the brand colours, with a responsive sidebar shell for the
three signed-in roles and a split hero/panel layout for authentication pages.

## Setup

```powershell
npm install
npm run dev
```

Open **http://localhost:5173**. Vite proxies `/api` and `/health` to
`http://localhost:8000` (`vite.config.js`), so run the backend on port 8000 first.

```powershell
npm run build      # production bundle in dist/
npm run preview    # serve the production build locally
```

For production, serve `dist/` behind a reverse proxy that forwards `/api` to the backend, or
change the axios `baseURL` in `src/api.js` to an absolute API URL and configure CORS. The refresh
cookie is `HttpOnly`, `SameSite=Lax` and scoped to `/api/v1/auth`, so the app and API should be
same-origin.

## Routes

| Page | Route |
| --- | --- |
| 1 Sign in | `/login` |
| 2 Create account | `/register` |
| 3 Forgot password | `/forgot-password` |
| 4 Reset / error pages | `/reset-password`, `/session-expired`, `/403`, `/404`, `/500` |
| 5 Student onboarding | `/student/onboarding` |
| 6 Student dashboard | `/student/dashboard` |
| 7 Mentor discovery | `/student/mentors` |
| 8 Mentor profile (student view) | `/student/mentors/:mentor_id` |
| 9 Send mentoring request | `/student/mentors/:mentor_id/request` |
| 10 My requests | `/student/requests` |
| 11 Mentorship overview | `/student/mentorships`, `/student/mentorships/:mentorship_id` |
| 12 Sessions and feedback | `/student/mentorships/:mentorship_id/sessions` |
| 13 Student profile | `/student/profile` |
| 14 Student notifications | `/student/notifications` |
| 15 Mentor dashboard | `/mentor/dashboard` |
| 16 Incoming requests | `/mentor/requests` |
| 17 Request detail | `/mentor/requests/:request_id` |
| 18 My mentees | `/mentor/mentees` |
| 19 Schedule and availability | `/mentor/schedule` |
| 20 Mentor profile | `/mentor/profile` |
| 21 Mentor notifications | `/mentor/notifications` |
| 22 Admin dashboard | `/admin/dashboard` |
| 23 User and catalogue management | `/admin/users` (`?tab=catalogue`) |
| 24 Mentor review | `/admin/mentors` |
| 25 Mentorship and request oversight | `/admin/mentorships` (`?tab=requests`) |
| 26 Programme analytics | `/admin/analytics` |

`/` redirects to the signed-in user's home area (or `/login`). `/student/mentorships` opens the
active or most recent mentorship. A catch-all route renders the 404 page. Role guards redirect
signed-in users to their own area and send anonymous users to `/login` with a return path.

## Layout

```
src/
  main.jsx             providers: Router, Toast, Auth
  App.jsx              route table and role guards
  auth.jsx             AuthProvider, session restore, RequireAuth, homeFor()
  api.js               axios instance, normalized ApiError, refresh queue,
                       getAll() paging helper, downloadCsv()
  styles.css           theme tokens, shell, cards, tables, charts, week grid

  components/
    shell.jsx          top bar, sidebar navigation, mobile drawer, user menu
    ui.jsx             PageHeader, Panel, StatCard, DataTable, Pager, Tabs, badges,
                       empty/error/loading states, formatters, useApi()
    dialogs.jsx        booking, feedback, reason/confirm, request drawer, catalogue,
                       session edit and availability editor dialogs
    editors.jsx        skill/interest pickers, password form, missing-fields note
    toast.jsx          toast provider used by every page

  pages/
    public.jsx         login, register, forgot/reset password, error pages
    student.jsx        pages 5-14 plus the shared notifications page
    mentor.jsx         pages 15-21
    admin.jsx          pages 22-26
```

## Conventions

- **Data loading** — `useApi(loader, deps)` returns `{ data, loading, error, reload }`; mutations
  call the API client and then `reload({ silent: true })`. Lists use the shared `Pager`.
- **Paging** — the API caps page size at 50. `getAll(path, params)` follows pages and returns the
  concatenated rows; use it for client-side counts and for sessions/mentorships.
- **Errors** — every non-2xx response becomes an `ApiError` with `code`, `message`, `details`,
  `requestId` and `fieldError(field)`. Pages render `ErrorState`/`ApiErrorBanner`; forms map
  server field errors next to inputs.
- **Auth** — the access token lives only in memory. On load the app calls `/auth/refresh`; a 401
  triggers one queued refresh and replay. If refresh fails, the API layer emits session expiry and
  the user is sent to `/session-expired`.
- **Dialogs** — booking supports student slot booking and mentor slot-or-custom-time booking;
  destructive actions use `ReasonDialog` (optional/required reason) or `ConfirmDialog`.
- **Notifications** — shared component for students and mentors; row click marks an event read
  and opens the target, with a mark-all-as-read action.
- **Accessibility** — semantic tables/headings, labelled form controls, keyboard-dismissable
  modals, focus styles, `aria-label`s on icon buttons, and a skip-to-content link.
- **Responsive** — tables collapse to stacked cards under 768px; the sidebar becomes an
  off-canvas drawer.

## Demo experience

The login page exposes demo-account shortcuts (student, mentor, administrator). Seeded data
includes a student with an accepted mentorship and rated session, a pending request, a mentor at
capacity, a paused mentor and a mentor awaiting review, so every page has meaningful content on
first run. See `../RUN.md` for credentials and seeding.

## Checks

`npm run build` must pass. There is no committed unit or browser test suite; the UI was verified
during development with Playwright flows covering all roles and every page, including booking and
cancelling sessions, availability editing, registration → profile submission → admin
approve/suspend, account suspend/reactivate and CSV download. When changing shared components,
re-run the backend checks as well — most UI failures surface as contract mismatches.

## Known limitations

- No server-side rendering or i18n; copy and date formats are English/`en-IN`-friendly.
- Email is not sent while `EMAIL_ENABLED=false` on the backend; password-reset tokens are logged
  server-side for local development.
- CSV export is a browser download (blob + anchor) and depends on the
  `Content-Disposition` header.
- The bundle is a single ~510 kB chunk; Vite warns about chunk size. Route-level code splitting is
  deliberate future work, not required for this deliverable.
