"""Wireframes: mentor pages (15-21)."""
from wirelib import *
from wire_a import notif_list

DRAW = {}
MN = "Rohan Iyer"


def page(n):
    def deco(fn):
        DRAW[n] = fn
        return fn
    return deco


def kpi(w, x, y, cw, label, val, sub=None):
    w.card(x, y, cw, 36)
    w.text(x + 7, y + 6, label, 5.9, MUTE, "DVC-B")
    w.bold(x + 7, y + 15, val, 11, NAVY)
    if sub:
        w.text(x + 7, y + 28, sub, 5.5, STR)


# ------------------------------------------------------------------ 15 Mentor dashboard
@page(15)
def p15(w):
    w.chrome("/mentor/dashboard")
    x0, y0, cw, ch = w.shell("mentor", "Dashboard", MN)
    w.banner(x0, 40, cw, "Your profile is approved and visible to students.", "ok", 14)
    w.call(1, x0 - 4, 47)
    kw = (cw - 16) / 3
    kpi(w, x0, 60, kw, "Pending requests", "2", "oldest 3 days")
    kpi(w, x0 + kw + 8, 60, kw, "Active mentees", "3", "of 5 capacity")
    kpi(w, x0 + 2 * (kw + 8), 60, kw, "Sessions this month", "4", "1 awaiting completion")
    w.call(2, x0 - 4, 66)
    w.toggle(x0, 104, True)
    w.text(x0 + 24, 105, "Accepting new mentees", 6.6, INK, "DVC-B")
    w.call(3, x0 - 4, 108)
    w.text(x0 + cw - 4, 105, "Capacity 3 / 5", 6.4, MUTE, "DVC-B", "r")
    w.progress(x0 + cw - 110, 114, 106, 0.6, 4)
    w.call(6, x0 + cw - 116, 112)
    lw = (cw - 8) / 2
    w.card(x0, 124, lw, 160, "Incoming requests")
    w.table(x0 + 6, 143, lw - 12, [("Student", .36), ("Sent", .22), ("", .42)],
            [["Asha Menon", "2 d ago", ""], ["Dev Patel", "3 d ago", ""], ["Neha Rao", "5 d ago", ""]], 17, size=6,
            actions={2: ["View", "Accept"]})
    w.link(x0 + 8, 262, "View all requests", 6.2)
    w.text(x0 + 100, 263, "Empty: 'No pending requests'", 5.6, STR, "DVC-I")
    w.call(4, x0 - 4, 130)
    rx = x0 + lw + 8
    w.card(rx, 124, lw, 160, "Upcoming sessions")
    w.table(rx + 6, 143, lw - 12, [("When", .42), ("Mentee", .3), ("Mode", .28)],
            [["Wed 12 Nov, 18:00", "Asha Menon", "Online"], ["Thu 13 Nov, 17:30", "Dev Patel", "Phone"], ["Sat 15 Nov, 10:00", "Neha Rao", "Online"]], 17, size=6)
    w.link(rx + 8, 262, "Open schedule", 6.2)
    w.text(rx + 80, 263, "Empty: 'Nothing scheduled'", 5.6, STR, "DVC-I")
    w.call(5, rx - 4, 130)


# ------------------------------------------------------------------ 16 Incoming requests
@page(16)
def p16(w):
    w.chrome("/mentor/requests")
    x0, y0, cw, ch = w.shell("mentor", "Requests", MN)
    w.tabs(x0, 38, ["Pending", "Accepted", "Declined", "All"], 0, w=x0 + cw - 120 - x0 + x0)
    w.call(1, x0 - 4, 45)
    w.text(x0 + cw, 42, "Capacity 3 / 5", 6.4, MUTE, "DVC-B", "r")
    w.progress(x0 + cw - 70, 52, 70, 0.6, 3.5)
    w.call(6, x0 + cw - 76, 54)
    cols = [("Student", .15), ("Goal", .27), ("Matched on", .14), ("Sent", .08), ("Status", .1), ("Actions", .26)]
    rows = [["Asha Menon", "Move into data science role", "Python, SQL", "2 d ago", "pending", ""],
            ["Dev Patel", "Prepare for software interviews", "Algorithms", "3 d ago", "pending", ""],
            ["Neha Rao", "Plan higher studies abroad", "Statistics", "5 d ago", "pending", ""],
            ["Imran Khan", "Understand analytics careers", "SQL", "6 d ago", "pending", ""],
            ["Tara Nair", "Build a research profile", "ML basics", "8 d ago", "pending", ""]]
    rh = 22
    w.table(x0, 64, cw, cols, rows, rh, badges=(4,), size=6)
    bx = x0 + cw * (.15 + .27 + .14 + .08 + .1) + 3
    for i in range(5):
        yy = 64 + 22 + i * rh
        yy = 64 + rh * (i + 1)
        w.rect(bx, yy + 5, 20, 12, colors.white, NAVY, 0.6, r=2)
        w.text(bx + 10, yy + 8.2, "View", 5.4, NAVY, "DVC-B", "c")
        w.rect(bx + 23, yy + 5, 26, 12, NAVY, None, r=2)
        w.text(bx + 36, yy + 8.2, "Accept", 5.4, colors.white, "DVC-B", "c")
        w.rect(bx + 52, yy + 5, 28, 12, colors.white, RED, 0.6, r=2)
        w.text(bx + 66, yy + 8.2, "Decline", 5.4, RED, "DVC-B", "c")
    w.call(2, x0 - 4, 76)
    w.call(3, bx + 1, 64 + rh + 5)
    w.call(4, bx + 24, 64 + rh + 5)
    w.call(5, bx + 53, 64 + rh + 5)
    w.pager(x0, 64 + rh * 6 + 8)
    w.text(x0 + 200, 64 + rh * 6 + 10, "Empty: 'No pending requests'  ·  Accept at capacity: 409 MENTOR_AT_CAPACITY", 5.6, STR, "DVC-I")


# ------------------------------------------------------------------ 17 Request details
@page(17)
def p17(w):
    w.chrome("/mentor/requests/9b21c4e0-...")
    x0, y0, cw, ch = w.shell("mentor", "Requests", MN)
    w.link(x0, 40, "‹ Back to requests", 6.2)
    w.bold(x0 + 10, 52, "Request from Asha Menon", 9.5, NAVY)
    w.badge(x0 + 150, 53, "Pending")
    w.text(x0 + 190, 54, "Sent 2 days ago · expires in 12 days", 6, MUTE)
    w.call(1, x0 - 4, 58)
    lw = 262
    w.card(x0, 70, lw, 100, "Goal and message")
    w.text(x0 + 8, 90, "Goal", 5.9, MUTE, "DVC-B")
    w.para(x0 + 8, 99, lw - 16, "Move into a data science role after graduation.", 6.4, INK, 8)
    w.text(x0 + 8, 116, "Message", 5.9, MUTE, "DVC-B")
    w.para(x0 + 8, 125, lw - 16, "Hello, I saw your work in analytics. I am building a portfolio and would value feedback on my projects and interview preparation.", 6.2, MUTE, 8, maxlines=4)
    w.call(2, x0 - 4, 76)
    w.card(x0, 176, lw, 62, "Skills and interests")
    w.text(x0 + 8, 194, "Skills", 5.9, MUTE, "DVC-B")
    w.chips(x0 + 40, 192, ["Python", "SQL", "Statistics"], lw - 50, sel=("Python", "SQL"))
    w.text(x0 + 8, 214, "Interests", 5.9, MUTE, "DVC-B")
    w.chips(x0 + 40, 212, ["Data Science", "Higher Studies"], lw - 50, sel=("Data Science",))
    w.call(4, x0 - 4, 182)
    w.card(x0, 244, lw, 40, "Capacity")
    w.text(x0 + 8, 262, "You have 3 of 5 mentee places in use. Accepting leaves 1 place.", 6.2, INK)
    w.call(5, x0 - 4, 250)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 70, rw, 100, "Student profile summary")
    w.imgph(rx + 8, 90, 30, 30)
    w.bold(rx + 46, 91, "Asha Menon", 7.6, NAVY)
    w.text(rx + 46, 102, "BSc degree · graduating 2027", 6, MUTE)
    w.text(rx + 46, 111, "Needs: portfolio, interviews", 6, MUTE)
    w.para(rx + 8, 128, rw - 16, "Final-year student interested in analytics roles and higher studies.", 6, MUTE, 7.6, maxlines=3)
    w.call(3, rx - 4, 76)
    w.card(rx, 176, rw, 108, "Decision")
    w.button(rx + 8, 198, rw - 16, 17, "Accept request", "primary")
    w.call(6, rx + 3, 206)
    w.button(rx + 8, 220, rw - 16, 17, "Decline request", "danger")
    w.call(7, rx + 3, 228)
    w.text(rx + 8, 246, "Decline opens a dialog: optional reason", 5.6, STR, "DVC-I")
    w.text(rx + 8, 255, "(max 500 characters). Student sees it.", 5.6, STR, "DVC-I")
    w.text(rx + 8, 268, "Already decided: buttons hidden (409).", 5.6, STR, "DVC-I")


# ------------------------------------------------------------------ 18 My mentees
@page(18)
def p18(w):
    w.chrome("/mentor/mentees")
    x0, y0, cw, ch = w.shell("mentor", "My mentees", MN)
    w.tabs(x0, 38, ["Active (3)", "Closed (4)"], 0, w=cw)
    w.call(1, x0 - 4, 45)
    lw = 150
    w.card(x0, 58, lw, 226, "Mentees")
    for i, (n, st, sel) in enumerate([("Asha Menon", "Next: 12 Nov", True), ("Dev Patel", "Next: 13 Nov", False), ("Neha Rao", "Next: 15 Nov", False)]):
        y = 78 + i * 30
        w.rect(x0 + 5, y, lw - 10, 26, colors.HexColor("#E3ECF7") if sel else colors.white, TEAL if sel else FAINT, 0.7, r=3)
        w.avatar(x0 + 16, y + 13, 7, "".join(p[0] for p in n.split()))
        w.bold(x0 + 28, y + 5, n, 6.6, NAVY)
        w.text(x0 + 28, y + 15, st, 5.8, MUTE)
    w.text(x0 + 8, 172, "Empty: 'No active mentees yet'", 5.6, STR, "DVC-I")
    w.link(x0 + 8, 181, "Go to requests", 6)
    w.call(2, x0 - 4, 84)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 58, rw, 226)
    w.bold(rx + 8, 64, "Asha Menon", 8.5, NAVY)
    w.badge(rx + 8, 77, "Active")
    w.text(rx + 44, 78, "Since 22 Oct 2026 \u00B7 Goal: data science role", 6, MUTE)
    w.call(3, rx - 4, 70)
    w.button(rx + rw - 164, 62, 76, 14, "Schedule session", "primary", 5.8)
    w.call(5, rx + rw - 169, 69)
    w.button(rx + rw - 82, 62, 76, 14, "Close mentorship", "danger", 5.8)
    w.call(7, rx + rw - 87, 69)
    w.line(rx + 6, 92, rx + rw - 6, 92, FAINT, 0.6)
    w.text(rx + 8, 97, "Sessions", 6.6, NAVY, "DVC-B")
    cols = [("Date and time", .3), ("Mode", .14), ("Status", .2), ("Actions", .36)]
    rows = [["Wed 12 Nov, 18:00", "Online", "scheduled", ""], ["Sun 2 Nov, 18:00", "Online", "completed", ""], ["Sun 26 Oct, 18:00", "Phone", "scheduled", ""]]
    w.table(rx + 6, 109, rw - 12, cols, rows, 20, badges=(2,), size=6)
    bx = rx + 6 + (rw - 12) * .64 + 3
    yy = 109 + 20 * 3
    w.rect(bx, yy + 4, 62, 12, NAVY, None, r=2)
    w.text(bx + 31, yy + 7.2, "Mark completed", 5.5, colors.white, "DVC-B", "c")
    w.rect(bx, 109 + 20 + 4, 30, 12, colors.white, RED, 0.6, r=2)
    w.text(bx + 15, 109 + 20 + 7.2, "Cancel", 5.5, RED, "DVC-B", "c")
    w.call(4, rx - 4, 116)
    w.call(6, bx - 4, 109 + 60 + 10)
    w.text(rx + 8, 190, "Past sessions in an ended mentorship are read-only.", 5.8, STR, "DVC-I")
    w.text(rx + 8, 200, "Closing asks for confirmation and an optional note.", 5.8, STR, "DVC-I")


# ------------------------------------------------------------------ 19 Schedule and availability
@page(19)
def p19(w):
    w.chrome("/mentor/schedule")
    x0, y0, cw, ch = w.shell("mentor", "Schedule", MN)
    w.tabs(x0, 38, ["Sessions", "Availability"], 1, w=cw)
    w.call(1, x0 - 4, 45)
    w.button(x0, 58, 14, 14, "‹", "secondary")
    w.text(x0 + 64, 61, "10 Nov – 16 Nov 2026", 6.6, NAVY, "DVC-B", "c")
    w.button(x0 + 114, 58, 14, 14, "›", "secondary")
    w.call(2, x0 - 4, 65)
    w.button(x0 + cw - 82, 58, 82, 14, "Add slots", "primary", 6)
    w.call(4, x0 + cw - 88, 65)
    gx, gy = x0, 80
    gw = cw * 0.62
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cwid = (gw - 26) / 7
    hrs = ["08", "10", "12", "14", "16", "18"]
    w.rect(gx, gy, gw, 14 + 6 * 24, colors.white, colors.HexColor("#CBD3DE"), 0.6, r=3)
    for i, d in enumerate(days):
        w.text(gx + 26 + cwid * i + cwid / 2, gy + 4, d, 6, MUTE, "DVC-B", "c")
    open_ = {(0, 4), (0, 5), (1, 4), (2, 3), (2, 4), (2, 5), (3, 4), (4, 2), (5, 0), (5, 1), (5, 2)}
    booked = {(2, 5), (3, 4), (5, 1)}
    for r, h in enumerate(hrs):
        yy = gy + 14 + r * 24
        w.line(gx, yy, gx + gw, yy, FAINT, 0.4)
        w.text(gx + 5, yy + 8, h + "-" + str(int(h) + 2), 5.6, STR)
        for c in range(7):
            xx = gx + 26 + cwid * c
            if (c, r) in booked:
                w.rect(xx + 1.5, yy + 2, cwid - 3, 20, colors.HexColor("#DFE6F2"), NAVY, 0.6, r=2)
            elif (c, r) in open_:
                w.rect(xx + 1.5, yy + 2, cwid - 3, 20, colors.HexColor("#D9EEF1"), TEAL, 0.6, r=2)
    w.call(3, gx - 4, gy + 22)
    # sessions list
    rx = gx + gw + 8
    rw = cw - gw - 8
    w.card(rx, 80, rw, 158, "Sessions this week")
    for i, (t, who, st) in enumerate([("Wed 12, 18:00", "Asha Menon", "scheduled"), ("Thu 13, 17:30", "Dev Patel", "scheduled"), ("Sat 15, 10:00", "Neha Rao", "scheduled")]):
        y = 100 + i * 44
        w.rect(rx + 5, y, rw - 10, 40, colors.white, FAINT, 0.6, r=3)
        w.bold(rx + 10, y + 4, t, 6.4, NAVY)
        w.text(rx + 10, y + 13, who, 6, MUTE)
        w.badge(rx + rw - 44, y + 4, "Scheduled" if False else "scheduled")
        w.rect(rx + 10, y + 24, 36, 11, NAVY, None, r=2)
        w.text(rx + 28, y + 26.6, "Complete", 5.4, colors.white, "DVC-B", "c")
        w.rect(rx + 50, y + 24, 28, 11, colors.white, RED, 0.6, r=2)
        w.text(rx + 64, y + 26.6, "Cancel", 5.4, RED, "DVC-B", "c")
    w.call(5, rx - 4, 106)
    w.call(6, rx + 84, 130)
    # legend
    ly = 246
    w.rect(gx, ly, 10, 8, colors.HexColor("#D9EEF1"), TEAL, 0.6, r=1.5)
    w.text(gx + 14, ly + 1, "Open slot", 6, MUTE)
    w.rect(gx + 62, ly, 10, 8, colors.HexColor("#DFE6F2"), NAVY, 0.6, r=1.5)
    w.text(gx + 76, ly + 1, "Booked session", 6, MUTE)
    w.rect(gx + 144, ly, 10, 8, colors.white, STR, 0.6, r=1.5)
    w.text(gx + 158, ly + 1, "Unavailable", 6, MUTE)
    w.call(7, gx - 4, ly + 4)
    w.text(gx, 262, "Empty: 'Add availability so mentees can book you'", 5.8, STR, "DVC-I")
    w.text(gx, 272, "Overlapping slots or a booked slot being removed: 409 SESSION_CONFLICT", 5.8, STR, "DVC-I")


# ------------------------------------------------------------------ 20 Mentor profile editing
@page(20)
def p20(w):
    w.chrome("/mentor/profile")
    x0, y0, cw, ch = w.shell("mentor", "Profile", MN)
    w.banner(x0, 40, cw, "Changes requested: please add your current employer. Submit again for review.", "warn", 14)
    w.badge(x0 + cw - 56, 43, "Draft", "draft")
    w.call(1, x0 - 4, 47)
    w.tabs(x0, 58, ["Professional", "Expertise and interests", "Capacity and availability", "Account"], 0, w=cw)
    w.call(2, x0 - 4, 65)
    lw = 238
    w.card(x0, 76, lw, 150, "Tab: Professional")
    w.inp(x0 + 8, 96, 108, "Job title", "Senior Data Scientist")
    w.inp(x0 + 122, 96, 108, "Organisation", "", error="Required")
    w.inp(x0 + 8, 124, 108, "Mentor type", "Industry professional", kind="select")
    w.inp(x0 + 122, 124, 108, "Years of experience", "6", kind="select")
    w.text(x0 + 8, 152, "Professional summary", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 161, lw - 16, 30, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 165, "I help students move into analytics...", 6, MUTE)
    w.inp(x0 + 8, 196, lw - 16, "Public profile link", "Optional, https://...", h=12)
    w.call(3, x0 - 4, 102)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 76, rw, 90, "Tab: Expertise and interests")
    for i, (nm, lv) in enumerate([("Python", "Advanced"), ("SQL", "Advanced"), ("Machine learning", "Intermediate")]):
        y = 96 + i * 16
        w.rect(rx + 8, y, rw - 16, 13, colors.white, FAINT, 0.5, r=2)
        w.text(rx + 12, y + 3.5, nm, 6, INK, "DVC-B")
        w.text(rx + 80, y + 3.5, lv + " ▾", 5.6, MUTE)
        w.text(rx + rw - 14, y + 2.6, "×", 7, STR, "DV", "c")
    w.link(rx + 8, 146, "+ Add expertise", 6)
    w.call(4, rx - 4, 102)
    w.card(rx, 172, rw, 54, "Tab: Capacity and availability")
    w.inp(rx + 8, 190, 60, "Max mentees", "5", kind="select", h=12)
    w.toggle(rx + 80, 195, True)
    w.text(rx + 104, 196, "Accepting", 6, INK, "DVC-B")
    w.call(5, rx - 4, 178)
    w.rect(x0, 234, cw, 50, colors.HexColor("#FAFBFD"), FAINT, 0.6, r=3)
    w.text(x0 + 8, 241, "Review flow: draft → pending review → approved / rejected (with note).", 6, MUTE)
    w.text(x0 + 8, 251, "Only approved profiles appear in student search. Edits to an approved profile return it to review.", 6, MUTE)
    w.button(x0 + 8, 264, 70, 15, "Save draft", "secondary")
    w.call(6, x0 + 3, 271)
    w.button(x0 + 84, 264, 100, 15, "Submit for review", "primary")
    w.call(7, x0 + 79, 271)


# ------------------------------------------------------------------ 21 Notifications (mentor)
@page(21)
def p21(w):
    w.chrome("/mentor/notifications")
    x0, y0, cw, ch = w.shell("mentor", "Notifications", MN)
    w.tabs(x0, 38, ["All", "Unread (2)"], 0, w=cw - 100)
    w.call(1, x0 - 4, 45)
    w.button(x0 + cw - 90, 38, 90, 14, "Mark all as read", "secondary", 6)
    w.call(4, x0 + cw - 96, 45)
    items = [(True, "R", "New mentoring request", "Asha Menon sent you a request. Respond within 14 days.", "2 d ago"),
             (True, "S", "Session reminder", "Wed 12 Nov, 18:00 with Asha Menon (online).", "Today"),
             (False, "F", "Feedback received", "Asha Menon rated your 2 Nov session 5 of 5.", "4 d ago"),
             (False, "P", "Profile approved", "Your mentor profile is visible to students.", "9 d ago"),
             (False, "R", "Request expired", "A request from Dev Patel expired without a response.", "20 d ago")]
    yb = notif_list(w, x0, cw, items, 60, 27)
    w.call(2, x0 - 4, 66)
    w.call(3, x0 + 24, 60)
    w.pager(x0, yb + 4)
    w.call(5, x0 - 8, yb + 10)
    w.rect(x0, yb + 24, cw, 40, colors.HexColor("#FAFBFD"), STR, 0.6, r=3, dash=(3, 2))
    w.text(x0 + cw / 2, yb + 31, "Empty state: You're all caught up  /  No notifications yet", 6.4, MUTE, "DVC-B", "c")
    w.text(x0 + cw / 2, yb + 43, "Requests, session reminders and feedback will appear here.", 6, STR, "DVC", "c")
