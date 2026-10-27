"""Sections 4-6."""
from doc import *
import schema, api, pages, flows, uml_figs, components_data as CD
from uml import fig as uml_fig
from wirelib import WF, DW, DH
import wire_a, wire_states
try:
    import wire_b, wire_c
except ImportError:
    wire_b = wire_c = None
from reportlab.platypus import Table, TableStyle, CondPageBreak
from content_a import tag, D

EP = api.EP
DRAW = dict(wire_a.DRAW)
DRAW.update(wire_b.DRAW)
DRAW.update(wire_c.DRAW)
PG = pages.PAGE


def ep_label(e):
    x = EP[e]
    return f"<b>{e}</b> <font face='DVM'>{x['method']} {x['path']}</font>"


def wf_fig(n, width=CW):
    sc = width / DW
    h = DH * sc

    def fn(c, w, hh):
        c.saveState()
        c.setStrokeColor(LINE)
        c.setLineWidth(0.6)
        c.rect(0, 0, w, hh, stroke=1, fill=0)
        c.scale(sc, sc)
        DRAW[n](WF(c))
        c.restoreState()
    f = Fig(width, h, fn)
    f.hAlign = "CENTER"
    return f


def states_fig(width=CW):
    sc = width / DW

    def fn(c, w, hh):
        c.saveState()
        c.scale(sc, sc)
        wire_states.states(WF(c))
        c.restoreState()
    f = Fig(width, DH * sc, fn)
    f.hAlign = "CENTER"
    return f


def scaled_uml(u, maxw, maxh):
    s = min(maxw / u.W, maxh / u.H, 1.0)
    f = Fig(u.W * s, u.H * s, lambda c, w, h: (c.saveState(), c.scale(s, s), u.draw(c), c.restoreState()))
    f.hAlign = "CENTER"
    return f


def action_row(a):
    label, kind, target, eps, wf = a
    if kind == "nav":
        dest = f"Opens page {target}: {PG[target]['title']}" if target else "Opens the role home page"
    elif kind == "modal":
        dest = f"Opens {target}"
    else:
        dest = "Calls the API"
    return [label, dest, ", ".join(eps) if eps else "-", wf]


def page_spec(n, first=False):
    p = PG[n]
    st = ([] if first else [NP()]) + [H3(f"Page {n}: {p['title']}", toc=True)]
    steps = sorted({a[4] for a in p["actions"]}, key=lambda x: (x[0], int(x[1:]) if x[1:].isdigit() else 0))
    kv = [("Role / route / steps", f"{p['role']}  |  <font face='DVM'>{p['route']}</font>  |  workflow steps {', '.join(steps)}"), ("Purpose", p["purpose"])]
    if p["tabs"]:
        kv.append(("Tabs / sections", " | ".join(p["tabs"])))
    st.append(kv_table(kv, [92, 390], pad=2))
    st.append(Spacer(1, 3))
    load = len(p["elements"]) + len(p["actions"]) + len(p["endpoints"])
    st.append(vfig(wf_fig(n, CW if load < 16 else 440), f"Wireframe {n}: {p['title']} (sample data; amber numbers match the element table)."))
    st.append(table(["#", "Element", "Behaviour"], [[str(i), f"<b>{e[0]}</b>", e[1]] for i, e in enumerate(p["elements"], 1)], [20, 120, 342], pad=2))
    st.append(Spacer(1, 3))
    st.append(table(["Action", "Result", "Endpoints", "Step"], [action_row(a) for a in p["actions"]], [150, 200, 90, 42], pad=2))
    st.append(Spacer(1, 3))
    ep_rows = [[ep_label(e), EP[e]["purpose"].split(". ")[0].rstrip(".")] for e in p["endpoints"]]
    st.append(table(["Endpoints used", "Purpose"], ep_rows, [200, 282], pad=2))
    st.append(Spacer(1, 3))
    st.append(kv_table([("Empty state", p["empty"]), ("Error states", p["error"])], [92, 390], pad=2))
    return st


# =============================================================================================
def sec4():
    s = H1("wireframes")
    s.append(P("This section specifies all 26 pages. Each page has a wireframe, a numbered element table, the actions with their endpoints, and its empty and error states. "
               "Wireframes are low-fidelity on purpose: they fix structure, content and behaviour, not colour or typography. <b>Every name, e-mail address, count and rating on a wireframe is sample data</b> "
               "and the wireframes carry a visible ribbon saying so. " + tag("P")))

    s.append(H2("inventory"))
    rows = []
    for p in pages.PAGES:
        rows.append([str(p["num"]), f"<b>{p['title']}</b>", p["role"], f"<font face='DVM'>{p['route']}</font>", ", ".join(p["endpoints"][:4]) + (" ..." if len(p["endpoints"]) > 4 else "")])
    s.append(tab_caption("Page inventory"))
    s.append(table(["#", "Page", "Role", "Route", "Main endpoints"], rows, [20, 118, 54, 150, 140], style="tds"))
    s.append(Spacer(1, 6))
    s.append(tab_caption("Sidebar navigation by role (page numbers in brackets)"))
    s.append(table(["Role", "Sidebar items in order"], [
        [r.capitalize(), " | ".join(f"{label} [{num}]" for label, num in items)] for r, items in pages.SIDEBAR.items()], [70, 412]))
    s.append(Spacer(1, 5))
    s.append(P("<b>Access rules.</b> Pages 1-3 are public. Page 4 (access denied or session expired) is shown to any user. Pages 5-14 require the <i>student</i> role, 15-21 the <i>mentor</i> role and 22-26 the <i>admin</i> role. "
               "The route guard sends an unauthenticated visitor to page 1 and remembers the wanted route; a signed-in user on a page of another role sees page 4. "
               "Guards only improve usability: every API call is authorised again on the server (" + R("api.rbac") + "). A mentor whose profile is not yet approved can use pages 15, 20 and 21 only and sees a banner explaining the review state."))

    s.append(H2("nav"))
    s.append(P("The navigation maps show every route, every link between pages and the modal dialogs. Solid arrows are navigation; dotted arrows open a modal or drawer. "
               "The sidebar note on each map means that every sidebar page is reachable from every other page of the same role."))
    s.append(vfig(image(D + "navmap_student.png", CW, 560), "Navigation map: student area (pages 5-14) and its shared entry points."))
    s.extend(to_land())
    s.append(vfig(image(D + "navmap_public.png", LCW, 255), "Navigation map: public and shared pages (1-4)."))
    s.append(vfig(image(D + "navmap_admin.png", LCW, 175), "Navigation map: administrator area (pages 22-26)."))
    s.append(NP())
    s.append(vfig(image(D + "navmap_mentor.png", LCW, 400), "Navigation map: mentor area (pages 15-21)."))
    s.extend(to_port())

    s.append(H2("shared"))
    s.append(P("Twelve shared components keep the 26 pages consistent and cheap to build. Each is implemented once in the React component library and reused."))
    s.append(tab_caption("Shared UI components"))
    s.append(table(["Component", "Purpose and behaviour"], [[f"<b>{a}</b>", b] for a, b in pages.SHARED], [130, 352]))
    s.append(Spacer(1, 6))
    s.append(vfig(states_fig(), "State patterns used on every page: loading, empty, error, toast, confirmation dialog and drawer. Proposed behaviour, not verified against any IITM interface."))
    s.append(P("<b>Responsive behaviour.</b> At widths under 768 px the sidebar collapses to a menu button, tables become stacked cards and dialogs fill the screen. "
               "Touch targets are at least 44 px high. These rules apply to every page and are not repeated in the page specifications."))

    for key, rng, title in (("pub", [1, 2, 3, 4], None), ("stu", range(5, 15), None), ("men", range(15, 22), None), ("adm", range(22, 27), None)):
        s.append(CondPageBreak(PFH * 0.6))
        s.append(H2(key))
        intro = {"pub": "Pages available before signing in, plus the shared access-denied page.",
                 "stu": "The student journey: home, onboarding, discovery, requests, mentorship, sessions and notifications.",
                 "men": "The mentor journey: home, requests, mentees, schedule, profile and notifications.",
                 "adm": "The administrator console: home, users and catalogues, mentor reviews, mentorships and analytics."}[key]
        s.append(P(intro))
        for i, n in enumerate(rng):
            s.extend(page_spec(n, first=(i == 0)))

    s.append(H2("stories"))
    s.append(P("Each user story is traced to the pages that realise it, the endpoints it needs and the workflow steps in " + R("workflows") + ". "
               "Acceptance criteria for each story are written when the card is created from this table."))
    rows = []
    for sid, role, text, pgs, eps, wfs in pages.STORIES:
        who = "an " + role.lower() if role[0] in "AE" else "a " + role.lower() if role != "Any user" else "any user"
        rows.append([f"<b>{sid}</b>", f"As {who}, I want to {text}.", ", ".join(map(str, pgs)), ", ".join(eps), ", ".join(wfs)])
    s.append(tab_caption("Traceability matrix: user story to pages, endpoints and workflow steps"))
    s.append(table(["Story", "Description", "Pages", "Endpoints", "Steps"], rows, [40, 240, 32, 110, 60], style="tds"))
    covered = {e for st in pages.STORIES for e in st[4]}
    missing = sorted(set(EP) - covered)
    s.append(Spacer(1, 5))
    s.append(P(f"<b>Coverage.</b> The {len(pages.STORIES)} stories exercise {len(covered)} of the {len(EP)} endpoints directly. The remaining {len(missing)} "
               f"({', '.join(missing)}) are supporting operations used by pages but not by a story of their own (for example e-mail verification, logout, dashboards and the catalogue lists); "
               f"each is still referenced by at least one page specification above."))
    return s


# =============================================================================================
def sec5():
    s = H1("components")
    s.append(P("The platform is divided into twelve software components. A component is a unit of <i>behaviour</i> with one owner and a stable interface; it is not a table. "
               "Several components share tables, and every table has exactly one component that is allowed to write it. Database entities are described in " + R("database") + "; "
               "this section describes responsibilities."))
    s.append(H2("overview"))
    s.append(vfig(flows.as_fig(flows.component()), "Component diagram: front end, REST API layer, twelve components in four groups, persistence and optional integrations."))
    s.append(tab_caption("Components, services and write ownership"))
    rows = []
    for c in CD.COMPS:
        rows.append([f"<b>{c['id']}</b>", c["name"], c["service"], ", ".join(c["wtables"]) or "(read-only)", str(len(c["eps"]))])
    s.append(table(["ID", "Component", "Service class", "Tables written", "Endpoints"], rows, [28, 110, 116, 176, 52], style="tds"))
    s.append(Spacer(1, 5))
    s.extend(bullets([
        "<b>Layering.</b> Blueprints (HTTP) call services (rules); services call the ORM. A service never calls a Blueprint, and a Blueprint never queries tables directly.",
        "<b>Write ownership.</b> Only the owning component writes a table. Other components read through its service or through a read-only query, which keeps rules in one place.",
        "<b>No cycles.</b> Component dependencies form a directed acyclic graph (matrix in " + R("components.depmatrix") + "). Where two components need each other, one raises an internal event instead of calling (C07 raises 'mentorship closed', C08 handles it).",
        "<b>Optional integrations</b> (e-mail, iCalendar export, single sign-on) are called through interfaces owned by C10, C08 and C01 respectively; with them switched off the core still works.",
    ]))
    for c in CD.COMPS:
        blk = [CondPageBreak(300), H2(c["key"]), P(c["purpose"])]
        rb = lambda items: "<br/>".join("&bull; " + i for i in items)
        eps = "<br/>".join(ep_label(e) for e in c["eps"])
        deps = ", ".join(("AuditService (C11)" if d == "AUD" else f"{d} {CD.BY[d]['name']}") for d in c["deps"]) or "none (leaf component)"
        kv = [("Responsibilities", rb(c["resp"])), ("Inputs", c["inputs"]), ("Outputs", c["outputs"]), ("Business rules", rb(c["rules"])),
              ("Tables written", ", ".join(f"<font face='DVM'>{t}</font>" for t in c["wtables"]) or "none"),
              ("Tables read", ", ".join(f"<font face='DVM'>{t}</font>" for t in c["rtables"]) or "none"),
              ("Endpoints", eps), ("Depends on", deps)]
        if c["ext"]:
            kv.append(("Integrations", c["ext"]))
        blk.append(kv_table(kv, [92, 390]))
        s.extend(blk)
    s.append(H2("depmatrix"))
    s.append(P("A filled cell means the row component calls the column component (or reads its data through its service). AUD is the AuditService owned by C11; it only receives writes and calls nothing, so it creates no cycle."))
    ids = [c["id"] for c in CD.COMPS] + ["AUD"]
    rows = []
    for c in CD.COMPS:
        rows.append([f"<b>{c['id']}</b>"] + ["<b>X</b>" if i in c["deps"] else "" for i in ids])
    hdr = [""] + [i for i in ids]
    wd = [34] + [(482 - 34) / len(ids)] * len(ids)
    t = table(hdr, rows, wd, style="td", extra=[("ALIGN", (1, 0), (-1, -1), "CENTER")])
    s.append(tab_caption("Component dependency matrix (row depends on column)"))
    s.append(t)
    s.append(Spacer(1, 5))
    s.append(P("<b>Build order implied by the matrix:</b> C10, C03 and C01 first (no dependencies); then C02; then C08 and C07; then C06, C04 and C09; then C05 and C11; C12 last. "
               "This order is used by the roadmap in " + R("roadmap") + "."))
    return s


# =============================================================================================
def sec6():
    s = to_land() + H1("uml")
    s.append(P("Three landscape pages keep attributes and methods readable: identity and catalogue classes, the mentoring lifecycle, and the service layer. "
               "Classes carry typed attributes (<font face='DVM'>UUID</font> identifiers), public methods and multiplicities at both ends of each association. "
               "<b>Entity classes</b> hold state and state-only rules; <b>service classes</b> hold use-case logic spanning entities. A service is never a table, and an entity never calls the database."))
    s.append(H2("identity"))
    s.append(vfig(scaled_uml(uml_figs.identity(), LCW, 262), "Class diagram, part 1: User, profiles, Skill, CareerInterest and Notification. Skill and interest links carry attributes only for skills (association classes StudentSkill and MentorExpertise)."))
    s.append(table(["Relationship", "Multiplicity", "Meaning"], [
        ["User - StudentProfile", "1 to 0..1", "A user with role student has exactly one profile; other roles have none (enforced by the composite key on role)."],
        ["User - MentorProfile", "1 to 0..1", "A user with role mentor has one mentor profile."],
        ["User - Notification", "1 to 0..*", "A user receives many notifications; a notification belongs to one user."],
        ["StudentProfile / MentorProfile - Skill", "* to *", "Many-to-many through StudentSkill (level, focus flag) and MentorExpertise (level)."],
        ["StudentProfile / MentorProfile - CareerInterest", "* to *", "Many-to-many through plain junctions student_interests and mentor_interests."]],
        [200, 60, 479]))
    s.append(NP())
    s.append(H2("lifecycle"))
    s.append(vfig(scaled_uml(uml_figs.lifecycle(), LCW, 438), "Class diagram, part 2: the request-to-feedback lifecycle. The filled diamond marks composition (a session cannot exist without its mentorship)."))
    s.append(NP())
    s.append(H2("services"))
    s.append(vfig(scaled_uml(uml_figs.services(), LCW, 438), "Class diagram, part 3: the service layer. Dashed arrows are dependencies (a service calls another); the AuthenticationService, MatchingService and AnalyticsService stand alone."))
    s.extend(to_port())
    s.append(H2("relations"))
    s.append(P("Three kinds of relationship are used, and the difference matters when the code is written."))
    s.append(table(["Kind", "Notation", "Meaning in this model", "In code and database"], [
        ["<b>Association</b>", "Plain line with multiplicities", "A durable link between two entities that is stored.", "Foreign key or junction table; ORM relationship; loaded when needed."],
        ["<b>Composition</b>", "Filled diamond", "The part cannot outlive the whole: sessions belong to one mentorship; feedback belongs to one session.", "Foreign key NOT NULL with ON DELETE RESTRICT (history is never deleted); no cascading delete."],
        ["<b>Dependency</b>", "Dashed open arrow", "A service uses another service or entity for one operation but keeps no link to it.", "A constructor-injected collaborator or a function call; no table, no foreign key."]],
        [74, 90, 170, 148]))
    s.append(Spacer(1, 5))
    s.append(tab_caption("All associations between entity classes"))
    s.append(table(["From", "To", "From..To", "Stored as", "Notes"], [
        ["User", "StudentProfile", "1 .. 0..1", "student_profiles.user_id UNIQUE", "Composite FK (user_id, user_role) forces role = student."],
        ["User", "MentorProfile", "1 .. 0..1", "mentor_profiles.user_id UNIQUE", "Same for mentors."],
        ["User", "Notification", "1 .. 0..*", "notifications.user_id", "ON DELETE CASCADE (operational data)."],
        ["StudentProfile", "MentoringRequest", "1 .. 0..*", "mentoring_requests.student_id", "References student_profiles(user_id)."],
        ["MentorProfile", "MentoringRequest", "1 .. 0..*", "mentoring_requests.mentor_id", "References mentor_profiles(user_id)."],
        ["MentoringRequest", "Mentorship", "1 .. 0..1", "mentorships.request_id UNIQUE", "Composite FK repeats student and mentor so parties cannot differ."],
        ["StudentProfile", "Mentorship", "1 .. 0..*", "mentorships.student_id", "One active mentorship per pair (partial unique index)."],
        ["MentorProfile", "Mentorship", "1 .. 0..*", "mentorships.mentor_id", "Capacity enforced against max_active_mentees."],
        ["Mentorship", "Session", "1 .. 0..* (composition)", "sessions.mentorship_id", "Composite FK with student_id and mentor_id."],
        ["MentorProfile", "AvailabilitySlot", "1 .. 0..*", "availability_slots.mentor_id", "Exclusion constraint forbids overlap."],
        ["AvailabilitySlot", "Session", "0..1 .. 0..1", "sessions.slot_id (nullable)", "Partial unique index: one scheduled session per slot."],
        ["Session", "Feedback", "1 .. 0..2 (composition)", "feedback.session_id", "UNIQUE (session_id, submitted_by): one per participant."]],
        [78, 82, 78, 124, 120], style="tds"))
    s.append(Spacer(1, 5))
    s.append(tab_caption("Service dependency matrix (row service calls column service)"))
    names = ["Auth", "Match", "Ana", "Men", "Ses", "Fb", "Aud", "Not", "Adm"]
    full = {k: n for k, n, _, _ in uml_figs.SERVICES}
    calls = {"Men": ["Not", "Aud"], "Ses": ["Men", "Not"], "Fb": ["Ses", "Not"], "Adm": ["Not", "Aud", "Auth", "Men"], "Auth": ["Aud"], "Match": [], "Ana": [], "Aud": [], "Not": []}
    rows = [[f"<b>{full[r].replace('Service', '')}</b>"] + ["<b>X</b>" if c in calls[r] else "" for c in names] for r in names]
    short = {"Auth": "Auth", "Match": "Match", "Ana": "Anal.", "Men": "Mentor.", "Ses": "Session", "Fb": "Feedb.", "Aud": "Audit", "Not": "Notif.", "Adm": "Admin"}
    s.append(table([""] + [short[c] for c in names], rows, [62] + [46.7] * 9, style="tds", extra=[("ALIGN", (1, 0), (-1, -1), "CENTER")]))
    s.append(P("The diagram draws only the dependencies that carry business meaning (checks, notifications, audit). AuthenticationService is called by the HTTP layer rather than by other services, and MatchingService, AnalyticsService and AuditService "
               "have no outgoing calls except to the database. Thin query services for profiles (C02), catalogues (C03) and discovery (C04) are not drawn because they only orchestrate the entity methods shown."))

    s.append(H2("mapping"))
    s.append(tab_caption("Class to table and key attribute naming"))
    s.append(table(["Class", "Table", "Notes"], [
        ["User", "users", "camelCase attribute names map to snake_case columns (userId = user_id)."],
        ["StudentProfile", "student_profiles (+ student_skills, student_interests)", "Class id studentProfileId; other tables reference the user_id."],
        ["MentorProfile", "mentor_profiles (+ mentor_expertise, mentor_interests)", "mentor_id in the API is users.user_id."],
        ["Skill", "skills", ""], ["CareerInterest", "career_interests", ""],
        ["MentoringRequest", "mentoring_requests", "status enumeration stored as VARCHAR with a CHECK constraint."],
        ["Mentorship", "mentorships", ""], ["AvailabilitySlot", "availability_slots", ""], ["Session", "sessions", "student_id and mentor_id are denormalised to allow exclusion constraints."],
        ["Feedback", "feedback", ""], ["Notification", "notifications", ""],
        ["AuditService (entity AuditLog)", "audit_logs", "Append-only."], ["AuthenticationService (entity RefreshToken)", "refresh_tokens", "Hash of the token only."]],
        [128, 170, 184], style="tds"))
    s.append(Spacer(1, 4))
    s.append(P("<b>Enumerations</b> used in the diagrams and their stored values: Role (" + ", ".join(schema.ROLES) + "); AccountStatus (" + ", ".join(schema.ACCOUNT_STATUS) +
               "); ProfileStatus (" + ", ".join(schema.PROFILE_STATUS) + "); RequestStatus (" + ", ".join(schema.REQUEST_STATUS) + "); MentorshipStatus (" + ", ".join(schema.MENTORSHIP_STATUS) +
               "); SessionStatus (" + ", ".join(schema.SESSION_STATUS) + "); MeetingMode (" + ", ".join(schema.MEETING_MODE) + "); Level (" + ", ".join(schema.LEVELS) +
               "); ProgrammeStage (" + ", ".join(schema.STAGES) + "); MentorType (" + ", ".join(schema.MENTOR_TYPES) + ")."))
    return s
