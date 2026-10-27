"""Sections 1-3."""
from doc import *
import schema, api, pages, matching
import flows
from reportlab.platypus import Table, TableStyle

D = "/home/claude/report_build/diagrams/"
EPS = api.EPS


def tag(kind):
    return {"V": '<font name="DV-B" color="#2F7D4F">[VERIFIED]</font>', "P": '<font name="DV-B" color="#1F3A5F">[PROPOSED]</font>',
            "A": '<font name="DV-B" color="#B7791F">[ASSUMPTION]</font>'}[kind]


def wf_rows(role):
    out = []
    for k, (r, text, eps) in pages.WF.items():
        if r == role:
            out.append([f"<b>{k}</b>", text, ", ".join(eps) if eps else "-"])
    return out


def wf_table(role):
    return table(["Step", "What happens", "Endpoints"], wf_rows(role), [34, 360, 88], style="td")


# =============================================================================================
def sec1():
    s = H1("exec")
    ntab = len(schema.T)
    ncol = sum(len(t["cols"]) for t in schema.T)
    s.append(callout("<b>Summary.</b> This report specifies a web platform on which IIT Madras BS students find, request and work with mentors "
                     "(recent graduates and alumni), and on which programme administrators approve mentors and observe whether mentoring is working. "
                     "It covers workflows, a technology stack, 26 wireframed pages, 12 software components, a UML class model, a PostgreSQL schema "
                     f"({ntab} tables), a REST API ({len(EPS)} endpoints), an explainable matching algorithm, a project structure, a test strategy, "
                     "a seven-phase roadmap and team responsibilities. <b>IIT Madras already runs an official Mentor Mentee Portal; this design does not claim to replace it.</b> "
                     "It is offered as a specified, testable design that can be compared with, partly adopted by, or integrated with that portal.", "info"))
    s.append(Spacer(1, 6))

    s.append(H2("purpose"))
    s.append(P("The report is the design baseline for project PS 2 of the Software Engineering course in the IIT Madras BS Degree Programme. "
               "It is written so that a team can start implementation from it: every page, endpoint, table and rule that appears in one section "
               "appears in the others under the same identifier, and the supporting artefacts (SQL, OpenAPI file, matching reference code, diagram sources) are delivered alongside."))
    s.append(P("<b>Audience.</b> Course evaluators and the client (who judge completeness and feasibility), the five project roles (who build from it), and any "
               "IITM programme staff who wish to compare the proposal with the official portal."))
    s.append(tab_caption("Where to find what"))
    s.append(table(["Need", "Go to"], [
        ["Why this exists, what is verified, what is not", f"{R('exec.context')} and {R('exec.verified')}"],
        ["How users move through the system, and the rules for duplicates, rejection, cancellation, conflicts", f"{R('workflows')}"],
        ["Why each technology was chosen", f"{R('stack')}"],
        ["Every screen, its elements, actions and endpoints", f"{R('wireframes')}"],
        ["The twelve components and their boundaries", f"{R('components')}"],
        ["Classes, tables and relationships", f"{R('uml')}, {R('database')} and {R('er')}"],
        ["The REST contract and security model", f"{R('api')} and {R('appA')}"],
        ["How mentors are ranked", f"{R('matching')}"],
        ["Folder structure, tests, roadmap and team", f"{R('structure')}, {R('testing')}, {R('roadmap')}, {R('team')}"],
        ["Assumptions, open questions, glossary, references", f"{R('quality')}"]], [250, 232], first_col_bold=False))

    s.append(H2("context"))
    s.append(P("IIT Madras operates an <b>IITM Mentor Mentee Portal</b>, presented on its own landing page as the official application built by the IITM BS team "
               "to help students and mentors manage their mentorship activities (source [1]). That fact shapes how this project must be positioned."))
    s.extend(bullets([
        "<b>No claim of replacement.</b> This report never states that the proposed platform replaces, supersedes or is better than the official portal. "
        "The official portal's internal features, data model and rules are not visible from public pages and have not been verified.",
        "<b>The portal is a discovery item.</b> Before implementation, the team should obtain a demonstration or documentation of the official portal and compare it with "
        "this design, feature by feature (the comparison questions are listed in " + R("quality.open") + ").",
        "<b>Three honest ways to use this design:</b> (a) as a self-contained reference implementation to evaluate design quality; (b) as a checklist of candidate requirements "
        "(matching, availability, feedback, analytics) to test against the official portal; (c) as the basis for an integration or extension if the programme office wants one.",
        "<b>What stays valid in every case:</b> the data model, the state machines, the business rules, the matching rules and the API contract are independent of whether the "
        "front end is this project's or IITM's.",
    ]))
    s.append(callout("<b>Discovery item D1.</b> Ask the programme office for read access to a demo of the official portal. Record, for each of the twelve components in "
                     + R("components") + ", whether the official portal already covers it. Any component already covered is a candidate to drop or to integrate instead of rebuild.", "warn"))

    s.append(H2("verified"))
    s.append(P("The facts below were checked against the public pages listed in " + R("quality.refs") + " on 16 October 2026. Pages change; the dated citation is part of the evidence."))
    s.append(tab_caption("Verified facts about the IITM context"))
    s.append(table(["#", "Fact (as stated on the page)", "Source", "Status"], [
        ["V1", "A site titled <b>IITM Mentor Mentee Portal</b> exists under the programme domain and describes itself as the official application, built by the IITM BS team, "
               "to help students and mentors manage their mentorship activities.", "[1]", tag("V")],
        ["V2", "That landing page publicly lists no features, matching rules or sign-in method. Everything about what the official portal does internally is therefore unverified.", "[1]", tag("V")],
        ["V3", "The programme site presents the BS Degree in Data Science and Applications as a 4-year Bachelor of Science with stages: Foundation, Diploma (programming or data science), "
               "BSc and BS, with exit options before the full BS.", "[2]", tag("V")],
        ["V4", "The programme site has a Placements section (overview, partnerships, a placement portal, career-choice documents). It does not describe a mentoring programme on that page.", "[2]", tag("V")],
        ["V5", "A separate Placement Portal exists for enrolled students and approved recruiters. Students register, take placement training and an assessment before applying; "
               "internships need at least one diploma and employment opportunities need a BSc. The page does not mention mentoring.", "[3]", tag("V")],
    ], [24, 330, 36, 92]))
    s.append(Spacer(1, 4))
    s.append(P("<b>How verified facts are used.</b> V3 justifies the four-value <font face='DVM'>programme_stage</font> enumeration (Foundation, Diploma, BSc, BS). "
               "V4 and V5 show that career support exists elsewhere in the ecosystem, so the proposed platform does not model placements or recruiters. "
               "V1 and V2 justify the discovery item above."))
    s.append(callout("<b>Not verified</b> (and therefore never stated as fact in this report): how mentors are chosen or matched in the official portal; whether it offers scheduling, feedback or analytics; "
                     "how users sign in (for example institute single sign-on); whether it exposes an API; how many students or mentors use it; whether the Electronic Systems degree programme is in scope for mentoring.", "warn"))

    s.append(H2("proposal"))
    s.append(P("The proposed platform is a role-based web application with three user groups. Everything here is " + tag("P") + "."))
    s.append(table(["Role", "Main goals", "Typical journey"], [
        ["<b>Student</b>", "Find a mentor whose experience fits a career goal; keep the relationship organised; give feedback.",
         "Register, complete profile, discover or get recommended mentors, send a request, schedule sessions, rate sessions, end the mentorship."],
        ["<b>Mentor</b> (recent graduate or alumnus)", "Offer guidance within personal capacity and time; see who needs help; keep records of sessions.",
         "Register, build profile, submit for review, publish availability, accept or decline requests, run sessions, give feedback."],
        ["<b>Administrator</b>", "Keep quality and safety; keep catalogues clean; know whether the programme works.",
         "Review mentor applications, suspend accounts if needed, watch stale requests, read analytics, maintain skills and pathways, read the audit trail."]],
        [96, 190, 196]))
    s.append(Spacer(1, 5))
    ntab = len(schema.T)
    ncol = sum(len(t["cols"]) for t in schema.T)
    s.append(tab_caption("The design in numbers (all counts are generated from the same source files that produce the tables and diagrams)"))
    s.append(table(["Item", "Count", "Where"], [
        ["Pages with wireframes", str(len(pages.PAGES)), R("wireframes")],
        ["User stories (with traceability)", str(len(pages.STORIES)), R("wireframes.stories")],
        ["Workflow steps", str(len(pages.WF)), R("workflows")],
        ["Software components", "12", R("components")],
        ["Database tables (15 baseline + 2 added)", f"{ntab} tables, {ncol} columns, {len(schema.FKS)} foreign keys", R("database")],
        ["REST endpoints under /api/v1", str(len(EPS)), R("api")],
        ["Error codes", str(len(api.ERRORS)), R("api.errorcat")],
        ["Database rule tests executed on PostgreSQL 16", "39 passed, plus a two-session concurrency test", R("database.dbtests")]],
        [230, 160, 92]))

    s.append(H2("scope"))
    s.append(table(["In scope (proposed)", "Out of scope (non-goals)"], [[
        Table([[b] for b in bullets([
            "Accounts for students, mentors and administrators with role-based access.",
            "Student and mentor profiles with skills and career interests.",
            "Mentor discovery with filters and rule-based recommendations.",
            "Requests, acceptance, mentorships, availability and session scheduling.",
            "Session feedback, in-app notifications, administration, analytics and audit trail.",
            "Documented REST API, database schema, test strategy and delivery plan."], "bul")], colWidths=[225]),
        Table([[b] for b in bullets([
            "Video conferencing or chat built into the platform (sessions store a meeting link or phone/in-person details).",
            "Machine-learning recommendation (the matching is deliberately rule-based and explainable).",
            "Placement, internship or recruiter workflows (a separate official Placement Portal exists, source [3]).",
            "Native mobile apps (the web UI is responsive).",
            "Replacing or re-implementing the official Mentor Mentee Portal.",
            "Payments, certificates, group mentoring."], "bul")], colWidths=[225])]],
        [241, 241], zebra=False, valign="TOP"))
    s.append(Spacer(1, 6))
    s.append(P("<b>Optional extensions</b> that the design supports but does not require: e-mail delivery of notifications, e-mail verification and password reset links, a calendar (iCalendar) export, "
               "and single sign-on if the programme office can provide it. Each is isolated behind a service interface so the core works without it."))

    s.append(H2("decisions"))
    s.append(tab_caption("Key design decisions"))
    s.append(table(["#", "Decision", "Why", "See"], [
        ["1", "Single role per account (student, mentor or admin).", "Keeps authorisation simple and auditable; a person who is both can use two accounts in this first version.", R("api.rbac")],
        ["2", "A mentor must be approved before being discoverable.", "Quality and safety gate; alumni claims can be checked from title, organisation and profile link.", R("workflows.mentor")],
        ["3", "Requests are explicit: one student, one mentor, a stated career goal, a 14-day expiry.", "Prevents spam and silent queues; every request ends in a recorded outcome.", R("workflows.rules")],
        ["4", "An accepted request creates exactly one mentorship in one database transaction.", "No half-accepted states, capacity can never be exceeded by concurrent accepts.", R("database.concurrency")],
        ["5", "Availability is stored as concrete slots; recurrence is a UI helper.", "Booking and overlap checks stay simple and fast.", R("database.slots")],
        ["6", "Matching is a transparent weighted score, 0.50 skills + 0.30 interests + 0.20 availability.", "Explainable to students and checkable by admins; weights are a proposal to validate with users.", R("matching")],
        ["7", "UUID keys; identities are taken from the token, never from the request body.", "Unguessable identifiers, no insecure direct object references.", R("api.rbac")],
        ["8", "Rules are enforced twice: in the service layer and again in PostgreSQL.", "Defence in depth; tested against a real PostgreSQL 16 instance.", R("database.dbtests")],
        ["9", "Short-lived access token plus rotated, hashed refresh token with reuse detection.", "Limits damage from a stolen token and supports real logout.", R("api.authn")],
        ["10", "Statistics hide small groups and exports contain no free text.", "Protects privacy of students in a small programme.", R("components.c12")]],
        [18, 190, 214, 60]))

    s.append(H2("conventions"))
    s.append(P("Readers can trust the report's claims because of how it labels them."))
    s.append(table(["Convention", "Meaning"], [
        [tag("V"), "A fact about the outside world (IITM pages) that was checked; it carries a source number and the access date."],
        [tag("P"), "A design choice made by this project. It can be changed; the reason is stated."],
        [tag("A"), "Something assumed because it could not be verified; listed again in " + R("quality.assume") + " with the consequence if it is wrong."],
        ["Sample data", "Names, e-mail addresses, UUIDs, counts and ratings in wireframes, examples and analytics are illustrative. Wireframes carry a visible 'sample data' ribbon. No real person or real statistics are represented."],
        ["Identifiers", "E01-E58 endpoints; C01-C12 components; D-01 to D-20 schema improvements; S/M/A/X workflow steps; US-xxx user stories; pages 1-26; DB-01 to DB-39 database tests."],
        ["Diagrams", "Sources (Mermaid, Graphviz, SQL and Python generators) are in the accompanying source archive; the large entity-relationship model is split into three diagrams so that text stays legible."],
        ["Typography", "Monospaced text is code, SQL, JSON or an identifier. Landscape pages are used where a diagram needs the width."]],
        [96, 386]))
    return s


# =============================================================================================
def sec2():
    s = H1("workflows")
    s.append(P("This section shows how the system is put together and how each role moves through it, then states the rules that decide edge cases. "
               "Flow charts use one visual language: rounded blocks are actions, diamonds are decisions, red blocks are refusals or ends, green blocks are successful ends."))

    s.append(H2("arch"))
    s.append(P("The platform is a three-tier web application: a single-page application, a stateless REST API that holds all business rules, and PostgreSQL. "
               "Optional integrations (e-mail, calendar export, single sign-on) attach to the API through service interfaces."))
    s.append(vfig(flows.as_fig(flows.architecture()), "Logical architecture. Solid arrows are mandatory paths, dashed boxes are optional integrations."))
    s.extend(bullets([
        "<b>React single-page application</b> renders pages and validates input for convenience only; it never decides who the user is or what they may do.",
        "<b>Flask REST API</b> (Blueprints per component) authenticates the JWT, authorises by role and ownership, validates input, runs the business rules in services and writes through SQLAlchemy.",
        "<b>PostgreSQL</b> stores all state and re-checks the key rules with constraints, partial unique indexes, exclusion constraints and triggers.",
        "<b>Statelessness</b>: the API keeps no session in memory, so more than one instance can run behind a load balancer. Scheduled jobs (request expiry, session reminders, retention purge) call the same services.",
    ]))

    s.extend(to_land())
    s.append(H2("e2e"))
    s.append(P("The end-to-end life of a mentoring relationship crosses all three roles. This landscape page shows the happy path and the main loops: "
               "rejection of a mentor profile, decline, cancellation and expiry of a request, and the end of a mentorship; the administrator flow follows."))
    s.append(vfig(image(D + "lifecycle.png", LCW, 150), "End-to-end flow across the three roles (mentor onboarding on the left, student journey in the middle, mentorship and sessions on the right)."))
    s.append(vfig(image(D + "admin_flow.png", LCW, 330), "Administrator flow (Section 2.5): review queue, user management, mentorship oversight, analytics, catalogues and the audit trail."))
    s.extend(to_port())

    s.append(H2("student"))
    s.append(P("A student starts by completing the profile because the profile gates mentor requests (rule R1) and feeds the matching score. The next two figures follow the student from registration to the end of a mentorship."))
    s.append(vfig(flows.as_fig(flows.student_a()), "Student flow, part 1: registration to the outcome of a request."))
    s.append(NP())
    s.append(vfig(flows.as_fig(flows.student_b()), "Student flow, part 2: running the mentorship, booking, feedback and ending."))
    s.append(tab_caption("Student workflow steps and the endpoints they use"))
    s.append(wf_table("Student"))
    s.append(Spacer(1, 5))
    s.append(wf_table("Shared"))

    s.append(H2("mentor"))
    s.append(P("A mentor is not visible to students until an administrator approves the profile. After approval the mentor controls exposure with two switches: "
               "<font face='DVM'>is_available</font> (accepting new mentees) and <font face='DVM'>max_active_mentees</font> (capacity, default 3, range 1-10)."))
    s.append(tab_caption("Mentor workflow steps and the endpoints they use"))
    s.append(wf_table("Mentor"))
    s.append(Spacer(1, 6))
    s.append(vfig(flows.as_fig(flows.mentor()), "Mentor flow: onboarding, review, requests, mentorship and sessions."))

    s.append(H2("admin"))
    s.append(P("The administrator flow is drawn on the landscape page in " + R("workflows.e2e") + ". Administrators are created by a command-line seed, never by self-registration. "
               "Each administrator action that changes data writes an entry to the append-only audit log."))
    s.append(tab_caption("Administrator workflow steps and the endpoints they use"))
    s.append(wf_table("Administrator"))

    s.append(H2("states"))
    s.append(P("Four entities have a life cycle. Each transition is performed by exactly one API operation, which checks the current state first and answers <font face='DVM'>409 INVALID_STATE_TRANSITION</font> otherwise."))
    s.append(vfig(image(D + "state_request.png", CW, 250), "Mentoring request states. 'expired' is set by a scheduled job when expires_at passes while the request is still pending."))
    s.append(vfig(image(D + "state_mentorship.png", CW, 250), "Mentorship states. Completing or ending a mentorship cancels future scheduled sessions."))
    s.append(vfig(image(D + "state_session.png", CW, 150), "Session states."))
    s.append(vfig(image(D + "state_profile.png", CW, 150), "Mentor profile review states. Only 'approved' mentors are discoverable."))

    s.append(H2("sequences"))
    s.append(P("Three interactions carry most of the risk and are drawn as sequences: authentication with refresh rotation, accepting a request (the concurrency-sensitive step), and booking a session."))
    s.append(vfig(image(D + "seq_auth.png", CW, 560), "Authentication: login, silent refresh with rotation, reuse detection and logout."))
    s.extend(to_land())
    s.append(vfig(image(D + "seq_accept.png", LCW, 440), "Accepting a request: one transaction locks the rows, checks state and capacity, then writes."))
    s.append(NP())
    s.append(vfig(image(D + "seq_book.png", LCW, 440), "Booking a session: availability, conflict checks and the database safety net."))
    s.extend(to_port())

    s.append(H2("rules"))
    s.append(P("The rules below are binding on the service layer. Where PostgreSQL can enforce the same rule, the right-hand column names the mechanism (tested in " + R("database.dbtests") + "). "
               "Numeric limits are " + tag("P") + " values that the programme office may change; they live in configuration, not in code."))
    rows = [
        ["R1", "Request prerequisites", "Only a student with <font face='DVM'>profile_completed = true</font> may request. The target must be an approved, available, active mentor with free capacity.",
         "PROFILE_INCOMPLETE, MENTOR_NOT_AVAILABLE, MENTOR_AT_CAPACITY (409)"],
        ["R2", "Duplicate requests", "At most one <i>pending</i> request per student-mentor pair; also no request while an active mentorship exists between the pair.",
         "DUPLICATE_PENDING_REQUEST, ACTIVE_MENTORSHIP_EXISTS. DB: partial unique index uq_pending_request, uq_active_pair"],
        ["R3", "Pending limit", "A student may hold at most 3 pending requests at once so that mentors are not flooded.", "PENDING_LIMIT_REACHED (409)"],
        ["R4", "Decline and cooldown", "A mentor may decline with an optional reason, shown to the student. The same student cannot re-request that mentor for 30 days; the error carries retry_after.",
         "REQUEST_COOLDOWN (409), notification request_declined"],
        ["R5", "Cancel by the student", "Only the sender may cancel, only while pending. A cancelled request frees the pair immediately (no cooldown).", "INVALID_STATE_TRANSITION (409), FORBIDDEN (403)"],
        ["R6", "Expiry", "A pending request not answered within 14 days becomes <i>expired</i>; the student is notified and may try the same or another mentor at once.", "Scheduled job; DB index ix_requests_expiry"],
        ["R7", "Accept", "Only the addressed mentor, only while pending. One transaction locks the request and the mentor row, re-checks capacity, sets the request to accepted, "
                         "creates the mentorship and the notification. Two simultaneous accepts cannot exceed capacity.",
         "MENTOR_AT_CAPACITY, INVALID_STATE_TRANSITION. DB: capacity trigger, unique mentorship per request"],
        ["R8", "Mentor changes while requests wait", "If a mentor is suspended, pending requests are cancelled with a notification. Capacity cannot be lowered below the current number of active mentees.",
         "VALIDATION_ERROR (422), notification"],
        ["R9", "Schedule a session", "Only inside an <i>active</i> mentorship. A student must pick an open slot; the mentor may pick a slot or give times. The start must be in the future and the duration at most 4 hours.",
         "MENTORSHIP_NOT_ACTIVE, SLOT_UNAVAILABLE, VALIDATION_ERROR"],
        ["R10", "Session conflicts", "Neither the mentor nor the student may have two scheduled sessions that overlap in time (back-to-back is allowed). A slot can back only one scheduled session.",
         "SESSION_CONFLICT (409). DB: two exclusion constraints and uq_session_slot_booked"],
        ["R11", "Slot changes", "A slot holding a scheduled session cannot be edited or deleted; slots of one mentor cannot overlap.", "SLOT_BOOKED, SLOT_OVERLAP. DB: ex_slot_no_overlap"],
        ["R12", "Cancel a session", "Either participant may cancel a scheduled session with a reason; the slot is released and the other party notified. Cancelling does not end the mentorship.",
         "INVALID_STATE_TRANSITION. DB: ck_session_cancel"],
        ["R13", "Complete a session", "Only the mentor, only after the scheduled start. Completion opens the 14-day feedback window.", "INVALID_STATE_TRANSITION"],
        ["R14", "End a mentorship", "Either party or an administrator may close an active mentorship: <i>completed</i> (natural end) or <i>ended</i> (early, reason required). "
                                    "Future scheduled sessions are cancelled, their slots released, history kept, and the other party notified. A closed mentorship cannot be reopened; a new request is needed.",
         "INVALID_STATE_TRANSITION. DB: ck_mentorship_ended"],
        ["R15", "Feedback", "Each participant may submit one rating (1-5) and optional comment per completed session within 14 days. The mentor sees the student's entry and the student sees the mentor's; admins see all.",
         "FEEDBACK_NOT_ALLOWED, FEEDBACK_ALREADY_SUBMITTED. DB: uq_feedback_once"],
        ["R16", "Account suspension", "A suspended user cannot sign in; their refresh tokens are revoked. History is retained and nothing is deleted.", "ACCOUNT_SUSPENDED (403)"],
    ]
    s.append(tab_caption("Business rules"))
    s.append(table(["#", "Topic", "Rule", "Error and database enforcement"], rows, [26, 78, 252, 126]))
    s.append(Spacer(1, 5))
    s.append(H3("Edge cases and how they resolve"))
    s.append(table(["Situation", "Resolution"], [
        ["Two students request the same mentor with one free place; the mentor accepts both quickly.", "The second accept fails with MENTOR_AT_CAPACITY; that request stays pending and the mentor sees why."],
        ["A mentor accepts at the instant the student cancels.", "Whichever transaction locks the request first wins; the other receives INVALID_STATE_TRANSITION. No partial state exists."],
        ["A student books the last open slot while the mentor deletes it.", "Deleting a booked slot is refused (SLOT_BOOKED); if the delete committed first, the booking fails with SLOT_UNAVAILABLE."],
        ["A student books two mentors at the same hour.", "The second booking is refused with SESSION_CONFLICT (student exclusion constraint)."],
        ["A mentorship ends while a session is scheduled.", "The session is cancelled automatically with the reason 'mentorship ended'; both parties are notified."],
        ["A mentor's approved profile is edited (title, organisation, link).", "The edit saves, is audit-logged and flagged to admins for re-check; the profile stays visible. Suspension is the remedy if a claim is false."],
        ["An administrator suspends a mentor who has active mentees.", "Active mentorships continue to exist but new sessions cannot be booked; the admin is shown the affected mentorships and may end them (rule R14)."],
        ["A user is erased on request.", "Personal fields are overwritten, the account is deactivated and history remains for integrity (" + R("database.retention") + ")."]],
        [236, 246]))

    s.append(H2("errors"))
    s.append(P("Errors are part of the design. Every failure is mapped to a stable machine-readable code (the full catalogue is in " + R("api.errorcat") + "), a clear message and a defined UI behaviour."))
    s.append(tab_caption("Error states by category and what the user sees"))
    s.append(table(["Category", "Examples (HTTP, code)", "UI behaviour"], [
        ["Not signed in or expired", "401 UNAUTHENTICATED, REFRESH_INVALID, REFRESH_REUSED", "Try one silent refresh; if that fails, clear local state and open Login with the message 'Your session has expired'. The page the user wanted is remembered."],
        ["Not allowed", "403 FORBIDDEN, ACCOUNT_SUSPENDED", "Full-page 'You do not have access' (page 4) or, for a suspended account, a message pointing to the programme office."],
        ["Missing or hidden", "404 NOT_FOUND", "'Not found' page; hidden resources look identical to missing ones, so existence is not leaked."],
        ["Rule conflict", "409 DUPLICATE_PENDING_REQUEST, REQUEST_COOLDOWN, PENDING_LIMIT_REACHED, MENTOR_AT_CAPACITY, SLOT_UNAVAILABLE, SESSION_CONFLICT ...", "Stay on the form; show the specific message next to the action. Refresh the data that changed (for example reload the slot list)."],
        ["Invalid input", "422 VALIDATION_ERROR with details[]", "Field-level messages under each input; focus moves to the first invalid field."],
        ["Too many requests", "429 RATE_LIMITED + Retry-After", "Toast 'Please wait a moment' and disable the button until the wait ends."],
        ["Server or network", "5xx, timeout, offline", "Banner 'Something went wrong' with Retry; data already entered is kept; the request id is shown for support."],
        ["Empty results", "200 with an empty list", "Empty-state panel with a primary action (for example 'Find mentors')."]],
        [92, 168, 222]))
    return s


# =============================================================================================
def sec3():
    s = H1("stack")
    s.append(P("The stack is the one prescribed for the course project. For each part this section gives the role it plays, why it is a good fit here, the main alternative considered, "
               "and the cost accepted by choosing it. All choices are " + tag("P") + "; none depends on IITM infrastructure."))

    s.append(H2("frontend"))
    s.append(table(["Technology", "Role in this project", "Why it fits", "Alternative and cost"], [
        ["<b>React</b>", "Component UI for 26 pages and 12 shared components.", "Component reuse (StatusBadge, DataTable, dialogs) across three role areas; large ecosystem; team skill is common.", "Vue or Svelte would also work; React chosen for mainstream support and testing libraries."],
        ["<b>Vite</b>", "Dev server and production build.", "Fast start and hot reload; simple configuration; static output deployable anywhere.", "Create React App is deprecated; Next.js adds server rendering not needed behind a login."],
        ["<b>React Router</b>", "Client routing with role-protected routes and redirect-after-login.", "Declarative route tree maps one-to-one to the page inventory (" + R("wireframes.inventory") + ").", "Manual routing is error-prone."],
        ["<b>Bootstrap</b>", "Layout grid, forms, tables, modals, toasts, responsive behaviour.", "Gives accessible, responsive primitives quickly so effort goes to workflows; one theme file carries the palette.", "Tailwind gives finer control but needs more design effort."],
        ["<b>Axios</b>", "HTTP client with interceptors.", "One interceptor attaches the access token and performs the single silent refresh on 401; another maps errors to the UI patterns.", "fetch works but needs hand-written interceptors."],
        ["<b>React Hook Form</b>", "Forms: registration, profiles, request, slots, feedback.", "Uncontrolled inputs keep large profile forms fast; server errors from 422 map onto fields.", "Formik is heavier; manual state is verbose."]],
        [70, 112, 168, 132]))
    s.append(Spacer(1, 4))
    s.extend(bullets([
        "<b>Token handling.</b> The access token lives in memory only; the refresh token is an HttpOnly cookie that scripts cannot read. A page reload calls the refresh endpoint once to restore the session.",
        "<b>Accessibility.</b> Status is always colour plus text; every control is reachable by keyboard; modals trap focus; form errors are announced to screen readers. Target WCAG 2.1 AA " + tag("P") + ".",
        "<b>State management.</b> Server data is fetched per page and held in component state with a small cache for catalogues; no global store is needed beyond the signed-in user and the unread count.",
    ]))

    s.append(H2("backend"))
    s.append(table(["Technology", "Role in this project", "Why it fits", "Alternative and cost"], [
        ["<b>Flask</b>", "HTTP API and application factory.", "Small, explicit and easy to learn; fits a 58-endpoint API; the team keeps full control of structure.", "Django REST Framework gives more batteries but more convention to learn."],
        ["<b>Blueprints</b>", "One blueprint per component group (auth, profiles, mentors, requests, mentorships, sessions, notifications, admin).", "Mirrors the component design; each Blueprint can be built and tested by one person.", "A single module would grow unmanageably."],
        ["<b>SQLAlchemy</b>", "ORM and query construction; transactions with row locks (SELECT ... FOR UPDATE).", "Maps the schema to model classes and gives parameterised queries by default, preventing SQL injection.", "Raw SQL is faster for a few reporting queries; allowed through text() where justified."],
        ["<b>Flask-Migrate</b> (Alembic)", "Versioned schema migrations.", "Every schema change is a reviewed, repeatable script; CI can create a database from nothing.", "Hand-run SQL drifts between environments."],
        ["<b>Flask-JWT-Extended</b>", "Access tokens, claims, token verification.", "Mature support for short-lived access tokens, custom claims (role) and error handlers; refresh tokens are handled by our own table for rotation and reuse detection.", "PyJWT directly means rewriting what the extension provides."],
        ["<b>Flask-CORS</b>", "Cross-origin policy.", "Explicit allow-list of origins; credentials allowed only for the web app origin.", "Proxying /api through the front-end host removes CORS in production (see " + R("api.security") + ")."]],
        [84, 106, 164, 128]))
    s.append(Spacer(1, 4))
    s.extend(bullets([
        "<b>Service layer.</b> Blueprints stay thin: parse, authorise, call a service, serialise. Business rules live in service classes so they can be tested without HTTP (" + R("structure.backendlayers") + ").",
        "<b>Validation.</b> Request bodies are validated against schemas before any service runs; the same schemas generate part of the OpenAPI file.",
        "<b>Password hashing.</b> Argon2id (or bcrypt where Argon2 is unavailable) with per-user salt; hashes are never logged or returned.",
    ]))

    s.append(H2("database"))
    s.append(table(["Technology", "Why it fits"], [
        ["<b>PostgreSQL 16</b>", "Relational integrity fits the domain (parties, states, capacity). Features used on purpose: UUID keys (gen_random_uuid), composite foreign keys, partial unique indexes, "
                                 "<font face='DVM'>EXCLUDE USING gist</font> with btree_gist for overlap prevention, CHECK constraints, triggers, JSONB for audit details, and full-text search for discovery. "
                                 "These were exercised on a real PostgreSQL 16 server (" + R("database.dbtests") + ")."],
        ["<b>Managed Postgres in production</b>", "Backups, patching and connection limits handled by the provider; a free or low-cost tier is enough for course scale " + tag("A") + ". Point-in-time recovery should be enabled if offered."],
        ["<b>Alternative considered</b>", "SQLite is simpler but cannot enforce range-overlap exclusion or partial unique indexes the same way and has weak concurrent-write behaviour. A document database would push integrity rules into application code."]],
        [120, 362]))

    s.append(H2("apitools"))
    s.append(table(["Technology", "Use"], [
        ["<b>OpenAPI 3.0</b>", "The REST contract (Appendix A). It is the single reference for front-end, back-end and test authors and is validated automatically; the front end can generate typed clients from it."],
        ["<b>Postman</b>", "Collection imported from the OpenAPI file, with environments for local and staging; used for exploratory testing and as a runnable demonstration. Newman can run the collection in CI."],
        ["<b>pytest</b>", "Back-end unit tests (services, matching), API tests with the Flask test client against a disposable PostgreSQL database, and the database rule tests."],
        ["<b>Vitest + React Testing Library</b>", "Front-end unit and component tests: forms, role-protected routes, status badges, error and empty states; interactions are tested the way a user performs them."],
        ["<b>Quality tools</b>", "ruff and black (Python), ESLint and Prettier (JavaScript), openapi-spec-validator, and pre-commit hooks so style is never debated in review."]],
        [120, 362]))

    s.append(H2("collab"))
    s.append(table(["Tool", "Use"], [
        ["<b>Git and GitHub</b>", "Version control, pull requests with required review, protected main branch, GitHub Actions for CI (" + R("structure.workflow") + ")."],
        ["<b>Figma</b>", "High-fidelity design and a shared component library after the wireframes in " + R("wireframes") + " are accepted; prototypes for usability checks."],
        ["<b>Draw.io</b>", "Editable diagrams (architecture, flows). In this report the diagrams are also generated from text sources so they can be diffed in Git."],
        ["<b>Trello or Jira</b>", "Backlog and board built from the user stories (" + R("wireframes.stories") + "); one card per story with acceptance criteria; labels for component C01-C12."]],
        [120, 362]))

    s.append(H2("deploy"))
    s.append(P("The proposed deployment uses three managed services with no servers to administer. The diagram shows trust boundaries and the one design choice that matters for security: the browser talks to a single origin."))
    s.append(vfig(image(D + "deployment.png", 300, 520), "Deployment view. The static front end on Vercel proxies /api to the Render-hosted API, so the browser sees one origin and the refresh cookie stays first-party."))
    s.append(table(["Element", "Choice", "Notes"], [
        ["Front end", "Vercel static hosting", "Built by Vite; a rewrite rule forwards /api/* to the API origin; every route falls back to index.html for client routing."],
        ["API", "Render web service (gunicorn, 2 workers)", "Health endpoint for the platform's checks; environment variables hold secrets; the scheduled job (expiry, reminders, purge) runs as a cron job using the same image."],
        ["Database", "Managed PostgreSQL", "Private connection string, TLS required, daily backups, migrations run at release before the new version receives traffic."],
        ["Environments", "local, staging, production", "Same configuration keys everywhere; staging is seeded with the sample data used in this report."]],
        [80, 150, 252]))

    s.append(H2("risks"))
    s.append(tab_caption("Technology risks"))
    s.append(table(["Risk", "Likelihood and impact", "Mitigation"], [
        ["Free-tier hosting sleeps or throttles, slowing the first request.", "High likelihood, low impact for a demo.", "Document it; use a health-check ping for demos; the design is stateless so a paid tier is a configuration change."],
        ["Cross-site cookies are blocked by browsers if front end and API are on different sites.", "Medium, high impact (login breaks).", "Same-origin proxy rewrite as the default; CORS only for local development."],
        ["Library major-version changes (React Router, SQLAlchemy 2.x).", "Medium, medium.", "Pin versions; renovate-style update pull requests; upgrade only with CI green."],
        ["Concurrency bugs in accept and book flows.", "Medium, high.", "Row locks plus database constraints; the concurrency test in " + R("database.dbtests") + " is repeated as an API test."],
        ["Over-building before client feedback on the official portal.", "Medium, high (wasted work).", "Discovery item D1 first (" + R("exec.context") + "); build the identity and request flow before analytics."]],
        [180, 112, 190]))
    return s
