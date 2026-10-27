"""Generate Graphviz sources (architecture, component, deployment, navigation map) and render PNGs."""
import subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import pages

D = "/home/claude/report_build/diagrams"
FONT = 'fontname="DejaVu Sans"'
HEAD = f'''graph [{FONT}, fontsize=11, splines=ortho, nodesep=0.28, ranksep=0.5, pad=0.15, bgcolor=white];
  node [{FONT}, fontsize=10, shape=box, style="rounded,filled", fillcolor="#E3ECF7", color="#1F3A5F", penwidth=1.1, margin="0.12,0.07"];
  edge [{FONT}, fontsize=9, color="#44546A", arrowsize=0.7, fontcolor="#1F3A5F"];'''


def write(name, body, dpi=230):
    p = f"{D}/{name}.dot"
    open(p, "w").write(body)
    subprocess.check_call(["dot", "-Tpng", f"-Gdpi={dpi}", p, "-o", f"{D}/{name}.png"])


def architecture():
    b = f'''digraph architecture {{
  rankdir=LR;
  {HEAD}
  users [label="Students, mentors\\nand administrators\\n(web browser)", shape=box, style="rounded,filled", fillcolor="#FFFFFF"];
  subgraph cluster_fe {{
    label="Frontend  -  React SPA built with Vite  (static hosting on Vercel)"; style="rounded,filled"; fillcolor="#F4F8FC"; color="#9FB3CC";
    router [label="React Router\\nrole-guarded routes"];
    ui [label="26 pages\\nBootstrap components"];
    forms [label="React Hook Form\\nclient-side validation"];
    axios [label="Axios client\\nJWT header, refresh on 401"];
    router -> ui -> forms -> axios [style=invis];
  }}
  proxy [label="Vercel rewrite\\n/api/* to Render\\n(same origin, no CORS\\nin production)", fillcolor="#FBF0D9", color="#C9922B"];
  subgraph cluster_be {{
    label="Backend  -  Flask REST API under /api/v1  (Render web service)"; style="rounded,filled"; fillcolor="#F2FAF5"; color="#8FBFA2";
    mw [label="Middleware\\nCORS allow-list, rate limiter,\\nJWT-Extended, error handler", fillcolor="#DDF0E4", color="#1F6B3F"];
    bp [label="Blueprints (route layer)\\nauth, catalogue, profiles, availability,\\ndiscovery, requests, mentorships,\\nsessions, feedback, notifications, admin", fillcolor="#DDF0E4", color="#1F6B3F"];
    svc [label="Service layer\\nAuthentication, Matching, Mentoring,\\nSession, Feedback, Notification,\\nAdmin, Analytics, Audit", fillcolor="#DDF0E4", color="#1F6B3F"];
    orm [label="SQLAlchemy models\\nand Flask-Migrate migrations", fillcolor="#DDF0E4", color="#1F6B3F"];
    mw -> bp -> svc -> orm;
  }}
  db [label="PostgreSQL 16\\n(managed)\\n17 tables, constraints,\\nindexes, triggers", shape=cylinder, fillcolor="#D9EEF1", color="#2A7F8E"];
  cron [label="Scheduled job (Render cron)\\nexpire stale requests,\\npurge old refresh tokens", fillcolor="#FBF0D9", color="#C9922B"];
  mail [label="E-mail provider (optional)\\nreset and verification links", style="rounded,filled,dashed", fillcolor="#FFFFFF"];
  users -> router [label="HTTPS"];
  axios -> proxy [label="HTTPS JSON"];
  proxy -> mw [label="HTTPS"];
  orm -> db [label="SQL over TLS"];
  cron -> db;
  svc -> mail [style=dashed, label="optional"];
}}
'''
    write("architecture", b)


def component():
    comps = [
        ("C01", "Authentication and\\nauthorisation"), ("C02", "User and profile\\nmanagement"), ("C03", "Skill and career-\\ninterest management"),
        ("C04", "Mentor discovery\\nand filtering"), ("C05", "Mentor matching\\nservice"), ("C06", "Mentoring request\\nmanagement"),
        ("C07", "Mentorship relationship\\nmanagement"), ("C08", "Availability and\\nsession scheduling"), ("C09", "Feedback\\nmanagement"),
        ("C10", "Notifications"), ("C11", "Administration"), ("C12", "Analytics and\\nreporting")]
    nodes = "\n".join(f'    {c.lower()} [label="{c} {t}", fillcolor="#DDF0E4", color="#1F6B3F"];' for c, t in comps)
    edges = [("c04", "c05"), ("c05", "c02"), ("c05", "c03"), ("c05", "c08"), ("c04", "c03"), ("c06", "c02"), ("c06", "c07"), ("c06", "c10"),
             ("c07", "c10"), ("c08", "c07"), ("c08", "c10"), ("c09", "c08"), ("c09", "c10"), ("c11", "c02"), ("c11", "c07"), ("c11", "c10"),
             ("c02", "c03")]
    es = "\n".join(f"  {a} -> {b};" for a, b in edges)
    b = f'''digraph components {{
  rankdir=TB;
  {HEAD}
  node [width=1.7];
  subgraph cluster_fe {{ label="Frontend (React SPA)"; style="rounded,filled"; fillcolor="#F4F8FC"; color="#9FB3CC";
    spa [label="Pages, route guards, Axios client,\\nforms and shared components", width=4.2];
  }}
  subgraph cluster_api {{ label="REST API layer (Flask Blueprints, /api/v1)"; style="rounded,filled"; fillcolor="#FFF7E6"; color="#C9922B";
    api [label="Request parsing and validation, JWT and role checks,\\nresponse and error envelope, rate limiting", fillcolor="#FBF0D9", color="#C9922B", width=5.6];
  }}
  subgraph cluster_svc {{ label="Business services (one component per box; services never import Flask objects)"; style="rounded,filled"; fillcolor="#F2FAF5"; color="#8FBFA2";
{nodes}
    c01 -> c12 [style=invis];
  }}
  subgraph cluster_data {{ label="Persistence"; style="rounded,filled"; fillcolor="#EEF8FA"; color="#7DB5BF";
    repo [label="SQLAlchemy models and queries", fillcolor="#D9EEF1", color="#2A7F8E", width=3];
    db [label="PostgreSQL 16", shape=cylinder, fillcolor="#D9EEF1", color="#2A7F8E"];
    repo -> db;
  }}
  ext [label="Optional integrations\\nE-mail provider, scheduler", style="rounded,filled,dashed", fillcolor="#FFFFFF"];
  spa -> api [label="HTTPS JSON"];
  api -> c01 [label="every call"];
  api -> c06; api -> c08; api -> c11;
{es}
  c01 -> repo [style=dashed]; c12 -> repo [label="read-only"];
  c10 -> ext [style=dashed];
  c01 -> ext [style=dashed];
}}
'''
    write("component", b)


def deployment():
    b = f'''digraph deployment {{
  rankdir=TB; compound=true; splines=true;
  {HEAD}
  subgraph cluster_dev {{ label="Developer machine"; style="rounded,filled"; fillcolor="#F4F6F9"; color="#B8C2D0";
    vite [label="Vite dev server\\nlocalhost:5173"]; flask [label="Flask dev server\\nlocalhost:5000"]; pg [label="PostgreSQL 16\\n(local or Docker)", shape=cylinder, fillcolor="#D9EEF1", color="#2A7F8E"];
    vite -> flask [label="/api proxy"]; flask -> pg;
  }}
  gh [label="GitHub\\nrepository, pull requests,\\ncode review", fillcolor="#FFFFFF"];
  ci [label="CI workflow\\nlint, pytest, Vitest,\\nOpenAPI validation", fillcolor="#FBF0D9", color="#C9922B"];
  subgraph cluster_prod {{ label="Production"; style="rounded,filled"; fillcolor="#F2FAF5"; color="#8FBFA2";
    vercel [label="Vercel\\nstatic SPA + /api rewrite", fillcolor="#DDF0E4", color="#1F6B3F"];
    render [label="Render web service\\nFlask + Gunicorn", fillcolor="#DDF0E4", color="#1F6B3F"];
    job [label="Render cron job", fillcolor="#DDF0E4", color="#1F6B3F"];
    mpg [label="Managed PostgreSQL\\nautomated backups", shape=cylinder, fillcolor="#D9EEF1", color="#2A7F8E"];
    vercel -> render [label="HTTPS"]; render -> mpg [label="TLS"]; job -> mpg;
  }}
  flask -> gh [label="git push", ltail=cluster_dev, style=dashed];
  gh -> ci; ci -> vercel [label="deploy main"];
  ci -> render [label="deploy main"];
}}
'''
    write("deployment", b)


def navmap():
    P = pages.PAGE
    colr = {"Public": "#FFFFFF", "Student": "#E3ECF7", "Mentor": "#DDF0E4", "Admin": "#FBF0D9"}
    role_of = {n: ("Public" if n <= 4 else "Student" if n <= 14 else "Mentor" if n <= 21 else "Admin") for n in range(1, 27)}
    side = {"Student": [6, 7, 10, 11, 14, 13], "Mentor": [15, 16, 18, 19, 20, 21], "Admin": [22, 23, 24, 25, 26]}
    extra = {"Public": [("p1", "p6", "student sign-in"), ("p1", "p15", "mentor sign-in"), ("p1", "p22", "admin sign-in"),
                        ("p2", "p5", "student registers"), ("p2", "p20", "mentor registers"), ("p4", "p6", "own dashboard")],
             "Student": [], "Mentor": [], "Admin": []}
    cfg = {"Public": ("LR", [1, 2, 3, 4], [5, 6, 15, 20, 22]), "Student": ("TB", list(range(5, 15)), [1]),
           "Mentor": ("TB", list(range(15, 22)), [1]), "Admin": ("TB", list(range(22, 27)), [1])}
    for role, (rd, nums, ghosts) in cfg.items():
        out = [f"digraph nav_{role} {{\n  rankdir={rd};\n  {HEAD}\n  splines=true; nodesep=0.35; ranksep=0.55;"]
        for n in nums:
            t = P[n]["title"].replace('"', "'")
            t = t.replace(" / ", " /\\n").replace(" and ", "\\nand ") if len(t) > 22 else t
            out.append(f'  p{n} [label="{n}  {t}", fillcolor="{colr[role_of[n]]}"];')
        for g in ghosts:
            t = P[g]["title"].replace('"', "'")
            t = t.replace(" and ", "\\nand ") if len(t) > 22 else t
            out.append(f'  p{g} [label="{g}  {t}\\n({role_of[g]} page)", style="rounded,dashed,filled", fillcolor="#FFFFFF", color="#6B7686"];')
        seen = set()
        for n in nums:
            for lab, kind, tgt, eps, step in P[n]["actions"]:
                if kind == "nav" and isinstance(tgt, int) and (tgt in nums or tgt in ghosts):
                    k = (n, tgt, lab)
                    if k in seen:
                        continue
                    seen.add(k)
                    out.append(f'  p{n} -> p{tgt} [label="{lab if len(lab) < 36 else lab[:33] + "..."}"];')
        for a_, b_, lab in extra[role]:
            out.append(f'  {a_} -> {b_} [label="{lab}", style=dashed];')
        if role in side:
            lst = "\\n".join(f"{n}  {P[n]['title'].split(' / ')[0].split(' (')[0]}" for n in side[role])
            out.append(f'  sb [label="Sidebar on every {role.lower()} page:\\n{lst}", shape=note, style=filled, fillcolor="#FFFFFF", color="#6B7686", fontsize=9];')
        out.append("}")
        write(f"navmap_{role.lower()}", "\n".join(out), dpi=200)


if __name__ == "__main__":
    for f in (deployment, navmap):
        f()
    print("ok")
