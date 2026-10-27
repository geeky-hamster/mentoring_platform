"""Serializers: model rows to the exact response shapes of the API contract (api.py COMP)."""
from __future__ import annotations

from app.models import (AvailabilitySlot, AuditLog, CareerInterest, Feedback, Mentorship,
                        MentoringRequest, MentorProfile, Notification, Session, Skill,
                        StudentProfile, User)

ISO = lambda d: d.isoformat() if d else None  # noqa: E731


def user_row(u: User, *, profile_completed: bool = False, profile_status: str | None = None) -> dict:
    return {"user_id": str(u.user_id), "full_name": u.full_name, "email": u.email, "role": u.role,
            "account_status": u.account_status, "email_verified": u.email_verified,
            "profile_completed": profile_completed, "profile_status": profile_status,
            "created_at": ISO(u.created_at)}


def skill_row(s: Skill) -> dict:
    return {"skill_id": str(s.skill_id), "skill_name": s.skill_name, "category": s.category, "is_active": s.is_active}


def interest_row(c: CareerInterest) -> dict:
    return {"interest_id": str(c.interest_id), "interest_name": c.interest_name,
            "description": c.description, "is_active": c.is_active}


def student_profile_row(p: StudentProfile, full_name: str, skills: list[dict], interests: list[dict]) -> dict:
    return {"student_profile_id": str(p.student_profile_id), "user_id": str(p.user_id), "full_name": full_name,
            "programme_stage": p.programme_stage, "expected_graduation_year": p.expected_graduation_year,
            "career_goals": p.career_goals, "guidance_needs": p.guidance_needs, "bio": p.bio,
            "profile_completed": p.profile_completed, "skills": skills, "interests": interests}


def mentor_profile_row(p: MentorProfile, full_name: str, expertise: list[dict], interests: list[dict],
                       rating: dict | None, *, linkedin: str | None = None, review: dict | None = None,
                       extra: dict | None = None) -> dict:
    row = {"mentor_id": str(p.user_id), "full_name": full_name, "mentor_type": p.mentor_type,
           "professional_title": p.professional_title, "organisation": p.organisation,
           "experience_years": p.experience_years, "graduation_year": p.graduation_year,
           "bio": p.bio, "is_available": p.is_available, "max_active_mentees": p.max_active_mentees,
           "profile_status": p.profile_status, "expertise": expertise, "interests": interests,
           "rating": rating}
    row["linkedin_url"] = linkedin if linkedin is not None else p.linkedin_url
    if review is not None:
        row.update(review)  # review_note / reviewed_at / reviewed_by (admins)
    if extra:
        row.update(extra)
    return row


def slot_row(s: AvailabilitySlot, *, booked: bool = False) -> dict:
    return {"slot_id": str(s.slot_id), "start_time": ISO(s.start_time), "end_time": ISO(s.end_time),
            "is_available": s.is_available, "booked": booked}


def request_row(r: MentoringRequest, *, student_name=None, mentor_name=None, extra: dict | None = None) -> dict:
    row = {"request_id": str(r.request_id), "student_id": str(r.student_id), "mentor_id": str(r.mentor_id),
           "career_goal": r.career_goal, "message": r.message, "status": r.status,
           "status_reason": r.status_reason, "created_at": ISO(r.created_at),
           "responded_at": ISO(r.responded_at), "expires_at": ISO(r.expires_at)}
    if student_name is not None:
        row["student_name"] = student_name
    if mentor_name is not None:
        row["mentor_name"] = mentor_name
    if extra:
        row.update(extra)
    return row


def mentorship_row(m: Mentorship, *, student_name=None, mentor_name=None, extra: dict | None = None) -> dict:
    row = {"mentorship_id": str(m.mentorship_id), "request_id": str(m.request_id),
           "student_id": str(m.student_id), "mentor_id": str(m.mentor_id), "status": m.status,
           "started_at": ISO(m.started_at), "ended_at": ISO(m.ended_at), "end_reason": m.end_reason}
    if student_name is not None:
        row["student_name"] = student_name
    if mentor_name is not None:
        row["mentor_name"] = mentor_name
    if extra:
        row.update(extra)
    return row


def session_row(s: Session, *, my_feedback_submitted: bool = False, extra: dict | None = None) -> dict:
    row = {"session_id": str(s.session_id), "mentorship_id": str(s.mentorship_id),
           "slot_id": str(s.slot_id) if s.slot_id else None,
           "student_id": str(s.student_id), "mentor_id": str(s.mentor_id),
           "scheduled_start": ISO(s.scheduled_start), "scheduled_end": ISO(s.scheduled_end),
           "meeting_mode": s.meeting_mode, "meeting_link": s.meeting_link, "status": s.status,
           "notes": s.notes, "my_feedback_submitted": my_feedback_submitted}
    if extra:
        row.update(extra)
    return row


def feedback_row(f: Feedback, *, submitted_by_name: str | None = None) -> dict:
    row = {"feedback_id": str(f.feedback_id), "session_id": str(f.session_id),
           "submitted_by": str(f.submitted_by), "rating": f.rating, "comments": f.comments,
           "created_at": ISO(f.created_at)}
    if submitted_by_name is not None:
        row["submitted_by_name"] = submitted_by_name
    return row


def notification_row(n: Notification) -> dict:
    return {"notification_id": str(n.notification_id), "title": n.title, "message": n.message,
            "notification_type": n.notification_type, "related_entity_type": n.related_entity_type,
            "related_entity_id": str(n.related_entity_id) if n.related_entity_id else None,
            "is_read": n.is_read, "created_at": ISO(n.created_at)}


def audit_row(a: AuditLog) -> dict:
    return {"audit_id": str(a.audit_id), "actor_user_id": str(a.actor_user_id) if a.actor_user_id else None,
            "action": a.action, "entity_type": a.entity_type, "entity_id": str(a.entity_id),
            "details": a.details, "created_at": ISO(a.created_at)}
