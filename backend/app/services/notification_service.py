"""NotificationService (component C10): writes events and lists them (E42-E44)."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import pagination
from app.models import Notification

NOTIF_TYPES = {
    "request_received", "request_accepted", "request_declined", "request_cancelled", "request_expired",
    "mentorship_ended", "session_scheduled", "session_cancelled", "session_reminder",
    "feedback_requested", "mentor_reviewed", "account_status_changed",
}


def notify(db: Session, user_id, title: str, message: str, notification_type: str,
           related_entity_type: str | None = None, related_entity_id=None) -> None:
    assert notification_type in NOTIF_TYPES, notification_type
    db.add(Notification(user_id=user_id, title=title[:150], message=message,
                        notification_type=notification_type, related_entity_type=related_entity_type,
                        related_entity_id=related_entity_id))


def serialize(n: Notification) -> dict:
    return {
        "notification_id": str(n.notification_id),
        "title": n.title,
        "message": n.message,
        "notification_type": n.notification_type,
        "related_entity_type": n.related_entity_type,
        "related_entity_id": str(n.related_entity_id) if n.related_entity_id else None,
        "is_read": n.is_read,
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "created_at": n.created_at.isoformat(),
    }


def list_for(db: Session, user_id, *, is_read: bool | None, page: int, page_size: int) -> dict:
    q = select(Notification).where(Notification.user_id == user_id)
    if is_read is not None:
        q = q.where(Notification.is_read == is_read)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = db.scalars(q.order_by(Notification.created_at.desc(), Notification.notification_id.desc())
                      .offset((page - 1) * page_size).limit(page_size)).unique().all()
    unread = db.scalar(select(func.count()).select_from(
        select(Notification.notification_id).where(Notification.user_id == user_id, Notification.is_read == False).subquery()))  # noqa: E712
    return {"data": [serialize(n) for n in rows], "meta": pagination.meta(page, page_size, total or 0),
            "unread_count": unread or 0}


def unread_count(db: Session, user_id) -> int:
    return db.scalar(select(func.count()).select_from(
        select(Notification.notification_id).where(Notification.user_id == user_id, Notification.is_read == False).subquery())) or 0  # noqa: E712


def mark_read(db: Session, user_id, notification_id) -> Notification | None:
    n = db.get(Notification, notification_id)
    if n is None or n.user_id != user_id:
        return None
    if not n.is_read:
        from datetime import datetime, timezone
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
    return n


def mark_all_read(db: Session, user_id) -> int:
    from datetime import datetime, timezone
    rows = db.scalars(select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)).all()  # noqa: E712
    for n in rows:
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
    return len(rows)
