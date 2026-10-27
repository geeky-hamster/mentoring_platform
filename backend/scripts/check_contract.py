"""Compare the app's OpenAPI paths with the design contract (src/api.py EPS, 58 endpoints).

Usage (from backend/): .\\.venv\\Scripts\\python scripts\\check_contract.py
"""
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parents[2] / "src"
for p in (BACKEND, SRC):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import api as contract  # noqa: E402

from app.main import app  # noqa: E402


def normalize(path: str) -> str:
    # contract uses ":param"; OpenAPI uses "{param}"
    return re.sub(r":([A-Za-z_][A-Za-z0-9_]*)", r"{\1}", path)


METHODS = {"get", "post", "patch", "delete", "put"}

spec = {(e["method"].lower(), contract.BASE + normalize(e["path"])) for e in contract.EPS}

schema = app.openapi()
have = {(m.lower(), p) for p, item in schema["paths"].items() for m in item if m.lower() in METHODS}

missing = sorted(spec - have)
extra = sorted(have - spec)

print(f"contract endpoints: {len(spec)}   app openapi operations: {len(have)}")
if missing:
    print("\nMISSING FROM APP (in contract, not implemented):")
    for m, p in missing:
        print(f"  {m.upper():6} {p}")
if extra:
    print("\nEXTRA IN APP (implemented, not in contract):")
    for m, p in extra:
        print(f"  {m.upper():6} {p}")
if not missing and not extra:
    print("MATCH: every contract endpoint is implemented, no extras.")
sys.exit(1 if missing else 0)
