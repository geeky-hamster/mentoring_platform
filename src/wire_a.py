"""Wireframes: shared and student pages (1-14)."""
from wirelib import *

DRAW = {}


def page(n):
    def deco(fn):
        DRAW[n] = fn
        return fn
    return deco


# ------------------------------------------------------------------ 1 Login
@page(1)
def p1(w):
    w.chrome("/login")
    cx = 170
    w.rect(cx, 42, 180, 232, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=4)
    w.rect(cx + 40, 52, 16, 15, NAVY, None, r=3)
    w.text(cx + 48, 55.4, "MP", 6.4, colors.white, "DVC-B", "c")
    w.bold(cx + 61, 55, "Mentoring Platform", 7, NAVY)
    w.bold(cx + 90, 78, "Sign in", 11, INK, "c")
    w.banner(cx + 12, 98, 156, "Invalid e-mail or password.", "error")
    w.call(6, cx + 5, 105)
    w.inp(cx + 12, 120, 156, "E-mail", "asha.menon@example.org")
    w.call(1, cx + 5, 123)
    w.inp(cx + 12, 150, 156, "Password", "x", kind="password")
    w.call(2, cx + 5, 153)
    w.button(cx + 12, 182, 156, 17, "Sign in", "primary", 7)
    w.call(3, cx + 5, 190)
    w.link(cx + 12, 210, "Forgot password?")
    w.call(4, cx + 5, 214)
    w.text(cx + 168, 210, "New here?", 6.2, MUTE, "DVC", "r")
    w.link(cx + 100, 224, "Create account")
    w.call(5, cx + 92, 228)
    w.text(cx + 90, 252, "Role-based redirect after sign in", 5.8, STR, "DVC-I", "c")
    # loading state inset
    w.text(380, 150, "Loading state", 6, MUTE, "DVC-B")
    w.button(380, 162, 100, 16, "◌  Signing in...", "disabled")
    w.text(380, 184, "Button disabled while E02 runs", 5.6, STR)
    w.text(30, 150, "Error state", 6, MUTE, "DVC-B")
    w.para(30, 161, 118, "Generic banner for 401, 403 (suspended) and 429 responses.", 5.8, STR)
    w.line(148, 106, cx + 12, 106, STR, 0.5, (2, 2))
    w.line(380, 170, cx + 168, 191, STR, 0.5, (2, 2))


# ------------------------------------------------------------------ 2 Registration
@page(2)
def p2(w):
    w.chrome("/register")
    cx = 150
    w.rect(cx, 38, 220, 250, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=4)
    w.bold(cx + 110, 46, "Create your account", 10, INK, "c")
    w.inp(cx + 14, 64, 192, "Full name", "Asha Menon")
    w.call(1, cx + 9, 67)
    w.inp(cx + 14, 92, 192, "E-mail", "asha.menon@example.org", error="E-mail already registered (409)")
    w.call(2, cx + 9, 95)
    w.inp(cx + 14, 130, 192, "Password (min 10 characters)", "x", kind="password")
    w.call(3, cx + 9, 133)
    w.progress(cx + 14, 155, 120, 0.55, 4)
    w.text(cx + 140, 154.2, "Strength: fair", 5.8, MUTE)
    w.text(cx + 14, 166, "Role", 5.9, MUTE, "DVC-B")
    w.rect(cx + 14, 175, 96, 14, NAVY, None, r=3)
    w.text(cx + 62, 178.4, "Student", 6.6, colors.white, "DVC-B", "c")
    w.rect(cx + 110, 175, 96, 14, colors.white, STR, 0.7, r=3)
    w.text(cx + 158, 178.4, "Mentor", 6.6, MUTE, "DVC", "c")
    w.call(4, cx + 9, 182)
    w.check(cx + 14, 198, "I accept the privacy notice", True)
    w.call(5, cx + 9, 202)
    w.button(cx + 14, 213, 192, 17, "Create account", "primary", 7)
    w.call(6, cx + 9, 221)
    w.banner(cx + 14, 237, 192, "Mentor profiles appear in search after admin approval.", "info", 13)
    w.call(7, cx + 9, 243)
    w.text(cx + 52, 262, "Already registered?", 6.2, MUTE, "DVC", "l")
    w.link(cx + 52 + sw("Already registered?", 6.2) + 5, 262, "Sign in")


# ------------------------------------------------------------------ 3 Forgot / reset
@page(3)
def p3(w):
    w.chrome("/forgot-password   |   /reset-password?token=...")
    w.rect(30, 44, 216, 230, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=4)
    w.bold(138, 52, "Forgot your password?", 9, INK, "c")
    w.text(138, 66, "Variant A - no token in the URL", 5.8, STR, "DVC-I", "c")
    w.inp(44, 86, 188, "E-mail", "asha.menon@example.org")
    w.call(1, 38, 89)
    w.button(44, 120, 188, 17, "Send reset link", "primary", 7)
    w.call(2, 38, 128)
    w.banner(44, 148, 188, "If the address is registered, a link has been sent.", "ok", 14)
    w.call(3, 38, 155)
    w.link(44, 178, "Back to sign in")
    w.text(44, 205, "Same message whether or not the e-mail exists.", 5.8, STR, "DVC-I")
    w.rect(274, 44, 216, 230, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=4)
    w.bold(382, 52, "Choose a new password", 9, INK, "c")
    w.text(382, 66, "Variant B - token present in the URL", 5.8, STR, "DVC-I", "c")
    w.inp(288, 86, 188, "New password (min 10 characters)", "x", kind="password")
    w.call(4, 282, 89)
    w.inp(288, 118, 188, "Confirm password", "x", kind="password", error="Passwords do not match")
    w.call(5, 282, 121)
    w.button(288, 160, 188, 17, "Set password", "primary", 7)
    w.call(6, 282, 168)
    w.banner(288, 190, 188, "Link expired or already used. Request a new one.", "error", 14)
    w.text(382, 214, "Shown for 400 INVALID_TOKEN", 5.8, STR, "DVC-I", "c")


# ------------------------------------------------------------------ 4 Error page
@page(4)
def p4(w):
    w.chrome("/403")
    w.rect(140, 54, 240, 150, PANEL, colors.HexColor("#CBD3DE"), 0.7, r=4)
    w.bold(260, 66, "403", 26, colors.HexColor("#9AA5B4"), "c")
    w.call(1, 156, 80)
    w.bold(260, 104, "Access denied", 10, INK, "c")
    w.para(160, 120, 200, "You do not have permission to open this page. If you think this is a mistake, contact the programme office.", 6.4, MUTE)
    w.call(2, 154, 124)
    w.button(160, 152, 98, 16, "Go to my dashboard", "primary", 6.4)
    w.call(3, 154, 160)
    w.button(264, 152, 96, 16, "Go back", "secondary", 6.4)
    w.call(4, 368, 160)
    w.text(260, 182, "Reference: req_01HZX3K8M2", 5.8, STR, "DVM", "c")
    w.call(5, 154, 186)
    w.text(260, 222, "Variants rendered by the same ErrorPage component", 6, MUTE, "DVC-B", "c")
    x = 14
    for lb, on in [("401 Session expired", False), ("403 Access denied", True), ("404 Not found", False), ("500 / network error", False)]:
        cw = 118
        w.rect(x, 236, cw, 34, colors.HexColor("#E3ECF7") if on else colors.white, STR if not on else TEAL, 0.7, r=3)
        w.bold(x + cw / 2, 241, lb.split(" ", 1)[0], 8, NAVY if on else MUTE, "c")
        w.text(x + cw / 2, 254, lb.split(" ", 1)[1], 6, MUTE, "DVC", "c")
        x += cw + 8


# ------------------------------------------------------------------ 5 Onboarding
@page(5)
def p5(w):
    w.chrome("/student/onboarding")
    x0, y0, cw, ch = w.shell("student", "", sidebar=False)
    # stepper
    xs = [x0 + 70, x0 + 250, x0 + 430]
    labels = ["About you", "Skills", "Career interests and goals"]
    w.line(xs[0], 52, xs[2], 52, STR, 0.8)
    for i, (x, lb) in enumerate(zip(xs, labels)):
        w.circle(x, 52, 7, fill=NAVY if i < 2 else colors.white, stroke=NAVY, lw=0.9)
        w.text(x, 49, "✓" if i < 1 else str(i + 1), 7, colors.white if i < 2 else NAVY, "DV-B", "c")
        w.text(x, 62, lb, 6.4, NAVY, "DVC-B", "c")
    w.call(1, x0 + 6, 52)
    cards = [(x0, "Step 1 - About you"), (x0 + 172, "Step 2 - Skills"), (x0 + 344, "Step 3 - Interests and goals")]
    for x, t in cards:
        w.card(x, 78, 160, 172, t)
    # step 1
    w.inp(x0 + 8, 100, 144, "Programme stage", "BSc degree level", kind="select")
    w.call(2, x0 + 4, 103)
    w.inp(x0 + 8, 128, 70, "Graduation year", "2027", kind="select")
    w.text(x0 + 8, 160, "Bio (optional)", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 169, 144, 52, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 173, "Final-year student interested in...", 6.2, MUTE)
    w.text(x0 + 150, 224, "36/1000", 5.6, STR, "DVC", "r")
    w.call(3, x0 + 4, 173)
    # step 2
    x = x0 + 180
    w.search(x, 100, 144, "Search skills")
    rows = [("Python", "Intermediate", True), ("SQL", "Beginner", True), ("Statistics", "Intermediate", False), ("React", "Beginner", False)]
    yy = 120
    for nm, lv, star in rows:
        w.rect(x, yy, 144, 15, colors.white, FAINT, 0.5, r=2)
        w.text(x + 5, yy + 4, nm, 6.4, INK, "DVC-B")
        w.text(x + 64, yy + 4, lv + " ▾", 6, MUTE)
        w.text(x + 136, yy + 2.5, "★" if star else "☆", 8, AMBER if star else STR, "DV", "r")
        yy += 18
    w.text(x, yy + 3, "★ = focus skill (max 5): 2 of 5 chosen", 5.8, MUTE)
    w.call(4, x - 4, 103)
    # step 3
    x = x0 + 352
    w.text(x, 98, "Career interests", 5.9, MUTE, "DVC-B")
    w.chips(x, 109, ["Data Science", "Higher Studies", "Research", "Product Mgmt", "Startups"], 144, sel=("Data Science", "Higher Studies"))
    w.call(5, x - 4, 112)
    w.text(x, 146, "Career goals (required)", 5.9, MUTE, "DVC-B")
    w.rect(x, 155, 144, 34, colors.white, STR, 0.7, r=2)
    w.text(x + 4, 159, "Move into a data science role...", 6.2, MUTE)
    w.text(x, 193, "Guidance needs", 5.9, MUTE, "DVC-B")
    w.rect(x, 202, 144, 34, colors.white, STR, 0.7, r=2)
    w.text(x + 4, 206, "Portfolio and interview prep", 6.2, MUTE)
    w.call(6, x - 4, 158)
    w.button(x0, 262, 60, 16, "Back", "secondary")
    w.button(x0 + 70, 262, 110, 16, "Save and continue", "primary")
    w.button(x0 + 344, 262, 60, 16, "Finish", "success")
    w.call(7, x0 - 3, 270)


# ------------------------------------------------------------------ 6 Student dashboard
@page(6)
def p6(w):
    w.chrome("/student/dashboard")
    x0, y0, cw, ch = w.shell("student", "Dashboard")
    w.bold(x0, 42, "Welcome back, Asha", 10, NAVY)
    w.banner(x0, 60, cw, "Your profile is 70% complete. Finish it to send mentoring requests.", "warn", 14)
    w.link(x0 + cw - 70, 64, "Complete profile", 6.2)
    w.call(1, x0 - 4, 67)
    cwid = (cw - 16) / 3
    for i, (lb, v) in enumerate([("Pending requests", "1"), ("Active mentorships", "1"), ("Upcoming sessions", "2")]):
        x = x0 + i * (cwid + 8)
        w.card(x, 80, cwid, 34)
        w.bold(x + 8, 85, v, 12, NAVY)
        w.text(x + 26, 90, lb, 6.4, MUTE)
    w.call(2, x0 - 4, 97)
    lw = 204
    ya = 120
    w.card(x0, ya, lw, 52, "Next session")
    w.text(x0 + 8, ya + 20, "Wed 12 Nov, 6:00 PM  ·  Online", 6.4, INK)
    w.text(x0 + 8, ya + 31, "with Rohan Iyer", 6.2, MUTE)
    w.button(x0 + lw - 62, ya + 30, 54, 14, "Open", "secondary", 6)
    w.call(3, x0 - 4, ya + 6)
    yb = ya + 58
    w.card(x0, yb, lw, 74, "My requests")
    w.table(x0 + 6, yb + 17, lw - 12, [("Mentor", 0.4), ("Sent", 0.25), ("Status", 0.35)],
            [["Meera Nair", "20 Oct", "pending"], ["Rohan Iyer", "14 Oct", "accepted"], ["K. Rao", "2 Oct", "declined"]], 11.5, badges=(2,), size=5.9)
    w.call(5, x0 - 4, yb + 6)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, ya, rw, 132, "Recommended mentors")
    for i, (nm, sc, why) in enumerate([("Rohan Iyer", "78", "Covers 3 of 3 focus skills"), ("Meera Nair", "77", "Matches both interests"), ("Karthik Rao", "48", "Python, SQL basics")]):
        y = ya + 19 + i * 33
        w.avatar(rx + 14, y + 11, 7, "".join(p[0] for p in nm.split()))
        w.bold(rx + 26, y + 2, nm, 6.6)
        w.text(rx + 26, y + 12, why, 5.8, MUTE)
        w.badge(rx + rw - 36, y + 3, sc, "approved")
        w.line(rx + 6, y + 27, rx + rw - 6, y + 27, FAINT, 0.5)
    w.link(rx + rw - 52, ya + 3, "See all", 6)
    w.call(4, rx - 4, ya + 6)
    yc = yb + 80
    w.card(x0, yc, cw, 36, "Notifications")
    w.text(x0 + 8, yc + 17, "● Rohan Iyer accepted your request   ·   2 h ago", 6.2, INK)
    w.text(x0 + 8, yc + 26, "○ Session reminder: Wed 12 Nov, 6:00 PM", 6.2, MUTE)
    w.call(6, x0 - 4, yc + 6)


# ------------------------------------------------------------------ 7 Discovery
def mentor_card(w, x, y, cw, nm, sub, yrs, chips, match=None, show_btn=True, call=None):
    w.card(x, y, cw, 72)
    w.avatar(x + 14, y + 16, 8, "".join(p[0] for p in nm.split()))
    w.bold(x + 27, y + 7, nm, 6.8)
    w.text(x + 27, y + 17, fit(sub, cw - 70, 5.8), 5.8, MUTE)
    w.text(x + 27, y + 26, yrs, 5.8, MUTE)
    if match:
        w.badge(x + cw - 42, y + 6, "Match " + match, "approved")
    w.chips(x + 8, y + 38, chips, cw - 14)
    if show_btn:
        w.button(x + 8, y + 54, 46, 13, "View profile", "secondary", 5.8)
        w.button(x + 58, y + 54, 40, 13, "Request", "primary", 5.8)
    if call:
        w.call(call[0], x - 1, y + 4)


@page(7)
def p7(w):
    w.chrome("/student/mentors")
    x0, y0, cw, ch = w.shell("student", "Find mentors")
    w.tabs(x0, 40, ["Recommended", "All mentors"], 0, w=cw)
    w.call(1, x0 - 4, 47)
    w.search(x0 + 120, 40, 150, "Search title, organisation, bio")
    w.call(2, x0 + 114, 47)
    w.text(x0 + cw - 70, 43, "Sort: Newest ▾", 6.2, MUTE)
    w.call(4, x0 + cw - 78, 47)
    fx, fy = x0, 62
    w.rect(fx, fy, 108, 225, PANEL, colors.HexColor("#CBD3DE"), 0.6, r=3)
    w.bold(fx + 6, fy + 5, "Filters", 6.8, NAVY)
    w.text(fx + 6, fy + 19, "Skills", 5.9, MUTE, "DVC-B")
    for i, (lb, on) in enumerate([("Python", True), ("SQL", False), ("Machine Learning", True)]):
        w.check(fx + 6, fy + 29 + i * 11, lb, on, 6)
    w.text(fx + 6, fy + 66, "Career pathway", 5.9, MUTE, "DVC-B")
    for i, (lb, on) in enumerate([("Data Science", True), ("Higher Studies", False)]):
        w.check(fx + 6, fy + 76 + i * 11, lb, on, 6)
    w.inp(fx + 6, fy + 102, 94, "Mentor type", "Any", kind="select", h=12)
    w.text(fx + 6, fy + 130, "Min. experience: 3 yrs", 5.9, MUTE, "DVC-B")
    w.rect(fx + 6, fy + 141, 94, 2, STR, None)
    w.circle(fx + 40, fy + 142, 3.5, fill=TEAL)
    w.toggle(fx + 6, fy + 154, True, "Accepting mentees")
    w.button(fx + 6, fy + 174, 94, 13, "Apply filters", "primary", 6)
    w.button(fx + 6, fy + 191, 94, 13, "Clear", "secondary", 6)
    w.call(3, fx - 4, fy + 6)
    gx = x0 + 116
    gw = (cw - 116 - 8) / 2
    mentor_card(w, gx, 62, gw, "Rohan Iyer", "Sr Data Scientist, Example Analytics", "6 yrs  ·  Alumnus", ["Python", "SQL", "ML"], "78", call=(5, 0))
    w.call(6, gx + 9, 116)
    w.call(7, gx + 60, 116)
    mentor_card(w, gx + gw + 8, 62, gw, "Meera Nair", "Research Engineer, Example Lab", "5 yrs  ·  Alumna", ["ML", "Statistics"], "77")
    mentor_card(w, gx, 140, gw, "Karthik Rao", "Software Engineer, Example Soft", "4 yrs  ·  Alumnus", ["Python", "SQL"], "48")
    # loading skeleton card
    sx = gx + gw + 8
    w.card(sx, 140, gw, 72)
    w.skel(sx + 8, 148, gw - 16, 3, 8, 6)
    w.text(sx + gw / 2, 202, "loading state (skeleton)", 5.4, STR, "DVC-I", "c")
    w.rect(gx, 218, cw - 116, 50, colors.HexColor("#FAFBFD"), STR, 0.6, r=3, dash=(3, 2))
    w.text(gx + (cw - 116) / 2, 224, "Empty state: No mentors match your filters", 6.4, MUTE, "DVC-B", "c")
    w.button(gx + (cw - 116) / 2 - 30, 238, 60, 12, "Clear filters", "secondary", 6)
    w.pager(gx, 276)
    w.call(8, gx - 8, 282)


# ------------------------------------------------------------------ 8 Mentor details
@page(8)
def p8(w):
    w.chrome("/student/mentors/9d4c7e52-...")
    x0, y0, cw, ch = w.shell("student", "Find mentors")
    lw = 286
    w.card(x0, 42, lw, 62)
    w.imgph(x0 + 8, 50, 40, 40)
    w.bold(x0 + 56, 50, "Rohan Iyer", 10, NAVY)
    w.text(x0 + 56, 64, "Senior Data Scientist, Example Analytics Pvt Ltd", 6.4, INK)
    w.text(x0 + 56, 75, "6 years experience  ·  Graduated 2020", 6, MUTE)
    w.badge(x0 + 56, 87, "Alumnus", "completed")
    w.badge(x0 + 96, 87, "Accepting mentees", "approved")
    w.call(1, x0 - 4, 48)
    w.card(x0, 110, lw, 50, "About")
    w.para(x0 + 8, 128, lw - 16, "Moved from the programme into data science. Happy to discuss portfolios, interview preparation and applying for master's programmes.", 6.2, MUTE, 8, maxlines=3)
    w.call(2, x0 - 4, 116)
    w.card(x0, 166, lw, 48, "Expertise")
    w.chips(x0 + 8, 184, ["Python - Advanced", "SQL - Advanced", "Machine Learning - Intermediate"], lw - 16)
    w.call(3, x0 - 4, 172)
    w.card(x0, 220, lw, 40, "Career pathways")
    w.chips(x0 + 8, 238, ["Data Science", "Higher Studies"], lw - 16, "sel")
    w.call(4, x0 - 4, 226)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 42, rw, 52, "Rating")
    w.stars(rx + 8, 58, 4, 9)
    w.text(rx + 8, 72, "4.5 (12 ratings)", 6.2, MUTE)
    w.text(rx + 8, 82, "Hidden until 3+ ratings", 5.4, STR, "DVC-I")
    w.call(5, rx - 4, 48)
    w.card(rx, 100, rw, 58, "Availability")
    w.text(rx + 8, 118, "4 open slots, next 14 days", 6.2, INK)
    w.text(rx + 8, 129, "2 of 5 mentee spots free", 6.2, INK)
    w.text(rx + 8, 141, "Exact times shown after you", 5.4, STR, "DVC-I")
    w.text(rx + 8, 149, "start a mentorship", 5.4, STR, "DVC-I")
    w.call(6, rx - 4, 106)
    w.button(rx, 166, rw, 17, "Request mentoring", "primary", 6.8)
    w.call(7, rx - 4, 174)
    w.button(rx, 188, rw, 13, "Disabled when pending / full", "disabled", 5.6)
    w.link(rx, 212, "‹ Back to results", 6.4)
    w.call(8, rx - 4, 216)


# ------------------------------------------------------------------ 9 Send request
@page(9)
def p9(w):
    w.chrome("/student/mentors/9d4c7e52-.../request")
    x0, y0, cw, ch = w.shell("student", "Find mentors")
    w.bold(x0, 40, "Request mentoring from Rohan Iyer", 9.5, NAVY)
    lw = 280
    w.card(x0, 60, lw, 228)
    w.banner(x0 + 8, 66, lw - 16, "Example error: pending request limit reached (409).", "warn", 12)
    w.text(x0 + 8, 85, "Career goal *", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 94, lw - 16, 46, colors.white, STR, 0.7, r=2)
    w.para(x0 + 12, 98, lw - 24, "I want to move into a data science role after graduation and need advice on building a portfolio.", 6.2, MUTE, 8)
    w.text(x0 + lw - 10, 143, "98 / 1000  (min 20)", 5.6, STR, "DVC", "r")
    w.call(2, x0 + 3, 98)
    w.text(x0 + 8, 156, "Message (optional)", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 165, lw - 16, 30, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 169, "Hello Rohan, ...", 6.2, MUTE)
    w.call(3, x0 + 3, 170)
    w.rect(x0 + 8, 201, lw - 16, 36, FAINT, None, r=2)
    w.text(x0 + 12, 205, "Mentor will see: BSc level, 2027 · Python, SQL, ML · Data Science", 5.8, MUTE)
    w.link(x0 + 12, 217, "Edit profile", 6)
    w.call(4, x0 + 3, 208)
    w.text(x0 + 8, 243, "Requests expire after 14 days. Maximum 3 pending requests.", 5.8, STR, "DVC-I")
    w.call(5, x0 + 1, 246)
    w.button(x0 + 8, 262, 110, 17, "Send request", "primary", 7)
    w.call(6, x0 + 3, 270)
    w.link(x0 + 140, 266, "Cancel", 6.6)
    w.call(7, x0 + 126, 270)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 60, rw, 90)
    w.call(1, rx - 4, 66)
    w.avatar(rx + 18, 80, 9, "RI")
    w.bold(rx + 32, 72, "Rohan Iyer", 7)
    w.text(rx + 32, 82, "Sr Data Scientist", 5.8, MUTE)
    w.text(rx + 8, 100, "Example Analytics Pvt Ltd", 6, INK)
    w.chips(rx + 8, 112, ["Python", "SQL", "ML"], rw - 12)
    w.text(rx + 8, 130, "2 mentee spots free", 5.8, MUTE)
    w.text(rx + 8, 160, "On success: toast and redirect to", 5.8, STR, "DVC-I")
    w.text(rx + 8, 169, "My requests (page 10).", 5.8, STR, "DVC-I")


# ------------------------------------------------------------------ 10 My requests
@page(10)
def p10(w):
    w.chrome("/student/requests")
    x0, y0, cw, ch = w.shell("student", "My requests")
    w.tabs(x0, 40, ["All (6)", "Pending (1)", "Accepted (1)", "Declined (2)", "Cancelled / expired (2)"], 0, w=cw)
    w.call(1, x0 - 4, 47)
    cols = [("Mentor", .15), ("Career goal", .27), ("Sent", .09), ("Status", .12), ("Decision / expiry", .14), ("Actions", .23)]
    rows = [["Meera Nair", "Portfolio and research paths...", "20 Oct", "pending", "expires 3 Nov", ""],
            ["Rohan Iyer", "Move into data science roles...", "14 Oct", "accepted", "15 Oct", ""],
            ["Karthik Rao", "Advice on MS applications...", "2 Oct", "declined", "4 Oct", ""],
            ["S. Patel", "Start-up careers...", "10 Sep", "expired", "24 Sep", ""],
            ["L. Pillai", "Interview preparation...", "1 Sep", "cancelled", "2 Sep", ""]]
    rh = 22
    yy = w.table(x0, 64, cw, cols, rows, rh, badges=(3,), size=6.2)
    ry = 64 + rh
    labs = [["View", "Cancel"], ["View", "Open mentorship"], ["View"], ["View"], ["View"]]
    ax = x0 + cw * (.15 + .27 + .09 + .12 + .14) + 3
    for i, ls in enumerate(labs):
        bx = ax
        yb = ry + i * rh + 5
        for lb in ls:
            bw = sw(lb, 5.6, "DVC-B") + 9
            red = lb == "Cancel"
            w.rect(bx, yb, bw, 12, colors.white, RED if red else NAVY, 0.6, r=2)
            w.text(bx + bw / 2, yb + 3, lb, 5.6, RED if red else NAVY, "DVC-B", "c")
            bx += bw + 3
    w.call(2, x0 - 4, 78)
    w.call(3, ax, ry + 5)
    w.call(4, ax + 27, ry + 5)
    w.call(5, ax + 27, ry + rh + 5)
    w.pager(x0, yy + 8)
    w.call(6, x0 - 4, yy + 14)
    w.rect(x0, yy + 30, cw, 62, colors.HexColor("#FAFBFD"), STR, 0.6, r=3, dash=(3, 2))
    w.text(x0 + cw / 2, yy + 36, "Empty state (Pending tab with no rows)", 6.4, MUTE, "DVC-B", "c")
    w.text(x0 + cw / 2, yy + 47, "You have no pending requests.", 6, STR, "DVC", "c")
    w.button(x0 + cw / 2 - 30, yy + 62, 60, 13, "Find a mentor", "secondary", 6)


# ------------------------------------------------------------------ 11 Mentorship details
@page(11)
def p11(w):
    w.chrome("/student/mentorships/5a9c2e7f-...")
    x0, y0, cw, ch = w.shell("student", "My mentorship")
    w.bold(x0, 40, "Mentorship with Rohan Iyer", 9.5, NAVY)
    w.inp(x0 + cw - 142, 38, 142, None, "Rohan Iyer (active)", h=13, kind="select", size=6)
    w.call(1, x0 + cw - 148, 44)
    w.card(x0, 58, cw, 46)
    w.imgph(x0 + 8, 64, 34, 34)
    w.bold(x0 + 50, 65, "Rohan Iyer", 8.5, NAVY)
    w.text(x0 + 50, 77, "Senior Data Scientist, Example Analytics Pvt Ltd", 6.2, INK)
    w.badge(x0 + 50, 88, "Active")
    w.text(x0 + 84, 89, "Started 22 Oct 2026", 6, MUTE)
    w.link(x0 + cw - 90, 66, "View mentor profile", 6.2)
    w.call(2, x0 - 4, 64)
    w.tabs(x0, 108, ["Overview", "Sessions and feedback"], 0, w=cw)
    w.call(8, x0 - 4, 115)
    lw = 250
    w.card(x0, 128, lw, 50, "Goal from your request")
    w.para(x0 + 8, 146, lw - 16, "I want to move into a data science role after graduation and need advice on building a portfolio.", 6.1, MUTE, 7.6, maxlines=2)
    w.call(3, x0 - 4, 134)
    w.card(x0, 184, lw, 100, "Upcoming sessions")
    w.table(x0 + 6, 203, lw - 12, [("When", .38), ("Mode", .2), ("Link", .22), ("", .2)],
            [["Wed 12 Nov, 18:00", "Online", "Join link", ""], ["Wed 26 Nov, 18:00", "Phone", "-", ""]], 15, size=5.9, actions={3: ["Cancel"]})
    w.text(x0 + 8, 272, "Empty state: 'No upcoming sessions' + Schedule session", 5.6, STR, "DVC-I")
    w.call(5, x0 - 4, 190)
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 128, rw, 50, "Progress")
    w.text(rx + 8, 146, "Completed: 3   Scheduled: 2", 6.4, INK)
    w.text(rx + 8, 157, "Last session: 2 Nov 2026", 6, MUTE)
    w.progress(rx + 8, 168, rw - 16, 0.5, 4)
    w.call(4, rx - 4, 134)
    w.card(rx, 184, rw, 100, "Actions")
    w.button(rx + 8, 205, rw - 16, 17, "Schedule session", "primary")
    w.call(6, rx + 3, 213)
    w.button(rx + 8, 230, rw - 16, 17, "End mentorship", "danger")
    w.call(7, rx + 3, 238)
    w.text(rx + 8, 254, "Disabled when the mentorship", 5.6, STR, "DVC-I")
    w.text(rx + 8, 262, "is not active (409).", 5.6, STR, "DVC-I")


# ------------------------------------------------------------------ 12 Session history and feedback
@page(12)
def p12(w):
    w.chrome("/student/mentorships/5a9c2e7f-.../sessions")
    x0, y0, cw, ch = w.shell("student", "My mentorship")
    w.tabs(x0, 38, ["Overview", "Sessions and feedback"], 1, w=cw)
    x = x0
    for i, lb in enumerate(["All", "Scheduled", "Completed", "Cancelled"]):
        tw = sw(lb, 6.2, "DVC-B") + 12
        w.rect(x, 60, tw, 12, NAVY if i == 0 else colors.white, STR, 0.5, r=6)
        w.text(x + tw / 2, 62.6, lb, 6.2, colors.white if i == 0 else MUTE, "DVC-B", "c")
        x += tw + 4
    w.call(1, x0 - 4, 66)
    w.button(x0 + cw - 76, 59, 76, 14, "Schedule session", "primary", 6)
    w.call(7, x0 + cw - 82, 66)
    cols = [("Date and time", .19), ("Mode", .10), ("Status", .13), ("Notes", .27), ("Feedback", .16), ("Actions", .15)]
    rows = [["Wed 12 Nov, 18:00", "Online", "scheduled", "Agenda: portfolio review", "-", ""],
            ["Sun 2 Nov, 18:00", "Online", "completed", "Reviewed two projects  ▾", "Rated 5/5", ""],
            ["Sun 26 Oct, 18:00", "Phone", "completed", "Interview preparation tips", "Not rated", ""],
            ["Mon 20 Oct, 17:00", "Online", "cancelled", "-", "-", ""]]
    rh = 20
    yy = w.table(x0, 78, cw, cols, rows, rh, badges=(2,), size=6)
    ax = x0 + cw * (.19 + .10 + .13 + .27 + .16) + 3
    w.rect(ax, 78 + rh + 4 - rh, 0, 0)
    # action buttons
    by = 78 + rh
    w.rect(ax, by + 4, 34, 12, colors.white, RED, 0.6, r=2)
    w.text(ax + 17, by + 7, "Cancel", 5.6, RED, "DVC-B", "c")
    w.rect(ax, by + 2 * rh + 4, 26, 12, NAVY, None, r=2)
    w.text(ax + 13, by + 2 * rh + 7, "Rate", 5.6, colors.white, "DVC-B", "c")
    w.call(2, x0 - 4, 91)
    w.call(3, x0 + cw * .625, by + rh + 10)
    w.call(4, ax - 2, by + 4)
    w.call(5, ax - 2, by + 2 * rh + 4)
    w.call(6, x0 + cw * .69 - 2, by + 2 * rh + 10)
    # feedback dialog inset
    dx, dy = x0 + cw / 2 - 118, 176
    w.rect(dx + 3, dy + 3, 236, 110, colors.HexColor("#C9D0DA"), None, r=4)
    w.rect(dx, dy, 236, 110, PANEL, STR, 0.8, r=4)
    w.bold(dx + 10, dy + 7, "Rate this session  (FeedbackDialog)", 7, NAVY)
    w.stars(dx + 10, dy + 22, 4, 12)
    w.rect(dx + 10, dy + 42, 216, 30, colors.white, STR, 0.7, r=2)
    w.text(dx + 14, dy + 46, "Optional comment (max 1000 characters)", 6, STR)
    w.button(dx + 10, dy + 82, 60, 16, "Submit", "primary")
    w.button(dx + 76, dy + 82, 60, 16, "Cancel", "secondary")
    w.text(dx + 226, dy + 86, "One entry per session", 5.6, STR, "DVC-I", "r")


# ------------------------------------------------------------------ 13 Edit student profile
@page(13)
def p13(w):
    w.chrome("/student/profile")
    x0, y0, cw, ch = w.shell("student", "Profile")
    w.tabs(x0, 38, ["Profile", "Skills and interests", "Account"], 0, w=cw)
    w.call(1, x0 - 4, 45)
    lw = 226
    w.card(x0, 60, lw, 226, "Tab: Profile")
    w.inp(x0 + 8, 80, 102, "Full name", "Asha Menon")
    w.inp(x0 + 116, 80, 102, "Programme stage", "BSc degree", kind="select")
    w.inp(x0 + 8, 108, 102, "Graduation year", "2027", kind="select")
    w.text(x0 + 8, 138, "Bio", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 147, lw - 16, 24, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 151, "Final-year student interested in...", 6, MUTE)
    w.text(x0 + 8, 176, "Career goals", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 185, lw - 16, 24, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 189, "Move into a data science role...", 6, MUTE)
    w.text(x0 + 8, 214, "Guidance needs", 5.9, MUTE, "DVC-B")
    w.rect(x0 + 8, 223, lw - 16, 22, colors.white, STR, 0.7, r=2)
    w.text(x0 + 12, 227, "Portfolio and interview prep", 6, MUTE)
    w.call(2, x0 - 4, 86)
    w.button(x0 + 8, 258, 84, 17, "Save changes", "primary")
    w.call(6, x0 + 3, 266)
    w.text(x0 + 100, 262, "● Unsaved changes", 6, AMBER, "DVC-B")
    rx = x0 + lw + 8
    rw = cw - lw - 8
    w.card(rx, 60, rw, 124, "Tab: Skills and interests")
    for i, (nm, lv, st) in enumerate([("Python", "Intermediate", True), ("SQL", "Beginner", True), ("Statistics", "Intermediate", False)]):
        y = 80 + i * 17
        w.rect(rx + 8, y, rw - 16, 14, colors.white, FAINT, 0.5, r=2)
        w.text(rx + 12, y + 3.5, nm, 6, INK, "DVC-B")
        w.text(rx + 62, y + 3.5, lv + " ▾", 5.6, MUTE)
        w.text(rx + rw - 22, y + 2, "★" if st else "☆", 7.5, AMBER if st else STR, "DV")
        w.text(rx + rw - 12, y + 3, "×", 7, STR, "DV", "c")
    w.call(3, rx - 4, 82)
    w.text(rx + 8, 134, "Career interests", 5.9, MUTE, "DVC-B")
    w.chips(rx + 8, 145, ["Data Science", "Higher Studies", "Research"], rw - 16, sel=("Data Science", "Higher Studies"))
    w.call(4, rx - 4, 148)
    w.card(rx, 192, rw, 94, "Tab: Account")
    w.inp(rx + 8, 210, rw - 16, "Current password", "x", kind="password", h=12)
    w.inp(rx + 8, 234, rw - 16, "New password", "x", kind="password", h=12)
    w.button(rx + 8, 262, 90, 15, "Change password", "secondary", 6)
    w.call(5, rx - 4, 214)


# ------------------------------------------------------------------ 14 Notifications
def notif_list(w, x0, cw, items, y=62, rh=27):
    for i, (unread, kind, title, msg, when) in enumerate(items):
        yy = y + i * rh
        w.rect(x0, yy, cw, rh - 3, colors.HexColor("#EEF4FB") if unread else colors.white, FAINT, 0.5, r=3)
        w.circle(x0 + 8, yy + (rh - 3) / 2, 2.4, fill=TEAL if unread else None, stroke=None if unread else STR, lw=0.6)
        w.rect(x0 + 17, yy + 5, 15, 15, colors.HexColor("#DFE6F2"), None, r=3)
        w.text(x0 + 24.5, yy + 8.4, kind, 6.4, NAVY, "DVC-B", "c")
        w.bold(x0 + 38, yy + 4.5, title, 6.4, INK if unread else MUTE)
        w.text(x0 + 38, yy + 14, fit(msg, cw - 110, 5.9), 5.9, MUTE)
        w.text(x0 + cw - 8, yy + 8, when, 5.8, STR, "DVC", "r")
    return y + len(items) * rh


@page(14)
def p14(w):
    w.chrome("/student/notifications")
    x0, y0, cw, ch = w.shell("student", "Notifications")
    w.tabs(x0, 38, ["All", "Unread (3)"], 0, w=cw - 100)
    w.call(1, x0 - 4, 45)
    w.button(x0 + cw - 90, 38, 90, 14, "Mark all as read", "secondary", 6)
    w.call(4, x0 + cw - 96, 45)
    items = [(True, "R", "Request accepted", "Rohan Iyer accepted your mentoring request.", "2 h ago"),
             (True, "S", "Session scheduled", "Wed 12 Nov, 18:00 with Rohan Iyer (online).", "Yesterday"),
             (True, "F", "Feedback requested", "How was your session on 2 Nov? Rate it within 14 days.", "3 d ago"),
             (False, "R", "Request declined", "Karthik Rao declined your request. Reason shown in the request.", "12 d ago"),
             (False, "S", "Session cancelled", "Mon 20 Oct, 17:00 was cancelled by the mentor.", "26 d ago")]
    yb = notif_list(w, x0, cw, items, 60, 27)
    w.call(2, x0 - 4, 66)
    w.call(3, x0 + 24, 60)
    w.pager(x0, yb + 4)
    w.call(5, x0 - 8, yb + 10)
    w.rect(x0, yb + 24, cw, 40, colors.HexColor("#FAFBFD"), STR, 0.6, r=3, dash=(3, 2))
    w.text(x0 + cw / 2, yb + 31, "Empty state (Unread tab): You're all caught up", 6.4, MUTE, "DVC-B", "c")
    w.text(x0 + cw / 2, yb + 43, "New events about requests and sessions will appear here.", 6, STR, "DVC", "c")
