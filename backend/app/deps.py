"""FastAPI dependencies: request-scoped DB session, JWT identity, role guards, paging, rate limit."""
from __future__ import annotations

import time
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.core import rate_limit
from app.core.errors import DomainError
from app.core.security import decode_access_token
from app.extensions import SessionLocal
from app.models import User


def get_db(request: Request = None):
    """Provide the request-scoped session.

    ``TransactionRoute`` (app/core/transactions.py) owns commit/rollback for API requests
    so the data is durable BEFORE the response bytes are sent; this dependency only hands
    out the session. Standalone usage (no middleware) falls back to self-managed commit.
    """
    db = getattr(request.state, "db", None) if request is not None else None
    if db is not None:
        yield db
        return
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(request: Request, db: DbSession, authorization: Annotated[str | None, Header()] = None) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise DomainError("UNAUTHENTICATED")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except pyjwt.ExpiredSignatureError:
        raise DomainError("UNAUTHENTICATED", "Your session has expired.")
    except pyjwt.PyJWTError:
        raise DomainError("UNAUTHENTICATED")
    request.state.token_family = payload.get("fam")
    user = db.get(User, payload["sub"])
    if user is None:
        raise DomainError("UNAUTHENTICATED")
    if user.account_status != "active":
        raise DomainError("ACCOUNT_SUSPENDED")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    def checker(user: CurrentUser) -> User:
        if roles and user.role not in roles:
            raise DomainError("FORBIDDEN")
        return user
    return checker


StudentUser = Annotated[User, Depends(require_roles("student"))]
MentorUser = Annotated[User, Depends(require_roles("mentor"))]
AdminUser = Annotated[User, Depends(require_roles("admin"))]
AnyUser = Annotated[User, Depends(require_roles("student", "mentor", "admin"))]
MentorOrAdmin = Annotated[User, Depends(require_roles("mentor", "admin"))]


class PageParams:
    """page / page_size query parameters with contract defaults (10, max 50)."""

    def __init__(self, page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=200)):
        cfg = config.cfg
        self.page = page
        self.page_size = max(1, min(page_size, cfg.MAX_PAGE_SIZE))


Page = Annotated[PageParams, Depends(PageParams)]


def naive_to_utc(dt):
    """Dates parsed without an offset are treated as UTC."""
    from datetime import timezone
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def rate_limited(bucket: str, max_calls: int, window_seconds: float):
    """Dependency factory: sliding-window limiter keyed by client IP + bucket."""

    def checker(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        allowed, retry = rate_limit.hit(f"{bucket}:{ip}", max_calls, window_seconds)
        if not allowed:
            raise DomainError("RATE_LIMITED", headers={"Retry-After": str(retry)})

    return checker


def request_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def monotonic_ms() -> int:
    return int(time.time() * 1000)
