"""Management commands: seed-admin, seed-catalogues, seed-demo, run-jobs.

Admins are created only here (never self-registered), per the API contract for E01.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app import config
from app.core import security
from app.extensions import SessionLocal
from app.models import (AvailabilitySlot, CareerInterest, Feedback, MentorExpertise, MentorInterests,
                        MentorProfile, Mentorship, MentoringRequest, Session as SessionModel, Skill,
                        StudentInterests, StudentProfile, StudentSkills, User)

SKILLS = [
    ("Python", "Programming"), ("SQL", "Data"), ("Machine Learning", "Data"), ("Statistics", "Data"),
    ("Data Visualisation", "Data"), ("Deep Learning", "Data"), ("Java", "Programming"), ("C++", "Programming"),
    ("Web Development", "Programming"), ("React", "Programming"), ("Node.js", "Programming"),
    ("Databases", "Data"), ("Cloud Computing", "Infrastructure"), ("DevOps", "Infrastructure"),
    ("Cybersecurity", "Infrastructure"), ("Product Management", "Business"), ("Communication", "Professional"),
    ("Public Speaking", "Professional"), ("Technical Writing", "Professional"), ("Project Management", "Business"),
    ("Data Structures", "Programming"), ("Algorithms", "Programming"), ("Entrepreneurship", "Business"),
    ("Financial Modelling", "Business"), ("UI/UX Design", "Design"), ("Graphic Design", "Design"),
    ("Research Methods", "Academic"), ("Academic Writing", "Academic"), ("Electronics", "Engineering"),
    ("Embedded Systems", "Engineering"),
]

INTERESTS = [
    ("Data Science", "Analytics, machine learning and data-driven roles"),
    ("Software Engineering", "Building software systems and services"),
    ("Higher Studies", "Masters and doctoral programmes in India or abroad"),
    ("Product Management", "Product discovery, delivery and strategy"),
    ("Consulting", "Advisory roles across industries"),
    ("Entrepreneurship", "Founding or joining early-stage ventures"),
    ("Civil Services", "Public administration careers"),
    ("Finance", "Investment, risk and quantitative finance"),
    ("Design", "Product, UX and visual design careers"),
    ("Electronics", "VLSI, embedded and hardware careers"),
    ("Research", "Academic and industrial research"),
    ("Marketing", "Growth, brand and product marketing"),
]


def _session():
    db = SessionLocal()
    return db


def seed_admin() -> None:
    db = _session()
    try:
        existing = db.scalars(select(User).where(User.email == config.cfg.ADMIN_EMAIL.lower())).first()
        if existing:
            print(f"admin already exists: {existing.email}")
            return
        db.add(User(full_name="Programme Administrator", email=config.cfg.ADMIN_EMAIL.lower(),
                    password_hash=security.hash_password(config.cfg.ADMIN_PASSWORD), role="admin",
                    account_status="active"))
        db.commit()
        print(f"created admin {config.cfg.ADMIN_EMAIL} (password from ADMIN_PASSWORD env)")
    finally:
        db.close()


def seed_catalogues() -> None:
    db = _session()
    try:
        existing = {name for name, in db.execute(select(Skill.skill_name)).all()}
        added = 0
        for name, category in SKILLS:
            if name not in existing:
                db.add(Skill(skill_name=name, category=category))
                added += 1
        existing_i = {name for name, in db.execute(select(CareerInterest.interest_name)).all()}
        for name, description in INTERESTS:
            if name not in existing_i:
                db.add(CareerInterest(interest_name=name, description=description))
                added += 1
        db.commit()
        print(f"catalogues seeded ({added} rows added)")
    finally:
        db.close()


def _get_skill(db, name) -> Skill:
    return db.scalars(select(Skill).where(Skill.skill_name == name)).first()


def _get_interest(db, name) -> CareerInterest:
    return db.scalars(select(CareerInterest).where(CareerInterest.interest_name == name)).first()


def _make_user(db, *, name, email, role, password) -> User:
    user = User(full_name=name, email=email, password_hash=security.hash_password(password),
                role=role, account_status="active", email_verified=True)
    db.add(user)
    db.flush()
    if role == "student":
        db.add(StudentProfile(user_id=user.user_id, user_role="student"))
    else:
        db.add(MentorProfile(user_id=user.user_id, user_role="mentor"))
    return user


def _complete_student(db, user: User, *, stage="bsc_degree", grad=2027, focus):
    p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
    p.programme_stage = stage
    p.expected_graduation_year = grad
    p.career_goals = "Grow into an industry role that matches my interests and build a portfolio."
    p.guidance_needs = "Project guidance, interview preparation and course selection."
    p.bio = "Programme student eager to learn from mentors who have walked this path."
    interests = ["Data Science", "Higher Studies", "Software Engineering"]
    for i in interests[:2]:
        ci = _get_interest(db, i)
        if ci:
            db.add(StudentInterests(student_profile_id=p.student_profile_id, interest_id=ci.interest_id))
    for i, level in focus:
        s = _get_skill(db, i)
        if s:
            db.add(StudentSkills(student_profile_id=p.student_profile_id, skill_id=s.skill_id,
                                 proficiency_level=level, is_focus=True))
    p.profile_completed = True
    return p


def seed_demo() -> None:
    """Sample data mirroring the report's worked example (Section 10) for local exploration."""
    db = _session()
    try:
        if db.scalars(select(User).where(User.email == "asha.menon@example.org")).first():
            print("demo data already present; skipping")
            return
        pw = "correct-horse-battery-9"
        now = datetime.now(timezone.utc)
        admin_user = db.scalars(select(User).where(User.role == "admin")).first()

        # students
        asha = _make_user(db, name="Asha Menon", email="asha.menon@example.org", role="student", password=pw)
        vikram = _make_user(db, name="Vikram Shah", email="vikram.shah@example.org", role="student", password=pw)
        ravi = _make_user(db, name="Ravi Kumar", email="ravi.kumar@example.org", role="student", password=pw)
        _complete_student(db, asha, focus=[("Python", "intermediate"), ("SQL", "beginner"), ("Machine Learning", "beginner")])
        _complete_student(db, vikram, focus=[("Python", "beginner")])
        _complete_student(db, ravi, focus=[("SQL", "intermediate")])

        # mentors: Rohan / Meera / Karthik are eligible; Divya at capacity; Sanjay paused; Lakshmi pending review
        rohan = _make_user(db, name="Rohan Iyer", email="rohan.iyer@example.org", role="mentor", password=pw)
        meera = _make_user(db, name="Meera Nair", email="meera.nair@example.org", role="mentor", password=pw)
        karthik = _make_user(db, name="Karthik Rao", email="karthik.rao@example.org", role="mentor", password=pw)
        divya = _make_user(db, name="Divya Sharma", email="divya.sharma@example.org", role="mentor", password=pw)
        sanjay = _make_user(db, name="Sanjay Patel", email="sanjay.patel@example.org", role="mentor", password=pw)
        lakshmi = _make_user(db, name="Lakshmi Pillai", email="lakshmi.pillai@example.org", role="mentor", password=pw)

        def mentor_setup(m, *, title, org, years, skills, interests, status="approved", available=True, cap=3):
            p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == m.user_id)).first()
            p.mentor_type = "alumni"
            p.professional_title = title
            p.organisation = org
            p.experience_years = years
            p.graduation_year = 2016
            p.linkedin_url = "https://www.linkedin.com/example"
            p.bio = f"{title} at {org}. Happy to help programme students with projects and careers."
            p.is_available = available
            p.max_active_mentees = cap
            if status in ("approved", "suspended", "rejected"):
                # ck_mentor_reviewed: record the reviewer before flipping the status
                if admin_user is not None:
                    p.reviewed_by = admin_user.user_id
                    p.reviewed_at = now - timedelta(days=10)
            p.profile_status = status
            for s, level in skills:
                sk = _get_skill(db, s)
                if sk:
                    db.add(MentorExpertise(mentor_profile_id=p.mentor_profile_id, skill_id=sk.skill_id,
                                           expertise_level=level))
            for i in interests:
                ci = _get_interest(db, i)
                if ci:
                    db.add(MentorInterests(mentor_profile_id=p.mentor_profile_id, interest_id=ci.interest_id))
            # open slots on the next three weekdays
            base = now + timedelta(days=1)
            for d in range(2, 16):
                day = base + timedelta(days=d)
                if day.weekday() < 5:
                    start = day.replace(hour=13, minute=0, second=0, microsecond=0)
                    db.add(AvailabilitySlot(mentor_id=m.user_id, start_time=start,
                                            end_time=start + timedelta(hours=1), is_available=True))
            return p

        mentor_setup(rohan, title="Senior Data Scientist", org="Example Analytics Pvt Ltd", years=6,
                     skills=[("Python", "advanced"), ("SQL", "advanced"), ("Machine Learning", "intermediate")],
                     interests=["Data Science"], cap=3)
        mentor_setup(meera, title="Research Engineer", org="Example Research Lab", years=5,
                     skills=[("Python", "intermediate"), ("Machine Learning", "expert"), ("Statistics", "advanced")],
                     interests=["Data Science", "Higher Studies"], cap=2)
        mentor_setup(karthik, title="Software Engineer", org="Example Software Ltd", years=4,
                     skills=[("Python", "advanced"), ("SQL", "beginner")],
                     interests=["Higher Studies"], cap=3)
        mentor_setup(divya, title="Engineering Manager", org="Example Cloud Ltd", years=9,
                     skills=[("Python", "expert"), ("SQL", "expert"), ("Machine Learning", "expert")],
                     interests=["Data Science", "Higher Studies"], cap=2)
        mentor_setup(sanjay, title="Principal Engineer", org="Example Systems", years=11,
                     skills=[("Python", "expert")], interests=["Data Science"], available=False)
        mentor_setup(lakshmi, title="Data Analyst", org="Example Health", years=3,
                     skills=[("Python", "advanced"), ("SQL", "advanced")], interests=["Data Science"],
                     status="pending_review")

        # Divya is at capacity: two active mentorships
        def pair(student, mentor, goal="Advance towards a data role with a strong portfolio."):
            r = MentoringRequest(student_id=student.user_id, mentor_id=mentor.user_id, career_goal=goal,
                                 status="accepted", created_at=now - timedelta(days=20),
                                 responded_at=now - timedelta(days=19), expires_at=now + timedelta(days=8))
            db.add(r)
            db.flush()
            ms = Mentorship(request_id=r.request_id, student_id=student.user_id, mentor_id=mentor.user_id,
                            status="active", started_at=now - timedelta(days=19))
            db.add(ms)
            return ms

        ms1 = pair(vikram, divya)
        ms2 = pair(ravi, divya)
        # a completed session + feedback for Divya & Vikram (rating history)
        s1_start = now - timedelta(days=5)
        s1 = SessionModel(
            mentorship_id=ms1.mentorship_id, student_id=vikram.user_id, mentor_id=divya.user_id,
            scheduled_start=s1_start, scheduled_end=s1_start + timedelta(hours=1), status="completed",
            meeting_mode="online", notes="Kick-off: goals and portfolio plan.")
        db.add(s1)
        db.flush()
        db.add(Feedback(session_id=s1.session_id, submitted_by=vikram.user_id, rating=5,
                        comments="Very helpful first session."))
        db.add(Feedback(session_id=s1.session_id, submitted_by=divya.user_id, rating=4, comments=None))

        # a pending request for the mentor queue
        db.add(MentoringRequest(student_id=asha.user_id, mentor_id=rohan.user_id,
               career_goal="Move into a data science role after graduation and need portfolio advice.",
               message="Hello Rohan, your path into industry matches what I am aiming for.",
               status="pending", created_at=now - timedelta(days=1), expires_at=now + timedelta(days=13)))

        db.commit()
        print("demo data seeded:")
        print("  admin:       admin@example.org / ADMIN_PASSWORD (default admin-password-123)")
        print("  student:     asha.menon@example.org / correct-horse-battery-9")
        print("  mentors:     rohan.iyer@ / meera.nair@ / karthik.rao@ / divya.sharma@ / sanjay.patel@ / lakshmi.pillai@ (example.org, same password)")
    finally:
        db.close()


def run_jobs() -> None:
    from app.jobs import runner as jobs
    print(jobs.run_all())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"
    if cmd == "seed-admin":
        seed_admin()
    elif cmd == "seed-catalogues":
        seed_catalogues()
    elif cmd == "seed-demo":
        seed_admin()
        seed_catalogues()
        seed_demo()
    elif cmd == "run-jobs":
        run_jobs()
    else:
        print("usage: python -m app.cli seed-admin|seed-catalogues|seed-demo|run-jobs")
