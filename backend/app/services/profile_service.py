"""ProfileService (component C02): student onboarding/profile (E12-E13) and mentor
professional profile with review submission (E14-E15), plus public mentor view (E16)."""
from __future__ import annotations

from datetime import timedelta
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.errors import DomainError
from app.models import (CareerInterest, Feedback, MentorExpertise, MentorInterests, MentorProfile,
                        Mentorship, Skill, StudentInterests, StudentProfile, StudentSkills, User)
from app.serializers import mentor_profile_row, student_profile_row
from app.services import audit_service, notification_service

STAGES = ("foundation", "diploma", "bsc_degree", "bs_degree")
LEVELS = ("beginner", "intermediate", "advanced", "expert")


# ------------------------------------------------------------------ student profile (E12/E13)
def _student_profile(db: Session, user: User) -> StudentProfile:
    p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
    if p is None:  # profiles are created at registration; defensive repair
        p = StudentProfile(user_id=user.user_id, user_role="student")
        db.add(p)
        db.flush()
    return p


def _student_skills(db: Session, profile_id) -> list[dict]:
    rows = db.execute(
        select(StudentSkills, Skill)
        .join(Skill, Skill.skill_id == StudentSkills.skill_id)
        .where(StudentSkills.student_profile_id == profile_id)
        .order_by(Skill.skill_name)).all()
    return [{"skill_id": str(ss.skill_id), "skill_name": s.skill_name, "category": s.category,
             "proficiency_level": ss.proficiency_level, "is_focus": ss.is_focus} for ss, s in rows]


def _student_interests(db: Session, profile_id) -> list[dict]:
    rows = db.execute(
        select(StudentInterests, CareerInterest)
        .join(CareerInterest, CareerInterest.interest_id == StudentInterests.interest_id)
        .where(StudentInterests.student_profile_id == profile_id)
        .order_by(CareerInterest.interest_name)).all()
    return [{"interest_id": str(ci.interest_id), "interest_name": ci.interest_name} for _, ci in rows]


def get_student_profile(db: Session, user: User) -> dict:
    p = _student_profile(db, user)
    return student_profile_row(p, user.full_name, _student_skills(db, p.student_profile_id),
                               _student_interests(db, p.student_profile_id))


def _recompute_completed(p: StudentProfile, interests_count: int) -> None:
    """profile_completed: stage + career goals + at least one interest (design page 5)."""
    p.profile_completed = bool(p.programme_stage and (p.career_goals or "").strip() and interests_count > 0)


def update_student_profile(db: Session, user: User, payload: dict) -> dict:
    p = _student_profile(db, user)
    details = []
    if "full_name" in payload and payload["full_name"] is not None:
        name = str(payload["full_name"]).strip()
        if not (1 <= len(name) <= 120):
            details.append({"field": "full_name", "issue": "must be 1-120 characters"})
        else:
            user.full_name = name
    if "programme_stage" in payload and payload["programme_stage"] is not None:
        if payload["programme_stage"] not in STAGES:
            details.append({"field": "programme_stage", "issue": "must be one of " + "|".join(STAGES)})
        else:
            p.programme_stage = payload["programme_stage"]
    if "expected_graduation_year" in payload and payload["expected_graduation_year"] is not None:
        y = payload["expected_graduation_year"]
        if not isinstance(y, int) or not (2024 <= y <= 2100):
            details.append({"field": "expected_graduation_year", "issue": "must be between 2024 and 2100"})
        else:
            p.expected_graduation_year = y
    for key, limit in (("career_goals", 2000), ("guidance_needs", 2000), ("bio", 1000)):
        if key in payload and payload[key] is not None:
            value = str(payload[key])
            if len(value) > limit:
                details.append({"field": key, "issue": f"must be at most {limit} characters"})
            else:
                setattr(p, key, value or None)
    if "skills" in payload and payload["skills"] is not None:
        skills = payload["skills"]
        if not isinstance(skills, list):
            details.append({"field": "skills", "issue": "must be a list"})
        else:
            cleaned, focus = [], 0
            for item in skills:
                sid = item.get("skill_id")
                level = item.get("proficiency_level", "beginner")
                row = db.get(Skill, sid) if sid else None
                if row is None or not row.is_active:
                    details.append({"field": "skills", "issue": f"unknown skill {sid}"})
                    break
                if level not in LEVELS:
                    details.append({"field": "skills", "issue": f"proficiency_level must be one of {', '.join(LEVELS)}"})
                    break
                is_focus = bool(item.get("is_focus"))
                focus += 1 if is_focus else 0
                cleaned.append((sid, level, is_focus))
            if focus > 5:
                details.append({"field": "skills", "issue": "at most 5 focus skills"})
            if not details:
                db.query(StudentSkills).filter(StudentSkills.student_profile_id == p.student_profile_id).delete()
                for sid, level, is_focus in cleaned:
                    db.add(StudentSkills(student_profile_id=p.student_profile_id, skill_id=sid,
                                         proficiency_level=level, is_focus=is_focus))
    if "interest_ids" in payload and payload["interest_ids"] is not None:
        ids = list(dict.fromkeys(payload["interest_ids"]))
        found = db.scalars(select(CareerInterest.interest_id)
                           .where(CareerInterest.interest_id.in_([str(i) for i in ids]),
                                  CareerInterest.is_active == True)).all()  # noqa: E712
        unknown = [str(i) for i in ids if str(i) not in {str(x) for x in found}]
        if unknown:
            details.append({"field": "interest_ids", "issue": f"unknown career interests: {', '.join(unknown)}"})
        else:
            db.query(StudentInterests).filter(StudentInterests.student_profile_id == p.student_profile_id).delete()
            for i in ids:
                db.add(StudentInterests(student_profile_id=p.student_profile_id, interest_id=str(i)))
    if details:
        raise DomainError("VALIDATION_ERROR", details=details)
    interests_count = db.scalar(select(func.count()).select_from(
        select(StudentInterests.interest_id).where(StudentInterests.student_profile_id == p.student_profile_id).subquery()))
    _recompute_completed(p, interests_count or 0)
    return get_student_profile(db, user)


# ------------------------------------------------------------------ mentor profile (E14/E15)
def _mentor_profile(db: Session, user: User) -> MentorProfile:
    p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()
    if p is None:
        p = MentorProfile(user_id=user.user_id, user_role="mentor")
        db.add(p)
        db.flush()
    return p


def mentor_rating(db: Session, mentor_user_id) -> dict | None:
    """Average rating shown only when at least 3 ratings exist (design page 8)."""
    return _mentor_rating(db, mentor_user_id)


def _mentor_rating(db: Session, mentor_user_id) -> dict | None:
    from app.models import Session as SessionModel
    row = db.execute(
        select(func.avg(Feedback.rating), func.count())
        .select_from(Feedback)
        .join(SessionModel, SessionModel.session_id == Feedback.session_id)
        .where(SessionModel.mentor_id == mentor_user_id)).one()
    avg, count = row
    if (count or 0) < 3:
        return None
    return {"average": round(float(avg), 2), "count": int(count)}


def _mentor_expertise(db: Session, profile_id) -> list[dict]:
    rows = db.execute(
        select(MentorExpertise, Skill)
        .join(Skill, Skill.skill_id == MentorExpertise.skill_id)
        .where(MentorExpertise.mentor_profile_id == profile_id)
        .order_by(Skill.skill_name)).all()
    return [{"skill_id": str(me.skill_id), "skill_name": s.skill_name, "category": s.category,
             "expertise_level": me.expertise_level} for me, s in rows]


def _mentor_interests(db: Session, profile_id) -> list[dict]:
    rows = db.execute(
        select(MentorInterests, CareerInterest)
        .join(CareerInterest, CareerInterest.interest_id == MentorInterests.interest_id)
        .where(MentorInterests.mentor_profile_id == profile_id)
        .order_by(CareerInterest.interest_name)).all()
    return [{"interest_id": str(ci.interest_id), "interest_name": ci.interest_name} for _, ci in rows]


def get_mentor_profile(db: Session, user: User, *, include_review: bool = True) -> dict:
    p = _mentor_profile(db, user)
    return mentor_profile_row(
        p, user.full_name, _mentor_expertise(db, p.mentor_profile_id), _mentor_interests(db, p.mentor_profile_id),
        _mentor_rating(db, p.user_id),
        review=({"review_note": p.review_note, "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None}
                if include_review else None))


def public_mentor_profile(db: Session, viewer: User, mentor_id) -> dict:
    """E16: students see approved mentors only; admins see any status."""
    p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == mentor_id)).first()
    if p is None:
        raise DomainError("NOT_FOUND")
    is_admin = viewer.role == "admin"
    if not is_admin and (viewer.role != "student" or p.profile_status != "approved"):
        raise DomainError("NOT_FOUND")
    user = db.get(User, p.user_id)
    from datetime import datetime, timezone
    from app.models import AvailabilitySlot
    now = datetime.now(timezone.utc)
    open_slots = db.scalar(select(func.count()).select_from(
        select(AvailabilitySlot.slot_id)
        .where(AvailabilitySlot.mentor_id == p.user_id, AvailabilitySlot.is_available == True,  # noqa: E712
               AvailabilitySlot.start_time > now, AvailabilitySlot.start_time < now + timedelta(days=14)).subquery()))
    active = db.scalar(select(func.count()).select_from(
        select(Mentorship.mentorship_id).where(Mentorship.mentor_id == p.user_id, Mentorship.status == "active").subquery()))
    row = mentor_profile_row(
        p, user.full_name, _mentor_expertise(db, p.mentor_profile_id), _mentor_interests(db, p.mentor_profile_id),
        _mentor_rating(db, p.user_id),
        review=({"review_note": p.review_note, "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None}
                if is_admin else None),
        extra={"open_slots_14d": int(open_slots or 0), "free_mentee_spots": max(0, p.max_active_mentees - int(active or 0))})
    return row


def update_mentor_profile(db: Session, user: User, payload: dict, *, ip: str | None = None) -> dict:
    p = _mentor_profile(db, user)
    user_before = (user.full_name, p.mentor_type, p.professional_title, p.organisation, p.experience_years,
                   p.graduation_year, p.linkedin_url, p.bio, p.is_available, p.max_active_mentees)
    details = []
    if "full_name" in payload and payload["full_name"] is not None:
        name = str(payload["full_name"]).strip()
        if not (1 <= len(name) <= 120):
            details.append({"field": "full_name", "issue": "must be 1-120 characters"})
        else:
            user.full_name = name
    if "mentor_type" in payload and payload["mentor_type"] is not None:
        if payload["mentor_type"] not in ("recent_graduate", "alumni"):
            details.append({"field": "mentor_type", "issue": "must be recent_graduate or alumni"})
        else:
            p.mentor_type = payload["mentor_type"]
    for key, limit in (("professional_title", 120), ("organisation", 150)):
        if key in payload and payload[key] is not None:
            value = str(payload[key]).strip()
            if not (1 <= len(value) <= limit):
                details.append({"field": key, "issue": f"must be 1-{limit} characters"})
            else:
                setattr(p, key, value)
    if "experience_years" in payload and payload["experience_years"] is not None:
        y = payload["experience_years"]
        if not isinstance(y, int) or not (0 <= y <= 60):
            details.append({"field": "experience_years", "issue": "must be between 0 and 60"})
        else:
            p.experience_years = y
    if "graduation_year" in payload and payload["graduation_year"] is not None:
        y = payload["graduation_year"]
        if not isinstance(y, int) or not (2000 <= y <= 2100):
            details.append({"field": "graduation_year", "issue": "must be between 2000 and 2100"})
        else:
            p.graduation_year = y
    if "linkedin_url" in payload and payload["linkedin_url"] is not None:
        link = str(payload["linkedin_url"]).strip()
        if len(link) > 255:
            details.append({"field": "linkedin_url", "issue": "must be at most 255 characters"})
        else:
            p.linkedin_url = link or None
    if "bio" in payload and payload["bio"] is not None:
        value = str(payload["bio"])
        if len(value) > 1500:
            details.append({"field": "bio", "issue": "must be at most 1500 characters"})
        else:
            p.bio = value or None
    if "is_available" in payload and payload["is_available"] is not None:
        p.is_available = bool(payload["is_available"])
    if "max_active_mentees" in payload and payload["max_active_mentees"] is not None:
        cap = payload["max_active_mentees"]
        if not isinstance(cap, int) or not (1 <= cap <= 10):
            details.append({"field": "max_active_mentees", "issue": "must be between 1 and 10"})
    if not details and "max_active_mentees" in payload and payload["max_active_mentees"] is not None:
        active = db.scalar(select(func.count()).select_from(
            select(Mentorship.mentorship_id).where(Mentorship.mentor_id == p.user_id, Mentorship.status == "active").subquery()))
        if payload["max_active_mentees"] < (active or 0):
            details.append({"field": "max_active_mentees", "issue": "cannot be lower than the current number of active mentees"})
        else:
            p.max_active_mentees = payload["max_active_mentees"]
    if "expertise" in payload and payload["expertise"] is not None:
        items = payload["expertise"]
        if not isinstance(items, list):
            details.append({"field": "expertise", "issue": "must be a list"})
        else:
            cleaned = []
            for item in items:
                row = db.get(Skill, item.get("skill_id")) if item.get("skill_id") else None
                if row is None or not row.is_active:
                    details.append({"field": "expertise", "issue": f"unknown skill {item.get('skill_id')}"})
                    break
                level = item.get("expertise_level", "advanced")
                if level not in LEVELS:
                    details.append({"field": "expertise", "issue": "expertise_level must be one of " + ", ".join(LEVELS)})
                    break
                cleaned.append((item["skill_id"], level))
            if not details:
                db.query(MentorExpertise).filter(MentorExpertise.mentor_profile_id == p.mentor_profile_id).delete()
                for sid, level in cleaned:
                    db.add(MentorExpertise(mentor_profile_id=p.mentor_profile_id, skill_id=sid, expertise_level=level))
    if "interest_ids" in payload and payload["interest_ids"] is not None:
        ids = list(dict.fromkeys(payload["interest_ids"]))
        found = db.scalars(select(CareerInterest.interest_id)
                           .where(CareerInterest.interest_id.in_([str(i) for i in ids]),
                                  CareerInterest.is_active == True)).all()  # noqa: E712
        unknown = [str(i) for i in ids if str(i) not in {str(x) for x in found}]
        if unknown:
            details.append({"field": "interest_ids", "issue": f"unknown career interests: {', '.join(unknown)}"})
        else:
            db.query(MentorInterests).filter(MentorInterests.mentor_profile_id == p.mentor_profile_id).delete()
            for i in ids:
                db.add(MentorInterests(mentor_profile_id=p.mentor_profile_id, interest_id=str(i)))
    if details:
        raise DomainError("VALIDATION_ERROR", details=details)

    # audit + admin flag when an approved profile's professional claims change (report R-rules)
    if p.profile_status == "approved":
        changed_claims = [k for k, a, b in (
            ("professional_title", user_before[2], p.professional_title),
            ("organisation", user_before[3], p.organisation),
            ("linkedin_url", user_before[6], p.linkedin_url)) if a != b]
        if changed_claims:
            audit_service.record(db, user.user_id, "mentor.approved_profile_edited", "mentor_profile", p.user_id,
                                 {"fields": changed_claims}, ip)
            for admin in db.scalars(select(User).where(User.role == "admin")).all():
                notification_service.notify(db, admin.user_id, "Approved mentor profile edited",
                                            f"{user.full_name} edited {', '.join(changed_claims)}; re-check advised.",
                                            "mentor_reviewed", "mentor_profile", p.user_id)

    if payload.get("submit_for_review"):
        if p.profile_status not in ("draft", "rejected"):
            raise DomainError("INVALID_STATE_TRANSITION", "The profile is not awaiting an editable review state.")
        missing = []
        if not p.professional_title:
            missing.append("professional_title")
        if not p.organisation:
            missing.append("organisation")
        if p.experience_years is None:
            missing.append("experience_years")
        if not p.bio:
            missing.append("bio")
        if not (_mentor_expertise(db, p.mentor_profile_id)):
            missing.append("expertise")
        if missing:
            raise DomainError("VALIDATION_ERROR",
                              details=[{"field": m, "issue": "required before submitting for review"} for m in missing])
        p.profile_status = "pending_review"
        p.reviewed_by = None
        p.reviewed_at = None
        p.review_note = None
    return get_mentor_profile(db, user)
