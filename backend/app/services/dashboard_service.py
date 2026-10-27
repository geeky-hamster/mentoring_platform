"""Dashboard read models (components C10/C12): E40 student, E41 mentor."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (Feedback, MentorProfile, Mentorship, MentoringRequest, Notification,
                        Session as SessionModel, User)
from app.serializers import session_row
from app.services import notification_service


def student_dashboard(db: Session, user) -> dict:
    now = datetime.now(timezone.utc)
    pending = db.scalar(select(func.count()).select_from(MentoringRequest).where(
        MentoringRequest.student_id == user.user_id, MentoringRequest.status == "pending")) or 0
    active = db.scalar(select(func.count()).select_from(Mentorship).where(
        Mentorship.student_id == user.user_id, Mentorship.status == "active")) or 0
    next_session = None
    row = db.scalars(select(SessionModel).where(
        SessionModel.student_id == user.user_id, SessionModel.status == "scheduled",
        SessionModel.scheduled_start >= now).order_by(SessionModel.scheduled_start)).first()
    if row is not None:
        mentor = db.get(User, row.mentor_id)
        next_session = session_row(row, extra={"mentor_name": mentor.full_name if mentor else None})
    unread = notification_service.unread_count(db, user.user_id)
    from app.models import StudentProfile
    profile = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
    return {"profile_completed": bool(profile.profile_completed) if profile else False,
            "pending_requests": int(pending), "active_mentorships": int(active),
            "next_session": next_session, "unread_notifications": int(unread)}


def mentor_dashboard(db: Session, user) -> dict:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()
    pending = db.scalar(select(func.count()).select_from(MentoringRequest).where(
        MentoringRequest.mentor_id == user.user_id, MentoringRequest.status == "pending")) or 0
    active = db.scalar(select(func.count()).select_from(Mentorship).where(
        Mentorship.mentor_id == user.user_id, Mentorship.status == "active")) or 0
    upcoming_rows = db.scalars(select(SessionModel).where(
        SessionModel.mentor_id == user.user_id, SessionModel.status == "scheduled",
        SessionModel.scheduled_start >= now).order_by(SessionModel.scheduled_start).limit(5)).all()
    from app.models import StudentProfile
    upcoming = []
    for s in upcoming_rows:
        student = db.scalars(select(User).join(StudentProfile, StudentProfile.user_id == User.user_id)
                             .where(User.user_id == s.student_id)).first()
        upcoming.append(session_row(s, extra={"student_name": student.full_name if student else None}))
    rating = None
    row = db.execute(select(func.avg(Feedback.rating), func.count())
                     .select_from(Feedback)
                     .join(SessionModel, SessionModel.session_id == Feedback.session_id)
                     .where(SessionModel.mentor_id == user.user_id)).one()
    if (row[1] or 0) >= 3:
        rating = {"average": round(float(row[0]), 2), "count": int(row[1])}
    return {"profile_status": p.profile_status if p else "draft",
            "pending_requests": int(pending), "active_mentees": int(active),
            "max_active_mentees": p.max_active_mentees if p else 3,
            "upcoming_sessions": upcoming, "rating_summary": rating,
            "unread_notifications": notification_service.unread_count(db, user.user_id)}
