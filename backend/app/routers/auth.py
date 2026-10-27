"""E01-E09: Authentication and account."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.core.transactions import TransactionRoute
from app.deps import (AdminUser, AnyUser, DbSession, StudentUser, MentorUser, get_db, rate_limited,
                      request_ip)
from app.models import User
from app.services import auth_service as auth

router = APIRouter(prefix="/auth", tags=["Authentication and account"], route_class=TransactionRoute)
users_router = APIRouter(prefix="/users", tags=["Authentication and account"], route_class=TransactionRoute)

COOKIE = "refresh_token"


class RegisterBody(BaseModel):
    full_name: str
    email: str
    password: str
    role: str


class LoginBody(BaseModel):
    email: str
    password: str


class PasswordBody(BaseModel):
    current_password: str
    new_password: str


class ResetBody(BaseModel):
    token: str
    new_password: str


class VerifyBody(BaseModel):
    token: str


class ForgotBody(BaseModel):
    email: str


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE, token, max_age=config.cfg.REFRESH_TOKEN_DAYS * 24 * 3600,
        httponly=True, samesite="lax", secure=config.cfg.ENV != "local",
        path="/api/v1/auth")


def _read_refresh_cookie(request: Request) -> str | None:
    return request.cookies.get(COOKIE)


@router.post("/register", status_code=201,
             dependencies=[Depends(rate_limited("register", max_calls=10, window_seconds=60))])
def register(body: RegisterBody, db: DbSession, request: Request):
    user = auth.register(db, full_name=body.full_name, email=body.email, password=body.password,
                         role=body.role, ip=request_ip(request))
    profile_status = None
    profile_completed = False
    from app.models import MentorProfile, StudentProfile
    if user.role == "student":
        p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
        profile_completed = bool(p and p.profile_completed)
    else:
        p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()
        profile_status = p.profile_status if p else "draft"
    from app.serializers import user_row
    return {"data": user_row(user, profile_completed=profile_completed, profile_status=profile_status)}


@router.post("/login", dependencies=[Depends(rate_limited("login", max_calls=10, window_seconds=60))])
def login(body: LoginBody, db: DbSession, request: Request, response: Response):
    user = auth.authenticate(db, email=body.email, password=body.password, ip=request_ip(request))
    access, refresh_plain = auth.start_session(db, user)
    _set_refresh_cookie(response, refresh_plain)
    from app.serializers import user_row
    profile_completed = False
    profile_status = None
    from app.models import MentorProfile, StudentProfile
    if user.role == "student":
        p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
        profile_completed = bool(p and p.profile_completed)
    else:
        p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()
        profile_status = p.profile_status if p else "draft"
        profile_completed = profile_status == "approved"
    return {"data": {"access_token": access, "token_type": "Bearer",
                     "expires_in": config.cfg.ACCESS_TOKEN_MINUTES * 60,
                     "user": user_row(user, profile_completed=profile_completed, profile_status=profile_status)}}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: DbSession):
    user, access, refresh_plain = auth.rotate_refresh(db, _read_refresh_cookie(request))
    _set_refresh_cookie(response, refresh_plain)
    from app.serializers import user_row
    profile_completed = False
    profile_status = None
    from app.models import MentorProfile, StudentProfile
    if user.role == "student":
        p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()
        profile_completed = bool(p and p.profile_completed)
    else:
        p = db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()
        profile_status = p.profile_status if p else "draft"
        profile_completed = profile_status == "approved"
    return {"data": {"access_token": access, "token_type": "Bearer",
                     "expires_in": config.cfg.ACCESS_TOKEN_MINUTES * 60,
                     "user": user_row(user, profile_completed=profile_completed, profile_status=profile_status)}}


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response, user: AnyUser, db: DbSession):
    auth.revoke_family(db, _read_refresh_cookie(request), user.user_id)
    response.delete_cookie(COOKIE, path="/api/v1/auth")


@router.post("/forgot-password", status_code=202,
             dependencies=[Depends(rate_limited("forgot", max_calls=5, window_seconds=60))])
def forgot_password(body: ForgotBody, db: DbSession):
    auth.forgot_password(db, body.email)


@router.post("/reset-password", status_code=204)
def reset_password(body: ResetBody, db: DbSession, request: Request):
    auth.reset_password(db, token=body.token, new_password=body.new_password, ip=request_ip(request))


@router.post("/verify-email", status_code=204)
def verify_email(body: VerifyBody, db: DbSession):
    auth.verify_email(db, token=body.token)


@users_router.get("/me")
def me(user: AnyUser, db: DbSession):
    return {"data": auth.me(db, user)}


@users_router.post("/me/password", status_code=204)
def change_password(body: PasswordBody, user: AnyUser, db: DbSession, request: Request):
    auth.change_password(db, user, current_password=body.current_password,
                         new_password=body.new_password,
                         current_family=getattr(request.state, "token_family", None))
