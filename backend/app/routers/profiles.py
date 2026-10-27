"""E12-E15: own profiles (student / mentor)."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.transactions import TransactionRoute
from app.deps import MentorUser, DbSession, StudentUser, request_ip
from app.services import profile_service as profile

router = APIRouter(tags=["Profiles"], route_class=TransactionRoute)


class StudentProfileBody(BaseModel):
    full_name: str | None = None
    programme_stage: str | None = None
    expected_graduation_year: int | None = None
    career_goals: str | None = None
    guidance_needs: str | None = None
    bio: str | None = None
    skills: list[dict] | None = None
    interest_ids: list[str] | None = None


class MentorProfileBody(BaseModel):
    full_name: str | None = None
    mentor_type: str | None = None
    professional_title: str | None = None
    organisation: str | None = None
    experience_years: int | None = None
    graduation_year: int | None = None
    linkedin_url: str | None = None
    bio: str | None = None
    is_available: bool | None = None
    max_active_mentees: int | None = None
    expertise: list[dict] | None = None
    interest_ids: list[str] | None = None
    submit_for_review: bool = False


@router.get("/students/me/profile")
def get_student_profile(student: StudentUser, db: DbSession):
    return {"data": profile.get_student_profile(db, student)}


@router.patch("/students/me/profile")
def update_student_profile(body: StudentProfileBody, student: StudentUser, db: DbSession):
    return {"data": profile.update_student_profile(db, student, body.model_dump(exclude_unset=True))}


@router.get("/mentors/me/profile")
def get_mentor_profile(mentor: MentorUser, db: DbSession):
    return {"data": profile.get_mentor_profile(db, mentor)}


@router.patch("/mentors/me/profile")
def update_mentor_profile(body: MentorProfileBody, mentor: MentorUser, db: DbSession, request: Request):
    return {"data": profile.update_mentor_profile(db, mentor, body.model_dump(exclude_unset=True),
                                                  ip=request_ip(request))}
