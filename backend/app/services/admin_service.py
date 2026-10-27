"""AdminService (component C11): users (E45/E46), mentor review queue (E47/E48),
oversight lists (E49/E50), audit trail listing (E54)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import (MentorProfile, Mentorship, MentoringRequest, Notification, RefreshToken,
                        Session as SessionModel, User)
from app.serializers import audit_row, mentor_profile_row, mentorship_row, request_row, user_row
from app.services import audit_service, notification_service, profile_service


def list_users(db: Session, *, role: str | None, account_status: str | None, q: str | None,
               page: int, page_size: int) -> dict:
    stmt = select(User)
    if role:
        if role not in ("student", "mentor", "admin"):
            raise DomainError("BAD_REQUEST", "Unknown role filter.")
        stmt = stmt.where(User.role == role)
    if account_status:
        if account_status not in ("active", "suspended", "deactivated"):
            raise DomainError("BAD_REQUEST", "Unknown account status filter.")
        stmt = stmt.where(User.account_status == account_status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(like), User.email.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"data": [{"user_id": str(u.user_id), "full_name": u.full_name, "email": u.email, "role": u.role,
                      "account_status": u.account_status,
                      "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
                      "created_at": u.created_at.isoformat()} for u in rows],
            "meta": meta(page, page_size, total or 0)}


def change_user_status(db: Session, admin: User, user_id, *, account_status: str, reason: str | None,
                       ip: str | None) -> dict:
    if account_status not in ("active", "suspended", "deactivated"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "account_status", "issue": "must be active, suspended or deactivated"}])
    target = db.get(User, user_id)
    if target is None:
        raise DomainError("NOT_FOUND")
    if target.user_id == admin.user_id:
        raise DomainError("FORBIDDEN", "An administrator cannot change their own status.")
    if target.account_status == account_status:
        raise DomainError("INVALID_STATE_TRANSITION", f"The account is already {account_status}.")
    target.account_status = account_status
    now = datetime.now(timezone.utc)
    if account_status in ("suspended", "deactivated"):
        db.execute(RefreshToken.__table__.update()
                   .where(RefreshToken.user_id == target.user_id, RefreshToken.revoked_at.is_(None))
                   .values(revoked_at=now, revoked_reason="admin_action"))
        if target.role == "mentor":
            pending = db.scalars(select(MentoringRequest).where(
                MentoringRequest.mentor_id == target.user_id, MentoringRequest.status == "pending")).all()
            for r in pending:
                r.status = "cancelled"
                r.status_reason = "mentor suspended"
                notification_service.notify(db, r.student_id, "Request cancelled",
                                            "The mentor is currently unavailable; the request was cancelled.",
                                            "request_cancelled", "mentoring_request", r.request_id)
    notification_service.notify(db, target.user_id, "Account status changed",
                                f"Your account is now {account_status}"
                                + (f": {reason}" if reason else "."),
                                "account_status_changed", "user", target.user_id)
    audit_service.record(db, admin.user_id, f"user.{account_status}", "user", target.user_id,
                         {"reason": reason}, ip)
    return {"user_id": str(target.user_id), "full_name": target.full_name, "email": target.email,
            "role": target.role, "account_status": target.account_status,
            "last_login_at": target.last_login_at.isoformat() if target.last_login_at else None,
            "created_at": target.created_at.isoformat()}


# ------------------------------------------------------------------ E47/E48
def list_mentor_queue(db: Session, *, profile_status: str | None, q: str | None, page: int, page_size: int) -> dict:
    stmt = select(MentorProfile, User).join(User, User.user_id == MentorProfile.user_id)
    status = profile_status or "pending_review"
    if status not in ("draft", "pending_review", "approved", "rejected", "suspended"):
        raise DomainError("BAD_REQUEST", "Unknown profile status filter.")
    stmt = stmt.where(MentorProfile.profile_status == status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(User.full_name.ilike(like), MentorProfile.organisation.ilike(like),
                              MentorProfile.professional_title.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.execute(stmt.order_by(MentorProfile.updated_at.asc()).offset((page - 1) * page_size).limit(page_size)).all()
    data = []
    for p, u in rows:
        data.append(mentor_profile_row(
            p, u.full_name, profile_service._mentor_expertise(db, p.mentor_profile_id),
            profile_service._mentor_interests(db, p.mentor_profile_id),
            profile_service._mentor_rating(db, p.user_id),
            review={"review_note": p.review_note, "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None},
            extra={"email": u.email, "account_status": u.account_status,
                   "created_at": p.created_at.isoformat(), "updated_at": p.updated_at.isoformat()}))
    return {"data": data, "meta": meta(page, page_size, total or 0)}


def decide_mentor(db: Session, admin: User, mentor_id, *, decision: str, note: str | None,
                  ip: str | None) -> dict:
    if decision not in ("approve", "reject", "suspend"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "decision", "issue": "must be approve, reject or suspend"}])
    p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == mentor_id)).first()
    if p is None:
        raise DomainError("NOT_FOUND")
    if decision == "reject" and not (note or "").strip():
        raise DomainError("VALIDATION_ERROR", details=[{"field": "note", "issue": "a note is required when rejecting"}])
    now = datetime.now(timezone.utc)
    if decision == "approve":
        if p.profile_status not in ("pending_review", "suspended", "rejected"):
            raise DomainError("INVALID_STATE_TRANSITION", f"Cannot approve a profile that is {p.profile_status}.")
        p.profile_status = "approved"
    elif decision == "reject":
        if p.profile_status not in ("pending_review",):
            raise DomainError("INVALID_STATE_TRANSITION", f"Cannot reject a profile that is {p.profile_status}.")
        p.profile_status = "rejected"
    else:  # suspend
        if p.profile_status not in ("approved", "pending_review"):
            raise DomainError("INVALID_STATE_TRANSITION", f"Cannot suspend a profile that is {p.profile_status}.")
        p.profile_status = "suspended"
        pending = db.scalars(select(MentoringRequest).where(
            MentoringRequest.mentor_id == mentor_id, MentoringRequest.status == "pending")).all()
        for r in pending:
            r.status = "cancelled"
            r.status_reason = "mentor suspended"
            notification_service.notify(db, r.student_id, "Request cancelled",
                                        "The mentor is currently unavailable; the request was cancelled.",
                                        "request_cancelled", "mentoring_request", r.request_id)
    p.reviewed_by = admin.user_id
    p.reviewed_at = now
    p.review_note = (note or "").strip() or None
    titles = {"approve": "Profile approved", "reject": "Profile rejected", "suspend": "Profile suspended"}
    messages = {
        "approve": "Your mentor profile is approved; students can now find you in search.",
        "reject": f"Your mentor profile was rejected. Note: {note}" if note else "Your mentor profile was rejected.",
        "suspend": "Your mentor profile is suspended" + (f": {note}" if note else "."),
    }
    notification_service.notify(db, mentor_id, titles[decision], messages[decision],
                                "mentor_reviewed", "mentor_profile", mentor_id)
    audit_service.record(db, admin.user_id, f"mentor.{decision}", "mentor_profile", mentor_id,
                         {"note": note}, ip)
    user = db.get(User, mentor_id)
    return mentor_profile_row(
        p, user.full_name, profile_service._mentor_expertise(db, p.mentor_profile_id),
        profile_service._mentor_interests(db, p.mentor_profile_id),
        profile_service._mentor_rating(db, mentor_id),
        review={"review_note": p.review_note, "reviewed_at": p.reviewed_at.isoformat() if p.reviewed_at else None})


# ------------------------------------------------------------------ E49/E50
def list_all_mentorships(db: Session, *, status: str | None, mentor_id, student_id,
                         page: int, page_size: int) -> dict:
    stmt = select(Mentorship)
    if status:
        if status not in ("active", "completed", "ended"):
            raise DomainError("BAD_REQUEST", "Unknown mentorship status filter.")
        stmt = stmt.where(Mentorship.status == status)
    if mentor_id:
        stmt = stmt.where(Mentorship.mentor_id == mentor_id)
    if student_id:
        stmt = stmt.where(Mentorship.student_id == student_id)
    rows = db.scalars(stmt.order_by(Mentorship.started_at.desc())).all()
    users = {str(u.user_id): u.full_name for u in db.scalars(select(User)).all()}
    data = []
    for m in rows:
        completed = db.scalar(select(func.count()).select_from(SessionModel).where(
            SessionModel.mentorship_id == m.mentorship_id, SessionModel.status == "completed")) or 0
        data.append(mentorship_row(m, student_name=users.get(str(m.student_id)),
                                   mentor_name=users.get(str(m.mentor_id)),
                                   extra={"sessions_completed": int(completed)}))
    start = (max(1, page) - 1) * page_size
    return {"data": data[start:start + page_size], "meta": meta(page, page_size, len(data))}


def list_all_requests(db: Session, *, status: str | None, older_than_days: int | None,
                      page: int, page_size: int) -> dict:
    stmt = select(MentoringRequest)
    if status:
        stmt = stmt.where(MentoringRequest.status == status)
    if older_than_days:
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        stmt = stmt.where(MentoringRequest.created_at < cutoff)
    rows = db.scalars(stmt.order_by(MentoringRequest.created_at.desc())).all()
    users = {str(u.user_id): u.full_name for u in db.scalars(select(User)).all()}
    data = [request_row(r, student_name=users.get(str(r.student_id)), mentor_name=users.get(str(r.mentor_id)))
            for r in rows]
    start = (max(1, page) - 1) * page_size
    return {"data": data[start:start + page_size], "meta": meta(page, page_size, len(data))}


# ------------------------------------------------------------------ E54
def list_audit(db: Session, *, entity_type: str | None, entity_id, actor_user_id, action: str | None,
               from_dt, to_dt, page: int, page_size: int) -> dict:
    from app.models import AuditLog
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        stmt = stmt.where(AuditLog.action.like(f"{action}%"))
    if from_dt:
        stmt = stmt.where(AuditLog.created_at >= from_dt)
    if to_dt:
        stmt = stmt.where(AuditLog.created_at <= to_dt)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {"data": [audit_row(a) for a in rows], "meta": meta(page, page_size, total or 0)}
