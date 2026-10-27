"""E35-E39: the caller's sessions across mentorships, detail, update, feedback."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import AnyUser, DbSession, Page, naive_to_utc
from app.services import feedback_service, session_service

router = APIRouter(prefix="/sessions", tags=["Mentorships, sessions and feedback"],
                   route_class=TransactionRoute)


class SessionPatchBody(BaseModel):
    status: str | None = None
    cancel_reason: str | None = None
    notes: str | None = None
    meeting_mode: str | None = None
    meeting_link: str | None = None


class FeedbackBody(BaseModel):
    rating: int
    comments: str | None = None


@router.get("")
def list_all(user: AnyUser, db: DbSession, page: Page,
             from_dt: datetime | None = Query(None, alias="from"),
             to_dt: datetime | None = Query(None, alias="to"),
             status: str | None = Query(None)):
    return session_service.calendar_sessions(db, user, from_dt=naive_to_utc(from_dt),
                                             to_dt=naive_to_utc(to_dt), status=status,
                                             page=page.page, page_size=page.page_size)


@router.get("/{session_id}")
def detail(session_id: uuid.UUID, user: AnyUser, db: DbSession):
    return {"data": session_service.get_session(db, user, session_id)}


@router.patch("/{session_id}")
def update(session_id: uuid.UUID, body: SessionPatchBody, user: AnyUser, db: DbSession):
    return {"data": session_service.update_session(db, user, session_id, body.model_dump(exclude_unset=True))}


@router.post("/{session_id}/feedback", status_code=201)
def submit_feedback(session_id: uuid.UUID, body: FeedbackBody, user: AnyUser, db: DbSession):
    return {"data": feedback_service.submit_feedback(db, user, session_id, rating=body.rating,
                                                     comments=body.comments)}


@router.get("/{session_id}/feedback")
def get_feedback(session_id: uuid.UUID, user: AnyUser, db: DbSession):
    return feedback_service.visible_feedback(db, user, session_id)
