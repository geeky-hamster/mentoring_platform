# AGENTS.md

## What this repo is

A design deliverable, not a running application. `src/` generates the PDF design report; `api-spec.yaml`, `database/schema.sql` and `diagrams/*` are generated artifacts. Per the README, the REST API, React front end and UI behaviour are specifications only — do not add app scaffolding or "fix" missing implementations unless asked.

## Commands (run from `src/`)

Consistency checks, no third-party deps:

- `python schema.py` — tables/columns/FKs
- `python pages.py` — pages, stories, workflow steps, unused endpoints
- `python components_data.py` — component dependency graph (must be acyclic)
- `python matching.py` — scoring self-tests; `python matching_reference.py` at the repo root is a byte-identical copy

`python api.py` verifies and then **crashes** writing `/home/claude/report_build/api-spec.yaml`; on non-Linux use `python -c "import api; api.verify()"`.

- `python wire_test.py [page ...]` renders a wireframe contact sheet plus callout/element mismatch report (needs `reportlab`).
- `python build.py [out.pdf] [--sections=a,b]` builds the report (needs `reportlab`, `pyyaml`, Pillow for figures). The docstring says `--sections a,b,c`, but only `--sections=a,b` is parsed.
- `python make_er.py` / `python make_dot.py` regenerate the ER, architecture, component and nav-map diagrams with Graphviz `dot`. The `.mmd` diagrams are rendered separately with `mmdc -p diagrams/pp.json -c diagrams/mm.json -i in.mmd -o out.png`.
- Database checks need PostgreSQL 16 and `psql`: apply `database/schema.sql`, then run `database/db_integrity_tests.sql`. The concurrency test is bash: `PSQL="psql ..." ./database/db_concurrency_test.sh <db>`.

## Edit sources, not artifacts

| Source | Generates |
| --- | --- |
| `src/schema.py` | `database/schema.sql` (identical to `schema.ddl()`) |
| `src/api.py` | `api-spec.yaml` (identical to `api.openapi()`) |
| `src/pages.py` | 26 page specs, user stories, nav maps |
| `src/components_data.py` | C01–C12 components, dependency matrix |
| `src/matching.py` | matching rule and worked example |

Report prose lives in `src/content_a..e.py` (section list in `build.py`); `doc.py`, `kit.py`, `outline.py` are the layout engine and `R("section-key")` cross-reference numbering. Never hand-edit generated `.sql`, `.yaml`, `.dot` or `.png` files.

## Gotchas

- No package layout: modules are flat siblings imported as `from kit import *`. Run scripts with `src/` as CWD.
- `/home/claude/report_build/` is hardcoded in 10 files (`build.py`, `api.py`, `doc.py`, `content_a/c/e.py`, `make_er.py`, `make_dot.py`, `uml_figs.py`, `wire_test.py`), and `kit.py` expects DejaVu fonts at `/usr/share/fonts/truetype/dejavu/`. Repoint both to build elsewhere.
- `diagrams/pp.json` hardcodes a Linux Chromium path for `mmdc`.
- There is no pytest, CI, lockfile or `requirements.txt`; the cross-file assertions in the scripts above are the test suite.
- Prose hardcodes counts that are also computed ("26 pages", "58 operations", "17 tables", "12 components"); update both when source data changes. Version/date strings live in `src/doc.py` and `README.md`.
- Keep the evidence honest: `database/db_test_results.txt` (39 PASS) and `db_concurrency_result.txt` are recorded PostgreSQL 16 output, not a live run.
