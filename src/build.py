"""Assemble the report: python3 build.py [out.pdf] [--sections a,b,c]"""
import sys, importlib, time
sys.path.insert(0, "/home/claude/report_build/src")
from doc import *

MODS = [("content_a", ["sec1", "sec2", "sec3"]), ("content_b", ["sec4", "sec5", "sec6"]), ("content_c", ["sec7", "sec8", "sec9"]),
        ("content_d", ["sec10", "sec11", "sec12", "sec13", "sec14", "sec15"]), ("content_e", ["appA", "appB", "appC", "appD"])]


def story(only=None):
    st = [NextPageTemplate("portrait"), PageBreak()]
    toc_title = Paragraph("Contents", S["h1"])
    st += [SetSec("Contents"), toc_title, make_toc()]
    for modname, fns in MODS:
        try:
            m = importlib.import_module(modname)
        except ImportError:
            continue
        for fn in fns:
            if hasattr(m, fn) and (only is None or fn in only):
                st += getattr(m, fn)()
    return st


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/home/claude/report_build/report.pdf"
    only = None
    for a in sys.argv:
        if a.startswith("--sections="):
            only = a.split("=")[1].split(",")
    t = time.time()
    d = ReportDoc(out)
    d.multiBuild(story(only), canvasmaker=NumCanvas)
    print("built", out, round(time.time() - t, 1), "s")
