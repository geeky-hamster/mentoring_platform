"""Sections 7-9."""
import re
from doc import *
import schema, api
from content_a import tag, D
from content_b import ep_label
from reportlab.platypus import Table, TableStyle

EP = api.EP
RES = "/home/claude/report_build/"


def mono(t):
    return f"<font face='DVM'>{esc(t)}</font>"


# =============================================================================================
def sec7():
    s = H1("database")
    s.append(P("The database is PostgreSQL 16. The brief supplied a baseline of 15 tables; this design keeps all 15, tightens them, and adds two tables the workflows need. "
               "Everything in this section (data dictionary, indexes, foreign keys, ER diagrams, class attributes, DDL in " + R("appB") + ") is generated from one machine-readable definition, "
               "and the rules were executed on a real PostgreSQL 16 server (" + R("database.dbtests") + ")."))
    s.append(H2("principles"))
    s.extend(bullets([
        "<b>UUID primary keys</b> (<font face='DVM'>gen_random_uuid()</font>) on every principal table; junction tables use composite primary keys of the two foreign keys.",
        "<b>Rules at the lowest layer that can hold them.</b> A rule that PostgreSQL can enforce (uniqueness, state consistency, overlap, capacity) is enforced there as well as in the service, so a bug or a second writer cannot corrupt data.",
        "<b>Closed vocabularies as CHECK constraints</b> on VARCHAR columns instead of native ENUM types, so adding a value is a simple migration.",
        "<b>All timestamps are TIMESTAMPTZ in UTC</b>; the front end converts to the user's zone. <font face='DVM'>updated_at</font> is maintained by trigger.",
        "<b>No hard deletes of people or history.</b> Accounts are deactivated or anonymised; catalogue entries are retired with <font face='DVM'>is_active</font>.",
        "<b>Naming:</b> plural snake_case tables, singular snake_case columns, <font face='DVM'>_id</font> for keys, <font face='DVM'>_at</font> for timestamps, <font face='DVM'>is_</font> for booleans.",
    ]))
    s.append(tab_caption("Tables: 15 baseline and 2 added"))
    rows = []
    for t in schema.T:
        rows.append([str(t["num"]), f"<b>{t['name']}</b>", "baseline" if t["group"] == "baseline" else "<b>added</b>", str(len(t["cols"])), t["purpose"]])
    s.append(table(["#", "Table", "Group", "Cols", "Purpose"], rows, [20, 100, 46, 28, 288], style="tds"))
    s.append(P("Tables 16 and 17 are new: <font face='DVM'>mentor_interests</font> (mentor-side career pathways, needed for the interest score in " + R("matching") + ") and "
               "<font face='DVM'>refresh_tokens</font> (server-side state for refresh rotation and revocation, " + R("api.authn") + ")."))

    s.append(H2("improvements"))
    s.append(P("Each change to the baseline is listed with its reason, so reviewers can accept or reject it individually."))
    s.append(tab_caption("Improvements over the baseline schema"))
    s.append(table(["ID", "Area", "Change", "Reason"], [[f"<b>{a}</b>", b, c, d] for a, b, c, d in schema.IMPROVEMENTS], [30, 70, 200, 182], style="tds"))

    s.append(H2("dictionary"))
    s.append(P("Columns marked PK are primary keys and FK foreign keys; UQ means unique. NULL = yes means the column may be empty. Defaults are the database defaults. "
               "Rules show CHECK expressions. Constraints that span columns follow each table."))
    for t in schema.T:
        blk = [H3(f"Table {t['num']}: {t['name']}" + ("  (added)" if t["group"] == "added" else ""), toc=False), P(t["purpose"], "small")]
        rows = []
        for c in t["cols"]:
            rules = "; ".join(x for x in [("UQ" if c["unique"] else ""), (esc(c["check"]) if c["check"] else "")] if x)
            rows.append([f"<b>{c['name']}</b>", c["type"], c["key"], "yes" if c["null"] else "no", esc(c["default"]), rules, c["purpose"]])
        blk.append(table(["Column", "Type", "Key", "Null", "Default", "Rules", "Purpose"], rows, [80, 60, 28, 26, 56, 100, 132], style="tds", pad=2))
        s.extend(blk)
        if t["constraints"]:
            s.append(Spacer(1, 2))
            s.append(table(["Constraint", "Definition", "Purpose"], [[f"<b>{a}</b>", esc(b), c] for a, b, c in t["constraints"]], [90, 232, 160], style="tds", pad=2, header_bg=TEAL))
        s.append(Spacer(1, 4))

    s.append(H2("indexes"))
    s.append(P("Primary keys and UNIQUE constraints create indexes implicitly. The indexes below are the additional ones, each tied to a query in the UI. Partial indexes (WHERE clause) keep them small and double as business rules."))
    rows = []
    for t in schema.T:
        for n, d, why in t["indexes"]:
            rows.append([f"<b>{t['name']}</b>", n, mono(d) if len(d) < 90 else f"<font face='DVM' size='5.6'>{esc(d)}</font>", why])
    s.append(tab_caption("Indexes"))
    s.append(table(["Table", "Index", "Definition", "Supports"], rows, [92, 96, 148, 146], style="tds", pad=2))

    s.append(H2("concurrency"))
    s.append(P("Two kinds of simultaneous action can break the rules: two accepts racing for the last place of a mentor, and two bookings racing for one slot or one hour. "
               "The design handles both with the same three layers."))
    s.append(table(["Layer", "Mechanism", "Protects"], [
        ["1. Service transaction", "<font face='DVM'>BEGIN</font>; lock the request row (<font face='DVM'>SELECT ... FOR UPDATE</font>), then the mentor profile row; re-check state and capacity; write; <font face='DVM'>COMMIT</font>. Locks are always taken in the same order (request, then mentor) so transactions cannot deadlock each other.", "Capacity (R7), state transitions"],
        ["2. Constraints", "Partial unique indexes (pending pair, active pair, booked slot) and exclusion constraints (slot overlap, mentor and student session overlap).", "Duplicates, overlap, double booking, even for a second writer"],
        ["3. Trigger", "Capacity guard on mentorship insert; mentorship requires an accepted request.", "Safety net if a code path forgets the lock"]],
        [90, 280, 112]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Mapping to errors.</b> A violated unique index (SQLSTATE 23505), exclusion (23P01) or check (23514) raised by the database is caught in the service and translated to the matching 409 code "
               "(for example 23P01 on the student exclusion constraint becomes SESSION_CONFLICT). The default isolation level READ COMMITTED is sufficient because correctness relies on row locks and constraints, not on snapshot reads."))
    s.append(P("<b>Accept request - the transaction as implemented in the test script:</b>", "small"))
    s.append(code_block("""BEGIN;
-- 1. lock the request (0 rows => 409 INVALID_STATE_TRANSITION)
SELECT 1 FROM mentoring_requests WHERE request_id = :rid AND status = 'pending' FOR UPDATE;
-- 2. lock the mentor row: serialises concurrent accepts for this mentor
SELECT 1 FROM mentor_profiles WHERE user_id = :mentor_id FOR UPDATE;
-- 3. capacity check (count >= max_active_mentees => 409 MENTOR_AT_CAPACITY)
SELECT count(*) FROM mentorships WHERE mentor_id = :mentor_id AND status = 'active';
-- 4. write
UPDATE mentoring_requests SET status = 'accepted', responded_at = now() WHERE request_id = :rid;
INSERT INTO mentorships (request_id, student_id, mentor_id)
  SELECT request_id, student_id, mentor_id FROM mentoring_requests WHERE request_id = :rid;
INSERT INTO notifications (user_id, title, message, notification_type,
                           related_entity_type, related_entity_id) VALUES (...);
COMMIT;""", size=6.2))
    s.append(Spacer(1, 4))
    s.append(callout("<b>Tested.</b> Two sessions accepted two different requests for a mentor with capacity 1 at the same moment (the first holding its lock for 1.5 s). "
                     "Result: one 'ACCEPTED: mentorship created', one 'REJECTED: mentor at capacity', and exactly one active mentorship afterwards. Output is in " + R("appD") + ".", "verified"))

    s.append(H2("fkpolicy"))
    rows = []
    for child, ccols, parent, pcols, od, card, opt, verb in schema.FKS:
        rows.append([f"<b>{child}</b>", ", ".join(ccols), f"{parent}({', '.join(pcols)})", od, card, "optional" if opt else "required", verb])
    s.append(tab_caption(f"All {len(schema.FKS)} single-column foreign keys (three composite keys follow)"))
    s.append(table(["Child table", "Column", "Parent", "ON DELETE", "Card.", "Link", "Reads as"], rows, [86, 74, 120, 44, 28, 40, 90], style="tds", pad=2))
    s.append(Spacer(1, 4))
    s.append(P("<b>Composite foreign keys</b> (they carry the business guarantees): <font face='DVM'>(user_id, user_role)</font> from each profile to users; "
               "<font face='DVM'>(request_id, student_id, mentor_id)</font> from mentorships to mentoring_requests; "
               "<font face='DVM'>(mentorship_id, student_id, mentor_id)</font> from sessions to mentorships. Because the party columns are part of the key, a mentorship or session cannot name a student or mentor that differs from its parent."))
    s.append(P("<b>Why some keys reference profile user_id.</b> Requests, mentorships, slots and sessions reference <font face='DVM'>student_profiles(user_id)</font> or <font face='DVM'>mentor_profiles(user_id)</font>, not the profile id. "
               "The value is the same users.user_id the API uses, and the reference proves the party really has the right profile (D-09)."))
    s.append(tab_caption("Delete policy"))
    s.append(table(["Relationship", "Rule", "Reason"], [list(r) for r in schema.CASCADE_POLICY], [180, 90, 212], style="tds"))

    s.append(H2("slots"))
    s.append(P("Availability is stored as <b>concrete slots</b>: each row is one bookable window of at most four hours with a start and end time. A recurrence table was rejected because it makes every overlap, booking and exception query harder."))
    s.extend(bullets([
        "<b>Weekly helper.</b> The mentor chooses weekdays, a start and end time, and a number of weeks (up to 12). The API (E18) expands this into individual slots (up to 100 per call) inside one transaction; if any slot overlaps an existing one, the whole call fails with SLOT_OVERLAP and nothing is saved.",
        "<b>Time zones.</b> The mentor's zone is taken from the browser (IANA name) and the expansion is done in that zone, so a 18:00 slot stays at 18:00 local time across daylight-saving changes; storage is UTC.",
        "<b>Editing.</b> Only unbooked slots can be changed or deleted. Blocking a slot sets <font face='DVM'>is_available = false</font> without deleting it.",
        "<b>Booking.</b> Booking a slot creates a session that references it; the partial unique index allows one scheduled session per slot. Cancelling the session frees the slot automatically because the index only looks at scheduled sessions.",
        "<b>Ad-hoc sessions.</b> A mentor may schedule explicit times without a slot (slot_id empty); the same exclusion constraints still apply.",
    ]))
    s.append(table(["Input to E18", "Expansion result (sample)"], [
        ["weekdays = [Mon, Wed], 18:00-19:00, weeks = 2, zone Asia/Kolkata", "4 slots: Mon 2026-11-02, Wed 2026-11-04, Mon 2026-11-09, Wed 2026-11-11, each 12:30-13:30 UTC"],
        ["Same input where Wed 2026-11-04 already has a slot 18:30-19:30", "Whole call refused: 409 SLOT_OVERLAP naming the conflicting date; no slots created"]], [200, 282]))

    s.append(H2("dbtests"))
    res = open(RES + "db_test_results.txt").read().strip().splitlines()
    n_pass = sum(1 for r in res if r.startswith("PASS"))
    s.append(P(f"The schema was created on a throwaway PostgreSQL 16 cluster and {len(res)} integrity tests were executed (file db_integrity_tests.sql). "
               f"Each test attempts one action and states whether PostgreSQL must accept or reject it, with the SQLSTATE. <b>{n_pass} of {len(res)} passed.</b> A separate two-session script tested concurrent accepts. "
               "The full listing is in " + R("appD") + "."))
    cats = [("Users and profiles", "DB-01 to DB-07", "Case-insensitive unique e-mail, role validation, role-correct profiles, one profile per user, incomplete mentor approval"),
            ("Requests and mentorships", "DB-08 to DB-18", "Duplicate pending requests, wrong-role parties, goal length, response consistency, mentorship only from accepted requests, one per request, capacity, ended state"),
            ("Slots and sessions", "DB-19 to DB-28", "Slot overlap and adjacency, time order, double booking, mentor and student conflicts, party consistency, cancellation frees time"),
            ("Feedback, notifications, tokens, junctions", "DB-29 to DB-39", "One feedback per participant, rating range, read-flag consistency, notification types, hashed tokens, composite keys, RESTRICT on referenced skills")]
    s.append(tab_caption("What the tests cover"))
    s.append(table(["Area", "Tests", "Rules proved"], [[a, b, c] for a, b, c in cats], [120, 80, 282]))
    s.append(Spacer(1, 3))
    s.append(callout("<b>Scope of this evidence.</b> These tests prove the <i>database</i> rules on PostgreSQL 16. They do not test the API, the front end or the matching code; those tests are specified in " + R("testing") + " and have not been run, because the application is not yet implemented.", "warn"))

    s.append(H2("retention"))
    s.append(tab_caption("Retention and erasure (proposed values; confirm with IITM data-governance rules)"))
    s.append(table(["Data", "Rule", "Reason"], [list(r) for r in schema.RETENTION], [100, 240, 142], style="tds"))
    s.append(Spacer(1, 4))
    s.extend(bullets([
        "<b>Data minimisation.</b> The platform stores only what the workflows need: no government identifiers, no date of birth, no photographs, no free-text comments in exports.",
        "<b>Access.</b> Students never see other students; mentors see a student's profile summary only while a request or mentorship connects them; administrators' reads of personal data are limited to the admin screens and are logged for sensitive actions.",
        "<b>Backups</b> follow the managed provider's schedule; an erasure request is applied to the live database immediately and to backups when they expire " + tag("A") + ".",
    ]))

    s.append(H2("migrations"))
    s.extend(bullets([
        "<b>Alembic migrations</b> via Flask-Migrate: one revision per change, reviewed in pull requests; CI builds an empty database from migrations and compares it with the models to catch drift.",
        "<b>Required extension:</b> <font face='DVM'>btree_gist</font> (for exclusion constraints on UUID plus range). <font face='DVM'>gen_random_uuid()</font> is built in from PostgreSQL 13.",
        "<b>Seed data:</b> a CLI command creates the first administrator and loads starting catalogues (about 40 skills grouped into Programming, Data and AI, Systems, Web, Professional; about 8 career pathways such as Industry, Research, Higher Studies, Entrepreneurship). Lists are proposals for the programme office to edit.",
        "<b>Sample data for staging</b> is generated by a script and uses obviously fictional names and example.org addresses.",
        "<b>Rollback:</b> every migration has a downgrade; destructive changes (dropping a column) are split over two releases.",
    ]))
    return s


# =============================================================================================
def legend_fig():
    def fn(c, w, h):
        c.saveState()
        c.setStrokeColor(colors.HexColor("#33415C"))
        c.setFillColor(colors.HexColor("#33415C"))
        c.setLineWidth(0.9)
        items = [("Exactly one", "one"), ("Zero or one", "zeroone"), ("One or many", "onemany"), ("Zero or many", "zeromany")]
        colw = w / 4
        for i, (lab, kind) in enumerate(items):
            x0 = i * colw + 6
            y = h - 16
            x1 = x0 + 70
            c.line(x0, y, x1, y)
            # symbol at the right end (x1)
            if kind in ("one", "onemany", "zeroone"):
                pass
            if kind == "one":
                c.line(x1 - 8, y - 4, x1 - 8, y + 4)
                c.line(x1 - 12, y - 4, x1 - 12, y + 4)
            elif kind == "zeroone":
                c.line(x1 - 8, y - 4, x1 - 8, y + 4)
                c.setFillColor(colors.white)
                c.circle(x1 - 15, y, 3, stroke=1, fill=1)
                c.setFillColor(colors.HexColor("#33415C"))
            elif kind == "onemany":
                c.line(x1 - 10, y, x1, y + 4)
                c.line(x1 - 10, y, x1, y - 4)
                c.line(x1 - 10, y, x1, y)
                c.line(x1 - 13, y - 4, x1 - 13, y + 4)
            else:
                c.line(x1 - 10, y, x1, y + 4)
                c.line(x1 - 10, y, x1, y - 4)
                c.setFillColor(colors.white)
                c.circle(x1 - 16, y, 3, stroke=1, fill=1)
                c.setFillColor(colors.HexColor("#33415C"))
            c.setFont("DVC", 7)
            c.setFillColor(INK)
            c.drawString(x0, y - 15, lab)
        c.restoreState()
    return Fig(CW, 34, fn)


def sec8():
    s = H1("er")
    s.append(P("The entity-relationship model has 17 tables. A single diagram would need more than 19 inches of width to stay legible, so it is <b>split into three diagrams along natural boundaries</b>; "
               "each table is drawn in one diagram with its keys and main columns ('+ n more columns' stands for the rest, listed in " + R("database.dictionary") + "), and appears as a reference stub (key column only) in a neighbouring diagram where a relationship crosses the boundary. "
               "Tables added to the baseline are tinted amber. The column lists come from the same definition as the data dictionary."))
    s.append(H2("legend"))
    s.append(vfig(legend_fig(), "Crow's foot notation: the symbol next to a table gives how many rows of that table take part in the relationship."))
    s.append(P("Read a line from one table to the other: the symbol at each end says how many rows of <i>that</i> table relate to one row of the table at the other end. "
               "Bold column names are primary keys, <i>PK</i>/<i>FK</i> mark key roles, and a dashed table header marks a reference stub that is defined in another diagram."))
    s.extend(to_land())
    s.append(H2("accounts"))
    s.append(vfig(image(D + "er_accounts.png", LCW, 430), "ER diagram 1 of 3: accounts and operations (users, profiles, notifications, refresh tokens, audit log)."))
    s.append(NP())
    s.append(H2("catalogue"))
    s.append(vfig(image(D + "er_catalogue.png", LCW, 190), "ER diagram 2 of 3: skills, career interests and the four junction tables (stubs show the profile ids they reference)."))
    s.append(P("The four junction tables use composite primary keys and CASCADE from the profile side; the catalogue side is RESTRICT, so a skill or pathway still in use can only be retired, never deleted. "
               "Level attributes live on the junction rows (proficiency_level, expertise_level) and the focus flag on student_skills."))
    s.extend(to_port())
    s.append(H2("lifecycleer"))
    s.append(vfig(image(D + "er_lifecycle.png", CW, 640), "ER diagram 3 of 3: the mentoring lifecycle (requests, mentorships, slots, sessions, feedback). Stubs show the user_id key the tables reference."))
    s.append(H2("cards"))
    s.append(tab_caption("Relationships in words"))
    rows = []
    for child, ccols, parent, pcols, od, card, opt, verb in schema.FKS:
        if not verb:
            continue
        one = {"1:1": "exactly one" if not opt else "at most one", "1:N": "zero or more"}[card]
        rows.append([parent, f"{child}", one, verb + (" (optional link)" if opt else "")])
    s.append(table(["Parent", "Child", "Each parent has", "Relationship"], rows, [110, 110, 90, 172], style="tds", pad=2))
    s.append(P("Junction tables relate skills and pathways many-to-many: a student or mentor profile lists any number of skills and pathways, and each skill or pathway is listed by any number of profiles."))
    return s


# =============================================================================================
def spec_to_text(spec):
    req = spec.endswith("!")
    sp = spec.rstrip("!")
    return sp + ("*" if req else "")


def body_text(e):
    parts = [f"{k}: {spec_to_text(v)}" for k, v in e["body"].items()]
    return "; ".join(parts) if parts else "-"


def sec9():
    s = H1("api")
    s.append(P(f"The REST API lives under <font face='DVM'>{api.BASE}</font>. It has {len(EP)} endpoints in nine groups and {len(api.ERRORS)} error codes. "
               "This section states the conventions and security model, then lists every endpoint; the machine-readable contract is the OpenAPI file reproduced in " + R("appA") + "."))
    s.append(H2("conventions"))
    s.append(table(["Topic", "Convention"], [
        ["Versioning", f"Version in the path ({api.BASE}). A breaking change creates /api/v2; /v1 keeps working for a notice period. Adding optional fields or endpoints is not breaking."],
        ["Format", "JSON in and out (UTF-8, Content-Type: application/json). Property names snake_case. Identifiers are UUIDs. Timestamps are ISO 8601 in UTC (2026-11-02T12:30:00Z)."],
        ["Success envelope", "<font face='DVM'>{ \"data\": ... }</font>; lists add <font face='DVM'>\"meta\": { page, page_size, total, total_pages }</font>. 204 responses have no body."],
        ["Error envelope", "<font face='DVM'>{ \"error\": { \"code\", \"message\", \"details\": [ { \"field\", \"issue\" } ], \"request_id\" } }</font>. The code is stable and machine-readable; the message is for humans and may change."],
        ["Pagination", "<font face='DVM'>page</font> (default 1) and <font face='DVM'>page_size</font> (default 10, maximum 50) on every list. Out-of-range page returns an empty list, not an error. Sorting uses <font face='DVM'>sort</font> with documented values; default order is deterministic (newest first, id as tie-break)."],
        ["Filtering", "Query parameters named after the field (<font face='DVM'>status</font>, <font face='DVM'>skill_id</font>); repeatable parameters mean 'any of'. Unknown parameters are rejected with 400 so typos are noticed."],
        ["Validation", "Every body is validated before business logic runs: type, length, enum, required fields; strings are trimmed; unknown fields rejected. Failure returns 422 VALIDATION_ERROR with one detail per field. Rules that need data (duplicates, state, capacity) return 409 with a specific code."],
        ["Idempotency", "GET, PUT-like PATCH and DELETE are idempotent. POST actions (accept, cancel) are safe to repeat: a second call returns 409 INVALID_STATE_TRANSITION rather than repeating the effect."],
        ["Request id", "Every response carries <font face='DVM'>X-Request-Id</font>; errors repeat it in the body so a user can quote it to support."]], [80, 402]))
    s.append(Spacer(1, 4))
    s.append(tab_caption("HTTP status codes used"))
    s.append(table(["Status", "Use"], [
        ["200 OK / 201 Created / 202 Accepted / 204 No Content", "Success; created resource; accepted for asynchronous work (password reset); success with no body."],
        ["400 Bad Request", "Malformed JSON, bad query parameter, invalid signed token."],
        ["401 Unauthorized", "Missing, expired or invalid access token; wrong credentials; refresh problems."],
        ["403 Forbidden", "Authenticated but the role or ownership rule forbids the action; suspended account."],
        ["404 Not Found", "Missing resource, or one the caller may not know exists."],
        ["409 Conflict", "Valid request that clashes with current state or a business rule (duplicates, capacity, conflicts)."],
        ["422 Unprocessable Entity", "Field validation failed."],
        ["429 Too Many Requests", "Rate limit hit; Retry-After header tells when to retry."],
        ["500 / 503", "Unexpected error / dependency down. Body carries only the request id, never internal detail."]], [170, 312]))

    s.append(H2("authn"))
    s.append(tab_caption("Tokens"))
    s.append(table(["", "Access token", "Refresh token"], [
        ["Form", "Signed JWT (HS256, 256-bit secret from the environment; rotate by key id).", "Opaque random 256-bit value, not a JWT."],
        ["Claims / content", "sub = user_id, role, iat, exp, jti. No e-mail or personal data.", "Nothing readable; only its SHA-256 hash is stored (refresh_tokens.token_hash)."],
        ["Lifetime", "15 minutes", "7 days sliding; a token family ends at 30 days and the user signs in again " + tag("P")],
        ["Transport", "Authorization: Bearer header; kept in memory by the SPA.", "HttpOnly, Secure, SameSite=Strict cookie scoped to Path=/api/v1/auth."],
        ["Server state", "None (stateless); suspension takes effect at the next refresh, at most 15 minutes later, unless the deny-list shortcut is added.", "One row per issued token with family_id, revoked_at and reason."]],
        [80, 200, 202]))
    s.append(Spacer(1, 4))
    s.append(P("<b>Refresh rotation.</b> Each call to E03 marks the presented token revoked with reason <i>rotated</i> and issues a new token in the same family. "
               "If a token that is already revoked as rotated is presented again, someone has copied it: the whole family is revoked with reason <i>reuse_detected</i> and the call fails with 401 REFRESH_REUSED, forcing a fresh login. "
               "This is the sequence drawn in " + R("workflows.sequences") + "."))
    s.append(tab_caption("Events that revoke refresh tokens"))
    s.append(table(["Event", "Revoked", "Reason stored"], [
        ["Refresh (normal rotation)", "The presented token", "rotated"], ["Logout (E04)", "The whole family", "logout"],
        ["Reuse of a rotated token", "The whole family", "reuse_detected"], ["Password change or reset (E06, E09)", "All tokens of the user", "password_change"],
        ["Suspension or deactivation (E46)", "All tokens of the user", "admin_action"]], [180, 160, 142]))
    s.append(Spacer(1, 4))
    s.extend(bullets([
        "<b>CSRF.</b> The access token travels in a header, so normal calls are not exposed to CSRF. The two cookie-authenticated calls (refresh, logout) rely on SameSite=Strict, accept only JSON bodies and verify the Origin header against the allow-list.",
        "<b>Passwords.</b> Minimum 10 characters, maximum 128; checked against a short list of common passwords; stored as Argon2id. Login timing is equalised for unknown e-mails.",
        "<b>Account state.</b> Suspended or deactivated accounts are refused at login and at refresh (403 ACCOUNT_SUSPENDED).",
    ]))

    s.append(H2("rbac"))
    s.append(P("Authorisation has two steps on every request: the <b>role</b> check (is this kind of user allowed to call this operation?) and the <b>ownership</b> check (is this the user's own resource, or one they are connected to?). "
               "<b>Identifiers sent by the front end are never trusted for identity.</b> The caller is always the user in the token."))
    by_role = {r: [] for r in ["public", "any", "student", "mentor", "admin"]}
    for e in api.EPS:
        for r in e["roles"]:
            by_role[r].append(e["id"])
    s.append(tab_caption("Endpoints by caller role (any = every signed-in role)"))
    s.append(table(["Role", "Count", "Endpoints"], [[r.capitalize(), str(len(v)), ", ".join(v)] for r, v in by_role.items()], [60, 40, 382], style="tds"))
    s.append(Spacer(1, 4))
    s.append(tab_caption("Where identity and scope come from"))
    s.append(table(["Operation", "Rule", "Mistake prevented"], [
        ["Create request (E24)", "student_id is read from the token; the body carries only mentor_id and text.", "A student sending a request as someone else"],
        ["Own profile (E12-E15, E17-E20)", "Routes say /me; the server loads the profile of the token's user.", "Reading or editing another person's profile by changing an id"],
        ["Request, mentorship, session (E26, E31, E36...)", "Visible only to the two participants and administrators; otherwise 404.", "Enumerating other people's requests by guessing UUIDs"],
        ["Accept / decline (E27, E28)", "The request's mentor_id must equal the token's user; state must be pending.", "A mentor acting on someone else's request"],
        ["Feedback (E38)", "The caller must be a participant of the session; the session must be completed.", "Rating a session one did not attend"],
        ["Mentor availability (E21)", "Visible to the mentor, administrators and students in an active mentorship with that mentor.", "Scraping every mentor's calendar"],
        ["Student profile summary (E26, E31)", "Shown to a mentor only when a request or mentorship connects them.", "Mentors browsing the student population"],
        ["Admin routes (E45-E58)", "Role claim must be admin; the claim comes from the signed token, not from the request.", "Privilege escalation by editing the body"]],
        [140, 214, 128], style="tds"))
    s.append(Spacer(1, 4))
    s.append(P("Resources the caller may not know about return <b>404</b> instead of 403, so UUID guessing reveals nothing. UUIDs are not secrets and are never the only protection."))

    s.append(H2("security"))
    s.append(tab_caption("CORS"))
    s.append(table(["Setting", "Value"], [
        ["Production", "Same-origin: the front-end host proxies /api to the API (rewrite rule), so the browser makes no cross-origin call and no CORS headers are needed."],
        ["Local development", "Allow only http://localhost:5173 with credentials; methods GET, POST, PATCH, DELETE, OPTIONS; headers Authorization, Content-Type; max-age 600 s."],
        ["Never", "Access-Control-Allow-Origin: * together with credentials; reflecting the Origin header without an allow-list check."]], [110, 372]))
    s.append(Spacer(1, 4))
    s.append(tab_caption("Rate limits (proposed values, configurable)"))
    s.append(table(["Scope", "Limit", "Notes"], [
        ["Login (E02)", "5 attempts per 15 min per account and 20 per 15 min per IP", "Counted on failure; response is 429 with Retry-After."],
        ["Register (E01)", "5 per hour per IP", "Prevents bulk account creation."],
        ["Forgot password (E05)", "3 per hour per e-mail and 10 per hour per IP", "Always 202 so e-mails are not revealed."],
        ["Mentoring request (E24)", "10 per day per student", "In addition to the pending limit (R3)."],
        ["CSV export (E53)", "5 per hour per admin", "Large reads."],
        ["All other authenticated calls", "120 per minute per user", "Generous for normal use; protects the API."]], [130, 200, 152]))
    s.append(Spacer(1, 3))
    s.append(P("Limits are counted in a store shared by all API instances (Redis in production; in-process memory only for a single instance or tests). Responses carry <font face='DVM'>Retry-After</font>."))
    s.extend(bullets([
        "<b>Transport:</b> HTTPS only; HSTS; cookies Secure. <b>Headers:</b> X-Content-Type-Options: nosniff, Referrer-Policy: same-origin, a restrictive Content-Security-Policy on the SPA host (no inline scripts).",
        "<b>Injection and XSS:</b> parameterised queries only (SQLAlchemy); React escapes output; free text is stored as plain text, never as HTML; meeting links must be https or tel and are shown as text with an external-link warning.",
        "<b>Logging:</b> structured logs with request id, user id and route; never passwords, tokens or full bodies. Sensitive admin actions go to the audit log.",
        "<b>Secrets</b> live in environment variables of the hosting platform, never in the repository; dependency scanning runs in CI.",
    ]))

    s.append(H2("catalogue"))
    s.append(P("Roles: public = no token, any = every signed-in role. In the request column, <b>*</b> marks a required field and <b>path:</b> lists path parameters. "
               "Error codes are described in " + R("api.errorcat") + "; 401 UNAUTHENTICATED applies to every protected endpoint and is omitted from the list."))
    s.extend(to_land())
    groups = []
    for e in api.EPS:
        if not groups or groups[-1][0] != e["group"]:
            groups.append((e["group"], []))
        groups[-1][1].append(e)
    for g, es in groups:
        rows = []
        for e in es:
            pp = re.findall(r":(\w+)", e["path"])
            req = []
            if pp:
                req.append("path: " + ", ".join(pp))
            if e["params"]:
                req.append("query: " + ", ".join(p[0] for p in e["params"]))
            if e["body"]:
                req.append("body: " + body_text(e))
            ok = e["ok"]
            errs = [x for x in e["errs"] if "UNAUTHENTICATED" not in x]
            rows.append([f"<b>{e['id']}</b>", f"<b>{e['method']}</b> <font face='DVM'>{e['path']}</font>", ", ".join(e["roles"]), esc(" | ".join(req)) if req else "-",
                         f"{ok[0]} {ok[1] or ''}".strip(), esc(", ".join(errs)) or "-", e["purpose"]])
        s.append(tab_caption(g))
        s.append(table(["ID", "Operation", "Roles", "Request", "OK", "Errors", "Purpose"], rows, [26, 138, 40, 126, 44, 112, 253], style="tds", pad=2))
        s.append(Spacer(1, 6))
    s.extend(to_port())

    s.append(H2("errorcat"))
    s.append(tab_caption("Error catalogue"))
    s.append(table(["Code", "HTTP", "Meaning"], [[f"<b>{k}</b>", str(v[0]), v[1]] for k, v in api.ERRORS.items()], [140, 36, 306], style="tds"))

    s.append(H2("examples"))
    s.append(P("Eight flows, each with the request and the response. Identifiers, names, dates and numbers are illustrative; the analytics example is labelled as sample data in the response itself. "
               "Protected calls carry <font face='DVM'>Authorization: Bearer &lt;access token&gt;</font>."))
    for i, (title, eid, line, body, status, resp) in enumerate(api.examples(), 1):
        s += [CondPageBreak(190), H3(f"{i}. {title} ({eid})"),
              KeepTogether([P("<b>Request</b>", "small"), code_block(line + ("\n" + body if body and not body.startswith("(") else ("\n# " + body if body else "")), size=6.2)]),
              Spacer(1, 3), KeepTogether([P(f"<b>Response</b> {esc(status)}", "small"), code_block(resp, size=6.2)]), Spacer(1, 4)]

    s.append(H2("errex"))
    for title, line, body in api.EXAMPLE_ERRORS:
        s += [CondPageBreak(120), H3(title), code_block(line + "\n" + body, size=6.2), Spacer(1, 4)]

    s.append(H2("openapi"))
    s.append(P("The contract is delivered as <font face='DVM'>api-spec.yaml</font> (OpenAPI 3.0.3) in the source archive and reproduced in compact form in " + R("appA") + ". "
               "It describes 58 operations on 50 paths with 47 reusable schemas, shared error responses and the bearer security scheme, and it passes <font face='DVM'>openapi-spec-validator</font>."))
    s.extend(bullets([
        "<b>Postman:</b> import api-spec.yaml (File, Import); create an environment with <font face='DVM'>baseUrl</font> and <font face='DVM'>accessToken</font>; a test script on the login request stores the token in the environment. The generated collection becomes the basis of the Newman smoke run in CI.",
        "<b>Contract testing:</b> API tests validate real responses against the schemas in this file, so the document and the code cannot drift apart silently.",
        "<b>Front end:</b> typed clients can be generated from the same file to avoid hand-written fetch code.",
    ]))
    return s
