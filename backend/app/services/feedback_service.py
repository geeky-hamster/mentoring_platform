"""FeedbackService (component C09): E38/E39. Rule R15."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import Feedback, Session as SessionModel, User
from app.serializers import feedback_row

cfg = config.cfg


def submit_feedback(db: Session, user: User, session_id, *, rating: int, comments: str | None) -> dict:
    s = db.get(SessionModel, session_id)
    if s is None:
        raise DomainError("NOT_FOUND")
    if user.user_id not in (s.student_id, s.mentor_id):
        raise DomainError("NOT_FOUND")
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "rating", "issue": "must be an integer between 1 and 5"}])
    if comments and len(comments) > 1000:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "comments", "issue": "must be at most 1000 characters"}])
    if s.status != "completed":
        raise DomainError("FEEDBACK_NOT_ALLOWED", "Feedback is allowed only for completed sessions.")
    end = s.scheduled_end if s.scheduled_end.tzinfo else s.scheduled_end.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > end + timedelta(days=cfg.FEEDBACK_WINDOW_DAYS):
        raise DomainError("FEEDBACK_NOT_ALLOWED", "The 14-day feedback window has closed.")
    existing = db.scalar(select(Feedback.feedback_id).where(
        Feedback.session_id == s.session_id, Feedback.submitted_by == user.user_id))
    if existing:
        raise DomainError("FEEDBACK_ALREADY_SUBMITTED")
    f = Feedback(session_id=s.session_id, submitted_by=user.user_id, rating=rating,
                 comments=(comments or "").strip() or None)
    db.add(f)
    db.flush()
    return feedback_row(f)


def visible_feedback(db: Session, user: User, session_id) -> dict:
    s = db.get(SessionModel, session_id)
    if s is None:
        raise DomainError("NOT_FOUND")
    if user.user_id not in (s.student_id, s.mentor_id) and user.role != "admin":
        raise DomainError("NOT_FOUND")
    rows = db.scalars(select(Feedback).where(Feedback.session_id == s.session_id)).all()
    visible = []
    for f in rows:
        if f.submitted_by == user.user_id:
            visible.append(f)  # own entry
        elif user.role == "admin":
            visible.append(f)  # admins see all
        elif user.role == "mentor" and f.submitted_by == s.student_id:
            visible.append(f)  # the mentor sees the student's entry
        elif user.role == "student" and f.submitted_by == s.mentor_id:
            visible.append(f)  # the student sees the mentor's entry
    names = {str(u.user_id): u.full_name for u in db.scalars(select(User)).all()}
    data = [feedback_row(f, submitted_by_name=names.get(str(f.submitted_by))) for f in visible]
    return {"data": data, "meta": meta(1, cfg.DEFAULT_PAGE_SIZE, len(data))}
