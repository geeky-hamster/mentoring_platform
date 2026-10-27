"""Student and mentor flow charts drawn with flowlib (vector)."""
from flowlib import Flow
from kit import Fig


def student_a():
    f = Flow(3, 10, py=54)
    f.node("S1", 0, 0, "S1 Register account", "proc")
    f.node("X0", 2, 0, "X0 Sign in", "proc")
    f.node("D", 1, 1, "Profile complete?", "dec")
    f.node("S3", 0, 2, "S3 Onboarding: stage, skills,\ninterests, goals", "proc")
    f.node("S4", 1, 2, "S4 Discover mentors\nfilters and recommendations", "proc")
    f.node("S5", 1, 3, "S5 View mentor profile", "proc")
    f.node("S6", 1, 4, "S6 Submit request\ncareer goal and message", "proc")
    f.node("V", 1, 5, "Server rules pass?", "dec")
    f.node("ERR", 2, 5, "Specific error (409), form stays open", "err")
    f.node("S7", 1, 6, "S7 Request pending, mentor notified", "proc")
    f.node("O", 1, 7, "Outcome", "dec", w=100)
    f.node("CN", 0, 8, "cancelled\n(student, E29)", "err", w=118)
    f.node("EX", 1, 8, "expired\n(no reply in 14 days)", "err", w=118)
    f.node("DC", 2, 8, "declined\n(reason shown)", "err", w=118)
    f.node("RET", 1, 9, "Back to S4: pick another mentor", "proc")
    f.node("S8", 2, 7, "S8 Mentorship active\n(next figure)", "term", w=122)
    f.edge("S1", "S3", None, "b", "t")
    f.edge("X0", "D", None, "b", "r", via=[(2, 1)])
    f.edge("D", "S3", "no (409)", "l", "t", via=[(0, 1)])
    f.edge("D", "S4", "yes", "b", "t")
    f.edge("S3", "S4", None, "r", "l")
    f.edge("S4", "S5")
    f.edge("S5", "S6")
    f.edge("S6", "V")
    f.edge("V", "ERR", "fails", "r", "l")
    f.edge("ERR", "S6", None, "t", "r", via=[(2, 4)])
    f.edge("V", "S7", "all pass")
    f.edge("S7", "O")
    f.edge("O", "S8", "accepts", "r", "l")
    f.edge("O", "CN", "student cancels", "b", "t", via=[(1, 7.5), (0, 7.5)], lseg=1)
    f.edge("O", "EX", "no reply", "b", "t", lseg=0) if False else f.edge("O", "EX", None, "b", "t")
    f.edge("O", "DC", "mentor declines", "b", "t", via=[(1, 7.5), (2, 7.5)], lseg=1)
    f.edge("CN", "RET", None, "b", "l", via=[(0, 9)])
    f.edge("EX", "RET", None, "b", "t")
    f.edge("DC", "RET", None, "b", "r", via=[(2, 9)])
    f.edge("RET", "S4", None, "t", "b", via=[]) if False else None
    return f


def student_b():
    f = Flow(3, 10, py=54)
    f.node("S8", 1, 0, "S8 Mentorship active, notification received", "term", w=210)
    f.node("S9", 1, 1, "S9 Schedule session\nchoose open slot, mode, link", "proc")
    f.node("SC", 1, 2, "Slot free and no conflict?", "dec")
    f.node("ERR", 2, 2, "409 SLOT_UNAVAILABLE or\nSESSION_CONFLICT", "err", w=124, dx=-16)
    f.node("BK", 1, 3, "Session scheduled, mentor notified", "ok")
    f.node("CS", 0, 3, "Cancelled by either party,\nslot released", "err")
    f.node("S10", 1, 4, "S10 Attend session", "proc")
    f.node("DN", 1, 5, "Mentor marks session completed", "proc")
    f.node("FB", 1, 6, "Rate session within 14 days\n(one entry per participant)", "proc")
    f.node("G", 1, 7, "Continue mentorship?", "dec")
    f.node("S11", 1, 8, "S11 End mentorship\noptional note", "proc")
    f.node("END", 1, 9, "Mentorship ended, history read-only", "term", w=210)
    f.edge("S8", "S9")
    f.edge("S9", "SC")
    f.edge("SC", "ERR", "no", "r", "l")
    f.edge("ERR", "S9", None, "t", "r", via=[(None, 1)])
    f.edge("SC", "BK", "yes")
    f.edge("BK", "CS", "cancel", "l", "r", dashed=True)
    f.edge("CS", "S9", None, "t", "l", via=[(0, 1)])
    f.edge("BK", "S10")
    f.edge("S10", "DN")
    f.edge("DN", "FB")
    f.edge("FB", "G")
    f.edge("G", "S9", "yes: next session", "r", "r", via=[(2.45, 7), (2.45, 1)], lseg=1)
    f.edge("G", "S11", "no")
    f.edge("S11", "END")
    return f


def mentor():
    f = Flow(3, 12, py=52)
    f.node("M1", 0, 0, "M1 Register as mentor", "proc")
    f.node("M2", 1, 0, "M2 Professional profile", "proc")
    f.node("M3", 2, 0, "M3 Expertise, pathways,\navailability slots", "proc")
    f.node("M4", 2, 1, "M4 Submit for review\n(pending_review)", "proc")
    f.node("R", 2, 2, "Admin decision", "dec", w=110)
    f.node("LIVE", 2, 3, "Profile approved: visible,\naccepting mentees", "term")
    f.node("M10", 0, 3, "M10 Capacity and\naccepting switch", "proc")
    f.node("M5", 1, 4, "M5 Review incoming request\nand student summary", "proc")
    f.node("M6", 1, 5, "M6 Accept or decline?", "dec")
    f.node("DC", 0, 6, "Declined, optional reason\n(max 500), student notified", "err")
    f.node("CAP", 1, 6, "Capacity free and\nrequest pending?", "dec", w=150, h=40)
    f.node("M7", 1, 7, "Mentorship created (active),\nstudent notified", "ok")
    f.node("M8", 1, 8, "M8 Schedule or confirm sessions\nin open slots", "proc")
    f.node("DONE", 1, 9, "Session held; mentor marks it completed with notes", "proc")
    f.node("M9", 1, 10, "M9 Give session feedback", "proc")
    f.node("CL", 1, 11, "M7 Close mentorship?", "dec", w=140)
    f.node("END", 0, 11, "Mentorship ended,\nsessions read-only", "term", w=124)
    f.edge("M1", "M2", None, "r", "l")
    f.edge("M2", "M3", None, "r", "l")
    f.edge("M3", "M4")
    f.edge("M4", "R")
    f.edge("R", "M2", "rejected with note", "l", "b", via=[(1, 2)])
    f.edge("R", "LIVE", "approved")
    f.edge("M10", "LIVE", "any time", "r", "l", dashed=True)
    f.edge("LIVE", "M5", None, "b", "t", via=[(2, 3.5), (1, 3.5)])
    f.edge("M5", "M6")
    f.edge("M6", "DC", "decline", "l", "t", via=[(0, 5)])
    f.edge("M6", "CAP", "accept")
    f.edge("CAP", "M5", "no: 409 at capacity or invalid state", "r", "r", via=[(2.0, 6), (2.0, 4)], lseg=1)
    f.edge("CAP", "M7", "yes")
    f.edge("M7", "M8")
    f.edge("M8", "DONE")
    f.edge("DONE", "M9")
    f.edge("M9", "CL")
    f.edge("CL", "END", "yes", "l", "r")
    f.edge("CL", "M8", "no: next session", "r", "r", via=[(2.0, 11), (2.0, 8)])
    return f


def _cx(i):
    return 14 + 115 * (i + 0.5)


def architecture():
    f = Flow(1, 1, px=482, py=340)
    f.H = 344
    f.anode("U", 241, 15, "Students, mentors and administrators (web browser)", "start", 300, 26)
    f.group(8, 44, 466, 80, "Frontend: React single-page app built with Vite, hosted on Vercel", "#F4F8FC", "#9FB3CC")
    for i, t in enumerate(["React Router\nrole-guarded routes", "26 pages\nBootstrap components", "React Hook Form\nclient-side validation", "Axios client\nJWT header, refresh on 401"]):
        f.anode(f"F{i}", _cx(i), 92, t, "proc", 100, 40)
    f.anode("PX", 241, 148, "Vercel rewrite: /api/* is forwarded to Render (same origin)", "warn", 380, 26)
    f.group(8, 176, 466, 92, "Backend: Flask REST API under /api/v1, one Render web service", "#F2FAF5", "#8FBFA2")
    for i, t in enumerate(["Middleware\nCORS allow-list, rate\nlimiter, JWT, errors", "Blueprints\nroute layer, input\nvalidation", "Service layer\nbusiness rules,\ntransactions", "SQLAlchemy models\nFlask-Migrate\nmigrations"]):
        f.anode(f"B{i}", _cx(i), 226, t, "ok", 100, 52)
    f.anode("EM", 90, 322, "E-mail provider (optional)\nreset and verification links", "proc", 150, 38)
    f.anode("CR", 250, 322, "Scheduled job (Render cron)\nexpire requests, purge tokens", "warn", 150, 38)
    f.anode("DB", 410, 322, "PostgreSQL 16 (managed)\n17 tables, constraints,\nindexes, triggers", "term", 134, 44)
    f.poly([(241, 28), (241, 44)], True, label="HTTPS", lseg=0)
    f.poly([(_cx(3), 112), (_cx(3), 135)], True, label="HTTPS JSON", lseg=0)
    f.poly([(241, 161), (241, 176)], True, label="HTTPS", lseg=0)
    for i in range(3):
        f.edge(f"B{i}", f"B{i+1}", None, "r", "l")
    f.poly([(_cx(3), 252), (_cx(3), 300)], True, label="SQL over TLS", lseg=0)
    f.poly([(250 + 75, 322), (410 - 67, 322)], True, label=None)
    f.poly([(_cx(2), 252), (_cx(2), 284), (90, 284), (90, 303)], True, dashed=True, label="optional", lseg=1)
    return f


def component():
    f = Flow(1, 1, px=482, py=430)
    f.H = 432
    f.anode("FE", 241, 16, "Frontend: React SPA (pages, route guards, Axios client)", "proc", 320, 26)
    f.anode("API", 241, 62, "REST API layer: Flask Blueprints under /api/v1\nJWT and role checks, validation, error envelope", "warn", 400, 34)
    gx, gw = 22, 442
    groups = [("Identity and reference data", 100), ("Discovery and matching", 172), ("Mentoring lifecycle", 244), ("Cross-cutting and governance", 316)]
    for lab, y in groups:
        f.group(gx, y, gw, 64, lab, "#F2FAF5", "#8FBFA2")
    cxs = [gx + gw / 8 * (2 * i + 1) for i in range(4)]
    rows = {0: 100, 1: 172, 2: 244, 3: 316}

    def comp(id, col, row, t):
        f.anode(id, cxs[col], rows[row] + 40, t, "ok", 100, 36)
    comp("C01", 0, 0, "C01 Authentication\nand authorisation")
    comp("C02", 1, 0, "C02 User and profile\nmanagement")
    comp("C03", 2, 0, "C03 Skill and career-\ninterest management")
    comp("C04", 0, 1, "C04 Mentor discovery\nand filtering")
    comp("C05", 1, 1, "C05 Mentor matching\nservice")
    comp("C06", 0, 2, "C06 Mentoring request\nmanagement")
    comp("C07", 1, 2, "C07 Mentorship\nrelationship mgmt")
    comp("C08", 2, 2, "C08 Availability and\nsession scheduling")
    comp("C09", 3, 2, "C09 Feedback\nmanagement")
    comp("C10", 0, 3, "C10 Notifications")
    comp("C11", 1, 3, "C11 Administration")
    comp("C12", 2, 3, "C12 Analytics and\nreporting")
    f.anode("ORM", 330, 410, "SQLAlchemy models and queries\nPostgreSQL 16", "term", 250, 34)
    f.anode("EXT", 110, 410, "Optional integrations\ne-mail provider, scheduler", "warn", 170, 34)
    f.poly([(241, 29), (241, 45)], True, label="HTTPS JSON", lseg=0)
    # left bus from the API layer into each group
    for lab, y in groups:
        f.poly([(41, 62), (10, 62), (10, y + 32), (gx, y + 32)], True)
    f.poly([(gx, 62), (41, 62)], False) if False else None
    # right bus from groups to persistence
    for k, (lab, y) in enumerate(groups):
        pts = [(gx + gw, y + 32), (474, y + 32), (474, 392)]
        f.poly(pts, False)
    f.poly([(474, 392), (474, 410), (455, 410)], True)
    f.poly([(110, 380), (110, 393)], True, dashed=True)
    f.edge("C04", "C05", None, "r", "l")
    f.edge("C06", "C07", None, "r", "l")
    f.edge("C07", "C08", None, "r", "l")
    f.edge("C08", "C09", None, "r", "l")
    return f


def as_fig(flow):
    return Fig(flow.W, flow.H, lambda c, w, h: flow.draw(c, w, h))
