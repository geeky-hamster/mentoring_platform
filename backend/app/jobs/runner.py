"""Scheduled maintenance jobs (design Section 11.1): request expiry, session reminders.

Runs in-process for development (config JOBS_ENABLED) and on demand via `cli.py run-jobs`
(the cron job in staging/production uses the same functions).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.extensions import SessionLocal
from app.models import MentoringRequest, Notification, Session as SessionModel
from app.services import notification_service

log = logging.getLogger("mentoring.jobs")


def expire_requests() -> int:
    """R6: pending requests older than expires_at become 'expired'; the student is notified."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        rows = db.scalars(select(MentoringRequest).where(
            MentoringRequest.status == "pending", MentoringRequest.expires_at < now)).all()
        for r in rows:
            r.status = "expired"
            notification_service.notify(db, r.student_id, "Request expired",
                                        "Your mentoring request expired without an answer; you can request the same mentor again.",
                                        "request_expired", "mentoring_request", r.request_id)
        db.commit()
        return len(rows)
    finally:
        db.close()


def session_reminders() -> int:
    """One 'session_reminder' notification per participant for sessions starting within 24h."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        rows = db.scalars(select(SessionModel).where(
            SessionModel.status == "scheduled",
            SessionModel.scheduled_start > now,
            SessionModel.scheduled_start <= now + timedelta(hours=24))).all()
        sent = 0
        for s in rows:
            for user_id in (s.student_id, s.mentor_id):
                exists = db.scalar(select(Notification.notification_id).where(
                    Notification.user_id == user_id, Notification.notification_type == "session_reminder",
                    Notification.related_entity_id == s.session_id))
                if not exists:
                    start = s.scheduled_start
                    if start.tzinfo is None:
                        start = start.replace(tzinfo=timezone.utc)
                    notification_service.notify(db, user_id, "Session reminder",
                                                f"Your session starts {start.strftime('%Y-%m-%d %H:%M')} UTC.",
                                                "session_reminder", "session", s.session_id)
                    sent += 1
        db.commit()
        return sent
    finally:
        db.close()


def run_all() -> dict:
    return {"expired_requests": expire_requests(), "session_reminders": session_reminders()}


# ------------------------------------------------------------------ in-process loop (dev)
class Runner:
    def __init__(self) -> None:
        self._task = None

    def start(self) -> None:
        self._task = asyncio.get_event_loop().create_task(self._loop())

    async def _loop(self) -> None:
        while True:
            try:
                await asyncio.to_thread(run_all)
            except Exception:  # pragma: no cover
                log.exception("job run failed")
            await asyncio.sleep(600)

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()


runner = Runner()
