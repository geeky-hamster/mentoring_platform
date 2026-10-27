"""MentoringService (components C06/C07): requests (E24-E29), mentorships (E30-E32).

Business rules R1-R8 and R14 are enforced here; the database (schema.sql) enforces the
same rules again as defence in depth.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app import config
from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import (Feedback, Mentorship, MentoringRequest, MentorProfile, Session as SessionModel,
                        StudentProfile, User, AvailabilitySlot)
from app.serializers import mentorship_row, request_row
from app.services import audit_service, matching_service, notification_service

cfg = config.cfg
PENDING, ACCEPTED, DECLINED, CANCELLED, EXPIRED = "pending", "accepted", "declined", "cancelled", "expired"


def _student_profile(db: Session, user_id):
    return db.scalars(select(StudentProfile).where(StudentProfile.user_id == user_id)).first()


def _mentor_profile(db: Session, user_id):
    return db.scalars(select(MentorProfile).where(MentorProfile.user_id == user_id)).first()


# ------------------------------------------------------------------ E24
def create_request(db: Session, student_user: User, *, mentor_id, career_goal: str, message: str | None,
                   ip: str | None) -> dict:
    p = _student_profile(db, student_user.user_id)
    if p is None or not p.profile_completed:
        raise DomainError("PROFILE_INCOMPLETE")
    goal = (career_goal or "").strip()
    if not (20 <= len(goal) <= 1000):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "career_goal", "issue": "must be between 20 and 1000 characters"}])
    if message is not None and len(message) > 1500:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "message", "issue": "must be at most 1500 characters"}])
    mentor_user = db.get(User, mentor_id)
    mp = _mentor_profile(db, mentor_id)
    if mp is None or mentor_user is None:
        raise DomainError("NOT_FOUND")
    if mp.profile_status != "approved" or mentor_user.account_status != "active" or not mp.is_available:
        raise DomainError("MENTOR_NOT_AVAILABLE")
    capacity = db.scalar(select(func.count()).select_from(
        select(Mentorship.mentorship_id).where(Mentorship.mentor_id == mentor_id,
              Mentorship.status == "active").subquery()))
    if (capacity or 0) >= mp.max_active_mentees:
        raise DomainError("MENTOR_AT_CAPACITY")
    active_pair = db.scalar(select(func.count()).select_from(
        select(Mentorship.mentorship_id).where(Mentorship.student_id == student_user.user_id,
              Mentorship.mentor_id == mentor_id, Mentorship.status == "active").subquery()))
    if active_pair:
        raise DomainError("ACTIVE_MENTORSHIP_EXISTS")
    pending_pair = db.scalar(select(func.count()).select_from(
        select(MentoringRequest.request_id).where(MentoringRequest.student_id == student_user.user_id,
              MentoringRequest.mentor_id == mentor_id, MentoringRequest.status == PENDING).subquery()))
    if pending_pair:
        raise DomainError("DUPLICATE_PENDING_REQUEST")
    cooldown = db.scalars(
        select(MentoringRequest).where(MentoringRequest.student_id == student_user.user_id,
                                       MentoringRequest.mentor_id == mentor_id, MentoringRequest.status == DECLINED)
        .order_by(MentoringRequest.responded_at.desc())).first()
    if cooldown and cooldown.responded_at and datetime.now(timezone.utc) < cooldown.responded_at + timedelta(days=cfg.COOLDOWN_DAYS):
        retry_at = cooldown.responded_at + timedelta(days=cfg.COOLDOWN_DAYS)
        raise DomainError("REQUEST_COOLDOWN",
                          f"You can request this mentor again on {retry_at.date().isoformat()}.",
                          headers={"Retry-After": str(int((retry_at - datetime.now(timezone.utc)).total_seconds()))})
    pending_count = db.scalar(select(func.count()).select_from(
        select(MentoringRequest.request_id).where(MentoringRequest.student_id == student_user.user_id,
              MentoringRequest.status == PENDING).subquery()))
    if (pending_count or 0) >= cfg.MAX_PENDING_REQUESTS:
        raise DomainError("PENDING_LIMIT_REACHED")
    now = datetime.now(timezone.utc)
    r = MentoringRequest(student_id=student_user.user_id, mentor_id=mentor_id, career_goal=goal,
                         message=(message or "").strip() or None, status=PENDING,
                         expires_at=now + timedelta(days=cfg.REQUEST_EXPIRY_DAYS))
    db.add(r)
    db.flush()
    mentor_user_row = db.get(User, mentor_id)
    notification_service.notify(db, mentor_id, "New mentoring request",
                                f"{student_user.full_name} sent you a mentoring request.",
                                "request_received", "mentoring_request", r.request_id)
    audit_service.record(db, student_user.user_id, "request.submitted", "mentoring_request", r.request_id,
                         {"mentor_id": str(mentor_id)}, ip)
    return request_row(r, mentor_name=mentor_user_row.full_name)


# ------------------------------------------------------------------ E25/E26
def list_requests(db: Session, user: User, *, status: str | None, page: int, page_size: int) -> dict:
    stmt = select(MentoringRequest)
    if user.role == "student":
        stmt = stmt.where(MentoringRequest.student_id == user.user_id)
    elif user.role == "mentor":
        stmt = stmt.where(MentoringRequest.mentor_id == user.user_id)
    else:
        raise DomainError("FORBIDDEN")
    if status:
        if status not in (PENDING, ACCEPTED, DECLINED, CANCELLED, EXPIRED):
            raise DomainError("BAD_REQUEST", "Unknown request status filter.")
        stmt = stmt.where(MentoringRequest.status == status)
    rows = db.scalars(stmt.order_by(MentoringRequest.created_at.desc())).all()
    users = {str(u.user_id): u.full_name for u in db.scalars(select(User)).all()}
    data = []
    for r in rows:
        data.append(request_row(r, student_name=users.get(str(r.student_id)), mentor_name=users.get(str(r.mentor_id))))
    start = (max(1, page) - 1) * page_size
    return {"data": data[start:start + page_size], "meta": meta(page, page_size, len(data))}


def get_request(db: Session, user: User, request_id, *, include_profile: bool) -> dict:
    r = db.get(MentoringRequest, request_id)
    if r is None:
        raise DomainError("NOT_FOUND")
    involved = user.user_id in (r.student_id, r.mentor_id)
    if not involved and user.role != "admin":
        raise DomainError("NOT_FOUND")
    student_user = db.get(User, r.student_id)
    mentor_user = db.get(User, r.mentor_id)
    extra = {}
    if (user.role == "mentor" and r.mentor_id == user.user_id) or user.role == "admin":
        if include_profile:
            from app.models import CareerInterest, StudentInterests
            from app.services import profile_service
            p = _student_profile(db, r.student_id)
            skills, interests = [], []
            if p is not None:
                skills = profile_service._student_skills(db, p.student_profile_id)
                interests = db.execute(
                    select(CareerInterest.interest_name)
                    .join(StudentInterests, StudentInterests.interest_id == CareerInterest.interest_id)
                    .where(StudentInterests.student_profile_id == p.student_profile_id)).scalars().all()
            extra["student_summary"] = {
                "programme_stage": p.programme_stage if p else None,
                "expected_graduation_year": p.expected_graduation_year if p else None,
                "bio": p.bio if p else None,
                "career_goals": p.career_goals if p else None,
                "guidance_needs": p.guidance_needs if p else None,
                "skills": skills, "interests": list(interests),
            }
    row = request_row(r, student_name=student_user.full_name if student_user else None,
                      mentor_name=mentor_user.full_name if mentor_user else None, extra=extra)
    if r.status == ACCEPTED:
        ms = db.scalars(select(Mentorship).where(Mentorship.request_id == r.request_id)).first()
        if ms is not None:
            row["mentorship_id"] = str(ms.mentorship_id)
    return row


# ------------------------------------------------------------------ E27 accept (R7)
def accept_request(db: Session, mentor_user: User, request_id, *, ip: str | None) -> dict:
    # lock order (contract Section 2.6): request row first, then the mentor profile row
    db.execute(select(MentoringRequest).where(MentoringRequest.request_id == request_id).with_for_update())
    r = db.get(MentoringRequest, request_id)
    if r is None or r.mentor_id != mentor_user.user_id:
        raise DomainError("NOT_FOUND")
    db.execute(select(MentorProfile).where(MentorProfile.user_id == mentor_user.user_id).with_for_update())
    mp = _mentor_profile(db, mentor_user.user_id)
    if r.status != PENDING:
        raise DomainError("INVALID_STATE_TRANSITION", f"The request is {r.status}, not pending.")
    if datetime.now(timezone.utc) >= r.expires_at:
        r.status = EXPIRED
        db.commit()  # persist the expiry even though we answer 409
        raise DomainError("INVALID_STATE_TRANSITION", "The request has expired.")
    active = db.scalar(select(func.count()).select_from(
        select(Mentorship.mentorship_id).where(Mentorship.mentor_id == mentor_user.user_id,
              Mentorship.status == "active").subquery()))
    if active >= mp.max_active_mentees:
        raise DomainError("MENTOR_AT_CAPACITY")
    if db.scalar(select(func.count()).select_from(
            select(Mentorship.mentorship_id).where(Mentorship.student_id == r.student_id,
                  Mentorship.mentor_id == r.mentor_id, Mentorship.status == "active").subquery())):
        raise DomainError("ACTIVE_MENTORSHIP_EXISTS")
    r.status = ACCEPTED
    r.responded_at = datetime.now(timezone.utc)
    ms = Mentorship(request_id=r.request_id, student_id=r.student_id, mentor_id=r.mentor_id, status="active")
    db.add(ms)
    db.flush()
    student_user = db.get(User, r.student_id)
    notification_service.notify(db, r.student_id, "Request accepted",
                                f"{mentor_user.full_name} accepted your mentoring request.",
                                "request_accepted", "mentorship", ms.mentorship_id)
    audit_service.record(db, mentor_user.user_id, "request.accepted", "mentoring_request", r.request_id,
                         {"mentorship_id": str(ms.mentorship_id)}, ip)
    return {"request": request_row(r, student_name=student_user.full_name if student_user else None),
            "mentorship": mentorship_row(ms)}


# ------------------------------------------------------------------ E28 decline / E29 cancel (R4, R5)
def decline_request(db: Session, mentor_user: User, request_id, *, reason: str | None, ip: str | None) -> dict:
    r = db.get(MentoringRequest, request_id)
    if r is None or r.mentor_id != mentor_user.user_id:
        raise DomainError("NOT_FOUND")
    if r.status != PENDING:
        raise DomainError("INVALID_STATE_TRANSITION", f"The request is {r.status}, not pending.")
    if reason and len(reason) > 500:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "reason", "issue": "must be at most 500 characters"}])
    r.status = DECLINED
    r.status_reason = (reason or "").strip() or None
    r.responded_at = datetime.now(timezone.utc)
    student_user = db.get(User, r.student_id)
    notification_service.notify(db, r.student_id, "Request declined",
                                f"{mentor_user.full_name} declined your mentoring request"
                                + (f": {r.status_reason}" if r.status_reason else "."),
                                "request_declined", "mentoring_request", r.request_id)
    audit_service.record(db, mentor_user.user_id, "request.declined", "mentoring_request", r.request_id, {}, ip)
    return request_row(r, student_name=student_user.full_name if student_user else None)


def cancel_request(db: Session, student_user: User, request_id, *, reason: str | None, ip: str | None) -> dict:
    r = db.get(MentoringRequest, request_id)
    if r is None or r.student_id != student_user.user_id:
        raise DomainError("NOT_FOUND")
    if r.status != PENDING:
        raise DomainError("INVALID_STATE_TRANSITION", f"The request is {r.status}, not pending.")
    if reason and len(reason) > 500:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "reason", "issue": "must be at most 500 characters"}])
    r.status = CANCELLED
    r.status_reason = (reason or "").strip() or None
    mentor_user = db.get(User, r.mentor_id)
    notification_service.notify(db, r.mentor_id, "Request cancelled",
                                f"{student_user.full_name} cancelled their mentoring request.",
                                "request_cancelled", "mentoring_request", r.request_id)
    audit_service.record(db, student_user.user_id, "request.cancelled", "mentoring_request", r.request_id, {}, ip)
    return request_row(r, mentor_name=mentor_user.full_name if mentor_user else None)


# ------------------------------------------------------------------ E30/E31/E32 (R14)
def list_mentorships(db: Session, user: User, *, status: str | None, page: int, page_size: int) -> dict:
    stmt = select(Mentorship)
    if user.role == "student":
        stmt = stmt.where(Mentorship.student_id == user.user_id)
    elif user.role == "mentor":
        stmt = stmt.where(Mentorship.mentor_id == user.user_id)
    if status:
        if status not in ("active", "completed", "ended"):
            raise DomainError("BAD_REQUEST", "Unknown mentorship status filter.")
        stmt = stmt.where(Mentorship.status == status)
    rows = db.scalars(stmt.order_by(Mentorship.started_at.desc())).all()
    users = {str(u.user_id): u.full_name for u in db.scalars(select(User)).all()}
    data = [mentorship_row(m, student_name=users.get(str(m.student_id)), mentor_name=users.get(str(m.mentor_id)))
            for m in rows]
    start = (max(1, page) - 1) * page_size
    return {"data": data[start:start + page_size], "meta": meta(page, page_size, len(data))}


def _session_stats(db: Session, mentorship_id) -> dict:
    rows = db.execute(select(SessionModel.status, func.count()).where(
        SessionModel.mentorship_id == mentorship_id).group_by(SessionModel.status)).all()
    by = {s: int(c) for s, c in rows}
    completed = by.get("completed", 0)
    scheduled = by.get("scheduled", 0)
    last = db.scalar(select(func.max(SessionModel.scheduled_start)).where(
        SessionModel.mentorship_id == mentorship_id, SessionModel.status.in_(("completed", "scheduled"))))
    return {"sessions_completed": completed, "sessions_scheduled": scheduled, "last_session_at": last.isoformat() if last else None}


def get_mentorship(db: Session, user: User, mentorship_id) -> dict:
    m = db.get(Mentorship, mentorship_id)
    if m is None:
        raise DomainError("NOT_FOUND")
    if user.user_id not in (m.student_id, m.mentor_id) and user.role != "admin":
        raise DomainError("NOT_FOUND")
    student_user = db.get(User, m.student_id)
    mentor_user = db.get(User, m.mentor_id)
    r = db.get(MentoringRequest, m.request_id)
    return mentorship_row(m, student_name=student_user.full_name if student_user else None,
                          mentor_name=mentor_user.full_name if mentor_user else None,
                          extra={"career_goal": r.career_goal if r else None,
                                 "originating_request": {"request_id": str(r.request_id), "status": r.status} if r else None,
                                 **_session_stats(db, m.mentorship_id)})


def close_mentorship(db: Session, user: User, mentorship_id, *, status: str, reason: str | None,
                     ip: str | None) -> dict:
    m = db.get(Mentorship, mentorship_id)
    if m is None:
        raise DomainError("NOT_FOUND")
    if user.user_id not in (m.student_id, m.mentor_id) and user.role != "admin":
        raise DomainError("NOT_FOUND")
    if status not in ("completed", "ended"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "status", "issue": "must be completed or ended"}])
    if m.status != "active":
        raise DomainError("INVALID_STATE_TRANSITION", f"The mentorship is already {m.status}.")
    if status == "ended" and not (reason or "").strip():
        raise DomainError("VALIDATION_ERROR", details=[{"field": "reason", "issue": "a reason is required when ending early"}])
    if (reason or "") and len(reason) > 500:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "reason", "issue": "must be at most 500 characters"}])
    now = datetime.now(timezone.utc)
    m.status = status
    m.ended_at = now
    m.ended_by = user.user_id
    m.end_reason = (reason or "").strip() or None
    # cancel future scheduled sessions; slots are released implicitly (uq_session_slot_booked is status-scoped)
    future = db.scalars(select(SessionModel).where(
        SessionModel.mentorship_id == m.mentorship_id, SessionModel.status == "scheduled",
        SessionModel.scheduled_end > now)).all()
    for s in future:
        s.status = "cancelled"
        s.cancelled_by = user.user_id
        s.cancel_reason = "mentorship ended"
    other_id = m.mentor_id if user.user_id == m.student_id else m.student_id
    notification_service.notify(db, other_id, "Mentorship ended",
                                f"Your mentorship was {status} by {user.full_name}.",
                                "mentorship_ended", "mentorship", m.mentorship_id)
    if user.role == "admin":
        notification_service.notify(db, m.student_id if other_id == m.mentor_id else m.mentor_id,
                                    "Mentorship ended", "An administrator closed the mentorship.",
                                    "mentorship_ended", "mentorship", m.mentorship_id)
    audit_service.record(db, user.user_id, "mentorship.closed", "mentorship", m.mentorship_id,
                         {"status": status}, ip)
    student_user = db.get(User, m.student_id)
    mentor_user = db.get(User, m.mentor_id)
    return mentorship_row(m, student_name=student_user.full_name if student_user else None,
                          mentor_name=mentor_user.full_name if mentor_user else None)
