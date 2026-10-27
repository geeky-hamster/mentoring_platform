"""Quick smoke test of the running API (httpx, sync). Usage: python scripts/smoke.py"""
import json
import sys
import time

import httpx

BASE = "http://localhost:8000/api/v1"
ok = fail = 0


class Client(httpx.Client):
    """HTTP client that waits out 429 rate-limit windows."""

    def request(self, *args, **kwargs):
        for _ in range(12):
            r = super().request(*args, **kwargs)
            if r.status_code != 429:
                return r
            time.sleep(6)
        return r


def check(name, resp, expect_status=None, expect_code=None):
    global ok, fail
    good = True
    if expect_status is not None and resp.status_code != expect_status:
        good = False
    if expect_code is not None:
        try:
            body = resp.json()
        except Exception:
            good = False
        else:
            code = body.get("error", {}).get("code") if isinstance(body.get("error"), dict) else None
            if code != expect_code:
                good = False
    if good:
        ok += 1
        print(f"PASS {name}")
    else:
        fail += 1
        print(f"FAIL {name}: {resp.status_code} {resp.text[:300]}")


def main():
    # one client (cookie jar) per role: the refresh cookie is per-session
    c = Client(base_url=BASE, timeout=15)
    admin_c = Client(base_url=BASE, timeout=15)
    stud_c = Client(base_url=BASE, timeout=15)
    ment_c = Client(base_url=BASE, timeout=15)

    # health (outside /api/v1)
    r = httpx.get("http://localhost:8000/health", timeout=10)
    check("health", r, 200)

    # login admin
    r = admin_c.post("/auth/login", json={"email": "admin@example.org", "password": "admin-password-123"})
    check("admin login", r, 200)
    admin_tok = r.json()["data"]["access_token"]

    # login student
    r = stud_c.post("/auth/login", json={"email": "asha.menon@example.org", "password": "correct-horse-battery-9"})
    check("student login", r, 200)
    student_tok = r.json()["data"]["access_token"]
    student_id = r.json()["data"]["user"]["user_id"]

    # login mentor
    r = ment_c.post("/auth/login", json={"email": "rohan.iyer@example.org", "password": "correct-horse-battery-9"})
    check("mentor login", r, 200)
    mentor_tok = r.json()["data"]["access_token"]
    mentor_id = r.json()["data"]["user"]["user_id"]

    # me
    r = stud_c.get("/users/me", headers={"Authorization": f"Bearer {student_tok}"})
    check("users/me", r, 200)

    # unauthenticated -> UNAUTHENTICATED
    r = c.get("/users/me")
    check("users/me anon", r, 401, "UNAUTHENTICATED")

    # bad credentials
    r = c.post("/auth/login", json={"email": "asha.menon@example.org", "password": "wrong"})
    check("bad login", r, 401, "INVALID_CREDENTIALS")

    # refresh: cookie flow (student's own cookie jar)
    r = stud_c.post("/auth/refresh")
    check("refresh", r, 200)
    student_tok = r.json()["data"]["access_token"]

    # catalogues
    r = stud_c.get("/skills", headers={"Authorization": f"Bearer {student_tok}"})
    check("skills list", r, 200)
    r = stud_c.get("/career-interests", headers={"Authorization": f"Bearer {student_tok}"})
    check("interests list", r, 200)

    # recommendations (asha profile completed)
    r = stud_c.get("/mentors/recommended", headers={"Authorization": f"Bearer {student_tok}"})
    check("recommended", r, 200)
    recs = r.json()["data"]
    if recs:
        print("   top:", recs[0]["mentor"]["full_name"], recs[0]["match_score"])

    # mentor search
    r = stud_c.get("/mentors", headers={"Authorization": f"Bearer {student_tok}"})
    check("mentor search", r, 200)

    # mentor public profile
    r = stud_c.get(f"/mentors/{mentor_id}", headers={"Authorization": f"Bearer {student_tok}"})
    check("mentor public profile", r, 200)

    # dashboards
    r = stud_c.get("/students/me/dashboard", headers={"Authorization": f"Bearer {student_tok}"})
    check("student dashboard", r, 200)
    r = ment_c.get("/mentors/me/dashboard", headers={"Authorization": f"Bearer {mentor_tok}"})
    check("mentor dashboard", r, 200)

    # notifications
    r = ment_c.get("/notifications", headers={"Authorization": f"Bearer {mentor_tok}"})
    check("notifications", r, 200)

    # requests lists
    r = stud_c.get("/mentoring-requests/mine", headers={"Authorization": f"Bearer {student_tok}"})
    check("student requests", r, 200)
    r = ment_c.get("/mentoring-requests/mine", headers={"Authorization": f"Bearer {mentor_tok}"})
    check("mentor requests", r, 200)

    # mentorships
    r = stud_c.get("/mentorships", headers={"Authorization": f"Bearer {student_tok}"})
    check("student mentorships", r, 200)

    # sessions
    r = stud_c.get("/sessions", headers={"Authorization": f"Bearer {student_tok}"})
    check("sessions", r, 200)

    # admin endpoints
    ah = {"Authorization": f"Bearer {admin_tok}"}
    r = admin_c.get("/admin/users", headers=ah)
    check("admin users", r, 200)
    r = admin_c.get("/admin/mentors", headers=ah)
    check("admin mentor queue", r, 200)
    r = admin_c.get("/admin/mentorships", headers=ah)
    check("admin mentorships", r, 200)
    r = admin_c.get("/admin/mentoring-requests", headers=ah)
    check("admin requests", r, 200)
    r = admin_c.get("/admin/analytics/overview", params={"from": "2026-01-01", "to": "2026-12-31"}, headers=ah)
    check("analytics overview", r, 200)
    r = admin_c.get("/admin/analytics/trends", params={"metric": "requests", "from": "2026-01-01", "to": "2026-12-31"}, headers=ah)
    check("analytics trends", r, 200)
    r = admin_c.get("/admin/audit-logs", headers=ah)
    check("audit logs", r, 200)
    r = admin_c.get("/admin/analytics/export", params={"report": "mentorships", "from": "2026-01-01", "to": "2026-12-31"}, headers=ah)
    check("analytics export csv", r, 200)

    # forbidden: student hitting admin
    r = stud_c.get("/admin/users", headers={"Authorization": f"Bearer {student_tok}"})
    check("student -> admin forbidden", r, 403, "FORBIDDEN")

    print(f"\n{ok} passed, {fail} failed")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
