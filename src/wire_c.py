"""Wireframes: admin pages (22-26)."""
from wirelib import *

DRAW = {}
AN = "Admin User"


def page(n):
    def deco(fn):
        DRAW[n] = fn
        return fn
    return deco


def kpi(w, x, y, cw, label, val, sub=None, h=36):
    w.card(x, y, cw, h)
    w.text(x + 7, y + 6, label, 5.9, MUTE, "DVC-B")
    w.bold(x + 7, y + 15, val, 11, NAVY)
    if sub:
        w.text(x + 7, y + 28, sub, 5.5, STR)


def daterange(w, x, y, label="Last 30 days"):
    w.rect(x, y, 96, 14, colors.white, STR, 0.7, r=2)
    w.text(x + 6, y + 4, label, 6.2, INK)
    w.text(x + 88, y + 3.6, "▾", 6.2, MUTE, "DV", "c")


# ------------------------------------------------------------------ 22 Admin dashboard
@page(22)
def p22(w):
    w.chrome("/admin/dashboard")
    x0, y0, cw, ch = w.shell("admin", "Dashboard", AN)
    w.bold(x0, 40, "Programme overview", 9.5, NAVY)
    daterange(w, x0 + cw - 96, 38)
    w.call(6, x0 + cw - 102, 45)
    kw = (cw - 24) / 4
    for i, (l, v, s) in enumerate([("Students", "412", "of which active 366"), ("Approved mentors", "58", "9 awaiting review"), ("Active mentorships", "131", "+12 in period"), ("Sessions completed", "287", "avg rating 4.5")]):
        kpi(w, x0 + i * (kw + 8), 58, kw, l, v, s)
    w.call(1, x0 - 4, 64)
    lw = cw * 0.55
    w.card(x0, 102, lw, 108, "Requests and sessions per week")
    w.lineplot(x0 + 12, 124, lw - 24, 68, [[18, 24, 22, 31, 29, 36], [9, 13, 15, 18, 17, 24]])
    for i, wk in enumerate(["W1", "W2", "W3", "W4", "W5", "W6"]):
        w.text(x0 + 12 + (lw - 24) * i / 5, 196, wk, 5.4, MUTE, "DVC", "c")
    w.line(x0 + lw - 90, 106, x0 + lw - 80, 106, TEAL, 1.4)
    w.text(x0 + lw - 77, 103, "Requests", 5.5, MUTE)
    w.line(x0 + lw - 44, 106, x0 + lw - 34, 106, AMBER, 1.4)
    w.text(x0 + lw - 31, 103, "Sessions", 5.5, MUTE)
    w.call(2, x0 - 4, 108)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 102, rw, 108, "Mentor review queue")
    w.table(rx + 6, 121, rw - 12, [("Applicant", .5), ("Waiting", .2), ("", .3)],
            [["Rohan Iyer", "1 d", ""], ["Meera Das", "2 d", ""], ["Arun Pillai", "4 d", ""]], 17, size=6, actions={2: ["Review"]})
    w.text(rx + 8, 196, "Empty: 'Queue is empty'", 5.6, STR, "DVC-I")
    w.call(3, rx - 4, 108)
    w.card(x0, 216, lw, 68, "Alert: stale requests")
    w.text(x0 + 8, 236, "4 requests pending for more than 10 days.", 6.4, INK)
    w.text(x0 + 8, 246, "Mentors will be reminded; requests expire after 14 days.", 6, MUTE)
    w.link(x0 + 8, 262, "Open request list", 6.2)
    w.call(4, x0 - 4, 222)
    w.card(rx, 216, rw, 68, "Recent activity")
    for i, t in enumerate(["Mentor approved · Meera Das", "Student suspended · ID 4f2a...", "Mentorship ended by admin"]):
        w.text(rx + 8, 236 + i * 10, t, 5.9, MUTE)
    w.call(5, rx - 4, 222)


# ------------------------------------------------------------------ 23 User management
@page(23)
def p23(w):
    w.chrome("/admin/users")
    x0, y0, cw, ch = w.shell("admin", "Users", AN)
    w.tabs(x0, 38, ["Users", "Catalogue"], 0, w=cw)
    w.call(1, x0 - 4, 45)
    w.search(x0, 58, 150, "Search name or e-mail")
    w.inp(x0 + 158, 58, 70, None, "All roles", kind="select", h=14)
    w.inp(x0 + 234, 58, 78, None, "All statuses", kind="select", h=14)
    w.call(2, x0 - 4, 65)
    cols = [("Name", .2), ("E-mail", .28), ("Role", .1), ("Status", .12), ("Joined", .12), ("Actions", .18)]
    rows = [["Asha Menon", "asha@example.org", "student", "active", "12 Oct", ""],
            ["Rohan Iyer", "rohan@example.org", "mentor", "active", "03 Oct", ""],
            ["Dev Patel", "dev@example.org", "student", "suspended", "28 Sep", ""],
            ["Meera Das", "meera@example.org", "mentor", "pending", "02 Oct", ""]]
    rh = 17
    w.table(x0, 80, cw, cols, rows, rh, badges=(3,), size=6)
    bx = x0 + cw * .82 + 3
    for i, (lb, red) in enumerate([("Suspend", True), ("Reactivate", False), ("Suspend", True)]):
        pass
    for i, (lb, red) in enumerate([("Suspend", True), ("Suspend", True), ("Reactivate", False), ("Suspend", True)]):
        yy = 80 + rh * (i + 1)
        bw = sw(lb, 5.4, "DVC-B") + 9
        w.rect(bx, yy + 2.5, bw, rh - 5, colors.white, RED if red else NAVY, 0.6, r=2)
        w.text(bx + bw / 2, yy + 5.6, lb, 5.4, RED if red else NAVY, "DVC-B", "c")
    w.call(3, x0 - 4, 80 + rh + 8)
    w.call(4, bx - 4, 80 + rh + 8)
    w.pager(x0, 80 + rh * 5 + 6)
    w.text(x0 + 200, 80 + rh * 5 + 8, "Empty: 'No users match the filters'", 5.6, STR, "DVC-I")
    # catalogue inset
    cy = 80 + rh * 5 + 26
    w.card(x0, cy, cw, 284 - cy, "Tab: Catalogue (skills, interests)")
    w.chips(x0 + 8, cy + 20, ["Python", "SQL", "Statistics", "Machine learning", "Algorithms", "Data Science", "Research"], 300, sel=("Python", "SQL"))
    w.button(x0 + cw - 150, cy + 6, 70, 13, "Add", "primary", 5.8)
    w.button(x0 + cw - 76, cy + 6, 70, 13, "Edit / Retire", "secondary", 5.8)
    w.call(6, x0 + cw - 156, cy + 12)
    w.call(5, x0 + 4, cy + 26)
    w.text(x0 + 8, cy + 46, "Retired items stay on existing profiles but are hidden from new selections.", 5.8, STR, "DVC-I")


# ------------------------------------------------------------------ 24 Mentor approval
@page(24)
def p24(w):
    w.chrome("/admin/mentors")
    x0, y0, cw, ch = w.shell("admin", "Mentor reviews", AN)
    w.tabs(x0, 38, ["Pending review (3)", "Approved", "Rejected", "Suspended"], 0, w=cw)
    w.call(1, x0 - 4, 45)
    lw = 130
    w.card(x0, 58, lw, 226, "Applicants")
    for i, (n, d, sel) in enumerate([("Rohan Iyer", "Submitted 1 d ago", True), ("Meera Das", "Submitted 2 d ago", False), ("Arun Pillai", "Submitted 4 d ago", False)]):
        y = 78 + i * 30
        w.rect(x0 + 5, y, lw - 10, 26, colors.HexColor("#E3ECF7") if sel else colors.white, TEAL if sel else FAINT, 0.7, r=3)
        w.bold(x0 + 10, y + 5, n, 6.6, NAVY)
        w.text(x0 + 10, y + 15, d, 5.8, MUTE)
    w.text(x0 + 8, 172, "Empty: 'No applications waiting'", 5.6, STR, "DVC-I")
    w.call(2, x0 - 4, 84)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 58, rw, 226)
    w.bold(rx + 8, 64, "Rohan Iyer", 8.5, NAVY)
    w.badge(rx + 8, 76, "Pending review", "pending")
    w.call(3, rx - 4, 70)
    w.text(rx + 8, 92, "Senior Data Scientist · Example Analytics Pvt Ltd · 6 years", 6.2, INK)
    w.text(rx + 8, 102, "Type: Industry professional · Capacity: 5 mentees", 6, MUTE)
    w.chips(rx + 8, 113, ["Python", "SQL", "Machine learning"], 200, sel=("Python", "SQL"))
    w.line(rx + 6, 130, rx + rw - 6, 130, FAINT, 0.6)
    w.text(rx + 8, 135, "Verification checklist", 6.6, NAVY, "DVC-B")
    for i, (lb, on) in enumerate([("Identity and employer details are plausible", True), ("Profile text is professional and complete", True), ("Expertise matches stated experience", False), ("Contact preference confirmed by e-mail", False)]):
        w.check(rx + 10, 148 + i * 12, lb, on)
    w.call(4, rx - 4, 152)
    w.text(rx + 8, 200, "Review note (required for Reject, shown to the mentor)", 5.9, MUTE, "DVC-B")
    w.rect(rx + 8, 209, rw - 16, 22, colors.white, STR, 0.7, r=2)
    w.text(rx + 12, 213, "Please add your current employer.", 6, MUTE)
    by = 244
    w.button(rx + 8, by, 78, 16, "Approve", "success")
    w.call(5, rx + 3, by + 8)
    w.button(rx + 94, by, 78, 16, "Reject", "danger")
    w.call(6, rx + 89, by + 8)
    w.button(rx + 180, by, 78, 16, "Suspend", "secondary")
    w.call(7, rx + 175, by + 8)
    w.text(rx + 8, 266, "Approve needs all checklist items ticked. Every decision is written to the audit log.", 5.6, STR, "DVC-I")


# ------------------------------------------------------------------ 25 Mentorship management
@page(25)
def p25(w):
    w.chrome("/admin/mentorships")
    x0, y0, cw, ch = w.shell("admin", "Mentorships", AN)
    w.tabs(x0, 38, ["Mentorships", "Requests"], 0, w=cw)
    w.call(1, x0 - 4, 45)
    w.search(x0, 58, 112, "Search student or mentor")
    w.inp(x0 + 118, 58, 72, None, "All statuses", kind="select", h=14)
    w.inp(x0 + 196, 58, 76, None, "Last 90 days", kind="select", h=14)
    w.call(2, x0 - 4, 65)
    cols = [("Student", .17), ("Mentor", .17), ("Started", .11), ("Sessions", .1), ("Status", .11), ("Actions", .12)]
    rows = [["Asha Menon", "Rohan Iyer", "22 Oct", "5", "active", ""],
            ["Dev Patel", "Rohan Iyer", "24 Oct", "3", "active", ""],
            ["Tara Nair", "Meera Das", "30 Sep", "6", "ended", ""],
            ["Neha Rao", "Arun Pillai", "11 Oct", "2", "active", ""]]
    tw = cw * 0.66
    rh = 18
    w.table(x0, 80, tw, cols, rows, rh, badges=(4,), size=6)
    bx = x0 + tw * (.17 + .17 + .11 + .1 + .11) / .78 + 2
    for i, st in enumerate(["active", "active", "ended", "active"]):
        yy = 80 + rh * (i + 1)
        if st == "active":
            w.rect(bx, yy + 3, 24, rh - 6, colors.white, RED, 0.6, r=2)
            w.text(bx + 12, yy + 6, "End", 5.4, RED, "DVC-B", "c")
    w.call(3, x0 - 4, 80 + rh + 9)
    w.call(5, bx - 4, 80 + rh + 9)
    w.pager(x0, 80 + rh * 5 + 8)
    w.text(x0 + 200, 80 + rh * 5 + 10, "Empty: 'No match'", 5.6, STR, "DVC-I")
    # drawer
    dx = x0 + tw + 8
    dw = cw - tw - 8
    w.rect(dx, 58, dw, 226, colors.white, colors.HexColor("#CBD3DE"), 0.8, r=3)
    w.bold(dx + 8, 64, "Mentorship detail", 7.4, NAVY)
    w.text(dx + dw - 8, 64, "×", 9, STR, "DV", "r")
    w.call(4, dx - 4, 70)
    w.text(dx + 8, 82, "Asha Menon ↔ Rohan Iyer", 6.4, INK, "DVC-B")
    w.text(dx + 8, 92, "Active since 22 Oct 2026", 6, MUTE)
    w.text(dx + 8, 108, "Sessions: 3 completed, 2 scheduled", 6, MUTE)
    w.text(dx + 8, 118, "Feedback: average 4.7 (3 ratings)", 6, MUTE)
    w.text(dx + 8, 134, "Goal", 5.9, MUTE, "DVC-B")
    w.para(dx + 8, 143, dw - 16, "Move into a data science role.", 6, INK, 7.6, maxlines=2)
    w.text(dx + 8, 166, "Audit trail", 5.9, MUTE, "DVC-B")
    for i, t in enumerate(["22 Oct  request accepted", "26 Oct  session completed", "2 Nov   session completed"]):
        w.text(dx + 8, 176 + i * 9, t, 5.6, MUTE, "DVM")
    w.button(dx + 8, 250, dw - 16, 16, "End mentorship", "danger")
    w.call(5, dx + 3, 258)
    w.text(dx + 8, 270, "Reason required; both parties notified.", 5.4, STR, "DVC-I")
    w.card(x0, 200, tw, 84, "Tab: Requests (read-only, same filters)")
    w.table(x0 + 6, 218, tw - 12, [("Student", .26), ("Mentor", .26), ("Sent", .16), ("Status", .32)],
            [["Imran Khan", "Rohan Iyer", "6 Nov", "pending"], ["Tara Nair", "Meera Das", "1 Nov", "declined"], ["Neha Rao", "Arun Pillai", "3 Oct", "accepted"]], 14, badges=(3,), size=5.8)
    w.call(6, x0 - 4, 206)


# ------------------------------------------------------------------ 26 Analytics
@page(26)
def p26(w):
    w.chrome("/admin/analytics")
    x0, y0, cw, ch = w.shell("admin", "Analytics", AN)
    w.bold(x0, 40, "Programme analytics", 9.5, NAVY)
    daterange(w, x0 + cw - 190, 38)
    for i, lb in enumerate(["7d", "30d", "90d"]):
        w.rect(x0 + cw - 190 + 0, 0, 0, 0)
    x = x0 + cw - 90
    for i, lb in enumerate(["7d", "30d", "90d"]):
        w.chip(x + i * 22, 40, lb, "sel" if i == 1 else "plain")
    w.call(1, x0 + cw - 196, 45)
    w.button(x0 + cw - 90, 56, 90, 13, "Export CSV", "secondary", 6)
    w.call(6, x0 + cw - 96, 62)
    kw = (cw - 24) / 4
    for i, (l, v, s) in enumerate([("Request acceptance", "71%", "of decided requests"), ("Median response", "1.8 d", "mentor to decision"), ("Session completion", "88%", "of scheduled"), ("Average rating", "4.5", "of 5 (n = 112)")]):
        kpi(w, x0 + i * (kw + 8), 74, kw, l, v, s)
    w.call(2, x0 - 4, 80)
    fw = cw * 0.4
    w.card(x0, 116, fw, 110, "Funnel")
    for i, (lb, v, frac) in enumerate([("Requests sent", 240, 1.0), ("Accepted", 170, .71), ("Session scheduled", 151, .63), ("Session completed", 133, .55)]):
        y = 136 + i * 20
        w.rect(x0 + 8, y, (fw - 16) * frac, 11, TEAL if i == 0 else colors.HexColor("#4C9AA7"), None, r=2)
        w.text(x0 + 12, y + 2.6, lb, 5.8, colors.white, "DVC-B")
        w.text(x0 + 8 + (fw - 16) * frac + 3 if frac < .9 else x0 + fw - 10, y + 2.6, str(v), 5.8, MUTE if frac < .9 else colors.white, "DVC-B", "l" if frac < .9 else "r")
    w.call(3, x0 - 4, 122)
    mx = x0 + fw + 8
    mw = cw - fw - 8
    w.card(mx, 116, mw, 110, "Weekly trend")
    w.lineplot(mx + 10, 138, mw - 20, 66, [[18, 24, 22, 31, 29, 36], [9, 13, 15, 18, 17, 24]])
    for i, wk in enumerate(["W1", "W2", "W3", "W4", "W5", "W6"]):
        w.text(mx + 10 + (mw - 20) * i / 5, 208, wk, 5.4, MUTE, "DVC", "c")
    w.call(4, mx - 4, 122)
    w.card(x0, 232, fw, 52, "Rating distribution")
    w.bars(x0 + 12, 250, fw - 24, 20, [3, 5, 14, 38, 52], labels=["1", "2", "3", "4", "5"], color=AMBER)
    w.call(5, x0 - 4, 238)
    w.rect(mx, 232, mw, 52, colors.HexColor("#FBF0D9"), None, r=3)
    w.rect(mx, 232, 2.6, 52, AMBER)
    w.bold(mx + 10, 238, "Privacy note", 6.6, colors.HexColor("#7A4E08"))
    w.para(mx + 10, 249, mw - 20, "Aggregates only. Groups smaller than 5 are hidden. Exports exclude names and e-mail addresses.", 6, colors.HexColor("#7A4E08"), 7.6, maxlines=3)
    w.call(7, mx - 4, 238)
