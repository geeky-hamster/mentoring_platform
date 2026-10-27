"""UML class diagrams drawn as vector graphics (reportlab). Three figures: identity domain, lifecycle domain, service layer."""
import math
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from kit import NAVY, INK, TEAL, Fig

FS = 6.7
LH = 8.6
LINE = colors.HexColor("#33415C")
HDR = colors.HexColor("#E3ECF7")
HDR_SVC = colors.HexColor("#DDF0E4")
HDR_STUB = colors.HexColor("#F1F3F6")


class Cls:
    def __init__(self, id, x, y, w, name, attrs=(), methods=(), kind="entity", stereo=None):
        self.id, self.x, self.y, self.w, self.name = id, x, y, w, name
        self.attrs, self.methods, self.kind = list(attrs), list(methods), kind
        self.stereo = stereo or {"entity": None, "service": "service", "stub": None}[kind]
        hh = 14 + (7 if self.stereo else 0)
        ah = max(len(self.attrs), 0) * LH + 5 if self.attrs else 4
        mh = len(self.methods) * LH + 5 if self.methods else 0
        self.hh, self.ah, self.mh = hh, ah, mh
        self.h = hh + ah + mh

    def side(self, s, t=0.5):
        if s == "t":
            return (self.x + self.w * t, self.y)
        if s == "b":
            return (self.x + self.w * t, self.y + self.h)
        if s == "l":
            return (self.x, self.y + self.h * t)
        return (self.x + self.w, self.y + self.h * t)

    def at(self, s, ypt=None, xpt=None):
        if s in "lr":
            return (self.x if s == "l" else self.x + self.w, self.y + ypt)
        return (self.x + xpt, self.y if s == "t" else self.y + self.h)


class UML:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.cls, self.edges, self.notes = {}, [], []

    def add(self, *a, **k):
        c = Cls(*a, **k)
        self.cls[c.id] = c
        return c

    def edge(self, pts, kind="assoc", m1=None, m2=None, label=None, lseg=0, lpos=0.5, arrow=None, ldx=0, ldy=0, m1off=None, m2off=None):
        self.edges.append(dict(pts=pts, kind=kind, m1=m1, m2=m2, label=label, lseg=lseg, lpos=lpos, ldx=ldx, ldy=ldy, m1off=m1off, m2off=m2off))

    def note(self, x, y, w, text):
        self.notes.append((x, y, w, text))

    # ------------------------------------------------------------------
    def draw(self, c, w=None, h=None):
        H = self.H
        Y = lambda y: H - y
        for e in self.edges:
            self._edge(c, e, Y)
        for k in self.cls.values():
            self._cls(c, k, Y)
        for x, y, w_, text in self.notes:
            self._note(c, x, y, w_, text, Y)

    def _cls(self, c, k, Y):
        fill = {"entity": HDR, "service": HDR_SVC, "stub": HDR_STUB}[k.kind]
        c.setLineWidth(0.9)
        c.setStrokeColor(LINE)
        c.setFillColor(colors.white)
        c.rect(k.x, Y(k.y + k.h), k.w, k.h, stroke=1, fill=1)
        c.setFillColor(fill)
        c.rect(k.x, Y(k.y + k.hh), k.w, k.hh, stroke=1, fill=1)
        c.setFillColor(INK)
        ty = k.y + (7 if k.stereo else 0)
        if k.stereo:
            c.setFont("DVC-I", 6)
            c.drawCentredString(k.x + k.w / 2, Y(k.y + 7.5), "«" + k.stereo + "»")
        c.setFont("DVC-B", 7.6)
        c.drawCentredString(k.x + k.w / 2, Y(ty + 10.3), k.name)
        y = k.y + k.hh
        c.setFont("DVC", FS)
        for a in k.attrs:
            y += LH
            c.drawString(k.x + 4, Y(y - 2.2), a)
        if k.methods:
            y = k.y + k.hh + k.ah
            c.line(k.x, Y(y), k.x + k.w, Y(y))
            for m in k.methods:
                y += LH
                c.drawString(k.x + 4, Y(y - 2.2), m)
        elif k.attrs:
            pass

    def _note(self, c, x, y, w, text, Y):
        lines = text.split("\n")
        hh = len(lines) * 8 + 6
        c.setFillColor(colors.HexColor("#FFF7E0"))
        c.setStrokeColor(colors.HexColor("#C9922B"))
        c.setLineWidth(0.6)
        p = c.beginPath()
        p.moveTo(x, Y(y)); p.lineTo(x + w - 7, Y(y)); p.lineTo(x + w, Y(y + 7)); p.lineTo(x + w, Y(y + hh)); p.lineTo(x, Y(y + hh)); p.close()
        c.drawPath(p, stroke=1, fill=1)
        c.setFillColor(colors.HexColor("#5B3A06"))
        c.setFont("DVC", 6.3)
        for i, ln in enumerate(lines):
            c.drawString(x + 4, Y(y + 9 + i * 8) , ln)

    def _edge(self, c, e, Y):
        pts = e["pts"]
        kind = e["kind"]
        c.setStrokeColor(LINE)
        c.setFillColor(LINE)
        c.setLineWidth(0.8)
        dashed = kind in ("dep", "assocnote")
        if dashed:
            c.setDash(3, 2)
        else:
            c.setDash()
        p0, p1 = pts[0], pts[1]
        body = list(pts)
        # shorten start for diamond
        if kind in ("comp", "aggr"):
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            body[0] = (p0[0] + ux * 9, p0[1] + uy * 9)
        end, prev = pts[-1], pts[-2]
        dx, dy = end[0] - prev[0], end[1] - prev[1]
        L = math.hypot(dx, dy) or 1
        ex, ey = dx / L, dy / L
        if kind == "dep":
            body[-1] = (end[0] - ex * 2, end[1] - ey * 2)
        p = c.beginPath()
        p.moveTo(body[0][0], Y(body[0][1]))
        for q in body[1:]:
            p.lineTo(q[0], Y(q[1]))
        c.drawPath(p, stroke=1, fill=0)
        c.setDash()
        if kind in ("comp", "aggr"):
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux
            pts_d = [(p0[0], p0[1]), (p0[0] + ux * 4.5 + nx * 3, p0[1] + uy * 4.5 + ny * 3), (p0[0] + ux * 9, p0[1] + uy * 9),
                     (p0[0] + ux * 4.5 - nx * 3, p0[1] + uy * 4.5 - ny * 3)]
            d = c.beginPath()
            d.moveTo(pts_d[0][0], Y(pts_d[0][1]))
            for q in pts_d[1:]:
                d.lineTo(q[0], Y(q[1]))
            d.close()
            c.setFillColor(LINE if kind == "comp" else colors.white)
            c.drawPath(d, stroke=1, fill=1)
        if kind == "dep":
            nx, ny = -ey, ex
            a = c.beginPath()
            a.moveTo(end[0] - ex * 6 + nx * 2.8, Y(end[1] - ey * 6 + ny * 2.8))
            a.lineTo(end[0], Y(end[1]))
            a.lineTo(end[0] - ex * 6 - nx * 2.8, Y(end[1] - ey * 6 - ny * 2.8))
            c.drawPath(a, stroke=1, fill=0)
        c.setFillColor(INK)
        # multiplicities
        c.setFont("DVC", 6.6)
        if e["m1"]:
            self._mult(c, pts[0], pts[1], e["m1"], Y, e["m1off"])
        if e["m2"]:
            self._mult(c, pts[-1], pts[-2], e["m2"], Y, e["m2off"])
        if e["label"]:
            s = e["lseg"]
            a, b = pts[s], pts[s + 1]
            t = e["lpos"]
            mx, my = a[0] + (b[0] - a[0]) * t + e["ldx"], a[1] + (b[1] - a[1]) * t + e["ldy"]
            c.setFont("DVC-I", 6.5)
            c.setFillColor(colors.HexColor("#1F3A5F"))
            wd = stringWidth(e["label"], "DVC-I", 6.5)
            c.setFillColor(colors.white)
            c.rect(mx - wd / 2 - 1.5, Y(my + 3.4), wd + 3, 8, stroke=0, fill=1)
            c.setFillColor(colors.HexColor("#1F3A5F"))
            c.drawCentredString(mx, Y(my + 2.4) , e["label"])

    def _mult(self, c, p, q, text, Y, off):
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        if off:
            x, y = p[0] + off[0], p[1] + off[1]
        else:
            nx, ny = -uy, ux
            x = p[0] + ux * 9 + (nx * 6 if abs(ux) > abs(uy) else 4 * (1 if True else -1))
            y = p[1] + uy * 9 + (ny * 7 if abs(ux) > abs(uy) else 0)
        c.setFont("DVC", 6.6)
        c.setFillColor(INK)
        c.drawString(x, Y(y) - 2, text)


def fig(u):
    return Fig(u.W, u.H, lambda c, w, h: u.draw(c, w, h))
