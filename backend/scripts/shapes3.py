"""Capture remaining response shapes for frontend coding (correct demo accounts)."""
import json
import time

import httpx

BASE = "http://localhost:8000/api/v1"
OUT = {}


class Client(httpx.Client):
    def request(self, *a, **kw):
        for _ in range(30):
            r = super().request(*a, **kw)
            if r.status_code != 429:
                return r
            time.sleep(2.2)
        return r


def login(email, password):
    c = Client(base_url=BASE, timeout=30)
    r = c.post("/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    data = r.json()["data"]
    c.headers["Authorization"] = f"Bearer {data['access_token']}"
    return c, data


admin, admin_tok = login("admin@example.org", "admin-password-123")
student, student_tok = login("asha.menon@example.org", "correct-horse-battery-9")
mentor, mentor_tok = login("rohan.iyer@example.org", "correct-horse-battery-9")

OUT["student dashboard"] = student.get("/students/me/dashboard").json()
OUT["mentor dashboard"] = mentor.get("/mentors/me/dashboard").json()
OUT["recommended mentors"] = student.get("/mentors/recommended", params={"page_size": 3}).json()
OUT["mentor directory"] = student.get("/mentors", params={"page_size": 2}).json()
OUT["student profile"] = student.get("/students/me/profile").json()
OUT["mentor profile"] = mentor.get("/mentors/me/profile").json()
OUT["mentor availability"] = mentor.get("/mentors/me/availability").json()
OUT["my mentorships student"] = student.get("/mentorships").json()
OUT["my requests student"] = student.get("/mentoring-requests/mine").json()
OUT["my requests mentor"] = mentor.get("/mentoring-requests/mine").json()
OUT["notifications"] = student.get("/notifications", params={"page_size": 2}).json()
OUT["admin pending mentors"] = admin.get("/admin/mentors", params={"profile_status": "pending_review"}).json()
OUT["analytics overview"] = admin.get("/admin/analytics/overview",
                                      params={"from": "2026-01-01", "to": "2026-12-31"}).json()
OUT["analytics trends"] = admin.get("/admin/analytics/trends",
                                    params={"metric": "sessions", "interval": "month",
                                            "from": "2026-01-01", "to": "2026-12-31"}).json()

mentors = OUT["mentor directory"]["data"]
if mentors:
    mid = mentors[0]["mentor_id"]
    OUT["mentor public profile"] = student.get(f"/mentors/{mid}").json()

# request detail as mentor (has student_summary)
reqs = OUT["my requests mentor"]["data"]
if reqs:
    OUT["request detail mentor"] = mentor.get(f"/mentoring-requests/{reqs[0]['request_id']}").json()

# Vikram/Divya mentorship has sessions (admin view)
ms = admin.get("/admin/mentorships", params={"status": "active"}).json()["data"]
if ms:
    m_id = ms[0]["mentorship_id"]
    OUT["mentorship detail (admin)"] = admin.get(f"/mentorships/{m_id}").json()
    OUT["mentorship sessions (admin)"] = admin.get(f"/mentorships/{m_id}/sessions").json()
    sessions = OUT["mentorship sessions (admin)"]["data"]
    if sessions:
        sid = sessions[0]["session_id"]
        OUT["session detail"] = admin.get(f"/sessions/{sid}").json()
        OUT["session feedback"] = admin.get(f"/sessions/{sid}/feedback").json()

OUT["sessions mine (mentor)"] = mentor.get("/sessions").json()
OUT["admin catalogue usage"] = admin.get("/admin/catalogue/usage").json() if False else None

with open("scripts/shapes3.json", "w", encoding="utf-8") as fh:
    json.dump(OUT, fh, indent=1)
print("written", len(OUT))

