"""E10/E11: catalogues for profile forms and filters; E55-E58: admin catalogue CRUD."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import AdminUser, DbSession, Page, request_ip
from app.services import catalogue_service as catalogue

router = APIRouter(tags=["Catalogues"], route_class=TransactionRoute)


@router.get("/skills")
def skills(db: DbSession, page: Page, q: str | None = Query(None), category: str | None = Query(None),
           include_inactive: bool = Query(False), with_usage: bool = Query(False)):
    return catalogue.list_skills(db, q=q, category=category, page=page.page, page_size=page.page_size,
                                 include_inactive=include_inactive, with_usage=with_usage)


@router.get("/career-interests")
def career_interests(db: DbSession, page: Page, include_inactive: bool = Query(False),
                     with_usage: bool = Query(False)):
    return catalogue.list_interests(db, page=page.page, page_size=page.page_size,
                                    include_inactive=include_inactive, with_usage=with_usage)


# ---------------- admin CRUD (E55-E58) ----------------
class SkillBody(BaseModel):
    skill_name: str | None = None
    category: str | None = None
    is_active: bool | None = None


class InterestBody(BaseModel):
    interest_name: str | None = None
    description: str | None = None
    is_active: bool | None = None


class NewSkillBody(BaseModel):
    skill_name: str
    category: str | None = None


class NewInterestBody(BaseModel):
    interest_name: str
    description: str | None = None


@router.post("/admin/skills", status_code=201)
def add_skill(body: NewSkillBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": catalogue.create_skill(db, skill_name=body.skill_name, category=body.category,
                                           actor=admin, ip=request_ip(request))}


@router.patch("/admin/skills/{skill_id}")
def update_skill(skill_id, body: SkillBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": catalogue.update_skill(db, skill_id, body.model_dump(exclude_unset=True),
                                           actor=admin, ip=request_ip(request))}


@router.post("/admin/career-interests", status_code=201)
def add_interest(body: NewInterestBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": catalogue.create_interest(db, interest_name=body.interest_name,
                                              description=body.description, actor=admin, ip=request_ip(request))}


@router.patch("/admin/career-interests/{interest_id}")
def update_interest(interest_id, body: InterestBody, admin: AdminUser, db: DbSession, request: Request):
    return {"data": catalogue.update_interest(db, interest_id, body.model_dump(exclude_unset=True),
                                              actor=admin, ip=request_ip(request))}
