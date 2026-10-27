"""Sections 10-15."""
from doc import *
import schema, api, matching as M, pages, components_data as CD
from content_a import tag, D
from reportlab.platypus import Table, TableStyle


def mono(t):
    return f"<font face='DVM'>{esc(t)}</font>"


# =============================================================================================
def sec10():
    s = H1("matching")
    s.append(P("Mentor matching ranks eligible mentors for one student. It is a <b>transparent weighted rule</b>, not a learned model: every point of the score can be traced to a fact in the two profiles, "
               "the student sees why a mentor was ranked, and an administrator can audit any result. The formula and weights are " + tag("P") + "; the weights in particular are a starting hypothesis that "
               "must be validated with real users (" + R("matching.validate") + ")."))
    s.append(H2("inputs"))
    s.append(table(["Side", "Inputs used", "Source"], [
        ["Student", "Skills with proficiency level; up to five <i>focus</i> skills (the skills the student most wants help with); career interests.", "student_skills, student_interests"],
        ["Mentor", "Expertise skills with level; career pathways advised on; open slots in the next 14 days; active mentees and maximum.", "mentor_expertise, mentor_interests, availability_slots, mentorships, mentor_profiles"],
        ["Context", "Existing pending request, active mentorship or 30-day cooldown between the pair.", "mentoring_requests, mentorships"]], [60, 280, 142]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Hard eligibility filters</b> run first and remove mentors entirely; they are never traded off against score. A mentor is eligible only if all of these hold:"))
    s.extend(bullets(["the mentor profile is <i>approved</i>;", "the mentor has switched <i>is_available</i> on;", "the mentor's account is active (not suspended or deactivated);",
                      "the mentor has a free place (active mentees below max_active_mentees);", "no pending request, active mentorship or cooldown exists between this student and the mentor."]))
    s.append(P("Filtering before scoring keeps the list honest (a student is never recommended someone who cannot accept) and makes the scoring set small."))

    s.append(H2("formula"))
    s.append(callout("<b>Score = 0.50 &middot; S + 0.30 &middot; C + 0.20 &middot; A</b> &nbsp;&nbsp; each part is on a 0-100 scale, so the score is also 0-100.", "proposed"))
    s.append(Spacer(1, 4))
    s.append(table(["Part", "Meaning", "Definition"], [
        ["<b>S</b> Skills (weight 0.50)", "How well the mentor's expertise covers the skills the student wants help with.",
         "Let F be the student's focus skills (at most 5; if none is flagged, the first five listed). For each skill k in F, q(k) = 1.0 if the mentor lists k at a <i>higher</i> level than the student, 0.6 if at the <i>same</i> level, 0.3 if <i>lower</i>, 0 if the mentor does not list k. "
         "<b>S = 100 &times; (sum of q(k)) / |F|.</b>"],
        ["<b>C</b> Career interests (weight 0.30)", "Overlap between the pathways the student cares about and those the mentor advises on.",
         "<b>C = 100 &times; |student interests &cap; mentor interests| / |student interests|.</b>"],
        ["<b>A</b> Availability (weight 0.20)", "Whether the mentor can realistically help soon.",
         f"<b>A = 70 &times; min(1, open slots in next 14 days / {M.SLOT_TARGET}) + 30 &times; free places / maximum places.</b> Six or more open slots earn the full slot part."]], [90, 150, 242]))
    s.append(Spacer(1, 4))
    s.append(table(["Constant", "Value", "Reason"], [
        ["Weights S, C, A", "0.50, 0.30, 0.20", "Skills decide whether a mentor can help; interests decide whether they should; availability decides whether they can soon. Order of importance is a judgement to test."],
        ["Level credits q", "1.0 higher, 0.6 equal, 0.3 lower, 0 absent", "A more experienced mentor is best; an equal-level mentor is useful as a peer; a lower level is a weak fit."],
        ["Focus skills", "at most 5", "Stops a long skill list from diluting the score."],
        ["Slot target", f"{M.SLOT_TARGET} slots in 14 days", "About three sessions a week of choice; more slots add no value."],
        ["Slot / capacity split", "70 / 30", "Real bookable time matters more than spare capacity."]], [100, 140, 242]))
    s.append(Spacer(1, 3))
    s.append(P("The displayed number is rounded to one decimal and labelled a <i>match score</i>, never a percentage chance of success."))

    s.append(H2("missing"))
    s.extend(bullets([
        "<b>Missing data rule.</b> If the student has no skills (S undefined) or no interests (C undefined), that part is left out and the remaining weights are divided by their sum, so a student is not punished for an empty field. "
        "Example: with no interests, Score = (0.50 S + 0.20 A) / 0.70. A is always defined.",
        "<b>Ordering.</b> Mentors are sorted by score (descending); ties are broken by S, then C, then more open slots, then more free places, then the smaller mentor id. The order is therefore deterministic, which keeps pagination stable.",
        "<b>Pagination</b> applies after sorting; page_size is limited to 50.",
    ]))

    s.append(H2("worked"))
    s.append(P("Student <b>Asha</b> (sample data) lists Python (intermediate), SQL (beginner) and Machine Learning (beginner), all three flagged as focus skills, and is interested in <i>Data Science</i> and <i>Higher Studies</i>. "
               "Six sample mentors exist; three are excluded by the hard filters."))
    st = M.ASHA
    rows = []
    reasons = {"Divya Sharma": "excluded: at capacity (2 of 2)", "Sanjay Patel": "excluded: not accepting new mentees", "Lakshmi Pillai": "excluded: profile not approved"}
    for m in M.MENTORS:
        ex = reasons.get(m.name, "eligible")
        rows.append([f"<b>{m.name}</b>", ", ".join({"python": "Python", "sql": "SQL", "ml": "Machine Learning", "stats": "Statistics"}[k] for k in ("python", "sql", "ml", "stats") if M.SK[k] in m.expertise) or "-",
                     f"{m.open_slots_14d}", f"{m.max_active_mentees - m.active_mentees} of {m.max_active_mentees}", ex])
    s.append(tab_caption("Sample mentors and eligibility (sample data)"))
    s.append(table(["Mentor", "Skills listed", "Open slots (14 d)", "Free places", "Eligibility"], rows, [100, 120, 70, 60, 132], style="tds"))
    s.append(Spacer(1, 4))
    res = M.worked_example()
    lv = lambda m, k: m.expertise.get(M.SK[k], "-")
    calc = {
        "Rohan Iyer": "S: Python advanced &gt; intermediate (1.0), SQL advanced &gt; beginner (1.0), ML intermediate &gt; beginner (1.0) = 3.0/3 = 100.0. C: shares Data Science only = 1/2 = 50.0. A: 70 &times; min(1, 4/6) + 30 &times; 2/3 = 46.7 + 20.0 = 66.7. "
                      "Score = 0.5&times;100 + 0.3&times;50 + 0.2&times;66.7 = 50.0 + 15.0 + 13.3 = <b>78.3</b>.",
        "Meera Nair": "S: Python intermediate = intermediate (0.6), SQL not listed (0), ML expert &gt; beginner (1.0) = 1.6/3 = 53.3. C: shares both pathways = 2/2 = 100.0. A: 70 &times; min(1, 6/6) + 30 &times; 2/2 = 100.0. "
                      "Score = 26.7 + 30.0 + 20.0 = <b>76.7</b>.",
        "Karthik Rao": "S: Python advanced &gt; intermediate (1.0), SQL beginner = beginner (0.6), ML not listed (0) = 1.6/3 = 53.3. C: shares Higher Studies = 1/2 = 50.0. A: 70 &times; 2/6 + 30 &times; 1/3 = 23.3 + 10.0 = 33.3. "
                        "Score = 26.7 + 15.0 + 6.7 = <b>48.3</b>."}
    rrows = []
    for i, r in enumerate(res, 1):
        rrows.append([str(i), f"<b>{r['name']}</b>", f"{r['S']}", f"{r['C']}", f"{r['A']}", f"<b>{r['score']}</b>", calc[r["name"]]])
    s.append(tab_caption("Ranking for Asha with the calculation (values are produced by the reference code in Appendix C)"))
    s.append(table(["#", "Mentor", "S", "C", "A", "Score", "Calculation"], rrows, [16, 62, 28, 28, 28, 36, 284], style="tds"))
    s.append(Spacer(1, 4))
    s.append(P("Rohan ranks first because he covers all three focus skills at a higher level, even though Meera is a better match on interests and availability. Note how close the top two are (1.6 points): "
               "this is why the weights need validation and why the explanation below the score matters more than the number."))
    # missing-data and tie-break demonstration
    s2 = M.Student(skills=M.ASHA.skills, focus=M.ASHA.focus, interests=set())
    r2 = M.score(s2, M.MENTORS[0])
    s.append(callout(f"<b>Missing-data check.</b> If Asha had listed no interests, Rohan's score would be (0.5 &times; 100 + 0.2 &times; 66.7) / 0.7 = <b>{r2['score']}</b> instead of 78.3 (C is left out and weights renormalised).", "info"))

    s.append(H2("explain"))
    s.append(P("Each recommendation shows the breakdown and up to three plain-language reasons built from the score parts. No reason is invented: each template is filled only from values that were used in the calculation."))
    s.append(table(["Part", "Reason template", "Example (Rohan Iyer)"], [
        ["S", "Covers {n} of your {m} focus skills [at a higher level]", "Covers 3 of your 3 focus skills at a higher level"],
        ["C", "Advises on {x} of your {y} career interests (named when one)", "Advises on Data Science"],
        ["A", "{k} mentee spots free, {n} open slots in the next 14 days", "2 mentee spots free, 4 open slots in the next 14 days"]], [40, 230, 212]))
    s.append(Spacer(1, 3))
    s.append(P("The cards on pages 6 and 7 show the match score and the first reason; the endpoint (E23) returns all reasons and the three part scores, which the UI shows in an expandable detail on the card (a detail not drawn in the wireframes). Mentors with a score below a floor (proposed: 20) are not shown in <i>Recommended</i> but remain reachable through search."))

    s.append(H2("impl"))
    s.extend(bullets([
        "<b>Pure functions.</b> The scoring code takes plain objects and returns numbers, with no database access (the reference implementation in " + R("appC") + " is exactly this). It is therefore unit-testable without a database.",
        "<b>Query plan.</b> One SQL query selects eligible mentors using the indexes ix_mentor_discoverable and ix_slots_open, joined with grouped counts of active mentees and open slots; a second query loads all expertise and interest rows for those mentors in one pass (no query per mentor).",
        "<b>Cost.</b> O(M &times; F) with M eligible mentors and F &le; 5 focus skills. For a few hundred mentors this is negligible; the target is a p95 response under 300 ms at 500 mentors (to be measured).",
        "<b>Caching.</b> Catalogues are cached; scores are not cached because availability changes quickly. A short per-student cache (60 s) is allowed for pagination consistency.",
        "<b>Configuration.</b> Weights and constants are read from configuration, so experiments need no deployment.",
    ]))
    s.append(table(["Step", "Service action"], [
        ["1", "Load the student's skills, focus flags and interests (by token user id)."],
        ["2", "Query eligible mentors with counts (hard filters in SQL)."], ["3", "Load expertise and interests for those mentors."],
        ["4", "Score each mentor with the pure function; drop scores below the floor."], ["5", "Sort with the tie-break key; slice the requested page; attach reasons."]], [40, 442]))

    s.append(H2("validate"))
    s.append(P("The weights are untested assumptions. The plan below turns them into evidence without inventing numbers in advance."))
    s.append(table(["Step", "Method", "Output"], [
        ["1 Instrument", "Log, for every recommendation list and every request, the three part scores, the rank shown and whether the student opened or requested the mentor (structured logs, retention limited).", "A dataset of shown rank versus action."],
        ["2 Expert review", "Ask 5 mentors and 5 students to rank 8 anonymised pairings by hand and compare with the algorithm's order (rank correlation).", "First reality check before launch."],
        ["3 Offline replay", "Replay logged student profiles against the scoring rule under alternative weights (for example 0.4/0.4/0.2 and 0.6/0.2/0.2); compare how often the mentor the student actually requested appears in the top 3.", "Sensitivity of ranking to weights."],
        ["4 Pilot", "Run the default weights with a small cohort; track request acceptance rate, time from request to first session, session completion and average feedback.", "Outcome metrics per weight setting."],
        ["5 Decide", "Change weights only if a different setting improves acceptance and feedback without concentrating requests on a few mentors; record the decision in the repository.", "A documented, reviewed change."]], [74, 300, 108]))
    # sensitivity computed
    sets = [("0.50 / 0.30 / 0.20 (proposed)", (0.5, 0.3, 0.2)), ("0.40 / 0.40 / 0.20", (0.4, 0.4, 0.2)), ("0.60 / 0.20 / 0.20", (0.6, 0.2, 0.2)), ("0.34 / 0.33 / 0.33 (equal)", (1 / 3, 1 / 3, 1 / 3))]
    rows = []
    for lab, (a, b, c) in sets:
        sc = sorted([(a * r["S"] + b * r["C"] + c * r["A"], r["name"]) for r in res], reverse=True)
        rows.append([lab] + [f"{n} ({v:.1f})" for v, n in sc])
    s.append(Spacer(1, 4))
    s.append(tab_caption("Sensitivity of the sample ranking to the weights (computed from the example above; sample data only)"))
    s.append(table(["Weights S / C / A", "1st", "2nd", "3rd"], rows, [130, 117, 117, 118], style="tds"))
    s.append(Spacer(1, 3))
    s.append(P("In this small example the order of the top two flips when interests are weighted at least as much as skills, which illustrates why the weights are a hypothesis, not a fact."))

    s.append(H2("limits"))
    s.extend(bullets([
        "<b>Self-reported, coarse data.</b> Levels are four steps chosen by users; the score cannot detect over- or under-claiming. Admin review of mentors partly mitigates this.",
        "<b>Cold start.</b> New mentors have no ratings; ratings are deliberately <i>not</i> in the score so new mentors are not buried. A rating signal may be added after validation.",
        "<b>Concentration.</b> Highly matched mentors may receive many requests. The capacity limit, the pending-request limit and the free-capacity term in A spread demand; exposure per mentor is a monitored metric.",
        "<b>Fairness.</b> No personal attribute (gender, location, caste, religion, ethnicity, college) is used. Only skills, interests and availability enter the score. Equal treatment is checked by reviewing exposure across mentor groups in analytics (with small-group suppression).",
        "<b>Catalogue dependence.</b> Results are only as good as the skill and interest vocabularies; retired entries keep history but stop influencing new matches.",
        "<b>Not a decision.</b> The student chooses; the score only orders the list. Search remains available for any approved, available mentor.",
    ]))
    return s


# =============================================================================================
def sec11():
    s = H1("structure")
    s.append(P("The repository is a single monorepo with a back end, a front end, documentation and CI, so that one pull request can change an API and its client together. " + tag("P")))
    s.append(H2("repo"))
    tree = """mentoring-platform/
|-- README.md                      how to run, test and deploy
|-- docker-compose.yml             local PostgreSQL 16 (and optional pgAdmin)
|-- .github/workflows/ci.yml       lint, tests, OpenAPI validation, build
|-- docs/
|   |-- design-report.pdf          this report
|   |-- api-spec.yaml              OpenAPI 3.0 contract (source of truth for the API)
|   |-- adr/                       architecture decision records (one file per decision)
|   `-- diagrams/                  .mmd / .dot / .drawio sources
|-- backend/
|   |-- pyproject.toml, requirements.txt
|   |-- app/
|   |   |-- __init__.py            create_app() factory
|   |   |-- config.py              settings from environment
|   |   |-- extensions.py          db, migrate, jwt, limiter, cors
|   |   |-- core/                  errors.py, security.py, pagination.py, rate_limit.py, ids.py
|   |   |-- models/                one module per table group (users, profiles, catalogue,
|   |   |                          requests, mentorships, availability, sessions,
|   |   |                          feedback, notifications, audit, tokens)
|   |   |-- schemas/               request/response validation per component
|   |   |-- services/              auth, profile, catalogue, discovery, matching, mentoring,
|   |   |                          session, feedback, notification, admin, audit, analytics
|   |   |-- api/v1/                Blueprints: auth, users, catalogues, profiles, mentors,
|   |   |                          requests, mentorships, sessions, notifications, admin
|   |   |-- jobs/                  expire_requests.py, reminders.py, purge.py
|   |   `-- cli.py                 seed-admin, seed-catalogues, run-jobs
|   |-- migrations/                Alembic revisions
|   `-- tests/
|       |-- unit/                  services and matching (no database)
|       |-- api/                   Flask test client + disposable PostgreSQL
|       `-- db/                    integrity and concurrency SQL tests
`-- frontend/
    |-- package.json, vite.config.js
    |-- src/
    |   |-- main.jsx, App.jsx
    |   |-- routes/                route table, guards (RequireAuth, RequireRole)
    |   |-- api/                   axios client, interceptors, one module per component
    |   |-- auth/                  AuthProvider (in-memory token, silent refresh)
    |   |-- components/            shared UI: AppShell, StatusBadge, DataTable, dialogs ...
    |   |-- pages/                 public/, student/, mentor/, admin/  (26 pages)
    |   |-- hooks/, utils/, styles/
    |   `-- tests/                 Vitest + React Testing Library
    `-- public/"""
    s.append(code_block(tree, size=6.3, chunk=14))
    s.append(Spacer(1, 4))
    s.append(tab_caption("Components mapped to code"))
    rows = []
    mapping = {"C01": ("services/auth_service.py, api/v1/auth.py", "pages/public (1-4), auth/"), "C02": ("services/profile_service.py, api/v1/profiles.py", "pages/student 5, 13; mentor 20"),
               "C03": ("services/catalogue_service.py, api/v1/catalogues.py", "forms; admin page 23"), "C04": ("services/discovery_service.py, api/v1/mentors.py", "student 7, 8"),
               "C05": ("services/matching_service.py", "student 6, 7"), "C06": ("services/mentoring_service.py, api/v1/requests.py", "student 9, 10; mentor 16, 17"),
               "C07": ("services/mentoring_service.py, api/v1/mentorships.py", "student 11; mentor 18"), "C08": ("services/session_service.py, api/v1/sessions.py", "student 12; mentor 19"),
               "C09": ("services/feedback_service.py", "FeedbackDialog"), "C10": ("services/notification_service.py, api/v1/notifications.py", "student 14; mentor 21"),
               "C11": ("services/admin_service.py, audit_service.py, api/v1/admin.py", "admin 23, 24, 25"), "C12": ("services/analytics_service.py, api/v1/admin.py", "dashboards 6, 15, 22; admin 26")}
    for c in CD.COMPS:
        b, f = mapping[c["id"]]
        rows.append([f"<b>{c['id']}</b>", c["name"], mono(b), f])
    s.append(table(["ID", "Component", "Backend modules (app/)", "Frontend"], rows, [28, 122, 200, 132], style="tds"))

    s.append(H2("backendlayers"))
    s.append(table(["Layer", "Responsibility", "May call", "Must not"], [
        ["api (Blueprints)", "Parse request, authenticate and authorise by role, call one service, serialise the response.", "schemas, services, core", "Contain business rules or SQL."],
        ["schemas", "Validate and normalise input; define output shapes (also feed OpenAPI).", "core", "Touch the database."],
        ["services", "Business rules and transactions; raise domain errors with stable codes.", "models, other services (per the dependency matrix), core", "Know about HTTP or Flask request objects."],
        ["models", "SQLAlchemy mapping and entity methods (state transitions, simple invariants).", "core", "Call services or commit."],
        ["core", "Errors, pagination, security helpers, rate limiting, id handling.", "(nothing above)", "Depend on any layer above."]], [80, 190, 120, 92]))
    s.append(Spacer(1, 3))
    s.append(P("<b>Error flow.</b> Services raise <font face='DVM'>DomainError(code)</font>; a single error handler maps the code to the HTTP status and the error envelope using the catalogue in " + R("api.errorcat") + ". "
               "Database exceptions (23505, 23P01, 23514) are caught in the service that knows their meaning and re-raised as domain errors."))

    s.append(H2("frontendlayout"))
    s.extend(bullets([
        "<b>One folder per role area</b> under pages/, one file per page, named after the page inventory (for example <font face='DVM'>MentorDetailPage.jsx</font> for page 8).",
        "<b>api/ modules mirror components</b> (requests.js, sessions.js ...) and are the only place that knows URLs; pages call them through small hooks.",
        "<b>Routes</b> are declared once in routes/, with <font face='DVM'>RequireAuth</font> and <font face='DVM'>RequireRole</font> wrappers; redirect-after-login keeps the wanted path.",
        "<b>Forms</b> use React Hook Form; the 422 detail list is mapped onto fields by one helper.",
        "<b>Shared components</b> (" + R("wireframes.shared") + ") live in components/ with their tests; pages contain layout and wiring only.",
    ]))

    s.append(H2("config"))
    s.append(tab_caption("Configuration keys (environment variables; defaults are the proposed values)"))
    s.append(table(["Key", "Default", "Meaning"], [
        ["DATABASE_URL", "(required)", "PostgreSQL connection string; TLS required outside local."],
        ["JWT_SECRET_KEY", "(required, 32+ bytes)", "Signing secret for access tokens; different per environment."],
        ["ACCESS_TOKEN_MINUTES / REFRESH_TOKEN_DAYS", "15 / 7", "Token lifetimes."],
        ["CORS_ORIGINS", "http://localhost:5173 (dev only)", "Allow-list; empty in production (same-origin proxy)."],
        ["RATE_LIMIT_STORAGE_URL", "memory:// (dev) / redis://...", "Shared counter store."],
        ["REQUEST_EXPIRY_DAYS / COOLDOWN_DAYS / FEEDBACK_WINDOW_DAYS", "14 / 30 / 14", "Rule parameters (R4, R6, R15)."],
        ["MAX_PENDING_REQUESTS", "3", "Rule R3."],
        ["MATCH_W_SKILLS / MATCH_W_INTERESTS / MATCH_W_AVAILABILITY", "0.50 / 0.30 / 0.20", "Matching weights; must sum to 1.0 (checked at start-up)."],
        ["EMAIL_ENABLED", "false", "Optional e-mail extension switch."]], [180, 110, 192], style="tds"))
    s.append(Spacer(1, 3))
    s.append(P("Environments: <b>local</b> (docker-compose PostgreSQL, Vite dev server proxying /api), <b>staging</b> (seeded with sample data) and <b>production</b>. Secrets are never committed; a sample <font face='DVM'>.env.example</font> lists keys without values."))

    s.append(H2("workflow"))
    s.extend(bullets([
        "<b>Branching:</b> trunk-based. <font face='DVM'>main</font> is protected and always deployable; work happens on short-lived branches named <font face='DVM'>feat/C06-request-accept</font>, <font face='DVM'>fix/...</font>, <font face='DVM'>docs/...</font>.",
        "<b>Commits</b> follow Conventional Commits (feat, fix, docs, test, refactor) and reference the story id (US-M07).",
        "<b>Pull requests</b> are small (aim under 400 changed lines), link a story, include tests, and need one approval from the Code Reviewer or a peer who did not write the code. The PR template carries a checklist (tests, OpenAPI updated, migration reviewed, accessibility checked).",
        "<b>CI stages:</b> (1) lint and format; (2) back-end unit tests; (3) PostgreSQL service container: migrations from scratch, database tests, API tests; (4) OpenAPI validation and contract tests; (5) front-end tests and build; (6) dependency audit. A failed stage blocks merge.",
        "<b>Release:</b> merge to main deploys staging automatically; production is promoted by a tagged release after the checklist in " + R("testing.gates") + ".",
    ]))
    return s


# =============================================================================================
TESTS = [
    # id, level, component, scenario, expected, status
    ("AU-01", "API", "C01", "Register with an e-mail that already exists (any letter case).", "409 EMAIL_ALREADY_REGISTERED; no second user row.", "Specified"),
    ("AU-02", "API", "C01", "Login with a wrong password and with an unknown e-mail.", "Both return 401 INVALID_CREDENTIALS with the same message and similar timing.", "Specified"),
    ("AU-03", "API", "C01", "Use the refresh cookie twice (second use after rotation).", "First 200 and rotated; second 401 REFRESH_REUSED and the whole family is revoked.", "Specified"),
    ("AU-04", "API", "C01", "Login as a suspended user; use an old refresh token after suspension.", "403 ACCOUNT_SUSPENDED in both cases.", "Specified"),
    ("AU-05", "Unit", "C01", "Password rules: length 9, length 10, common password.", "9 and common rejected with 422; 10 accepted; stored hash is Argon2id.", "Specified"),
    ("PR-01", "API", "C02", "Student profile without skills, then with required fields.", "profile_completed false then true; request endpoint answers PROFILE_INCOMPLETE then succeeds.", "Specified"),
    ("PR-02", "API", "C02", "Mark six skills as focus.", "422 VALIDATION_ERROR (at most 5).", "Specified"),
    ("PR-03", "API", "C02", "Lower max_active_mentees below current active mentees.", "422; value unchanged.", "Specified"),
    ("DI-01", "API", "C04", "Student searches with skill + experience filters; page 2 of size 5.", "Only approved, available mentors matching all filters; meta totals correct; stable order.", "Specified"),
    ("DI-02", "API", "C04", "Student requests an unapproved mentor's profile.", "404 NOT_FOUND (existence hidden).", "Specified"),
    ("MT-01", "Unit", "C05", "Worked example: rank Asha against six mentors.", "Order Rohan 78.3, Meera 76.7, Karthik 48.3; three mentors excluded.", "Executed (reference code self-test passes)"),
    ("MT-02", "Unit", "C05", "Student without interests.", "C is undefined; weights renormalised; score = (0.5 S + 0.2 A) / 0.7.", "Executed (reference code self-test passes)"),
    ("MT-03", "Unit", "C05", "Two mentors with identical scores.", "Order by S, C, slots, free places, then mentor id; repeatable across calls.", "Executed (reference code self-test passes)"),
    ("MT-04", "Unit", "C05", "Pagination of a three-item result at page 2, size 2.", "One item; total 3; total_pages 2.", "Executed (reference code self-test passes)"),
    ("RQ-01", "API", "C06", "Student sends a second pending request to the same mentor.", "409 DUPLICATE_PENDING_REQUEST.", "Specified"),
    ("RQ-02", "API", "C06", "Student already has three pending requests.", "409 PENDING_LIMIT_REACHED.", "Specified"),
    ("RQ-03", "API", "C06", "Re-request a mentor 10 days after a decline.", "409 REQUEST_COOLDOWN with retry_after of 20 days.", "Specified"),
    ("RQ-04", "API", "C06", "Mentor accepts when at capacity.", "409 MENTOR_AT_CAPACITY; request stays pending.", "Specified"),
    ("RQ-05", "API", "C06", "Two mentees' requests accepted simultaneously with one place free.", "Exactly one 200; one 409; one active mentorship.", "Executed at database level (concurrency script); API test specified"),
    ("RQ-06", "API", "C06", "Another mentor tries to accept or decline the request.", "403 FORBIDDEN (or 404 if the request is hidden).", "Specified"),
    ("RQ-07", "Job", "C06", "Request pending for 14 days.", "Scheduled job sets expired, notifies the student; re-request allowed.", "Specified"),
    ("ME-01", "API", "C07", "End a mentorship that has two future sessions.", "Mentorship ended; sessions cancelled; slots released; other party notified.", "Specified"),
    ("ME-02", "API", "C07", "Reopen or end an already ended mentorship.", "409 INVALID_STATE_TRANSITION.", "Specified"),
    ("SC-01", "API", "C08", "Add a slot overlapping an existing slot; add an adjacent slot.", "Overlap: 409 SLOT_OVERLAP; adjacent accepted.", "Executed at database level (DB-20, DB-21); API test specified"),
    ("SC-02", "API", "C08", "Two students book the same slot at the same time.", "One 201, one 409 SLOT_UNAVAILABLE.", "Executed at database level (DB-24); API test specified"),
    ("SC-03", "API", "C08", "Student books two mentors at overlapping hours.", "409 SESSION_CONFLICT.", "Executed at database level (DB-25); API test specified"),
    ("SC-04", "API", "C08", "Book a session in an ended mentorship.", "409 MENTORSHIP_NOT_ACTIVE.", "Specified"),
    ("SC-05", "API", "C08", "Mentor completes a session before its start time.", "409 INVALID_STATE_TRANSITION.", "Specified"),
    ("FB-01", "API", "C09", "Submit feedback for a scheduled session; for a completed one; after 15 days.", "409 FEEDBACK_NOT_ALLOWED; 201; 409 FEEDBACK_NOT_ALLOWED.", "Specified"),
    ("FB-02", "API", "C09", "Same participant submits twice.", "409 FEEDBACK_ALREADY_SUBMITTED.", "Executed at database level (DB-30); API test specified"),
    ("NT-01", "API", "C10", "User A reads or marks user B's notification.", "404 NOT_FOUND.", "Specified"),
    ("AD-01", "API", "C11", "Reject a mentor without a note.", "422 VALIDATION_ERROR; status unchanged.", "Specified"),
    ("AD-02", "API", "C11", "Admin suspends own account.", "403 FORBIDDEN.", "Specified"),
    ("AD-03", "API", "C11", "Approve then edit the organisation of an approved mentor.", "Edit saved, audit entry written, admin flag raised.", "Specified"),
    ("AN-01", "API", "C12", "Overview for a range with fewer than five users in a group.", "Group counts suppressed; export contains no free text.", "Specified"),
    ("SE-01", "Security", "all", "Student calls an admin endpoint; changes student_id in a request body.", "403; ignored (identity taken from token).", "Specified"),
    ("SE-02", "Security", "all", "Burst of 6 failed logins.", "429 with Retry-After on the sixth.", "Specified"),
    ("DB-xx", "Database", "all", "39 constraint, trigger and key tests (DB-01 to DB-39).", "All rejected or accepted as designed.", "Executed: 39 of 39 passed on PostgreSQL 16"),
    ("FE-01", "Component", "UI", "RequireRole wrapper with a student visiting /admin.", "Shows page 4 (access denied); no admin request sent.", "Specified"),
    ("FE-02", "Component", "UI", "Registration form receives 422 details.", "Messages appear under the right fields; focus on the first.", "Specified"),
    ("FE-03", "Component", "UI", "Requests list returns empty / error / loading.", "Empty-state, error banner with retry, skeleton rows appear.", "Specified"),
    ("E2E-01", "End to end", "all", "Student registers, completes profile, requests; mentor approved earlier accepts; session booked and completed; feedback given.", "Whole flow succeeds; notifications created; analytics counts increase by one.", "Specified"),
]


def sec12():
    s = H1("testing")
    s.append(P("Testing follows the risks in this design: rules that can be broken by concurrency, rules that protect privacy, and flows that cross components. "
               "The strategy distinguishes tests that <b>have been executed</b> (database rules and the matching reference code) from tests that are <b>specified</b> and will run once the application exists."))
    s.append(H2("levels"))
    s.append(table(["Level", "Tool", "What it checks", "Run when", "Lead"], [
        ["Unit (back end)", "pytest", "Services and matching without a database; state transitions; validation.", "Every commit", "Backend"],
        ["Database", "pytest + psql scripts on PostgreSQL 16", "Constraints, triggers, exclusion rules, concurrency.", "Every commit touching models or migrations", "Backend + QA"],
        ["API / integration", "pytest + Flask test client", "Endpoints end to end with a real database; role and ownership rules; error codes.", "Every pull request", "QA"],
        ["Contract", "OpenAPI validator + response schema checks", "Responses match api-spec.yaml.", "Every pull request", "Backend"],
        ["Component (front end)", "Vitest + React Testing Library", "Forms, guards, shared components and states.", "Every commit", "Frontend"],
        ["End to end", "Playwright", "Critical journeys (E2E-01) in a browser against staging data.", "Before release and nightly", "QA"],
        ["Security", "pytest, dependency audit, manual checklist", "Authorisation bypass, token reuse, rate limits, headers (OWASP ASVS level 1 items).", "Before release", "Reviewer + QA"],
        ["Performance", "Locust or k6", "Discovery, booking and accept under concurrent load.", "Before release", "QA"],
        ["Accessibility", "axe in component tests + manual keyboard and screen-reader pass", "WCAG 2.1 AA items for the 26 pages.", "Before release", "Frontend + QA"],
        ["Acceptance", "Scenarios with stakeholders", "Stories meet their acceptance criteria.", "End of each phase", "Product Manager"]], [74, 100, 160, 84, 64], style="tds"))

    s.append(H2("cases"))
    s.append(P("The table lists " + str(len(TESTS)) + " representative cases (the full suite will be larger). IDs are stable so that tickets, CI reports and this report can refer to them. "
               "The Status column is deliberately honest: <b>Executed</b> means it has been run and passed in this project; <b>Specified</b> means defined but not yet run."))
    rows = [[f"<b>{a}</b>", b, c, d, e, f] for a, b, c, d, e, f in TESTS]
    s.extend(to_land())
    s.append(tab_caption("Sample test cases"))
    s.append(table(["ID", "Level", "Comp.", "Scenario", "Expected result", "Status"], rows, [38, 52, 36, 255, 248, 110], style="tds", pad=2))
    s.extend(to_port())

    s.append(H2("dbev"))
    s.append(P("Database tests are the part of the strategy that has been run. They are in <font face='DVM'>db_integrity_tests.sql</font> and <font face='DVM'>db_concurrency_test.sh</font> (included in the source archive) and are summarised in " + R("database.dbtests") + "; the output is in " + R("appD") + ". "
               "The matching reference code in " + R("appC") + " includes assertions for the worked example, the missing-data rule, tie-breaking and pagination (cases MT-01 to MT-04), executed with the code as delivered."))
    s.append(H2("gates"))
    s.append(table(["Gate", "Rule (proposed)"], [
        ["Merge to main", "All CI stages green; at least one approval; no unresolved review comment; OpenAPI updated when an endpoint changes."],
        ["Coverage", "Services and matching: at least 85% line coverage and every business rule R1-R16 has a test; front-end shared components: at least 70%. Coverage is a floor, not a goal."],
        ["Release to production", "E2E-01 passes on staging; security checklist done; no open defect of severity 1 or 2; migrations rehearsed on a copy; rollback plan written."],
        ["Defect severity", "1 data loss or security hole; 2 a main flow blocked; 3 workaround exists; 4 cosmetic."],
        ["Performance", "p95 under 300 ms for discovery and under 500 ms for accept and book at 100 concurrent users (to be measured, adjust with evidence)."]], [110, 372]))

    s.append(H2("uat"))
    s.append(table(["Scenario", "Given / When / Then"], [
        ["Request and acceptance", "Given a complete student profile and an approved mentor with a free place, when the student sends a request and the mentor accepts, then a mentorship exists, both see it, and the student is notified."],
        ["Scheduling", "Given an active mentorship and an open slot, when the student books it, then the session appears for both with the same time in each person's zone and the slot is no longer offered."],
        ["Conflict handling", "Given a booked session, when another booking overlaps it for either party, then it is refused with a clear message and no data changes."],
        ["Mentor review", "Given a submitted mentor profile, when an administrator rejects it with a note, then the mentor sees the note and the profile is not discoverable."],
        ["Privacy", "Given two students, when one tries to open the other's request URL, then they see 'not found'."]], [110, 372]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Usability check.</b> Before the final phase, five students and three mentors complete a short task list (register, find a mentor, request, book, give feedback) on the staging site while thinking aloud. "
               "Task success, time and the points where they hesitate are recorded; fixes that block a task are made before release. No participant data beyond this is kept."))
    return s


# =============================================================================================
PHASES = [
    ("P1", "Foundations and discovery", "S",
     "Agree requirements and the discovery comparison with the official portal; repository, CI, local database, baseline migration, design tokens and the empty application shell.",
     "none (components set-up only)", "Page shell, login layout", ["Requirements baseline and discovery notes (D1)", "Repository with CI running a trivial test", "Baseline migration creating the 17 tables; database tests in CI", "Figma component kit from the wireframes"],
     "none", "A new developer can clone, run, test and see the empty app; discovery questions answered or logged."),
    ("P2", "Identity and profiles", "M",
     "Accounts, sign-in, token handling, profiles, catalogues and the notification core.", "C01, C02, C03, C10 (core)", "Pages 1-5, 13, 20, 4",
     ["Register, login, refresh, logout, reset flow", "Student and mentor profile editing", "Catalogue lists and seeds", "Role-guarded routes and the AppShell"], "P1",
     "A user can register, sign in, complete a profile and sign out; AU and PR test cases pass."),
    ("P3", "Discovery and matching", "M",
     "Mentor review by admin, discovery with filters and the recommendation score.", "C04, C05, C11 (review part)", "Pages 7, 8, 6 (partial), 24, 23 (partial)",
     ["Admin queue approves or rejects mentors", "Search and filters", "Matching service with reasons", "Discovery pages"], "P2 (C03 data, profiles)",
     "A student sees approved mentors and a ranked list with reasons; MT and DI cases pass."),
    ("P4", "Requests and mentorships", "L",
     "Requests with all rules, accept with capacity control, mentorships and their closing.", "C06, C07", "Pages 9, 10, 11, 16, 17, 18",
     ["Request submission, tracking, cancel, expiry job", "Accept and decline with transaction and locks", "Mentorship list, detail and end", "Notifications for each event"], "P3",
     "End-to-end request-to-mentorship flow works, including concurrent accepts; RQ and ME cases pass."),
    ("P5", "Scheduling and feedback", "L",
     "Availability, booking with conflict rules, session lifecycle, feedback, reminders and full notification pages.", "C08, C09, C10 (pages)", "Pages 12, 19, 14, 21",
     ["Slot editor and weekly helper", "Booking dialog and calendar", "Session complete/cancel; feedback dialog", "Reminder job"], "P4",
     "A mentorship can run sessions end to end; SC and FB cases pass; E2E-01 passes."),
    ("P6", "Administration and analytics", "M",
     "Remaining admin tools, dashboards, analytics, export and audit review.", "C11 (rest), C12", "Pages 6, 15 (dashboards), 22, 23, 25, 26",
     ["User management and mentorship oversight", "Analytics overview, trends and CSV export", "Audit log view", "Student and mentor dashboards"], "P4 for data; P5 for session metrics",
     "Administrators can answer the programme questions in the user stories; AD and AN cases pass."),
    ("P7", "Hardening, testing and release", "M",
     "Security review, performance, accessibility, usability check, documentation and deployment.", "all", "all",
     ["Security checklist and rate-limit tuning", "Load test and query tuning", "Accessibility pass on 26 pages", "Usability check, UAT, deployment runbook, final report update"], "P2-P6",
     "Release gate in " + "Section 12.4" + " passed; production deployment rehearsed; handover notes complete."),
]


def sec13():
    s = H1("roadmap")
    s.append(P("The roadmap is a sequence of seven phases with dependencies and completion criteria. <b>It contains no calendar dates or durations</b>: the team size, the course calendar and the outcome of discovery item D1 are not known, "
               "so only relative order and relative size (S small, M medium, L large) are given. Dates should be set after the planning session that follows approval of this report."))
    s.append(H2("phases"))
    s.append(tab_caption("Phases at a glance"))
    s.append(table(["Phase", "Name", "Size", "Components", "Pages", "Needs"], [[f"<b>{p[0]}</b>", p[1], p[2], p[4], p[5], p[7]] for p in PHASES], [34, 118, 28, 100, 112, 90], style="tds"))
    s.append(H2("detail"))
    for p in PHASES:
        s.append(CondPageBreak(150))
        s.append(H3(f"{p[0]}  {p[1]}"))
        s.append(kv_table([("Goal", p[3]), ("Components", p[4]), ("Pages", p[5]), ("Deliverables", "<br/>".join("&bull; " + d for d in p[6])), ("Depends on", p[7]),
                           ("Completion criteria", p[8])], [92, 390], pad=2.5))
    s.append(H2("critical"))
    s.append(P("The critical path is <b>P1 &rarr; P2 &rarr; P3 &rarr; P4 &rarr; P5 &rarr; P7</b>. P6 depends on data from P4 and P5 but its first parts (mentor review in P3, user management) can start early. "
               "Within a phase the front end and back end work in parallel because the OpenAPI contract is agreed first; the front end uses a mock server generated from it until the endpoints exist."))
    s.append(table(["Parallel work", "How it is made safe"], [
        ["Front end and back end in the same phase", "Contract first (api-spec.yaml); mock server; contract tests in CI."],
        ["QA preparing tests ahead of code", "Test cases are written from the rules table (R1-R16) and user stories during the previous phase."],
        ["Reviewer checking design drift", "Every pull request is compared with this report; deviations are recorded as ADRs and the report is updated at the end of P7."]], [170, 312]))
    s.append(H2("rrisks"))
    s.append(table(["Risk", "Effect", "Response"], [
        ["Official portal already covers a component (D1).", "Wasted build effort.", "Run discovery in P1; mark components to drop or integrate; keep interfaces clean."],
        ["Small team, unequal availability.", "Phases slip.", "Keep stories small; rotate reviews; cut optional extensions (e-mail, iCalendar) first."],
        ["Concurrency defects in accept and book.", "Wrong data or trust loss.", "Locks and constraints designed and tested from P1; API-level tests in P4 and P5."],
        ["Matching weights perform poorly.", "Poor suggestions.", "Search remains the primary path; weights configurable; validation plan in " + R("matching.validate") + "."],
        ["Accessibility and responsive work left to the end.", "Late rework.", "Shared components built accessible from P2; checks in CI; full pass in P7."],
        ["Scope creep (chat, video, placement features).", "Delay.", "Non-goals in " + R("exec.scope") + "; changes need a Product Manager decision recorded as an ADR."]], [150, 100, 232]))
    return s


# =============================================================================================
def sec14():
    s = H1("team")
    s.append(P("Five roles cover the project. Every role takes part in requirements analysis and design, because the quality of this report depends on each viewpoint, and every role has defined build-time ownership. "
               "One person may hold more than one role in a small team; what matters is that each responsibility has exactly one accountable owner."))
    s.append(H2("roles"))
    s.append(table(["Role", "Owns", "Main tasks"], [
        ["<b>Product Manager</b>", "Scope, priorities, user stories, acceptance criteria, discovery with the client and the official portal (D1), roadmap.",
         "Keep the backlog ordered by value; answer questions about rules; run acceptance (UAT); decide scope changes; keep the open-questions list (" + R("quality.open") + ") moving; maintain the report."],
        ["<b>Backend Developer</b>", "Database schema and migrations, REST API, services, matching, jobs; components C01-C12 on the server.",
         "Implement the contract; write unit and API tests; own performance and concurrency; keep OpenAPI and code in step."],
        ["<b>Frontend Developer</b>", "Wireframes to Figma, React application, shared component library, accessibility, API client.",
         "Build the 26 pages and 12 shared components; map errors to the UI patterns; write component tests."],
        ["<b>Code Reviewer</b>", "Code quality, architecture conformance, security review, consistency between code and this report.",
         "Review every pull request against the checklist; maintain ADRs; run the security checklist; guard layering and the dependency matrix."],
        ["<b>Tester / QA</b>", "Test strategy, test cases, API and end-to-end tests, test data, defect triage, release gate.",
         "Turn rules and stories into test cases before code exists; run exploratory and regression tests; verify fixes; report quality status."]], [90, 170, 222]))

    s.append(H2("shared"))
    s.append(P("The first activities are done together, because requirements and design decisions that only one role sees tend to be wrong in a way that only another role would notice."))
    s.append(table(["Activity", "Product Manager", "Backend", "Frontend", "Reviewer", "QA"], [
        ["Requirements analysis", "Elicits needs, writes stories, ranks them", "Checks feasibility and data needs", "Checks usability and flows", "Checks completeness and conflicts", "Checks testability, writes acceptance criteria"],
        ["Workflow and rules design", "Owns the intended behaviour", "Defines transactions, states, errors", "Defines how each state and error appears", "Challenges edge cases", "Derives cases from every rule"],
        ["Wireframes and navigation", "Validates against stories", "Confirms each element has data and an endpoint", "Draws and iterates", "Checks consistency with components", "Checks that states can be reached for testing"],
        ["Data model and API", "Confirms vocabulary and limits", "Authors schema and contract", "Reviews the contract for what pages need", "Reviews security and integrity", "Reviews error catalogue and examples"],
        ["Architecture and stack", "Accepts risks and costs", "Proposes services layering", "Proposes front-end structure", "Approves; records ADRs", "Confirms test tooling fits"]],
        [92, 76, 76, 76, 80, 82], style="tds"))
    s.append(H2("raci"))
    s.append(P("R = responsible (does the work), A = accountable (one per row; decides), C = consulted, I = informed."))
    rows = [
        ["Requirements and stories", "A/R", "C", "C", "C", "C"], ["Wireframes and UX", "A", "C", "R", "C", "C"], ["Database schema and migrations", "C", "A/R", "I", "C", "C"],
        ["API contract (OpenAPI)", "C", "A/R", "C", "C", "C"], ["Back-end implementation", "I", "A/R", "I", "C", "C"], ["Front-end implementation", "I", "C", "A/R", "C", "C"],
        ["Unit and component tests", "I", "R", "R", "C", "A"], ["API and end-to-end tests", "I", "C", "C", "C", "A/R"], ["Code review and standards", "I", "C", "C", "A/R", "C"],
        ["Security review", "I", "R", "C", "A/R", "C"], ["Acceptance testing (UAT)", "A/R", "C", "C", "I", "R"], ["Deployment and release", "C", "R", "R", "A", "C"],
        ["Report and documentation", "A", "R", "R", "R", "R"]]
    s.append(tab_caption("Responsibility matrix"))
    s.append(table(["Activity", "Product Manager", "Backend", "Frontend", "Reviewer", "QA"], rows, [140, 70, 62, 62, 66, 82], style="tds",
                   extra=[("ALIGN", (1, 0), (-1, -1), "CENTER")]))

    s.append(H2("handoffs"))
    s.append(table(["Handoff", "From to", "Definition of ready / done"], [
        ["Story to development", "Product Manager to developers", "Story has a user, goal, acceptance criteria, pages and endpoints from " + R("wireframes.stories") + "; open questions answered."],
        ["Contract to both sides", "Backend to Frontend and QA", "OpenAPI updated and validated; example responses present; error codes listed."],
        ["Design to build", "Frontend to Backend and QA", "Wireframe or Figma frame shows empty, loading and error states; element table agreed."],
        ["Code to review", "Developer to Reviewer", "Tests included and green; migration reviewed; story id in the title; screenshots for UI changes."],
        ["Build to test", "Developer to QA", "Deployed on staging; test data available; known limits listed."],
        ["Release", "QA to Product Manager", "Release gate (" + R("testing.gates") + ") passed; acceptance scenarios signed off."]], [110, 130, 242]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Definition of done</b> for any story: acceptance criteria met; code reviewed and merged; unit and API or component tests added and passing; OpenAPI and report text updated if behaviour changed; no new accessibility or security issue; demonstrated on staging."))

    s.append(H2("agreements"))
    s.extend(bullets([
        "<b>Cadence:</b> a short planning session at the start of each phase, a short check-in at least twice a week, and a demonstration at the end of each phase.",
        "<b>Review time:</b> a pull request gets a first review within one working day (proposed); authors do not merge their own work.",
        "<b>Decisions</b> that change behaviour are written as short ADRs in docs/adr and linked from the pull request; chat is not a record.",
        "<b>Communication:</b> one shared channel, questions asked with the story id, blockers raised the same day.",
        "<b>Quality ownership:</b> everyone writes tests for their own code; QA designs the wider strategy and does not become a gate that others wait behind.",
        "<b>Conflicts</b> about scope go to the Product Manager; about design to the Code Reviewer after hearing the two owners; both outcomes are recorded.",
    ]))
    return s


# =============================================================================================
def sec15():
    s = H1("quality")
    s.append(H2("assume"))
    s.append(P("Each assumption lists what changes if it turns out to be wrong."))
    A = [
        ("A1", "The mentoring platform is a stand-alone design that may be compared with, or integrated into, the official Mentor Mentee Portal; this project does not replace it.", "If the programme office wants only extensions to the official portal, components already covered there are dropped (D1)."),
        ("A2", "Sign-in uses accounts owned by this platform (e-mail and password).", "If institute single sign-on is required, C01 changes to delegate sign-in; roles and the rest stay."),
        ("A3", "The platform serves the BS Degree in Data Science and Applications; programme_stage uses Foundation, Diploma, BSc and BS (verified on the programme site).", "If the Electronic Systems programme is in scope, a programme column is added to student and mentor profiles and to filters."),
        ("A4", "Mentors are recent graduates and alumni who volunteer; no payments are involved.", "Paid mentoring would add invoices and tax handling, out of scope."),
        ("A5", "One role per account.", "A person who is both mentor and student needs a second account, or a later multi-role design."),
        ("A6", "Numerical limits (3 pending requests, 14-day expiry, 30-day cooldown, 14-day feedback window, 4-hour slots, capacity 1-10) are starting values.", "They are configuration and can change without code changes."),
        ("A7", "Scale is small: hundreds of students and tens to low hundreds of mentors.", "Indexes and the single-instance deployment suit this; larger scale needs load testing and a shared rate-limit store."),
        ("A8", "E-mail delivery is optional; in-app notifications are the primary channel.", "If e-mail is mandatory, C10's integration interface is implemented early."),
        ("A9", "Meetings happen on tools outside the platform; the platform stores a link, phone number or place.", "Built-in video would be a new component."),
        ("A10", "Free or low-cost managed hosting (Vercel, Render, managed PostgreSQL) is acceptable for the course.", "Production use needs paid tiers, backups and a data-protection review."),
        ("A11", "Retention periods in " + R("database.retention") + " are proposals.", "IITM data-governance rules take precedence."),
        ("A12", "Users have a modern browser and a stable connection.", "Offline use is not supported."),
    ]
    s.append(table(["#", "Assumption", "If it is wrong"], [[f"<b>{a}</b>", b, c] for a, b, c in A], [28, 250, 204]))

    s.append(H2("open"))
    s.append(P("Questions for the client, ordered by how much the answer changes the design."))
    Q = [("Q1", "Can we see the official Mentor Mentee Portal (demo or documentation)? Which of the twelve components does it already provide?", "Scope of the build (D1)."),
         ("Q2", "Is institute single sign-on available or required? Is there a user directory we may read?", "C01 design."),
         ("Q3", "Which programmes are in scope (Data Science and Applications only, or also Electronic Systems)?", "Profile model, filters."),
         ("Q4", "Who may become a mentor (alumni only, current senior students too) and how are claims verified?", "Review workflow and fields."),
         ("Q5", "Are the proposed limits (pending requests, expiry, cooldown, capacity) acceptable?", "Rules R3-R6, R15."),
         ("Q6", "Which data-protection and retention rules apply, and who is the data owner?", "Section 7.9, analytics suppression."),
         ("Q7", "Which reports does the programme office need, and who may see them?", "C12 scope."),
         ("Q8", "Is e-mail or messaging-app notification required?", "C10 integration."),
         ("Q9", "Should sessions support groups (one mentor, several mentees)?", "Data model change."),
         ("Q10", "Is a mobile app expected, or is a responsive website enough?", "Front-end approach."),
         ("Q11", "Is there an existing language or accessibility policy (for example Indian-language support)?", "Front-end and content."),
         ("Q12", "Who handles moderation and support queries after launch?", "Admin tooling and audit needs.")]
    s.append(table(["#", "Question", "Affects"], [[f"<b>{a}</b>", b, c] for a, b, c in Q], [28, 330, 124]))

    s.append(H2("glossary"))
    G = [("Access token", "Short-lived signed token (JWT) that proves who is calling the API."), ("ADR", "Architecture decision record: a short file explaining one design decision."),
         ("Alumnus / recent graduate", "A person who completed the programme; the two mentor types."), ("Association / composition / dependency", "UML relationships: a stored link / part cannot outlive whole / a service uses another (Section 6.4)."),
         ("Capacity", "Maximum number of active mentees a mentor accepts at once (max_active_mentees)."), ("Cooldown", "Period after a decline during which the same student cannot re-request that mentor."),
         ("Crow's foot", "Entity-relationship notation that shows cardinality with symbols at line ends."), ("Exclusion constraint", "PostgreSQL rule that forbids two rows whose ranges overlap, used for slots and sessions."),
         ("Focus skill", "One of up to five skills a student flags as most wanted; used by the matching score."), ("JWT", "JSON Web Token, a signed token format (RFC 7519)."),
         ("Match score", "0-100 number ordering mentors for a student: 0.50 S + 0.30 C + 0.20 A."), ("Mentorship", "The active relationship created when a request is accepted."),
         ("OpenAPI", "Standard format describing a REST API in a machine-readable file."), ("Partial unique index", "A unique index that only covers rows meeting a condition, e.g. pending requests."),
         ("RBAC", "Role-based access control: permissions are given to roles, not individuals."), ("Refresh token", "Long-lived opaque token, rotated at every use, used to obtain new access tokens."),
         ("Slot", "A bookable time window published by a mentor."), ("Stub (ER)", "A table drawn with only its key column to show a relationship across diagrams."),
         ("Token family", "All refresh tokens descended from one login; revoked together on reuse."), ("UUID", "128-bit universally unique identifier used for primary keys.")]
    s.append(table(["Term", "Meaning"], [[f"<b>{a}</b>", b] for a, b in G], [130, 352], style="tds"))

    s.append(H2("refs"))
    s.append(P("Sources [1]-[3] are the IITM pages checked on 16 October 2026. Technical references [4]-[11] are the standards and documentation the design relies on; no claim about IITM depends on them."))
    R_ = [("[1]", "IITM Mentor Mentee Portal (IITM BS Degree Programme), landing page.", "https://mentorship.study.iitm.ac.in/", "Accessed 16 Oct 2026"),
          ("[2]", "IIT Madras BS Degree in Data Science and Applications, programme site (levels, placements links).", "https://study.iitm.ac.in/ds/", "Accessed 16 Oct 2026"),
          ("[3]", "IIT Madras Study Placement Portal (placements and internships).", "https://placements.study.iitm.ac.in/", "Accessed 16 Oct 2026"),
          ("[4]", "PostgreSQL 16 documentation: constraints, including exclusion constraints.", "https://www.postgresql.org/docs/16/ddl-constraints.html", ""),
          ("[5]", "RFC 7519: JSON Web Token (JWT).", "https://www.rfc-editor.org/rfc/rfc7519", ""),
          ("[6]", "RFC 9110: HTTP Semantics (methods and status codes).", "https://www.rfc-editor.org/rfc/rfc9110", ""),
          ("[7]", "OpenAPI Specification 3.0.3.", "https://spec.openapis.org/oas/v3.0.3", ""),
          ("[8]", "OWASP Application Security Verification Standard.", "https://owasp.org/www-project-application-security-verification-standard/", ""),
          ("[9]", "W3C Web Content Accessibility Guidelines 2.1.", "https://www.w3.org/TR/WCAG21/", ""),
          ("[10]", "Flask and SQLAlchemy documentation.", "https://flask.palletsprojects.com/ and https://docs.sqlalchemy.org/", ""),
          ("[11]", "React and Vite documentation.", "https://react.dev/ and https://vite.dev/", "")]
    s.append(table(["Ref", "Title", "Address", "Note"], [[a, b, f"<font face='DVM' size='6.4'>{esc(c)}</font>", d] for a, b, c, d in R_], [28, 180, 200, 74], style="tds"))
    s.append(Spacer(1, 4))
    s.append(P("<b>What was and was not checked.</b> The three IITM pages were opened and read on the access date; only the facts in " + R("exec.verified") + " were taken from them. The database rules were executed on PostgreSQL 16. "
               "The OpenAPI file passes a validator. The matching code runs its own assertions. The wireframes, user interface behaviour, numerical limits, weights and retention periods are proposals that have not been tested with users. "
               "No application code beyond the matching reference exists yet."))

    s.append(H2("control"))
    s.append(table(["Item", "Value"], [
        ["Document", "Software design report - Student Mentoring and Career Support Platform (IITM BS, Software Engineering, PS 2)"],
        ["Version / date", f"{VERSION} / {DATE}"], ["Status", "Design baseline, ready for review by the client and course evaluators"],
        ["Companion files", "IITM_Mentoring_Platform_Source.zip: diagram sources (.mmd, .dot), generators (Python), SQL schema and tests, OpenAPI file, matching reference code and README"],
        ["Change history", "1.0 - first complete version of all fifteen sections and four appendices"],
        ["How to update", "Edit the sources, run the generators and the verification scripts (they cross-check tables, endpoints, pages and the schema), then rebuild the report."]], [110, 372]))
    return s
