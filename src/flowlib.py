"""Small orthogonal flow-chart drawing library (vector, reportlab). Grid based; y grows downward internally."""
from reportlab.lib import colors
from reportlab.pdfbase.pdfmetrics import stringWidth
from kit import NAVY, TEAL, INK, AMBER, RED, GREEN

STYLE = {
    "proc": (colors.HexColor("#E3ECF7"), NAVY),
    "dec": (colors.HexColor("#FBF0D9"), colors.HexColor("#C9922B")),
    "term": (colors.HexColor("#D9EEF1"), TEAL),
    "err": (colors.HexColor("#F8E1E4"), colors.HexColor("#8E2A37")),
    "ok": (colors.HexColor("#DDF0E4"), colors.HexColor("#1F6B3F")),
    "start": (colors.white, NAVY),
    "warn": (colors.HexColor("#FBF0D9"), colors.HexColor("#C9922B")),
}
LINE = colors.HexColor("#44546A")


def wrap(text, width, size, font="DVC"):
    out = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            t = (cur + " " + word).strip()
            if stringWidth(t, font, size) <= width or not cur:
                cur = t
            else:
                out.append(cur)
                cur = word
        out.append(cur)
    return out


class Flow:
    def __init__(self, cols, rows, px=161, py=50, ox=0, oy=0, size=7.1):
        self.cols, self.rows, self.px, self.py, self.ox, self.oy, self.size = cols, rows, px, py, ox, oy, size
        self.nodes, self.edges, self.notes = {}, [], []
        self.groups, self.polys = [], []
        self.W = cols * px + ox
        self.H = rows * py + oy

    def node(self, id, col, row, text, kind="proc", w=None, h=None, dx=0, dy=0):
        w = w or (130 if kind != "dec" else 136)
        h = h or (34 if kind != "dec" else 38)
        cx = self.ox + col * self.px + self.px / 2 + dx
        cy = self.oy + row * self.py + self.py / 2 + dy
        self.nodes[id] = dict(id=id, cx=cx, cy=cy, w=w, h=h, text=text, kind=kind)

    def anode(self, id, cx, cy, text, kind="proc", w=130, h=34):
        self.nodes[id] = dict(id=id, cx=cx, cy=cy, w=w, h=h, text=text, kind=kind)

    def pt(self, col, row):
        return (self.ox + col * self.px + self.px / 2, self.oy + row * self.py + self.py / 2)

    def anchor(self, id, side):
        n = self.nodes[id]
        return {"t": (n["cx"], n["cy"] - n["h"] / 2), "b": (n["cx"], n["cy"] + n["h"] / 2),
                "l": (n["cx"] - n["w"] / 2, n["cy"]), "r": (n["cx"] + n["w"] / 2, n["cy"])}[side]

    def edge(self, a, b, label=None, sa="b", sb="t", via=(), dashed=False, lseg=None, color=None):
        self.edges.append(dict(a=a, b=b, label=label, sa=sa, sb=sb, via=list(via), dashed=dashed, lseg=lseg, color=color))

    def group(self, x, y, w, h, label, fill="#F4F8FC", stroke="#9FB3CC"):
        self.groups.append((x, y, w, h, label, fill, stroke))

    def poly(self, pts, arrow=True, dashed=False, label=None, lseg=0, color=None):
        """Absolute-coordinate polyline (design units, y down)."""
        self.polys.append(dict(pts=pts, arrow=arrow, dashed=dashed, label=label, lseg=lseg, color=color))

    def note(self, x, y, text, w=140, kind="warn"):
        self.notes.append((x, y, text, w, kind))

    # ---------------------------------------------------------------- drawing
    def _poly(self, e):
        p0 = self.anchor(e["a"], e["sa"])
        p1 = self.anchor(e["b"], e["sb"])
        mid = [self.pt(c, r) if not isinstance(c, tuple) else c for c, r in []]
        pts = [p0]
        for v in e["via"]:
            x = self.pt(v[0], 0)[0] if v[0] is not None else None
            y = self.pt(0, v[1])[1] if v[1] is not None else None
            if x is None:
                x = pts[-1][0]
            if y is None:
                y = pts[-1][1]
            pts.append((x, y))
        if not e["via"] and abs(p0[0] - p1[0]) > 0.5 and abs(p0[1] - p1[1]) > 0.5:
            if e["sa"] in "bt":
                pts.append((p0[0], p1[1]))
            else:
                pts.append((p1[0], p0[1]))
        pts.append(p1)
        return pts

    def draw(self, c, w=None, h=None):
        H = self.H
        Y = lambda y: H - y
        for x, y, w_, h_, label, fill, stroke in self.groups:
            c.setFillColor(colors.HexColor(fill))
            c.setStrokeColor(colors.HexColor(stroke))
            c.setLineWidth(0.8)
            c.roundRect(x, Y(y + h_), w_, h_, 6, stroke=1, fill=1)
            c.setFillColor(colors.HexColor("#1F3A5F"))
            c.setFont("DVC-B", 7.4)
            c.drawString(x + 8, Y(y + 11), label)
        # edges first
        for e in self.edges:
            pts = self._poly(e)
            col = e["color"] or LINE
            c.setStrokeColor(col)
            c.setFillColor(col)
            c.setLineWidth(0.8)
            if e["dashed"]:
                c.setDash(2.5, 2)
            else:
                c.setDash()
            p = c.beginPath()
            end = pts[-1]
            prev = pts[-2]
            # shorten last segment for arrowhead
            import math
            dx, dy = end[0] - prev[0], end[1] - prev[1]
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            body_end = (end[0] - ux * 4.5, end[1] - uy * 4.5)
            p.moveTo(pts[0][0], Y(pts[0][1]))
            for q in pts[1:-1]:
                p.lineTo(q[0], Y(q[1]))
            p.lineTo(body_end[0], Y(body_end[1]))
            c.drawPath(p, stroke=1, fill=0)
            c.setDash()
            ah = c.beginPath()
            ah.moveTo(end[0], Y(end[1]))
            ah.lineTo(end[0] - ux * 5.5 - uy * 2.6, Y(end[1] - uy * 5.5 + ux * 2.6))
            ah.lineTo(end[0] - ux * 5.5 + uy * 2.6, Y(end[1] - uy * 5.5 - ux * 2.6))
            ah.close()
            c.drawPath(ah, stroke=0, fill=1)
        import math
        for pl in self.polys:
            pts = pl["pts"]
            col = pl["color"] or LINE
            c.setStrokeColor(col)
            c.setFillColor(col)
            c.setLineWidth(0.8)
            c.setDash(2.5, 2) if pl["dashed"] else c.setDash()
            end, prev = pts[-1], pts[-2]
            dx, dy = end[0] - prev[0], end[1] - prev[1]
            L = math.hypot(dx, dy) or 1
            ux, uy = dx / L, dy / L
            body = pts[:-1] + [(end[0] - ux * 4.5, end[1] - uy * 4.5)] if pl["arrow"] else pts
            p = c.beginPath()
            p.moveTo(body[0][0], Y(body[0][1]))
            for q in body[1:]:
                p.lineTo(q[0], Y(q[1]))
            c.drawPath(p, stroke=1, fill=0)
            c.setDash()
            if pl["arrow"]:
                ah = c.beginPath()
                ah.moveTo(end[0], Y(end[1]))
                ah.lineTo(end[0] - ux * 5.5 - uy * 2.6, Y(end[1] - uy * 5.5 + ux * 2.6))
                ah.lineTo(end[0] - ux * 5.5 + uy * 2.6, Y(end[1] - uy * 5.5 - ux * 2.6))
                ah.close()
                c.drawPath(ah, stroke=0, fill=1)
            if pl["label"]:
                s_ = (pts[pl["lseg"]], pts[pl["lseg"] + 1])
                mx, my = (s_[0][0] + s_[1][0]) / 2, (s_[0][1] + s_[1][1]) / 2
                c.setFillColor(colors.HexColor("#1F3A5F"))
                c.setFont("DVC-I", 6.4)
                if abs(s_[0][0] - s_[1][0]) < 0.5:
                    c.drawString(mx + 4, Y(my) - 2, pl["label"])
                else:
                    c.drawCentredString(mx, Y(my - 3), pl["label"])
        # nodes
        for n in self.nodes.values():
            fill, stroke = STYLE[n["kind"]]
            x, y, w_, h_ = n["cx"] - n["w"] / 2, n["cy"] - n["h"] / 2, n["w"], n["h"]
            c.setFillColor(fill)
            c.setStrokeColor(stroke)
            c.setLineWidth(0.9)
            if n["kind"] == "dec":
                p = c.beginPath()
                p.moveTo(n["cx"], Y(y))
                p.lineTo(x + w_, Y(n["cy"]))
                p.lineTo(n["cx"], Y(y + h_))
                p.lineTo(x, Y(n["cy"]))
                p.close()
                c.drawPath(p, stroke=1, fill=1)
                tw = w_ * 0.60
            elif n["kind"] in ("term", "start"):
                c.roundRect(x, Y(y + h_), w_, h_, h_ / 2, stroke=1, fill=1)
                tw = w_ - 22
            else:
                c.roundRect(x, Y(y + h_), w_, h_, 3, stroke=1, fill=1)
                tw = w_ - 10
            lines = wrap(n["text"], tw, self.size)
            lead = self.size + 1.6
            ty = n["cy"] - (len(lines) - 1) * lead / 2
            c.setFillColor(INK)
            for i, ln in enumerate(lines):
                bold = False
                c.setFont("DVC", self.size)
                c.drawCentredString(n["cx"], Y(ty + i * lead) - self.size * 0.35, ln)
        # edge labels: beside vertical segments, above horizontal ones
        for e in self.edges:
            if not e["label"]:
                continue
            pts = self._poly(e)
            segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
            if e["lseg"] is not None:
                s_ = segs[e["lseg"]]
            else:
                s_ = max(segs, key=lambda q: abs(q[0][0] - q[1][0]) + abs(q[0][1] - q[1][1]))
            vertical = abs(s_[0][0] - s_[1][0]) < 0.5
            mx, my = (s_[0][0] + s_[1][0]) / 2, (s_[0][1] + s_[1][1]) / 2
            lines = wrap(e["label"], 110 if not vertical else 96, 6.4, "DVC-I")
            wd = max(stringWidth(l, "DVC-I", 6.4) for l in lines)
            c.setFillColor(colors.HexColor("#1F3A5F"))
            c.setFont("DVC-I", 6.4)
            lh = 7.6
            if vertical:
                if mx + 4 + wd > self.W - 2:
                    for i, ln in enumerate(lines):
                        c.drawRightString(mx - 4, Y(my - len(lines) * lh / 2 + 6 + i * lh), ln)
                else:
                    for i, ln in enumerate(lines):
                        c.drawString(mx + 4, Y(my - len(lines) * lh / 2 + 6 + i * lh), ln)
            else:
                for i, ln in enumerate(lines):
                    c.drawCentredString(mx, Y(my - 3 - (len(lines) - 1 - i) * lh), ln)
        for x, y, text, w_, kind in self.notes:
            fill = colors.HexColor("#FFF7E0")
            lines = wrap(text, w_ - 8, 6.2, "DVC-I")
            hh = len(lines) * 7.6 + 6
            c.setFillColor(fill)
            c.setStrokeColor(colors.HexColor("#C9922B"))
            c.setLineWidth(0.6)
            c.setDash(2, 1.5)
            c.rect(x, Y(y + hh), w_, hh, stroke=1, fill=1)
            c.setDash()
            c.setFillColor(colors.HexColor("#5B3A06"))
            for i, ln in enumerate(lines):
                c.setFont("DVC-I", 6.2)
                c.drawString(x + 4, Y(y + 4 + 6.2 + i * 7.6) + 1, ln)
