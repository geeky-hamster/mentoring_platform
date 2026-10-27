"""Low-fidelity wireframe drawing library (vector). Design canvas is 520 x 300 units, y grows downward."""
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from kit import INK, NAVY, TEAL, SLATE, LINE, AMBER, RED, GREEN, LIGHT

DW, DH = 520, 300

BG = colors.HexColor("#F4F6F9")
PANEL = colors.white
STR = colors.HexColor("#8C96A4")
MUTE = colors.HexColor("#6B7686")
FAINT = colors.HexColor("#E6EAF0")
SKEL = colors.HexColor("#DDE2E9")
BADGE = {"pending": (colors.HexColor("#FBF0D9"), colors.HexColor("#8A5A0B")),
         "accepted": (colors.HexColor("#DDF0E4"), colors.HexColor("#1F6B3F")),
         "approved": (colors.HexColor("#DDF0E4"), colors.HexColor("#1F6B3F")),
         "declined": (colors.HexColor("#F6DDE0"), colors.HexColor("#8E2A37")),
         "rejected": (colors.HexColor("#F6DDE0"), colors.HexColor("#8E2A37")),
         "cancelled": (colors.HexColor("#E6E9EE"), colors.HexColor("#4B5563")),
         "expired": (colors.HexColor("#E6E9EE"), colors.HexColor("#4B5563")),
         "suspended": (colors.HexColor("#F6DDE0"), colors.HexColor("#8E2A37")),
         "active": (colors.HexColor("#D9EEF1"), colors.HexColor("#17606C")),
         "scheduled": (colors.HexColor("#D9EEF1"), colors.HexColor("#17606C")),
         "completed": (colors.HexColor("#DFE6F2"), colors.HexColor("#1F3A5F")),
         "ended": (colors.HexColor("#E6E9EE"), colors.HexColor("#4B5563")),
         "draft": (colors.HexColor("#E6E9EE"), colors.HexColor("#4B5563")),
         "info": (colors.HexColor("#DFE6F2"), colors.HexColor("#1F3A5F"))}


def sw(s, size=6.6, font="DVC"):
    return stringWidth(s, font, size)


def fit(s, w, size=6.6, font="DVC"):
    if sw(s, size, font) <= w:
        return s
    while s and sw(s + "...", size, font) > w:
        s = s[:-1]
    return s + "..."


class WF:
    def __init__(self, canvas):
        self.c = canvas
        self.used = []

    # ---- primitives ----
    def Y(self, y):
        return DH - y

    def rect(self, x, y, w, h, fill=None, stroke=None, lw=0.6, r=0, dash=None):
        c = self.c
        c.saveState()
        if fill is not None:
            c.setFillColor(fill)
        if stroke is not None:
            c.setStrokeColor(stroke)
            c.setLineWidth(lw)
        if dash:
            c.setDash(*dash)
        f = 1 if fill is not None else 0
        s = 1 if stroke is not None else 0
        if r:
            c.roundRect(x, self.Y(y + h), w, h, r, stroke=s, fill=f)
        else:
            c.rect(x, self.Y(y + h), w, h, stroke=s, fill=f)
        c.restoreState()

    def line(self, x1, y1, x2, y2, color=STR, lw=0.6, dash=None):
        c = self.c
        c.saveState()
        c.setStrokeColor(color)
        c.setLineWidth(lw)
        if dash:
            c.setDash(*dash)
        c.line(x1, self.Y(y1), x2, self.Y(y2))
        c.restoreState()

    def circle(self, x, y, r, fill=None, stroke=None, lw=0.6):
        c = self.c
        c.saveState()
        if fill is not None:
            c.setFillColor(fill)
        if stroke is not None:
            c.setStrokeColor(stroke)
            c.setLineWidth(lw)
        c.circle(x, self.Y(y), r, stroke=1 if stroke is not None else 0, fill=1 if fill is not None else 0)
        c.restoreState()

    def text(self, x, y, s, size=6.6, color=INK, font="DVC", align="l"):
        c = self.c
        c.saveState()
        c.setFont(font, size)
        c.setFillColor(color)
        yy = self.Y(y + size * 0.85)
        if align == "l":
            c.drawString(x, yy, s)
        elif align == "c":
            c.drawCentredString(x, yy, s)
        else:
            c.drawRightString(x, yy, s)
        c.restoreState()

    def bold(self, x, y, s, size=6.8, color=INK, align="l"):
        self.text(x, y, s, size, color, "DVC-B", align)

    def para(self, x, y, w, s, size=6.4, color=MUTE, lead=None, font="DVC", maxlines=99):
        lead = lead or size * 1.3
        words, line, yy, n = s.split(), "", y, 0
        for wd in words:
            t = (line + " " + wd).strip()
            if sw(t, size, font) <= w:
                line = t
            else:
                self.text(x, yy, line, size, color, font)
                yy += lead
                n += 1
                if n >= maxlines:
                    return yy
                line = wd
        if line:
            self.text(x, yy, line, size, color, font)
            yy += lead
        return yy

    # ---- callouts ----
    def call(self, n, x, y):
        """Numbered marker centred at (x, y); numbers map to the element table in the page specification."""
        self.used.append(n)
        self.circle(x, y, 5.3, fill=AMBER, stroke=colors.white, lw=0.8)
        self.text(x, y - 3.4, str(n), 6.2, colors.white, "DVC-B", "c")

    # ---- components ----
    def button(self, x, y, w, h, label, kind="primary", size=6.6):
        fills = {"primary": (NAVY, None, colors.white), "secondary": (colors.white, NAVY, NAVY), "ghost": (None, None, NAVY),
                 "danger": (colors.white, RED, RED), "disabled": (FAINT, None, STR), "success": (GREEN, None, colors.white)}
        fl, st, tc = fills[kind]
        self.rect(x, y, w, h, fl, st, 0.8, r=2.5)
        self.text(x + w / 2, y + (h - size) / 2 - 0.2, fit(label, w - 4, size, "DVC-B"), size, tc, "DVC-B", "c")

    def link(self, x, y, s, size=6.4):
        self.text(x, y, s, size, TEAL)
        self.line(x, y + size + 0.8, x + sw(s, size), y + size + 0.8, TEAL, 0.4)

    def inp(self, x, y, w, label=None, value="", h=14, kind="text", error=None, size=6.4):
        if label:
            self.text(x, y, label, 5.9, MUTE, "DVC-B")
            y += 8
        self.rect(x, y, w, h, colors.white, RED if error else STR, 0.7, r=2)
        if kind == "textarea":
            pass
        txt = value if kind != "password" else "•" * 9
        self.text(x + 4, y + (h - size) / 2 - 0.2, fit(txt, w - 18, size), size, MUTE if value or kind == "password" else STR)
        if kind == "select":
            self.text(x + w - 8, y + (h - size) / 2, "▾", size, MUTE, "DV", "c")
        if kind == "password":
            self.text(x + w - 16, y + (h - 5.6) / 2 - 0.2, "show", 5.2, TEAL)
        if error:
            self.text(x, y + h + 1.5, error, 5.6, RED)
        return y + h

    def chip(self, x, y, label, kind="plain", h=10, size=5.9):
        w = sw(label, size) + 9
        if kind == "sel":
            self.rect(x, y, w, h, colors.HexColor("#D9EEF1"), TEAL, 0.6, r=h / 2)
            self.text(x + w / 2, y + (h - size) / 2 - 0.2, label, size, colors.HexColor("#17606C"), "DVC-B", "c")
        else:
            self.rect(x, y, w, h, colors.white, STR, 0.5, r=h / 2)
            self.text(x + w / 2, y + (h - size) / 2 - 0.2, label, size, MUTE, "DVC", "c")
        return w

    def chips(self, x, y, labels, maxw, kind="plain", gap=3, rowh=12, sel=()):
        cx, cy = x, y
        for lb in labels:
            w = sw(lb, 5.9) + 9
            if cx + w > x + maxw:
                cx, cy = x, cy + rowh
            self.chip(cx, cy, lb, "sel" if (kind == "sel" or lb in sel) else "plain")
            cx += w + gap
        return cy + rowh

    def badge(self, x, y, label, kind=None, h=9.5, size=5.6):
        k = kind or label.lower().split()[0]
        bg, fg = BADGE.get(k, BADGE["info"])
        w = sw(label, size, "DVC-B") + 8
        self.rect(x, y, w, h, bg, None, r=h / 2)
        self.text(x + w / 2, y + (h - size) / 2 - 0.2, label, size, fg, "DVC-B", "c")
        return w

    def tabs(self, x, y, labels, active=0, w=None, h=13):
        cx = x
        for i, lb in enumerate(labels):
            tw = sw(lb, 6.6, "DVC-B" if i == active else "DVC") + 14
            self.text(cx + tw / 2, y + 2.5, lb, 6.6, NAVY if i == active else MUTE, "DVC-B" if i == active else "DVC", "c")
            if i == active:
                self.rect(cx + 2, y + h - 1.6, tw - 4, 1.8, TEAL)
            cx += tw
        self.line(x, y + h, w if w else cx, y + h, FAINT, 0.6) if False else self.line(x, y + h, x + (w if w else cx - x), y + h, FAINT, 0.6)
        return y + h + 4

    def stars(self, x, y, n, size=8, color=AMBER):
        for i in range(5):
            self.text(x + i * (size + 0.8), y, "★" if i < n else "☆", size, color if i < n else STR, "DV")

    def check(self, x, y, label, on=False, size=6.2):
        self.rect(x, y, 7, 7, colors.white, STR, 0.7, r=1.2)
        if on:
            self.text(x + 3.5, y - 0.6, "✓", 7, NAVY, "DV-B", "c")
        self.text(x + 10, y, label, size, MUTE)

    def toggle(self, x, y, on=True, label=None):
        self.rect(x, y, 17, 8.5, TEAL if on else STR, None, r=4.2)
        self.circle(x + (12.8 if on else 4.2), y + 4.25, 3.2, fill=colors.white)
        if label:
            self.text(x + 21, y + 1, label, 6.2, MUTE)

    def avatar(self, x, y, r=7, label="AM", fill=colors.HexColor("#C9D3E0")):
        self.circle(x, y, r, fill=fill)
        self.text(x, y - r * 0.38, label, r * 0.85, NAVY, "DVC-B", "c")

    def bell(self, x, y, count=None):
        self.rect(x - 4, y - 3, 8, 7, None, MUTE, 0.7, r=3)
        self.line(x - 5, y + 4.2, x + 5, y + 4.2, MUTE, 0.7)
        self.circle(x, y + 6, 1.2, fill=MUTE)
        if count:
            self.circle(x + 5, y - 4, 3.6, fill=RED)
            self.text(x + 5, y - 6.6, str(count), 4.8, colors.white, "DVC-B", "c")

    def card(self, x, y, w, h, title=None, fill=PANEL):
        self.rect(x, y, w, h, fill, colors.HexColor("#CBD3DE"), 0.6, r=3)
        if title:
            self.bold(x + 6, y + 5, title, 6.8, NAVY)
        return y + (17 if title else 4)

    def skel(self, x, y, w, rows=3, rowh=9, gap=5):
        for i in range(rows):
            self.rect(x, y + i * (rowh + gap), w * (0.95 if i % 2 else 1.0), rowh, SKEL, None, r=2)

    def imgph(self, x, y, w, h):
        self.rect(x, y, w, h, FAINT, STR, 0.5, dash=(2, 2))
        self.line(x, y, x + w, y + h, STR, 0.4)
        self.line(x + w, y, x, y + h, STR, 0.4)

    def banner(self, x, y, w, text, kind="info", h=14):
        bg = {"info": colors.HexColor("#E3ECF7"), "warn": colors.HexColor("#FBF0D9"), "error": colors.HexColor("#F8E1E4"),
              "ok": colors.HexColor("#DDF0E4")}[kind]
        fg = {"info": NAVY, "warn": colors.HexColor("#7A4E08"), "error": colors.HexColor("#8E2A37"), "ok": colors.HexColor("#1F6B3F")}[kind]
        self.rect(x, y, w, h, bg, None, r=2.5)
        self.rect(x, y, 2.6, h, fg, None)
        self.text(x + 8, y + (h - 6.2) / 2 - 0.2, fit(text, w - 12, 6.2), 6.2, fg, "DVC-B")

    def table(self, x, y, w, cols, rows, rowh=13, badges=(), hdr=True, size=6.2, actions=None, zebra=True):
        """cols: [(title, fraction)]; rows: list of lists of strings; badges: column indexes drawn as badges;
        actions: dict col_index -> list of small button labels."""
        tot = sum(f for _, f in cols)
        xs, cx = [], x
        for _, f in cols:
            xs.append(cx)
            cx += w * f / tot
        cwid = [w * f / tot for _, f in cols]
        yy = y
        if hdr:
            self.rect(x, yy, w, rowh, FAINT, None, r=2)
            for (t, _), px, pw in zip(cols, xs, cwid):
                self.text(px + 4, yy + (rowh - 6) / 2 - 0.2, fit(t, pw - 6, 6, "DVC-B"), 6, MUTE, "DVC-B")
            yy += rowh
        for ri, r in enumerate(rows):
            if zebra and ri % 2 == 1:
                self.rect(x, yy, w, rowh, colors.HexColor("#F8FAFC"), None)
            for ci, (val, px, pw) in enumerate(zip(r, xs, cwid)):
                if actions and ci in actions and val == "":
                    bx = px + 3
                    for lb in actions[ci]:
                        bw = sw(lb, 5.6, "DVC-B") + 9
                        self.rect(bx, yy + 2, bw, rowh - 4, colors.white, NAVY if lb not in ("Decline", "Cancel", "Suspend", "End") else RED, 0.6, r=2)
                        self.text(bx + bw / 2, yy + (rowh - 5.6) / 2 - 0.2, lb, 5.6, NAVY if lb not in ("Decline", "Cancel", "Suspend", "End") else RED, "DVC-B", "c")
                        bx += bw + 3
                elif ci in badges and val:
                    self.badge(px + 3, yy + (rowh - 9.5) / 2, val)
                else:
                    self.text(px + 4, yy + (rowh - size) / 2 - 0.2, fit(val, pw - 6, size), size, INK)
            self.line(x, yy + rowh, x + w, yy + rowh, FAINT, 0.4)
            yy += rowh
        return yy

    def pager(self, x, y, label="1-5 of 23"):
        self.text(x, y + 2, label, 6, MUTE)
        bx = x + 95
        for lb in ["‹", "1", "2", "3", "›"]:
            self.rect(bx, y, 11, 11, NAVY if lb == "1" else colors.white, STR, 0.5, r=2)
            self.text(bx + 5.5, y + 2, lb, 6.2, colors.white if lb == "1" else MUTE, "DVC-B", "c")
            bx += 14

    def search(self, x, y, w, ph="Search"):
        self.rect(x, y, w, 14, colors.white, STR, 0.7, r=7)
        self.circle(x + 9, y + 6.5, 3, None, MUTE, 0.7)
        self.line(x + 11, y + 8.8, x + 13.5, y + 11, MUTE, 0.8)
        self.text(x + 17, y + 3.6, ph, 6.2, STR)

    def progress(self, x, y, w, frac, h=5):
        self.rect(x, y, w, h, FAINT, None, r=h / 2)
        self.rect(x, y, w * frac, h, TEAL, None, r=h / 2)

    def empty(self, x, y, w, h, title, hint, btn=None):
        self.rect(x, y, w, h, colors.HexColor("#FAFBFD"), STR, 0.6, r=3, dash=(3, 2))
        self.circle(x + w / 2, y + h * 0.28, 7, None, STR, 0.8)
        self.text(x + w / 2, y + h * 0.28 - 3.2, "i", 7.5, STR, "DVC-B", "c")
        self.bold(x + w / 2, y + h * 0.28 + 12, title, 6.8, MUTE, "c")
        self.text(x + w / 2, y + h * 0.28 + 22, fit(hint, w - 8, 6), 6, STR, "DVC", "c")
        if btn:
            bw = sw(btn, 6.4, "DVC-B") + 16
            self.button(x + w / 2 - bw / 2, y + h * 0.28 + 33, bw, 12, btn, "secondary")

    def bars(self, x, y, w, h, vals, color=TEAL, labels=None, maxv=None, gap=4):
        maxv = maxv or max(vals)
        n = len(vals)
        bw = (w - gap * (n - 1)) / n
        self.line(x, y + h, x + w, y + h, STR, 0.5)
        for i, v in enumerate(vals):
            bh = h * v / maxv
            self.rect(x + i * (bw + gap), y + h - bh, bw, bh, color, None, r=1)
            if labels:
                self.text(x + i * (bw + gap) + bw / 2, y + h + 2, labels[i], 5.4, MUTE, "DVC", "c")

    def lineplot(self, x, y, w, h, series, colors_=(TEAL, AMBER)):
        for k in range(4):
            self.line(x, y + h * k / 3, x + w, y + h * k / 3, FAINT, 0.4)
        self.line(x, y + h, x + w, y + h, STR, 0.5)
        for si, vals in enumerate(series):
            mx = max(max(s) for s in series)
            pts = [(x + w * i / (len(vals) - 1), y + h - h * v / mx) for i, v in enumerate(vals)]
            for a, b in zip(pts, pts[1:]):
                self.line(a[0], a[1], b[0], b[1], colors_[si % len(colors_)], 1.2)
            for p in pts:
                self.circle(p[0], p[1], 1.4, fill=colors_[si % len(colors_)])

    # ---- page chrome ----
    def chrome(self, route, ribbon=True):
        self.rect(0, 0, DW, DH, BG, None)
        self.rect(0.5, 0.5, DW - 1, DH - 1, None, STR, 1.0, r=4)
        self.rect(0.5, 0.5, DW - 1, 13, colors.HexColor("#D5DBE4"), None, r=4)
        for i, col in enumerate(["#E26D6D", "#E5B84C", "#6DBE7A"]):
            self.circle(9 + i * 8, 7, 2.2, fill=colors.HexColor(col))
        self.rect(40, 3, 330, 8, colors.white, None, r=3)
        self.text(46, 3.6, fit(route, 318, 5.6), 5.6, MUTE, "DVM")
        if ribbon:
            self.text(DW - 6, 3.6, "SAMPLE DATA - illustrative only", 5.4, AMBER, "DVC-B", "r")

    def shell(self, role, active, name="Asha Menon", unread=3, sidebar=True):
        """Draws top bar + sidebar. Returns (x, y, w, h) of the content area."""
        from pages import SIDEBAR
        self.rect(1, 14, DW - 2, 21, colors.white, None)
        self.line(1, 35, DW - 1, 35, FAINT, 0.8)
        self.rect(8, 18, 14, 13, NAVY, None, r=2.5)
        self.text(15, 21.2, "MP", 6, colors.white, "DVC-B", "c")
        self.bold(27, 21.5, "Mentoring Platform", 7.4, NAVY)
        self.bell(DW - 86, 24, unread if role != "admin" else None)
        self.avatar(DW - 66, 24.5, 7, "".join(w[0] for w in name.split()[:2]).upper())
        self.text(DW - 56, 21.6, fit(name, 46, 6.4), 6.4, INK)
        self.text(DW - 10, 21.8, "▾", 6.4, MUTE, "DV", "r")
        if not sidebar:
            return 10, 41, DW - 20, DH - 48
        self.rect(1, 36, 84, DH - 37, colors.white, None)
        self.line(85, 36, 85, DH - 1, FAINT, 0.8)
        yy = 44
        for label, num in SIDEBAR[role]:
            if label == active:
                self.rect(5, yy - 3, 76, 15, colors.HexColor("#E3ECF7"), None, r=3)
                self.rect(5, yy - 3, 2.4, 15, TEAL, None)
            self.text(13, yy + 0.8, label, 6.6, NAVY if label == active else MUTE, "DVC-B" if label == active else "DVC")
            yy += 18
        self.text(13, DH - 20, "Sign out", 6.2, STR)
        return 92, 41, DW - 100, DH - 48

    def title(self, x, y, title, sub=None):
        self.bold(x, y, title, 10, NAVY)
        if sub:
            self.text(x, y + 13, sub, 6.4, MUTE)
        return y + (26 if sub else 18)
