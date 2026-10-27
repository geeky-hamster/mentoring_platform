"""Shared design kit: palette, fonts, paragraph styles, table helpers, figure flowable."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Paragraph, Table, TableStyle, Spacer, Flowable,
                                Preformatted, KeepTogether, PageBreak, Image)
from xml.sax.saxutils import escape

FD = "/usr/share/fonts/truetype/dejavu/"
for name, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
                ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf"),
                ("DVC", "DejaVuSansCondensed.ttf"), ("DVC-B", "DejaVuSansCondensed-Bold.ttf"),
                ("DVC-I", "DejaVuSansCondensed-Oblique.ttf"), ("DVC-BI", "DejaVuSansCondensed-BoldOblique.ttf"),
                ("DVM", "DejaVuSansMono.ttf"), ("DVM-B", "DejaVuSansMono-Bold.ttf")]:
    pdfmetrics.registerFont(TTFont(name, FD + f))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
pdfmetrics.registerFontFamily("DVC", normal="DVC", bold="DVC-B", italic="DVC-I", boldItalic="DVC-BI")
pdfmetrics.registerFontFamily("DVM", normal="DVM", bold="DVM-B", italic="DVM", boldItalic="DVM-B")

# ---- palette (restrained) ----
NAVY = colors.HexColor("#1F3A5F")
TEAL = colors.HexColor("#2A7F8E")
SLATE = colors.HexColor("#5A6472")
LIGHT = colors.HexColor("#EEF2F6")
LIGHTER = colors.HexColor("#F7F9FB")
LINE = colors.HexColor("#C5CED8")
AMBER = colors.HexColor("#B7791F")
AMBER_L = colors.HexColor("#FBF3E4")
RED = colors.HexColor("#B23A48")
GREEN = colors.HexColor("#2F7D4F")
INK = colors.HexColor("#1C2430")
CODEBG = colors.HexColor("#F3F5F8")

PW, PH = A4
LW, LH = landscape(A4)
MARGIN = 20 * mm
CW = PW - 2 * MARGIN            # portrait content width  (~482pt)
LMARGIN = 18 * mm
LCW = LW - 2 * LMARGIN          # landscape content width (~739pt)

S = {}
S["body"] = ParagraphStyle("body", fontName="DV", fontSize=8.8, leading=12.6, textColor=INK, spaceAfter=5)
S["bodyj"] = ParagraphStyle("bodyj", parent=S["body"])
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=7.6, leading=10.4, spaceAfter=3)
S["note"] = ParagraphStyle("note", parent=S["body"], fontSize=8, leading=11, textColor=SLATE, fontName="DV-I")
S["h1"] = ParagraphStyle("h1", fontName="DV-B", fontSize=16, leading=20, textColor=NAVY, spaceBefore=0, spaceAfter=8)
S["h2"] = ParagraphStyle("h2", fontName="DV-B", fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=11, spaceAfter=4, keepWithNext=1)
S["h3"] = ParagraphStyle("h3", fontName="DV-B", fontSize=9.6, leading=13, textColor=TEAL, spaceBefore=7, spaceAfter=3, keepWithNext=1)
S["cap"] = ParagraphStyle("cap", fontName="DV-I", fontSize=7.8, leading=10.5, textColor=SLATE, spaceBefore=3, spaceAfter=9)
S["bul"] = ParagraphStyle("bul", parent=S["body"], leftIndent=12, bulletIndent=2, spaceAfter=2.5)
S["bul2"] = ParagraphStyle("bul2", parent=S["body"], leftIndent=24, bulletIndent=14, spaceAfter=2, fontSize=8.4, leading=11.8)
S["th"] = ParagraphStyle("th", fontName="DVC-B", fontSize=7.4, leading=9.4, textColor=colors.white)
S["td"] = ParagraphStyle("td", fontName="DVC", fontSize=7.4, leading=9.4, textColor=INK)
S["tdb"] = ParagraphStyle("tdb", parent=S["td"], fontName="DVC-B")
S["tds"] = ParagraphStyle("tds", fontName="DVC", fontSize=6.8, leading=8.6, textColor=INK)
S["tdm"] = ParagraphStyle("tdm", fontName="DVM", fontSize=6.5, leading=8.3, textColor=INK)
S["tdxs"] = ParagraphStyle("tdxs", fontName="DVC", fontSize=6.3, leading=7.9, textColor=INK)
S["code"] = ParagraphStyle("code", fontName="DVM", fontSize=6.7, leading=8.5, textColor=INK)
S["callout"] = ParagraphStyle("callout", parent=S["body"], fontSize=8.3, leading=11.6, spaceAfter=0)
S["cover_t"] = ParagraphStyle("cover_t", fontName="DV-B", fontSize=26, leading=32, textColor=NAVY)
S["cover_s"] = ParagraphStyle("cover_s", fontName="DV", fontSize=12.5, leading=17, textColor=SLATE)
S["toc0"] = ParagraphStyle("toc0", fontName="DV-B", fontSize=9.4, leading=14, leftIndent=0, spaceBefore=4, textColor=NAVY)
S["toc1"] = ParagraphStyle("toc1", fontName="DV", fontSize=8.3, leading=11.6, leftIndent=14, textColor=INK)
S["toc2"] = ParagraphStyle("toc2", fontName="DV", fontSize=7.6, leading=10.4, leftIndent=28, textColor=SLATE)


def P(text, style="body"):
    return Paragraph(text, S[style])


def esc(t):
    return escape(str(t))


def bullets(items, style="bul"):
    return [Paragraph(i, S[style], bulletText="•") for i in items]


def sub_bullets(items):
    return [Paragraph(i, S["bul2"], bulletText="–") for i in items]


def cell(text, style="td"):
    if isinstance(text, (Flowable, list)):
        return text
    return Paragraph(str(text).replace("\n", "<br/>"), S[style])


def table(header, rows, widths, style="td", zebra=True, header_bg=NAVY, repeat=1,
          valign="TOP", pad=3.2, first_col_bold=False, extra=None):
    """Standard data table. widths in points (sum to the available width)."""
    data = [[Paragraph(h, S["th"]) for h in header]]
    for r in rows:
        row = []
        for i, c in enumerate(r):
            st = "tdb" if (first_col_bold and i == 0) else style
            row.append(cell(c, st))
        data.append(row)
    t = Table(data, colWidths=widths, repeatRows=repeat, splitByRow=1)
    ts = [("BACKGROUND", (0, 0), (-1, 0), header_bg),
          ("VALIGN", (0, 0), (-1, -1), valign),
          ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
          ("BOX", (0, 0), (-1, -1), 0.5, LINE),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                ts.append(("BACKGROUND", (0, i), (-1, i), LIGHTER))
    if extra:
        ts += extra
    t.setStyle(TableStyle(ts))
    return t


def kv_table(rows, widths, key_bg=LIGHT, pad=3):
    data = [[Paragraph(f"<b>{k}</b>", S["td"]), cell(v)] for k, v in rows]
    t = Table(data, colWidths=widths, splitByRow=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), key_bg), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, LINE), ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]))
    return t


def callout(text, kind="info", width=CW):
    bg, bar = {"info": (LIGHT, TEAL), "warn": (AMBER_L, AMBER), "verified": (colors.HexColor("#EAF4EE"), GREEN),
               "proposed": (LIGHT, NAVY), "risk": (colors.HexColor("#F8ECEE"), RED)}[kind]
    t = Table([[Paragraph(text, S["callout"])]], colWidths=[width])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, bar),
                           ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    return t


def code_block(text, width=CW, chunk=9, size=None):
    """Splittable monospaced block (rows of `chunk` lines) with a light background."""
    lines = text.rstrip("\n").split("\n")
    rows = []
    for i in range(0, len(lines), chunk):
        rows.append([Preformatted("\n".join(lines[i:i + chunk]), S["code"] if not size else
                                  ParagraphStyle("c", parent=S["code"], fontSize=size, leading=size * 1.27))])
    t = Table(rows, colWidths=[width], splitByRow=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                           ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                           ("TOPPADDING", (0, 0), (-1, 0), 4), ("BOTTOMPADDING", (0, -1), (-1, -1), 4)]))
    return t


class Fig(Flowable):
    """Vector figure drawn by fn(canvas, w, h) on a (w x h) box with origin bottom-left."""

    def __init__(self, w, h, fn):
        super().__init__()
        self.w, self.h, self.fn = w, h, fn

    def wrap(self, aw, ah):
        return self.w, self.h

    def draw(self):
        self.fn(self.canv, self.w, self.h)


def fit_image(path, max_w, max_h):
    from PIL import Image as PI
    im = PI.open(path)
    w, h = im.size
    s = min(max_w / w, max_h / h)
    return Image(path, width=w * s, height=h * s), (w * s, h * s), s, (w, h)
