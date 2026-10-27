"""E30-E34: mentorships and their sessions."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import (AdminUser, AnyUser, DbSession, MentorUser, Page, StudentUser, request_ip)
from app.services import mentoring_service, session_service

router = APIRouter(prefix="/mentorships", tags=["Mentorships, sessions and feedback"],
                   route_class=TransactionRoute)


class CloseBody(BaseModel):
    status: str
    reason: str | None = None


class ScheduleBody(BaseModel):
    slot_id: uuid.UUID | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    meeting_mode: str = "online"
    meeting_link: str | None = None
    notes: str | None = None


@router.get("")
def mine(user: AnyUser, db: DbSession, page: Page, status: str | None = Query(None)):
    return mentoring_service.list_mentorships(db, user, status=status, page=page.page, page_size=page.page_size)


@router.get("/{mentorship_id}")
def detail(mentorship_id: uuid.UUID, user: AnyUser, db: DbSession):
    return {"data": mentoring_service.get_mentorship(db, user, mentorship_id)}


@router.patch("/{mentorship_id}")
def close(mentorship_id: uuid.UUID, body: CloseBody, user: AnyUser, db: DbSession, request: Request):
    return {"data": mentoring_service.close_mentorship(db, user, mentorship_id, status=body.status,
                                                       reason=body.reason, ip=request_ip(request))}


@router.get("/{mentorship_id}/sessions")
def sessions(mentorship_id: uuid.UUID, user: AnyUser, db: DbSession, page: Page,
             status: str | None = Query(None)):
    return session_service.list_sessions(db, user, mentorship_id=mentorship_id, status=status,
                                         page=page.page, page_size=page.page_size)


@router.post("/{mentorship_id}/sessions", status_code=201)
def schedule(mentorship_id: uuid.UUID, body: ScheduleBody, user: AnyUser, db: DbSession):
    return {"data": session_service.schedule_session(
        db, user, mentorship_id, slot_id=body.slot_id,
        scheduled_start=naive(body.scheduled_start), scheduled_end=naive(body.scheduled_end),
        meeting_mode=body.meeting_mode, meeting_link=body.meeting_link, notes=body.notes)}


def naive(dt):
    if dt is not None and dt.tzinfo is None:
        from datetime import timezone
        return dt.replace(tzinfo=timezone.utc)
    return dt
