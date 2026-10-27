"""Appendices A-D."""
import textwrap
from doc import *
import schema, api
from reportlab.platypus import Table, TableStyle, Preformatted

RES = "/home/claude/report_build/"
FS = 6.0
LEAD = 7.4
COLW = (LCW - 8) / 2
WRAP = int(COLW / (FS * 0.602)) - 3


def wrap_lines(text, width=WRAP):
    out = []
    for ln in text.rstrip("\n").split("\n"):
        if len(ln) <= width:
            out.append(ln)
        else:
            ind = len(ln) - len(ln.lstrip())
            out += textwrap.wrap(ln, width=width, subsequent_indent=" " * (ind + 4), break_long_words=True, break_on_hyphens=False)
    return out


def two_col(text, per_col=58, first_per_col=None):
    """Two-column monospaced listing; each table row is one landscape page of text (left column then right)."""
    lines = wrap_lines(text)
    st = ParagraphStyle("tc", fontName="DVM", fontSize=FS, leading=LEAD, textColor=INK)
    flows = []
    i = 0
    first = True
    while i < len(lines):
        n = (first_per_col or per_col) if first else per_col
        left = lines[i:i + n]
        right = lines[i + n:i + 2 * n]
        i += 2 * n
        t = Table([[Preformatted("\n".join(left), st), Preformatted("\n".join(right), st)]], colWidths=[COLW + 4, COLW + 4])
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                               ("LINEAFTER", (0, 0), (0, 0), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                               ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
        flows.append(t)
        first = False
    return flows


def appA():
    s = to_land() + H1("appA")
    s.append(P("This is the compact print of the contract delivered as <font face='DVM'>api-spec.yaml</font> (OpenAPI 3.0.3, validated). Prose descriptions are removed here to save space and lines longer than the column are wrapped for print only; "
               "the file in the source archive carries all descriptions and has no wrapping. Endpoint identifiers E01-E58 match " + R("api.catalogue") + "."))
    s += two_col(api.openapi(True), per_col=62, first_per_col=48)
    return s


def appB():
    s = to_port_land_safe = to_land() + H1("appB")
    s.append(P("Complete DDL for PostgreSQL 16 (file <font face='DVM'>schema.sql</font>): extensions, tables with keys and checks, partial unique indexes, exclusion constraints, indexes, triggers. "
               "It is generated from the same definition as " + R("database.dictionary") + " and was executed on PostgreSQL 16 without error before the tests in " + R("appD") + " were run."))
    s += two_col(open(RES + "schema.sql").read(), per_col=62, first_per_col=48)
    return s


def appC():
    s = to_land() + H1("appC")
    s.append(P("Reference implementation of the matching rule (file <font face='DVM'>matching_reference.py</font>), including the sample data of " + R("matching.worked") + " and its self-tests. "
               "Weights are the proposed values; the code has no database access. Running the file executes the assertions and prints the ranking."))
    s += two_col(open("/home/claude/report_build/src/matching.py").read(), per_col=54, first_per_col=48)
    import matching
    s.append(Spacer(1, 6))
    out = []
    for r in matching.worked_example():
        out.append(f"{r['name']:<12} S={r['S']:>5}  C={r['C']:>5}  A={r['A']:>5}  score={r['score']:>5}  free={r['free_capacity']} slots={r['open_slots']}")
    out.append("matching self-tests passed")
    matching._selftest()
    s.append(KeepTogether([P("<b>Output of the delivered code</b> (the self-test assertions pass):", "small"),
                           code_block("\n".join(out), width=LCW, size=6.4)]))
    return s


def appD():
    s = to_port() + H1("appD")
    s.append(P("The schema was loaded into PostgreSQL 16 and the script <font face='DVM'>db_integrity_tests.sql</font> was executed. Each line states the test, whether PostgreSQL accepted or rejected the action and the SQLSTATE returned "
               "(23505 unique violation, 23503 foreign-key violation, 23514 check violation or trigger-raised check, 23P01 exclusion violation). All 39 tests behaved as designed."))
    rows = []
    for ln in open(RES + "db_test_results.txt").read().strip().splitlines():
        status, rest = ln.split(" ", 1)
        tid, desc = rest.split(" ", 1)
        m = desc.rsplit(" (", 1)
        rows.append([f"<b>{tid}</b>", m[0], m[1].rstrip(")") if len(m) > 1 else "", f"<font color='#2F7D4F'><b>{status}</b></font>"])
    s.append(tab_caption("Database integrity test results (PostgreSQL 16)"))
    s.append(table(["Test", "Action attempted", "Outcome", "Result"], rows, [44, 252, 140, 46], style="tds", pad=2))
    s.append(Spacer(1, 6))
    s.append(P("<b>Concurrency test</b> (<font face='DVM'>db_concurrency_test.sh</font>): two sessions accept different requests for a mentor with capacity 1 at the same moment; the first holds its lock for 1.5 seconds. Output:"))
    s.append(code_block(open(RES + "db_concurrency_result.txt").read(), size=6.4))
    s.append(Spacer(1, 4))
    s.append(callout("<b>Limits of this evidence.</b> The tests were run once on a throwaway PostgreSQL 16 cluster with the schema as delivered. They prove the database rules, not the application code, and they are not a substitute for the API-level tests listed in " + R("testing.cases") + ".", "warn"))
    return s
