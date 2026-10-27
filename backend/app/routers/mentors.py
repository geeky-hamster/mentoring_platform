"""E16-E23: mentor directory (public view, own availability, search, recommendations)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import (AdminUser, AnyUser, DbSession, MentorUser, Page, StudentUser,
                      get_current_user, naive_to_utc, request_ip)
from app.services import matching_service, profile_service, session_service

router = APIRouter(prefix="/mentors", tags=["Discovery and matching"], route_class=TransactionRoute)
availability_router = APIRouter(prefix="/mentors/me/availability", tags=["Availability"],
                                route_class=TransactionRoute)


class SlotBody(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    is_available: bool | None = None


class SlotsBody(BaseModel):
    slots: list[SlotBody] | None = None
    recurrence: dict | None = None


# NOTE: routes with the literal `me` are declared before the `/{mentor_id}` route so the
# path parameter never swallows them; main.py also includes the profiles router first.


@router.get("/me/availability")
def my_availability(mentor: MentorUser, db: DbSession,
                    from_dt: datetime | None = Query(None, alias="from"),
                    to_dt: datetime | None = Query(None, alias="to"),
                    is_available: bool | None = Query(None)):
    return session_service.my_slots(db, mentor.user_id, from_dt=naive_to_utc(from_dt),
                                    to_dt=naive_to_utc(to_dt), is_available=is_available)


@availability_router.post("", status_code=201)
def add_slots(body: SlotsBody, mentor: MentorUser, db: DbSession):
    return session_service.create_slots(
        db, mentor,
        slots=[s.model_dump() for s in body.slots] if body.slots else None,
        recurrence=body.recurrence)


@availability_router.patch("/{slot_id}")
def edit_slot(slot_id: uuid.UUID, body: SlotBody, mentor: MentorUser, db: DbSession):
    return {"data": session_service.update_slot(db, mentor, slot_id, body.model_dump(exclude_unset=True))}


@availability_router.delete("/{slot_id}", status_code=204)
def delete_slot(slot_id: uuid.UUID, mentor: MentorUser, db: DbSession):
    session_service.delete_slot(db, mentor, slot_id)


@router.get("/recommended")
def recommended(user: StudentUser, db: DbSession, page: Page):
    return matching_service.recommended(db, user.user_id, page=page.page, page_size=page.page_size)


@router.get("/{mentor_id}")
def mentor_public_profile(mentor_id: uuid.UUID, user: AnyUser, db: DbSession):
    return {"data": profile_service.public_mentor_profile(db, user, mentor_id)}


@router.get("/{mentor_id}/availability")
def mentor_open_slots(mentor_id: uuid.UUID, user: AnyUser, db: DbSession,
                      from_dt: datetime | None = Query(None, alias="from"),
                      to_dt: datetime | None = Query(None, alias="to")):
    return session_service.open_slots(db, user, mentor_id, from_dt=naive_to_utc(from_dt), to_dt=naive_to_utc(to_dt))


@router.get("")
def search_mentors(user: AnyUser, db: DbSession, page: Page,
                   q: str | None = Query(None),
                   skill_id: list[uuid.UUID] | None = Query(None),
                   interest_id: list[uuid.UUID] | None = Query(None),
                   mentor_type: str | None = Query(None),
                   min_experience: int | None = Query(None),
                   accepting: bool = True,
                   sort: str = Query("newest")):
    return matching_service.search(
        db, q=q, skill_ids=[str(s) for s in (skill_id or [])],
        interest_ids=[str(i) for i in (interest_id or [])], mentor_type=mentor_type,
        min_experience=min_experience, accepting=accepting, sort=sort,
        page=page.page, page_size=page.page_size)
