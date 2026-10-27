"""E40/E41: dashboards; E42-E44: notifications."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import AnyUser, DbSession, MentorUser, Page, StudentUser
from app.services import dashboard_service, notification_service as notif

router = APIRouter(tags=["Dashboards and notifications"], route_class=TransactionRoute)


class MarkBody(BaseModel):
    is_read: bool


@router.get("/students/me/dashboard")
def student_dashboard(student: StudentUser, db: DbSession):
    return {"data": dashboard_service.student_dashboard(db, student)}


@router.get("/mentors/me/dashboard")
def mentor_dashboard(mentor: MentorUser, db: DbSession):
    return {"data": dashboard_service.mentor_dashboard(db, mentor)}


@router.get("/notifications")
def notifications(user: AnyUser, db: DbSession, page: Page, is_read: bool | None = Query(None)):
    result = notif.list_for(db, user.user_id, is_read=is_read, page=page.page, page_size=page.page_size)
    unread = result.pop("unread_count")
    result["meta"]["unread_count"] = unread
    return result


@router.patch("/notifications/{notification_id}")
def mark_read(notification_id: uuid.UUID, body: MarkBody, user: AnyUser, db: DbSession):
    from app.core.errors import DomainError
    n = notif.mark_read(db, user.user_id, notification_id)
    if n is None:
        raise DomainError("NOT_FOUND")
    return {"data": notif.serialize(n)}


@router.post("/notifications/mark-all-read", status_code=204)
def mark_all_read(user: AnyUser, db: DbSession):
    notif.mark_all_read(db, user.user_id)
