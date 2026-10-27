"""E24-E29: mentoring requests."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import AdminUser, AnyUser, DbSession, MentorUser, Page, StudentUser, rate_limited, request_ip
from app.services import mentoring_service

router = APIRouter(prefix="/mentoring-requests", tags=["Mentoring requests"],
                   route_class=TransactionRoute)


class RequestBody(BaseModel):
    mentor_id: uuid.UUID
    career_goal: str
    message: str | None = None


class ReasonBody(BaseModel):
    reason: str | None = None


@router.post("", status_code=201, dependencies=[Depends(rate_limited("request", 10, 60))])
def submit(body: RequestBody, student: StudentUser, db: DbSession, request: Request):
    return {"data": mentoring_service.create_request(db, student, mentor_id=body.mentor_id,
                                                     career_goal=body.career_goal, message=body.message,
                                                     ip=request_ip(request))}


@router.get("/mine")
def mine(user: AnyUser, db: DbSession, page: Page, status: str | None = Query(None)):
    return mentoring_service.list_requests(db, user, status=status, page=page.page, page_size=page.page_size)


@router.get("/{request_id}")
def detail(request_id: uuid.UUID, user: AnyUser, db: DbSession):
    return {"data": mentoring_service.get_request(db, user, request_id, include_profile=True)}


@router.post("/{request_id}/accept")
def accept(request_id: uuid.UUID, mentor: MentorUser, db: DbSession, request: Request):
    return {"data": mentoring_service.accept_request(db, mentor, request_id, ip=request_ip(request))}


@router.post("/{request_id}/decline")
def decline(request_id: uuid.UUID, body: ReasonBody, mentor: MentorUser, db: DbSession, request: Request):
    return {"data": mentoring_service.decline_request(db, mentor, request_id, reason=body.reason,
                                                      ip=request_ip(request))}


@router.post("/{request_id}/cancel")
def cancel(request_id: uuid.UUID, body: ReasonBody, student: StudentUser, db: DbSession, request: Request):
    return {"data": mentoring_service.cancel_request(db, student, request_id, reason=body.reason,
                                                     ip=request_ip(request))}
