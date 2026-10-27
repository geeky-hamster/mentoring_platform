"""Render selected wireframes to a test PDF (contact sheet) and report callout/element consistency."""
import sys
sys.path.insert(0, "/home/claude/report_build/src")
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from wirelib import WF, DW, DH
import pages
import wire_a
try:
    import wire_b
except ImportError:
    wire_b = None
try:
    import wire_c
except ImportError:
    wire_c = None

DRAW = dict(wire_a.DRAW)
if wire_b:
    DRAW.update(wire_b.DRAW)
if wire_c:
    DRAW.update(wire_c.DRAW)

sel = [int(a) for a in sys.argv[1:]] or sorted(DRAW)
out = "/home/claude/report_build/wire_test.pdf"
c = canvas.Canvas(out, pagesize=(DW * 1.5, DH * 1.5))
bad = []
for n in sel:
    w = WF(c)
    c.saveState()
    c.scale(1.5, 1.5)
    DRAW[n](w)
    c.restoreState()
    want = list(range(1, len(pages.PAGE[n]["elements"]) + 1))
    got = sorted(set(w.used))
    if got != want:
        bad.append((n, "callouts", got, "expected", want))
    c.showPage()
c.save()
print("rendered", sel, "->", out)
for b in bad:
    print("MISMATCH", b)
