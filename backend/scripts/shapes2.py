"""Probe remaining response shapes: request detail, mentorship detail, sessions, feedback, availability."""
import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx

BASE = "http://localhost:8000/api/v1"
run = uuid.uuid4().hex[:6]
PW = "probe-password-2026"


class Client(httpx.Client):
    def request(self, *a, **kw):
        for _ in range(12):
            r = super().request(*a, **kw)
            if r.status_code != 429:
                return r
            import time
            time.sleep(6)
        return r


out = {}
adm = Client(base_url=BASE, timeout=20)
r = adm.post("/auth/login", json={"email": "admin@example.org", "password": "admin-password-123"})
out["login"] = r.json()["data"]
adm.headers["Authorization"] = f"Bearer {r.json()['data']['access_token']}"

# student
s = Client(base_url=BASE, timeout=20)
s.post("/auth/register", json={"full_name": "Probe Student", "email": f"probe.stu.{run}@example.org",
                               "password": PW, "role": "student"})
s.headers["Authorization"] = f"Bearer {s.post('/auth/login', json={'email': f'probe.stu.{run}@example.org', 'password': PW}).json()['data']['access_token']}"
skills = s.get("/skills").json()["data"]
interests = s.get("/career-interests").json()["data"]
s.patch("/students/me/profile", json={
    "programme_stage": "bsc_degree", "expected_graduation_year": 2028,
    "career_goals": "Probe goals for the student profile summary.",
    "skills": [{"skill_id": skills[0]["skill_id"], "proficiency_level": "beginner", "is_focus": True}],
    "interest_ids": [interests[0]["interest_id"]]})
out["student me profile"] = s.get("/students/me/profile").json()

# mentor (approve via admin)
m = Client(base_url=BASE, timeout=20)
m.post("/auth/register", json={"full_name": "Probe Mentor", "email": f"probe.men.{run}@example.org",
                               "password": PW, "role": "mentor"})
m.headers["Authorization"] = f"Bearer {m.post('/auth/login', json={'email': f'probe.men.{run}@example.org', 'password': PW}).json()['data']['access_token']}"
m.patch("/mentors/me/profile", json={
    "mentor_type": "alumni", "professional_title": "Probe Title", "organisation": "Probe Org",
    "experience_years": 5, "graduation_year": 2015, "bio": "Probe mentor bio.",
    "expertise": [{"skill_id": skills[0]["skill_id"], "expertise_level": "advanced"}],
    "interest_ids": [interests[0]["interest_id"]], "submit_for_review": True})
mid = m.get("/mentors/me/profile").json()["data"]["mentor_id"]
adm.patch(f"/admin/mentors/{mid}/approval", json={"decision": "approve", "note": "probe"})

# request -> accept
b = s.post("/mentoring-requests", json={"mentor_id": mid, "career_goal": f"Probe goal long enough {run}."}).json()
rid = b["data"]["request_id"]
out["request detail (student view)"] = m.get(f"/mentoring-requests/{rid}").json()

start = (datetime.now(timezone.utc) + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
m.post("/mentors/me/availability", json={"slots": [
    {"start_time": start.isoformat(), "end_time": (start + timedelta(hours=1)).isoformat()}]})

r = m.post(f"/mentoring-requests/{rid}/accept")
out["accept response"] = r.json()
msid = r.json()["data"]["mentorship"]["mentorship_id"]
out["mentorship detail (student)"] = s.get(f"/mentorships/{msid}").json()
r = s.post(f"/mentorships/{msid}/sessions", json={"slot_id": m.get(f"/mentors/{mid}/availability").json()["data"][0]["slot_id"]})
out["book session response"] = r.json()
sess = r.json()["data"]["session_id"]
out["session detail"] = s.get(f"/sessions/{sess}").json()
out["mentorship sessions list"] = s.get(f"/mentorships/{msid}/sessions").json()
m.patch(f"/sessions/{sess}", json={"status": "completed", "shared_agenda": "Probe agenda", "outcome_notes": "Probe outcome"})
s.post(f"/sessions/{sess}/feedback", json={"rating": 5, "comments": "Probe feedback"})
out["session feedback list"] = s.get(f"/sessions/{sess}/feedback").json()
out["mentor own availability"] = m.get("/mentors/me/availability").json()
out["student sessions mine"] = s.get("/sessions").json()

json.dump(out, open(__file__.replace("shapes2.py", "shapes2.json"), "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
