"""Generate crow's-foot ER diagrams (two parts) from schema.py with Graphviz."""
import subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import schema

D = "/home/claude/report_build/diagrams"
SHOW = {  # extra non-key columns drawn in addition to PK/FK
    "users": ["full_name", "email", "role", "account_status"],
    "student_profiles": ["programme_stage", "expected_graduation_year", "profile_completed"],
    "mentor_profiles": ["mentor_type", "profile_status", "max_active_mentees", "is_available"],
    "skills": ["skill_name", "category", "is_active"],
    "student_skills": ["proficiency_level", "is_focus"],
    "mentor_expertise": ["expertise_level"],
    "career_interests": ["interest_name", "is_active"],
    "student_interests": [], "mentor_interests": [],
    "mentoring_requests": ["career_goal", "status", "expires_at"],
    "mentorships": ["status", "started_at", "ended_at"],
    "availability_slots": ["start_time", "end_time", "is_available"],
    "sessions": ["scheduled_start", "scheduled_end", "status"],
    "feedback": ["rating", "comments"],
    "notifications": ["notification_type", "is_read"],
    "audit_logs": ["action", "entity_type", "created_at"],
    "refresh_tokens": ["family_id", "expires_at", "revoked_at"],
}
STUB_ONLY = {"users": "user_id", "student_profiles": "user_id", "mentor_profiles": "user_id"}
TB = {t["name"]: t for t in schema.T}
SHOW2 = {"mentoring_requests": ["status", "expires_at"], "mentorships": ["status"], "sessions": ["status"], "feedback": ["rating"], "availability_slots": ["start_time", "end_time"]}


def node(name, stub=None, compact=False):
    t = TB[name]
    added = t["group"] == "added"
    head = "#F6E3B4" if added else "#1F3A5F"
    fg = "#5B3A06" if added else "white"
    rows = [f'<TR><TD COLSPAN="3" BGCOLOR="{head}"><FONT COLOR="{fg}"><B>{name}</B></FONT>{" (added)" if added else ""}</TD></TR>']
    cols = t["cols"]
    if stub:
        cols = [c for c in cols if c["name"] == stub]
    else:
        keep = SHOW2.get(name, SHOW[name]) if compact else SHOW[name]
        cols = [c for c in cols if c["key"] or c["name"] in keep]
    for c in cols:
        key = c["key"]
        tag = key.replace(",", ",") if key else ""
        bg = "#EEF3FA" if key else "white"
        bold = "<B>%s</B>" if "PK" in key else "%s"
        typ = c["type"].replace("TIMESTAMPTZ", "TIMESTAMPTZ")
        rows.append(f'<TR><TD ALIGN="LEFT" BGCOLOR="{bg}">{tag}</TD><TD ALIGN="LEFT" BGCOLOR="{bg}">{bold % c["name"]}</TD><TD ALIGN="LEFT" BGCOLOR="{bg}"><FONT COLOR="#6B7686">{typ}</FONT></TD></TR>')
    if stub:
        rows.append('<TR><TD COLSPAN="3" ALIGN="LEFT"><FONT COLOR="#6B7686"><I>see accounts diagram</I></FONT></TD></TR>')
    elif len(TB[name]["cols"]) > len(cols):
        rows.append(f'<TR><TD COLSPAN="3" ALIGN="LEFT"><FONT COLOR="#6B7686"><I>+ {len(TB[name]["cols"]) - len(cols)} more columns</I></FONT></TD></TR>')
    return f'  {name} [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="3" COLOR="#1F3A5F">{"".join(rows)}</TABLE>>];'


def edges(include, stubs):
    out = []
    for child, ccols, parent, pcols, ondel, card, nullable, verb in schema.FKS:
        if child not in include or parent not in include + stubs:
            continue
        if child in stubs:
            continue
        if card == "1:1":
            tail, head = "teetee", "teeodot"
        elif nullable:
            tail, head = "teeodot", "crowodot"
        else:
            tail, head = "teetee", "crowodot"
        lab = verb or ""
        out.append(f'  {parent} -> {child} [dir=both, arrowtail={tail}, arrowhead={head}, label="{lab}", taillabel="", fontsize=8];')
    return out


def build(name, tables, stubs, rankdir="TB", ranks=(), order=(), compact=False):
    """stubs: dict table -> referenced column to show; ranks: lists of tables forced onto one rank;
    order: (a, b) pairs adding invisible edges to fix relative position."""
    body = [f'digraph {name} {{', f'  rankdir={rankdir}; splines=true; nodesep=0.4; ranksep=0.55; pad=0.15;',
            '  graph [fontname="DejaVu Sans"]; node [shape=plain, fontname="DejaVu Sans", fontsize=9];',
            '  edge [fontname="DejaVu Sans", fontsize=8, color="#44546A", fontcolor="#1F3A5F", arrowsize=0.9, penwidth=1.0];']
    for t in tables:
        body.append(node(t, compact=compact))
    for s_, col in stubs.items():
        body.append(node(s_, stub=col))
    body += edges(tables, list(stubs))
    for grp in ranks:
        body.append("  {rank=same; " + "; ".join(grp) + ";}")
    for a_, b_ in order:
        body.append(f"  {a_} -> {b_} [style=invis];")
    body.append("}")
    p = f"{D}/{name}.dot"
    open(p, "w").write("\n".join(body))
    subprocess.check_call(["dot", "-Tpng", "-Gdpi=220", p, "-o", f"{D}/{name}.png"])


if __name__ == "__main__":
    build("er_accounts", ["users", "student_profiles", "mentor_profiles", "notifications", "refresh_tokens", "audit_logs"], {},
          ranks=[["student_profiles", "mentor_profiles"], ["notifications", "refresh_tokens", "audit_logs"]],
          order=[("student_profiles", "notifications"), ("mentor_profiles", "audit_logs")])
    build("er_catalogue", ["skills", "career_interests", "student_skills", "mentor_expertise", "student_interests", "mentor_interests"],
          {"student_profiles": "student_profile_id", "mentor_profiles": "mentor_profile_id"})
    build("er_lifecycle", ["mentoring_requests", "mentorships", "availability_slots", "sessions", "feedback"],
          {"users": "user_id", "student_profiles": "user_id", "mentor_profiles": "user_id"}, compact=True,
          ranks=[["student_profiles", "mentor_profiles"], ["sessions", "users"]])
    print("ok")
