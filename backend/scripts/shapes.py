"""Dump the live JSON shapes of the main GET endpoints so the frontend can be
coded against reality. Usage (from backend/): .\\.venv\\Scripts\\python scripts\\shapes.py"""
import json
import sys
import time

import httpx

BASE = "http://localhost:8000/api/v1"


class Client(httpx.Client):
    def request(self, *a, **kw):
        for _ in range(12):
            r = super().request(*a, **kw)
            if r.status_code != 429:
                return r
            time.sleep(6)
        return r


def main():
    def login(email, pw):
        c = Client(base_url=BASE, timeout=20)
        r = c.post("/auth/login", json={"email": email, "password": pw})
        c.headers["Authorization"] = f"Bearer {r.json()['data']['access_token']}"
        return c

    stud = login("asha.menon@example.org", "correct-horse-battery-9")
    ment = login("rohan.iyer@example.org", "correct-horse-battery-9")
    adm = login("admin@example.org", "admin-password-123")

    show = [
        ("student login user", None),
        ("student dashboard", stud.get("/students/me/dashboard")),
        ("recommended[0]", stud.get("/mentors/recommended")),
        ("mentor search", stud.get("/mentors", params={"page_size": 2})),
        ("mentor public", stud.get("/mentors", params={"page_size": 1}).json()["data"][0]["mentor_id"]),
        ("student requests", stud.get("/mentoring-requests/mine", params={"page_size": 2})),
        ("student mentorships", stud.get("/mentorships")),
        ("student sessions", stud.get("/sessions", params={"page_size": 2})),
        ("notifications (stud)", stud.get("/notifications", params={"page_size": 2})),
        ("mentor me profile", ment.get("/mentors/me/profile")),
        ("mentor dashboard", ment.get("/mentors/me/dashboard")),
        ("mentor requests", ment.get("/mentoring-requests/mine", params={"page_size": 2})),
        ("mentor mentorships", ment.get("/mentorships")),
        ("open slots", None),
        ("admin users", adm.get("/admin/users", params={"page_size": 2})),
        ("admin mentors queue", adm.get("/admin/mentors", params={"profile_status": "pending_review"})),
        ("admin mentorships", adm.get("/admin/mentorships", params={"page_size": 2})),
        ("admin requests", adm.get("/admin/mentoring-requests", params={"page_size": 2})),
        ("analytics overview", adm.get("/admin/analytics/overview", params={"from": "2026-01-01", "to": "2026-12-31"})),
        ("analytics trends", adm.get("/admin/analytics/trends", params={"metric": "requests", "from": "2026-01-01", "to": "2026-12-31"})),
        ("audit logs", adm.get("/admin/audit-logs", params={"page_size": 2})),
    ]

    out = {}
    for name, r in show:
        if name == "mentor public":
            mid = r
            r = stud.get(f"/mentors/{mid}")
        if name == "open slots":
            data = ment.get("/mentors/me/profile").json()["data"]
            r = stud.get(f"/mentors/{data['mentor_id']}/availability")
        if r is None:
            continue
        try:
            body = r.json()
        except Exception:
            body = r.text[:200]
        out[name] = {"status": r.status_code, "body": body}

    json.dump(out, sys.stdout, indent=1, default=str)
    print()


if __name__ == "__main__":
    main()
