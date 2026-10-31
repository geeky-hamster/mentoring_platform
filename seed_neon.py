"""Seed Neon database with demo data (admin, catalogues, demo users)."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.extensions import engine, SessionLocal
from app.models import User, Skill, CareerInterest
from app.services import auth_service
from app.core.security import hash_password as get_password_hash

def seed_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@example.org").first()
        if not admin:
            admin = User(
                email="admin@example.org",
                full_name="Programme Administrator",
                password_hash=get_password_hash("admin-password-123"),
                role="admin",
                account_status="active"
            )
            db.add(admin)
            db.commit()
            print("[OK] Admin created")
        else:
            print("[OK] Admin already exists")
    finally:
        db.close()

def seed_catalogues():
    db = SessionLocal()
    try:
        # Skills
        skills_data = [
            ("Python", "Programming Languages"),
            ("SQL", "Databases"),
            ("Data Visualisation", "Data Science"),
            ("Machine Learning", "Data Science"),
            ("AWS", "Cloud"),
            ("Docker", "DevOps"),
            ("React", "Frontend"),
            ("FastAPI", "Backend"),
            ("PostgreSQL", "Databases"),
            ("TypeScript", "Programming Languages"),
            ("REST APIs", "Backend"),
            ("GraphQL", "Backend"),
            ("Kubernetes", "DevOps"),
            ("CI/CD", "DevOps"),
            ("System Design", "Architecture"),
            ("Data Engineering", "Data Science"),
            ("Statistics", "Data Science"),
            ("Pandas", "Data Science"),
            ("NumPy", "Data Science"),
            ("Git", "DevOps"),
        ]
        for name, cat in skills_data:
            if not db.query(Skill).filter(Skill.skill_name == name).first():
                db.add(Skill(skill_name=name, category=cat, is_active=True))
        db.commit()
        print(f"[OK] Skills seeded ({len(skills_data)} total)")

        # Career Interests
        interests_data = [
            ("Data Science", "Analytics, ML, and statistical modelling"),
            ("Software Engineering", "Building scalable software systems"),
            ("Product Management", "Product strategy and roadmap"),
            ("DevOps Engineering", "Infrastructure, CI/CD, reliability"),
            ("Machine Learning Engineering", "Production ML systems"),
            ("Data Engineering", "Data pipelines and warehousing"),
            ("Backend Development", "Server-side development"),
            ("Frontend Development", "Client-side development"),
            ("Full Stack Development", "End-to-end development"),
            ("Cloud Architecture", "Cloud infrastructure design"),
            ("Cybersecurity", "Security engineering"),
            ("Mobile Development", "iOS/Android apps"),
            ("AI Research", "Cutting-edge AI research"),
            ("Technical Writing", "Documentation and communication"),
            ("Engineering Management", "Leading engineering teams"),
        ]
        for name, desc in interests_data:
            if not db.query(CareerInterest).filter(CareerInterest.interest_name == name).first():
                db.add(CareerInterest(interest_name=name, description=desc, is_active=True))
        db.commit()
        print(f"[OK] Career Interests seeded ({len(interests_data)} total)")
    finally:
        db.close()

def seed_demo():
    db = SessionLocal()
    try:
        from app.models import StudentProfile, MentorProfile, MentorExpertise, MentorInterests, StudentSkills, StudentInterests, AvailabilitySlot
        from datetime import datetime, timezone, timedelta
        from sqlalchemy import select

        # Get skill/interest IDs
        skills = {s.skill_name: s.skill_id for s in db.query(Skill).all()}
        interests = {i.interest_name: i.interest_id for i in db.query(CareerInterest).all()}

        python_id = skills.get("Python")
        sql_id = skills.get("SQL")
        aws_id = skills.get("AWS")
        docker_id = skills.get("Docker")
        react_id = skills.get("React")
        fastapi_id = skills.get("FastAPI")
        postgres_id = skills.get("PostgreSQL")
        typescript_id = skills.get("TypeScript")
        k8s_id = skills.get("Kubernetes")
        cicd_id = skills.get("CI/CD")
        sysdesign_id = skills.get("System Design")
        dataeng_id = skills.get("Data Engineering")
        stats_id = skills.get("Statistics")
        pandas_id = skills.get("Pandas")
        numpy_id = skills.get("NumPy")
        git_id = skills.get("Git")
        ml_id = skills.get("Machine Learning")
        dataviz_id = skills.get("Data Visualisation")

        ds_interest = interests.get("Data Science")
        se_interest = interests.get("Software Engineering")
        pm_interest = interests.get("Product Management")
        devops_interest = interests.get("DevOps Engineering")
        mleng_interest = interests.get("Machine Learning Engineering")
        dataeng_interest = interests.get("Data Engineering")
        backend_interest = interests.get("Backend Development")
        frontend_interest = interests.get("Frontend Development")
        fs_interest = interests.get("Full Stack Development")
        cloud_interest = interests.get("Cloud Architecture")

        # Demo users data
        users_data = [
            # Students
            ("asha.menon@example.org", "Asha Menon", "student", "correct-horse-battery-9"),
            ("vikram.shah@example.org", "Vikram Shah", "student", "correct-horse-battery-9"),
            ("ravi.kumar@example.org", "Ravi Kumar", "student", "correct-horse-battery-9"),
            # Mentors
            ("rohan.iyer@example.org", "Rohan Iyer", "mentor", "correct-horse-battery-9"),
            ("meera.nair@example.org", "Meera Nair", "mentor", "correct-horse-battery-9"),
            ("karthik.rao@example.org", "Karthik Rao", "mentor", "correct-horse-battery-9"),
            ("divya.sharma@example.org", "Divya Sharma", "mentor", "correct-horse-battery-9"),
            ("sanjay.patel@example.org", "Sanjay Patel", "mentor", "correct-horse-battery-9"),
            ("lakshmi.pillai@example.org", "Lakshmi Pillai", "mentor", "correct-horse-battery-9"),
        ]

        user_objects = {}
        for email, name, role, pwd in users_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    email=email,
                    full_name=name,
                    password_hash=get_password_hash(pwd),
                    role=role,
                    account_status="active"
                )
                db.add(user)
                db.flush()
            user_objects[email] = user

        db.commit()

        # Student profiles
        student_profiles_data = [
            ("asha.menon@example.org", "bsc_degree", 2027,
             "Build a data engineering portfolio and prepare for internship interviews.",
             "Project reviews, portfolio feedback and interview practice.",
             "Second-year student exploring data engineering and analytics.",
             [(python_id, "intermediate", True), (sql_id, "beginner", False)],
             [ds_interest]),
            ("vikram.shah@example.org", "diploma", 2026,
             "Transition into a data analyst role and build a public portfolio of dashboards.",
             "Feedback on dashboards and preparation for analyst interviews.",
             "Diploma student building analytics projects.",
             [(python_id, "beginner", True), (sql_id, "beginner", False)],
             [ds_interest]),
            ("ravi.kumar@example.org", "foundation", 2028,
             "Learn full stack development and contribute to open source.",
             "Code reviews, project guidance, career advice.",
             "Foundation student interested in web development.",
             [(react_id, "beginner", True), (typescript_id, "beginner", False), (git_id, "beginner", False)],
             [frontend_interest, fs_interest]),
        ]

        for email, stage, grad_year, career_goals, guidance_needs, bio, skill_list, interest_list in student_profiles_data:
            user = user_objects[email]
            profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.user_id).first()
            if not profile:
                profile = StudentProfile(
                    user_id=user.user_id,
                    programme_stage=stage,
                    expected_graduation_year=grad_year,
                    career_goals=career_goals,
                    guidance_needs=guidance_needs,
                    bio=bio,
                    profile_completed=True
                )
                db.add(profile)
                db.flush()
                for skill_id, prof, is_focus in skill_list:
                    db.add(StudentSkills(student_profile_id=profile.student_profile_id, skill_id=skill_id, proficiency_level=prof, is_focus=is_focus))
                for interest_id in interest_list:
                    db.add(StudentInterests(student_profile_id=profile.student_profile_id, interest_id=interest_id))

        # Mentor profiles - include reviewed_by/reviewed_at for approved profiles
        admin_user = db.query(User).filter(User.email == "admin@example.org").first()
        mentor_profiles_data = [
            ("rohan.iyer@example.org", "alumni", "Senior Data Engineer", "TechCorp", 8, 2016,
             "https://linkedin.com/in/rohanyer",
             "Building scalable data platforms. Helping students bridge academic and industry skills.",
             True, 3, "approved", admin_user.user_id,
             [(python_id, "expert"), (sql_id, "advanced"), (aws_id, "expert"), (docker_id, "advanced"), (k8s_id, "intermediate")],
             [ds_interest, backend_interest]),
            ("meera.nair@example.org", "recent_graduate", "ML Engineer", "AIStartup", 2, 2022,
             "https://linkedin.com/in/meeranair",
             "Production ML systems and MLOps. Recent grad helping students enter the field.",
             True, 2, "approved", admin_user.user_id,
             [(python_id, "advanced"), (ml_id, "expert"), (pandas_id, "advanced"), (numpy_id, "advanced"), (docker_id, "intermediate")],
             [mleng_interest, ds_interest]),
            ("karthik.rao@example.org", "alumni", "Product Manager", "ProductCo", 6, 2018,
             "https://linkedin.com/in/karthikrao",
             "Product strategy and execution. Mentoring on PM careers and product sense.",
             True, 2, "approved", admin_user.user_id,
             [(sql_id, "intermediate"), (stats_id, "advanced"), (sysdesign_id, "advanced")],
             [pm_interest, ds_interest]),
            ("divya.sharma@example.org", "alumni", "Staff Data Engineer", "BigDataInc", 10, 2014,
             "https://linkedin.com/in/divyasharma",
             "Large-scale data engineering. At capacity but existing mentees active.",
             True, 2, "approved", admin_user.user_id,  # at capacity
             [(python_id, "expert"), (sql_id, "expert"), (dataeng_id, "expert"), (aws_id, "expert"), (k8s_id, "expert")],
             [dataeng_interest, backend_interest]),
            ("sanjay.patel@example.org", "alumni", "DevOps Lead", "CloudCorp", 7, 2017,
             "https://linkedin.com/in/sanjaypatel",
             "Cloud infrastructure and DevOps. Currently paused.",
             False, 2, "approved", admin_user.user_id,  # paused
             [(aws_id, "expert"), (k8s_id, "expert"), (docker_id, "expert"), (cicd_id, "expert")],
             [devops_interest, cloud_interest]),
            ("lakshmi.pillai@example.org", "recent_graduate", "Frontend Developer", "WebAgency", 1, 2023,
             "https://linkedin.com/in/lakshmipillai",
             "React/TypeScript specialist. Profile pending review.",
             True, 2, "pending_review", None,
             [(react_id, "advanced"), (typescript_id, "advanced"), (fastapi_id, "beginner")],
             [frontend_interest, fs_interest]),
        ]

        for email, mtype, title, org, exp, grad, linkedin, bio, avail, max_mentees, status, reviewed_by, skill_list, interest_list in mentor_profiles_data:
            user = user_objects[email]
            profile = db.query(MentorProfile).filter(MentorProfile.user_id == user.user_id).first()
            if not profile:
                from datetime import datetime, timezone
                profile = MentorProfile(
                    user_id=user.user_id,
                    mentor_type=mtype,
                    professional_title=title,
                    organisation=org,
                    experience_years=exp,
                    graduation_year=grad,
                    linkedin_url=linkedin,
                    bio=bio,
                    is_available=avail,
                    max_active_mentees=max_mentees,
                    profile_status=status,
                    reviewed_by=reviewed_by,
                    reviewed_at=datetime.now(timezone.utc) if reviewed_by else None,
                )
                db.add(profile)
                db.flush()
                for skill_id, level in skill_list:
                    db.add(MentorExpertise(mentor_profile_id=profile.mentor_profile_id, skill_id=skill_id, expertise_level=level))
                for interest_id in interest_list:
                    db.add(MentorInterests(mentor_profile_id=profile.mentor_profile_id, interest_id=interest_id))

        db.commit()
        print("[OK] Demo users and profiles seeded")

        # Add availability slots for approved mentors
        now = datetime.now(timezone.utc)
        base = now + timedelta(days=1)
        for email, _, _, _, _, _, _, _, avail, _, status, _, _, _ in mentor_profiles_data:
            if not avail or email == "lakshmi.pillai@example.org" or status != "approved":
                continue
            user = user_objects[email]
            profile = db.query(MentorProfile).filter(MentorProfile.user_id == user.user_id).first()
            if profile:
                # Add a few slots over the next 2 weeks
                for week in range(2):
                    monday = base + timedelta(weeks=week)
                    for wd in [0, 2]:  # Mon, Wed
                        day = monday + timedelta(days=wd)
                        start = day.replace(hour=10, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                        end = day.replace(hour=11, minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
                        slot = AvailabilitySlot(
                            mentor_id=user.user_id,
                            start_time=start,
                            end_time=end,
                            is_available=True
                        )
                        db.add(slot)
        db.commit()
        print("[OK] Availability slots added")

        # Create mentoring requests and mentorships
        # Vikram -> Divya (accepted)
        vikram = user_objects["vikram.shah@example.org"]
        divya = user_objects["divya.sharma@example.org"]
        divya_profile = db.query(MentorProfile).filter(MentorProfile.user_id == divya.user_id).first()

        if divya_profile:
            from app.models import MentoringRequest, Mentorship
            req = db.query(MentoringRequest).filter(
                MentoringRequest.student_id == vikram.user_id,
                MentoringRequest.mentor_id == divya.user_id
            ).first()
            if not req:
                req = MentoringRequest(
                    student_id=vikram.user_id,
                    mentor_id=divya.user_id,
                    career_goal="Build production-grade data pipelines for analytics platform.",
                    message="Would value guidance on scaling data infrastructure.",
                    status="accepted",
                    created_at=datetime.now(timezone.utc) - timedelta(days=20),
                    responded_at=datetime.now(timezone.utc) - timedelta(days=19),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=14)
                )
                db.add(req)
                db.flush()

                ms = Mentorship(
                    request_id=req.request_id,
                    student_id=vikram.user_id,
                    mentor_id=divya.user_id,
                    status="active",
                    started_at=datetime.now(timezone.utc) - timedelta(days=19)
                )
                db.add(ms)
                db.flush()

                # Add a completed session with feedback
                from app.models import Session as SessionModel, Feedback
                slot = db.query(AvailabilitySlot).filter(
                    AvailabilitySlot.mentor_id == divya.user_id,
                    AvailabilitySlot.is_available == True
                ).first()
                if slot:
                    session = SessionModel(
                        mentorship_id=ms.mentorship_id,
                        student_id=vikram.user_id,
                        mentor_id=divya.user_id,
                        slot_id=slot.slot_id,
                        scheduled_start=datetime.now(timezone.utc) - timedelta(days=5),
                        scheduled_end=datetime.now(timezone.utc) - timedelta(days=5, hours=-1),
                        meeting_mode="online",
                        meeting_link="https://meet.example.com/vikram-divya-1",
                        status="completed",
                        notes="Discussed pipeline architecture and scaling strategies."
                    )
                    db.add(session)
                    db.flush()
                    slot.is_available = False
                    slot.booked = True

                    # Mentor feedback
                    fb = Feedback(
                        session_id=session.session_id,
                        submitted_by=divya.user_id,
                        rating=5,
                        comments="Excellent progress on the pipeline design. Good understanding of partitioning strategies."
                    )
                    db.add(fb)

                    # Student feedback
                    fb2 = Feedback(
                        session_id=session.session_id,
                        submitted_by=vikram.user_id,
                        rating=5,
                        comments="Very helpful session. The mentor's experience with large-scale systems was invaluable."
                    )
                    db.add(fb2)

        # Ravi -> Divya (accepted)
        ravi = user_objects["ravi.kumar@example.org"]
        req2 = db.query(MentoringRequest).filter(
            MentoringRequest.student_id == ravi.user_id,
            MentoringRequest.mentor_id == divya.user_id
        ).first()
        if not req2:
            req2 = MentoringRequest(
                student_id=ravi.user_id,
                mentor_id=divya.user_id,
                career_goal="Learn full stack development with React and FastAPI.",
                message="Want to build a portfolio project end-to-end.",
                status="accepted",
                created_at=datetime.now(timezone.utc) - timedelta(days=18),
                responded_at=datetime.now(timezone.utc) - timedelta(days=17),
                expires_at=datetime.now(timezone.utc) + timedelta(days=14)
            )
            db.add(req2)
            db.flush()

            ms2 = Mentorship(
                request_id=req2.request_id,
                student_id=ravi.user_id,
                mentor_id=divya.user_id,
                status="active",
                started_at=datetime.now(timezone.utc) - timedelta(days=17)
            )
            db.add(ms2)

        # Asha -> Rohan (pending, 12 days old for stale filter)
        asha = user_objects["asha.menon@example.org"]
        rohan = user_objects["rohan.iyer@example.org"]
        req3 = db.query(MentoringRequest).filter(
            MentoringRequest.student_id == asha.user_id,
            MentoringRequest.mentor_id == rohan.user_id
        ).first()
        if not req3:
            req3 = MentoringRequest(
                student_id=asha.user_id,
                mentor_id=rohan.user_id,
                career_goal="Transition into a data engineering role with a strong portfolio and interview readiness.",
                message="I admire your work at the data platform team. Would value guidance on building production-grade pipelines.",
                status="pending",
                created_at=datetime.now(timezone.utc) - timedelta(days=12),
                expires_at=datetime.now(timezone.utc) + timedelta(days=2)
            )
            db.add(req3)

        db.commit()
        print("[OK] Mentoring requests and mentorships seeded")

    finally:
        db.close()

if __name__ == "__main__":
    print("Seeding Neon database...")
    seed_admin()
    seed_catalogues()
    seed_demo()
    print("Done!")