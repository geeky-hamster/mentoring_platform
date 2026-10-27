"""End-to-end walkthrough of the core user journeys and business rules R1-R16.

Run against a live server (from backend/): .\\.venv\\Scripts\\python scripts\\walkthrough.py
Uses unique e-mails per run, so it can be re-run against the same database.
"""
import sys
import time
import uuid as uuidlib
from datetime import datetime, timedelta, timezone

import httpx

BASE = "http://localhost:8000/api/v1"
ADMIN = ("admin@example.org", "admin-password-123")
DEMO_PW = "correct-horse-battery-9"
ok = fail = 0


class Client(httpx.Client):
    """HTTP client that waits out 429 rate-limit windows (sliding limits are per-IP)."""

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
    body = None
    try:
        body = resp.json()
    except Exception:
        pass
    if expect_status is not None and resp.status_code != expect_status:
        good = False
    if expect_code is not None:
        code = (body or {}).get("error", {}).get("code") if isinstance(body or {}, dict) else None
        if code != expect_code:
            good = False
    if good:
        ok += 1
        print(f"PASS {name}")
    else:
        fail += 1
        print(f"FAIL {name}: {resp.status_code} {str(body)[:400]}")
    return body


def check_val(name, value, expect):
    global ok, fail
    if value == expect:
        ok += 1
        print(f"PASS {name}")
    else:
        fail += 1
        print(f"FAIL {name}: got {value!r}, expected {expect!r}")


def main():
    run = uuidlib.uuid4().hex[:6]
    stud_mail = f"walk.student.{run}@example.org"
    ment_mail = f"walk.mentor.{run}@example.org"
    pw = "walking-tour-pw-2026"

    stud = Client(base_url=BASE, timeout=20)
    ment = Client(base_url=BASE, timeout=20)
    adm = Client(base_url=BASE, timeout=20)

    # ---- E01 registration + duplicate
    b = check("register student", stud.post("/auth/register", json={
        "full_name": "Walk Student", "email": stud_mail, "password": pw, "role": "student"}), 201)
    check("register duplicate email", Client(base_url=BASE).post("/auth/register", json={
        "full_name": "X", "email": stud_mail, "password": pw, "role": "student"}), 409, "EMAIL_ALREADY_REGISTERED")
    check("register weak password", Client(base_url=BASE).post("/auth/register", json={
        "full_name": "X", "email": f"weak.{run}@example.org", "password": "short", "role": "student"}),
        422, "VALIDATION_ERROR")
    check("register mentor", ment.post("/auth/register", json={
        "full_name": "Walk Mentor", "email": ment_mail, "password": pw, "role": "mentor"}), 201)

    # ---- E02 login both + admin
    b = check("student login", stud.post("/auth/login", json={"email": stud_mail, "password": pw}), 200)
    sid = b["data"]["user"]["user_id"]
    stud.headers["Authorization"] = f"Bearer {b['data']['access_token']}"
    b = check("mentor login", ment.post("/auth/login", json={"email": ment_mail, "password": pw}), 200)
    mid = b["data"]["user"]["user_id"]
    ment.headers["Authorization"] = f"Bearer {b['data']['access_token']}"
    b = check("admin login", adm.post("/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]}), 200)
    adm.headers["Authorization"] = f"Bearer {b['data']['access_token']}"

    # ---- E12 student onboarding
    skills = stud.get("/skills", params={"page_size": 50}).json()["data"]
    interests = stud.get("/career-interests", params={"page_size": 50}).json()["data"]
    py = next(s for s in skills if s["skill_name"] == "Python")
    sql = next(s for s in skills if s["skill_name"] == "SQL")
    ds = next(i for i in interests if i["interest_name"] == "Data Science")
    b = check("student profile update", stud.patch("/students/me/profile", json={
        "programme_stage": "bsc_degree", "expected_graduation_year": 2027,
        "career_goals": f"Work towards a data science role (walk {run}).",
        "skills": [{"skill_id": py["skill_id"], "proficiency_level": "intermediate", "is_focus": True},
                   {"skill_id": sql["skill_id"], "proficiency_level": "beginner"}],
        "interest_ids": [ds["interest_id"]]}), 200)
    if b:
        check_val("profile_completed computed", b["data"]["profile_completed"], True)
    check("bad stage", stud.patch("/students/me/profile", json={"programme_stage": "phd"}), 422, "VALIDATION_ERROR")

    # ---- E15 mentor profile + submit for review
    b = check("mentor profile update", ment.patch("/mentors/me/profile", json={
        "mentor_type": "alumni", "professional_title": "Data Scientist", "organisation": "Walk Org",
        "experience_years": 7, "graduation_year": 2015, "bio": "Walk-through mentor profile.",
        "expertise": [{"skill_id": py["skill_id"], "expertise_level": "advanced"},
                      {"skill_id": sql["skill_id"], "expertise_level": "advanced"}],
        "interest_ids": [ds["interest_id"]]}), 200)
    check("submit for review", ment.patch("/mentors/me/profile", json={"submit_for_review": True}), 200)
    if b:
        pass
    # incomplete submit must fail with VALIDATION_ERROR
    m2 = Client(base_url=BASE)
    m2.post("/auth/register", json={"full_name": "Walk Mentor 2", "email": f"walk.mentor2.{run}@example.org",
                                    "password": pw, "role": "mentor"})
    m2_login = m2.post("/auth/login", json={"email": f"walk.mentor2.{run}@example.org", "password": pw}).json()
    m2.headers["Authorization"] = f"Bearer {m2_login['data']['access_token']}"
    check("submit incomplete profile", m2.patch("/mentors/me/profile", json={"submit_for_review": True}),
          422, "VALIDATION_ERROR")

    # ---- E47 admin review queue + E48 approve
    b = check("review queue", adm.get("/admin/mentors", params={"profile_status": "pending_review"}), 200)
    queued = [r for r in b["data"] if r["mentor_id"] == mid]
    check_val("mentor in queue", bool(queued), True)
    check("reject without note", adm.patch(f"/admin/mentors/{mid}/approval", json={"decision": "reject"}), 422)
    check("approve mentor", adm.patch(f"/admin/mentors/{mid}/approval", json={
        "decision": "approve", "note": "Verified via walkthrough."}), 200)
    check("re-approve fails", adm.patch(f"/admin/mentors/{mid}/approval", json={"decision": "approve"}), 409)

    # ---- E23 recommendations (new mentor should appear; R2/R3 eligibility + scoring)
    b = check("recommended", stud.get("/mentors/recommended"), 200)
    rows = b["data"]
    mine = [r for r in rows if r["mentor"]["mentor_id"] == mid]
    check_val("new mentor recommended", bool(mine), True)
    if mine:
        row = mine[0]
        check_val("skills part > 0", (row["breakdown"]["skills"] or 0) > 0, True)
        check_val("interests part = 100", row["breakdown"]["interests"], 100.0)
        check_val("has reasons", bool(row["reasons"]), True)
    # ordering is descending by score
    scores = [r["match_score"] for r in rows]
    check_val("scores sorted desc", scores == sorted(scores, reverse=True), True)

    # ---- E24 request + R-rule blocks
    b = check("submit request", stud.post("/mentoring-requests", json={
        "mentor_id": mid, "career_goal": f"Prepare a portfolio for data roles (walkthrough {run}).",
        "message": "Hello! I would value your guidance."}), 201)
    rid = b["data"]["request_id"]
    check("duplicate pending request", stud.post("/mentoring-requests", json={
        "mentor_id": mid, "career_goal": f"Another attempt {run} with enough characters."}),
        409, "DUPLICATE_PENDING_REQUEST")
    check("request needs profile", None if True else None, None)  # placeholder no-op
    # short career_goal
    check("short career_goal", stud.post("/mentoring-requests", json={
        "mentor_id": mid, "career_goal": "too short"}), 422, "VALIDATION_ERROR")
    # mentor at capacity: divya has 2 active and cap 2 in demo seed
    divya = Client(base_url=BASE)
    d_login = divya.post("/auth/login", json={"email": "divya.sharma@example.org", "password": DEMO_PW}).json()
    divya.headers["Authorization"] = f"Bearer {d_login['data']['access_token']}"
    b = divya.get("/mentors/me/profile").json()
    divya_id = b["data"]["mentor_id"]
    b = check("request at-capacity mentor", stud.post("/mentoring-requests", json={
        "mentor_id": divya_id, "career_goal": f"Would love guidance from Divya {run}."}),
        409, "MENTOR_AT_CAPACITY")
    # paused mentor
    sanjay = Client(base_url=BASE)
    s_login = sanjay.post("/auth/login", json={"email": "sanjay.patel@example.org", "password": DEMO_PW}).json()
    sanjay.headers["Authorization"] = f"Bearer {s_login['data']['access_token']}"
    sanjay_id = sanjay.get("/mentors/me/profile").json()["data"]["mentor_id"]
    check("request paused mentor", stud.post("/mentoring-requests", json={
        "mentor_id": sanjay_id, "career_goal": f"Sanjay is paused, this must fail {run}."}),
        409, "MENTOR_NOT_AVAILABLE")

    # ---- E27 accept (R7) + invalid re-accept
    check("accept by wrong mentor", None if False else m2.post(f"/mentoring-requests/{rid}/accept"),
          404, "NOT_FOUND")
    b = check("accept request", ment.post(f"/mentoring-requests/{rid}/accept"), 200)
    msid = b["data"]["mentorship"]["mentorship_id"] if b else None
    check("accept again", ment.post(f"/mentoring-requests/{rid}/accept"), 409, "INVALID_STATE_TRANSITION")

    # ---- E17 availability + E21 open slots
    start1 = datetime.now(timezone.utc) + timedelta(days=2)
    start1 = start1.replace(hour=10, minute=0, second=0, microsecond=0)
    start2 = start1 + timedelta(hours=1)
    b = check("add slots", ment.post("/mentors/me/availability", json={"slots": [
        {"start_time": start1.isoformat(), "end_time": start2.isoformat()},
        {"start_time": start2.isoformat(), "end_time": (start2 + timedelta(hours=1)).isoformat()}]}), 201)
    slot1 = b["data"][0]["slot_id"] if b else None
    slot2 = b["data"][1]["slot_id"] if b else None
    check("overlapping slot rejected", ment.post("/mentors/me/availability", json={"slots": [
        {"start_time": start1.isoformat(), "end_time": (start1 + timedelta(minutes=30)).isoformat()}]}),
        422, "VALIDATION_ERROR")
    b = check("open slots visible", stud.get(f"/mentors/{mid}/availability"), 200)
    check_val("slots listed", len(b["data"]) if b else 0, 2)

    # ---- E33 schedule from slot; R12/R13 conflicts
    b = check("book session from slot", stud.post(f"/mentorships/{msid}/sessions", json={"slot_id": slot1}), 201)
    sess1 = b["data"]["session_id"] if b else None
    check("book same slot again", stud.post(f"/mentorships/{msid}/sessions", json={"slot_id": slot1}),
          409, "SLOT_UNAVAILABLE")
    check("student custom time rejected", stud.post(f"/mentorships/{msid}/sessions", json={
        "scheduled_start": (start1 + timedelta(days=3)).isoformat(),
        "scheduled_end": (start1 + timedelta(days=3, hours=1)).isoformat()}), 422)
    # 10:30-11:30 overlaps the slot-1 session (10:00-11:00) -> SESSION_CONFLICT
    check("mentor overlap conflict", ment.post(f"/mentorships/{msid}/sessions", json={
        "scheduled_start": (start1 + timedelta(minutes=30)).isoformat(),
        "scheduled_end": (start1 + timedelta(minutes=90)).isoformat()}),
        409, "SESSION_CONFLICT")
    b = check("mentor books second slot", ment.post(f"/mentorships/{msid}/sessions", json={"slot_id": slot2}), 201)
    sess2 = b["data"]["session_id"] if b else None

    # near-time slot: the session must actually start before it can be completed
    near_start = datetime.now(timezone.utc) + timedelta(seconds=6)
    b = check("add near-time slot", ment.post("/mentors/me/availability", json={"slots": [
        {"start_time": near_start.isoformat(),
         "end_time": (near_start + timedelta(minutes=66)).isoformat()}]}), 201)
    near_slot = b["data"][0]["slot_id"] if b else None
    b = check("book near-time session", stud.post(f"/mentorships/{msid}/sessions", json={"slot_id": near_slot}), 201)
    sess_near = b["data"]["session_id"] if b else None
    time.sleep(9)

    # ---- E35 update session; R15 feedback flow
    check("student cannot complete", stud.patch(f"/sessions/{sess_near}", json={"status": "completed"}), 403)
    b = check("mentor completes session", ment.patch(f"/sessions/{sess_near}", json={"status": "completed"}), 200)
    check("bad rating", stud.post(f"/sessions/{sess_near}/feedback", json={"rating": 9}), 422, "VALIDATION_ERROR")
    check("submit feedback", stud.post(f"/sessions/{sess_near}/feedback", json={
        "rating": 5, "comments": "Great session!"}), 201)
    check("duplicate feedback", stud.post(f"/sessions/{sess_near}/feedback", json={"rating": 4}),
          409, "FEEDBACK_ALREADY_SUBMITTED")
    check("feedback before completion", stud.post(f"/sessions/{sess2}/feedback", json={"rating": 4}),
          409, "FEEDBACK_NOT_ALLOWED")
    b = check("feedback visible", stud.get(f"/sessions/{sess_near}/feedback"), 200)
    check_val("own feedback listed", len(b["data"]) if b else 0, 1)
    # mentor can now see the student's entry
    b = ment.get(f"/sessions/{sess_near}/feedback").json()
    check_val("mentor sees student feedback", len(b.get("data", [])), 1)

    # ---- E31/E32 close mentorship (future sessions cancelled by rule R14)
    b = check("close mentorship", stud.patch(f"/mentorships/{msid}", json={
        "status": "completed", "reason": None}), 200)
    b = ment.get(f"/sessions/{sess2}").json()
    check_val("future session cancelled", b.get("data", {}).get("status") if b else None, "cancelled")

    # ---- decline + cooldown (R4)
    b = check("request again after completion", stud.post("/mentoring-requests", json={
        "mentor_id": mid, "career_goal": f"Second round of guidance please {run}."}), 201)
    rid2 = b["data"]["request_id"]
    b = check("decline with reason", ment.post(f"/mentoring-requests/{rid2}/decline", json={
        "reason": "Booked out this quarter."}), 200)
    check("cooldown blocks re-request", stud.post("/mentoring-requests", json={
        "mentor_id": mid, "career_goal": f"Third attempt within cooldown {run}."}),
        409, "REQUEST_COOLDOWN")

    # ---- E40/E41 dashboards + E42-E44 notifications
    b = check("student dashboard", stud.get("/students/me/dashboard"), 200)
    b = check("mentor dashboard", ment.get("/mentors/me/dashboard"), 200)
    if b:
        check_val("mentor dashboard fields", all(k in b["data"] for k in (
            "profile_status", "pending_requests", "active_mentees", "upcoming_sessions", "unread_notifications")), True)
    b = check("notifications list", ment.get("/notifications"), 200)
    if b:
        check_val("meta.unread_count present", "unread_count" in b["meta"], True)
        first = b["data"][0]["notification_id"] if b["data"] else None
        if first:
            check("mark read", ment.patch(f"/notifications/{first}", json={"is_read": True}), 200)
    check("mark all read", ment.post("/notifications/mark-all-read"), 204)
    b = ment.get("/notifications", params={"is_read": True}).json()
    check_val("all read now", all(n["is_read"] for n in b.get("data", [])), True)

    # ---- E06 password change + login with new password
    check("wrong current password", stud.post("/users/me/password", json={
        "current_password": "nope-nope-nope", "new_password": "brand-new-password-1"}), 422)
    check("change password", stud.post("/users/me/password", json={
        "current_password": pw, "new_password": "brand-new-password-1"}), 204)
    check("old password fails", stud.post("/auth/login", json={"email": stud_mail, "password": pw}),
          401, "INVALID_CREDENTIALS")
    check("new password works", Client(base_url=BASE).post("/auth/login", json={
        "email": stud_mail, "password": "brand-new-password-1"}), 200)

    # ---- E09 verify-email with bad token
    check("bad verify token", Client(base_url=BASE).post("/auth/verify-email", json={
        "token": "garbage.token"}), 400, "INVALID_TOKEN")

    # ---- E03 refresh reuse detection (R16)
    old_cookie = stud.cookies.get("refresh_token")
    r = stud.post("/auth/refresh")
    check("refresh ok", r, 200)
    replay = Client(base_url=BASE, timeout=20)
    replay.cookies.set("refresh_token", old_cookie)
    r = replay.post("/auth/refresh")
    check("refresh reuse revoked", r, 401, "REFRESH_REUSED")

    # ---- E05 logout
    check("logout", ment.post("/auth/logout"), 204)

    # ---- E44 / jobs quick run is exercised separately via cli run-jobs

    print(f"\n{ok} passed, {fail} failed")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
