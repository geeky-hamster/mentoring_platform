"""Document engine: page templates, headings with numbering, TOC, captions, header/footer canvas."""
import sys
sys.path.insert(0, "/home/claude/report_build/src")
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak, Paragraph,
                                KeepTogether, Spacer, Flowable, CondPageBreak)
from reportlab.platypus.flowables import PageBreakIfNotEmpty
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from kit import *
import outline as OL
from outline import R

REPORT_TITLE = "Student Mentoring and Career Support Platform"
SHORT = "IITM BS Software Engineering - PS 2 - Software Design Report"
VERSION = "Version 1.0"
DATE = "16 October 2026"

# frame geometry
P_TOP, P_BOT = 22 * mm, 18 * mm
L_TOP, L_BOT = 20 * mm, 16 * mm
PFH = PH - P_TOP - P_BOT
LFH = LH - L_TOP - L_BOT


class Heading(Paragraph):
    NEED = {1: 120, 2: 90, 3: 80}

    def __init__(self, text, style, level, toc_text, toc=True, key=None):
        style = ParagraphStyle("hx", parent=style, keepWithNext=0)
        super().__init__(text, style)
        self.level, self.toc_text, self.in_toc, self.hkey = level, toc_text, toc, key

    def wrap(self, aW, aH):
        w, h = super().wrap(aW, aH)
        if aH < h + self.NEED[self.level] and aH < PFH - 5:
            return w, aH + 1          # not enough room below: move to the next page
        return w, h

    def split(self, aW, aH):
        return []


class SetSec(Flowable):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def wrap(self, aW, aH):
        return 0, 0

    def draw(self):
        pass


class TabCap(Flowable):
    def __init__(self, text):
        super().__init__()
        self.p = Paragraph(text, ParagraphStyle("tc", parent=S["cap"], spaceBefore=6, spaceAfter=3))

    def wrap(self, aW, aH):
        w, h = self.p.wrap(aW, aH)
        self.w, self.h = w, h
        if aH < h + 70 and aH < PFH - 5:
            return w, aH + 1
        return w, h

    def split(self, aW, aH):
        return []

    def draw(self):
        self.p.drawOn(self.canv, 0, 0)


_cnt = {"h1": 0, "h2": 0, "h3": 0, "fig": 0, "tab": 0}
_sec = {"app": None}


def H1(key):
    """Section heading; starts a new page. Number and title come from the outline."""
    n, t = OL.NUM[key], OL.TITLE[key]
    _cnt["h2"] = 0
    _cnt["h3"] = 0
    _sec["cur"] = key
    label = f"{n}  {t}" if n.isdigit() else t
    st = S["h1"]
    return [PageBreakIfNotEmpty(), Heading(label, st, 1, label, True, key)]


def H2(sub, toc_extra=True, title=None):
    """Sub-section heading by outline key 'section.sub'."""
    key = f"{_sec['cur']}.{sub}"
    _cnt["h2"] += 1
    _cnt["h3"] = 0
    n = OL.NUM[key]
    assert n == f"{OL.NUM[_sec['cur']]}.{_cnt['h2']}", (key, n, _cnt)
    t = title or OL.TITLE[key]
    label = f"{n}  {t}"
    return Heading(label, S["h2"], 2, label, True, key)


def H3(text, toc=False):
    _cnt["h3"] += 1
    n = f"{OL.NUM[_sec['cur']]}.{_cnt['h2']}.{_cnt['h3']}"
    label = f"{n}  {text}"
    return Heading(label, S["h3"], 3, label, toc)


def fig_caption(text):
    _cnt["fig"] += 1
    return Paragraph(f"<b>Figure {_cnt['fig']}.</b> {text}", S["cap"])


def tab_caption(text):
    _cnt["tab"] += 1
    return TabCap(f"<b>Table {_cnt['tab']}.</b> {text}")


def figure(flowable, caption, align="CENTER"):
    from reportlab.platypus import Table
    cap = fig_caption(caption)
    return KeepTogether([flowable, cap])


def image(path, max_w, max_h, caption=None):
    im, (w, h), s, (pw, ph) = fit_image(path, max_w, max_h)
    im.hAlign = "CENTER"
    if caption:
        return figure(im, caption)
    return im


def vfig(f, caption):
    f.hAlign = "CENTER"
    return figure(f, caption)


def NP():
    return PageBreakIfNotEmpty()


def to_land():
    return [NextPageTemplate("landscape"), PageBreak()]


def to_port():
    return [NextPageTemplate("portrait"), PageBreak()]


class NumCanvas(rl_canvas.Canvas):
    """Draws headers, footers and 'Page x of y' after the page count is known."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for st in self._pages:
            self.__dict__.update(st)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total):
        pn = self._pageNumber
        if pn == 1:
            return
        w, h = self._pagesize
        lm = MARGIN if w < h else LMARGIN
        rm = w - lm
        self.saveState()
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        top = h - (P_TOP if w < h else L_TOP) + 12
        self.line(lm, top - 3, rm, top - 3)
        self.setFont("DVC", 7.2)
        self.setFillColor(SLATE)
        self.drawString(lm, top + 2, SHORT)
        sec = getattr(self, "sec_txt", "")
        self.setFont("DVC-B", 7.2)
        self.setFillColor(NAVY)
        self.drawRightString(rm, top + 2, sec)
        bot = (P_BOT if w < h else L_BOT) - 12
        self.setStrokeColor(LINE)
        self.line(lm, bot + 9, rm, bot + 9)
        self.setFont("DVC", 7.2)
        self.setFillColor(SLATE)
        self.drawString(lm, bot, f"{VERSION}  |  {DATE}")
        self.drawRightString(rm, bot, f"Page {pn} of {total}")
        self.restoreState()


class ReportDoc(BaseDocTemplate):
    def __init__(self, fn, **kw):
        super().__init__(fn, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=P_TOP, bottomMargin=P_BOT,
                         title=f"{REPORT_TITLE} - Software Design Report", author="Project team, IITM BS Software Engineering PS 2",
                         subject="Software design report", creator="reportlab", **kw)
        self.cur_sec = ""
        cover = PageTemplate("cover", frames=[Frame(MARGIN, 40, CW, 80, id="cf", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                             onPage=self._cover, pagesize=A4)
        port = PageTemplate("portrait", frames=[Frame(MARGIN, P_BOT, CW, PFH, id="pf", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                            onPageEnd=self._end, pagesize=A4)
        land = PageTemplate("landscape", frames=[Frame(LMARGIN, L_BOT, LCW, LFH, id="lf", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)],
                            onPageEnd=self._end, pagesize=(LW, LH))
        self.addPageTemplates([cover, port, land])

    def _end(self, canv, doc):
        canv.sec_txt = self.cur_sec

    def _cover(self, canv, doc):
        draw_cover(canv)

    def afterFlowable(self, f):
        if isinstance(f, SetSec):
            self.cur_sec = f.text
        if isinstance(f, Heading):
            key = f"bm{id(f)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(f.toc_text, key, level=f.level - 1, closed=(f.level > 1))
            if f.level == 1:
                self.cur_sec = f.toc_text
            if f.level <= 2 or f.in_toc:
                self.notify("TOCEntry", (f.level - 1, f.toc_text, self.page, key))


def make_toc():
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"], S["toc2"]]
    toc.dotsMinLevel = 0
    return toc


def draw_cover(c):
    w, h = A4
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, h - 250, w, 250, stroke=0, fill=1)
    c.setFillColor(TEAL)
    c.rect(0, h - 256, w, 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("DV", 10.5)
    c.drawString(MARGIN, h - 70, "IIT MADRAS BS DEGREE PROGRAMME  |  SOFTWARE ENGINEERING  |  PROJECT PS 2")
    c.setFont("DV-B", 31)
    c.drawString(MARGIN, h - 135, "Student Mentoring and")
    c.drawString(MARGIN, h - 172, "Career Support Platform")
    c.setFont("DV", 14)
    c.setFillColor(colors.HexColor("#CFE3E8"))
    c.drawString(MARGIN, h - 208, "Software Design Report")
    # info block
    y = h - 320
    c.setFillColor(INK)
    rows = [("Document", "Software design report (architecture, UI, data, API, algorithm, delivery plan)"),
            ("Version", "1.0 - design baseline for review"), ("Date", DATE),
            ("Prepared by", "Project team: Product Manager, Backend Developer, Frontend Developer, Code Reviewer, Tester / QA"),
            ("Status of claims", "Facts about IITM sites are marked VERIFIED and cite a source; every design choice is marked PROPOSED")]
    for k, v in rows:
        c.setFont("DV-B", 8.6)
        c.setFillColor(NAVY)
        c.drawString(MARGIN, y, k.upper())
        c.setFont("DV", 9.4)
        c.setFillColor(INK)
        from reportlab.lib.utils import simpleSplit
        for i, ln in enumerate(simpleSplit(v, "DV", 9.4, CW - 110)):
            c.drawString(MARGIN + 110, y - i * 12.5, ln)
        y -= 14 + 12.5 * max(1, len(simpleSplit(v, "DV", 9.4, CW - 110))) + 6
    c.setStrokeColor(LINE)
    c.line(MARGIN, y + 6, MARGIN + CW, y + 6)
    c.setFont("DV-I", 8.4)
    c.setFillColor(SLATE)
    note = ("IIT Madras already operates an official Mentor Mentee Portal. This report does not claim to replace it. "
            "It treats that portal as a discovery item and proposes a separately specified design that can be compared against it, "
            "adopted in part, or integrated. All names, numbers and identifiers shown in diagrams and examples are illustrative sample data.")
    for i, ln in enumerate(simpleSplit(note, "DV-I", 8.4, CW)):
        c.drawString(MARGIN, y - 12 - i * 11.5, ln)
    c.restoreState()
