"""E45-E54: administration."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import AdminUser, DbSession, Page, naive_to_utc, request_ip
from app.services import admin_service, analytics_service

router = APIRouter(prefix="/admin", tags=["Administration"], route_class=TransactionRoute)


class StatusBody(BaseModel):
    account_status: str
    reason: str | None = None


class ApprovalBody(BaseModel):
    decision: str
    note: str | None = None


@router.get("/users")
def users(admin: AdminUser, db: DbSession, page: Page, role: str | None = Query(None),
          account_status: str | None = Query(None), q: str | None = Query(None)):
    return admin_service.list_users(db, role=role, account_status=account_status, q=q,
                                    page=page.page, page_size=page.page_size)


@router.patch("/users/{user_id}/status")
def user_status(user_id: uuid.UUID, body: StatusBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": admin_service.change_user_status(db, admin, user_id,
                                                     account_status=body.account_status,
                                                     reason=body.reason, ip=request_ip(request))}


@router.get("/mentors")
def mentors(admin: AdminUser, db: DbSession, page: Page, profile_status: str | None = Query(None),
            q: str | None = Query(None)):
    return admin_service.list_mentor_queue(db, profile_status=profile_status, q=q,
                                           page=page.page, page_size=page.page_size)


@router.patch("/mentors/{mentor_id}/approval")
def approval(mentor_id: uuid.UUID, body: ApprovalBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": admin_service.decide_mentor(db, admin, mentor_id, decision=body.decision,
                                                note=body.note, ip=request_ip(request))}


@router.get("/mentorships")
def mentorships(admin: AdminUser, db: DbSession, page: Page, status: str | None = Query(None),
                mentor_id: uuid.UUID | None = Query(None), student_id: uuid.UUID | None = Query(None)):
    return admin_service.list_all_mentorships(db, status=status, mentor_id=mentor_id, student_id=student_id,
                                              page=page.page, page_size=page.page_size)


@router.get("/mentoring-requests")
def requests(admin: AdminUser, db: DbSession, page: Page, status: str | None = Query(None),
             older_than_days: int | None = Query(None)):
    return admin_service.list_all_requests(db, status=status, older_than_days=older_than_days,
                                           page=page.page, page_size=page.page_size)


@router.get("/analytics/overview")
def analytics_overview(admin: AdminUser, db: DbSession, from_d: date = Query(..., alias="from"),
                       to_d: date = Query(..., alias="to")):
    return {"data": analytics_service.overview(db, from_d.isoformat(), to_d.isoformat())}


@router.get("/analytics/trends")
def analytics_trends(admin: AdminUser, db: DbSession, metric: str, interval: str = Query("week"),
                     from_d: date = Query(..., alias="from"), to_d: date = Query(..., alias="to")):
    return {"data": analytics_service.trends(db, metric=metric, interval=interval,
                                             from_date=from_d.isoformat(), to_date=to_d.isoformat())}


@router.get("/analytics/export")
def analytics_export(admin: AdminUser, db: DbSession, report: str,
                     from_d: date = Query(..., alias="from"), to_d: date = Query(..., alias="to")):
    content, name = analytics_service.export_csv(db, report=report, from_date=from_d.isoformat(),
                                                 to_date=to_d.isoformat())
    import io
    return StreamingResponse(io.StringIO(content), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{name}_{from_d}_{to_d}.csv"'})


@router.get("/audit-logs")
def audit_logs(admin: AdminUser, db: DbSession, page: Page, entity_type: str | None = Query(None),
               entity_id: uuid.UUID | None = Query(None), actor_user_id: uuid.UUID | None = Query(None),
               action: str | None = Query(None),
               from_dt: datetime | None = Query(None, alias="from"),
               to_dt: datetime | None = Query(None, alias="to")):
    return admin_service.list_audit(db, entity_type=entity_type, entity_id=entity_id,
                                    actor_user_id=actor_user_id, action=action,
                                    from_dt=naive_to_utc(from_dt), to_dt=naive_to_utc(to_dt),
                                    page=page.page, page_size=page.page_size)
