"""Single error envelope and the catalogue from the API contract (api.py ERRORS, report R-rules).

Services raise DomainError(code); a handler maps it to the HTTP status and produces:
    { "error": { "code", "message", "details": [{field, issue}], "request_id" } }
"""
from __future__ import annotations

import uuid

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from starlette.status import (HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN,
                              HTTP_404_NOT_FOUND, HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY,
                              HTTP_429_TOO_MANY_REQUESTS)

HTTP_BY_STATUS: dict[int, str] = {
    HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    HTTP_401_UNAUTHORIZED: "UNAUTHENTICATED",
    HTTP_403_FORBIDDEN: "FORBIDDEN",
    HTTP_404_NOT_FOUND: "NOT_FOUND",
    HTTP_409_CONFLICT: "INVALID_STATE_TRANSITION",
    HTTP_422_UNPROCESSABLE_ENTITY: "VALIDATION_ERROR",
    HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMITED",
}

ERROR_STATUS = {  # code: http status (contract catalogue)
    "BAD_REQUEST": 400,
    "INVALID_TOKEN": 400,
    "UNAUTHENTICATED": 401,
    "INVALID_CREDENTIALS": 401,
    "REFRESH_INVALID": 401,
    "REFRESH_REUSED": 401,
    "FORBIDDEN": 403,
    "ACCOUNT_SUSPENDED": 403,
    "NOT_FOUND": 404,
    "EMAIL_ALREADY_REGISTERED": 409,
    "DUPLICATE_ENTRY": 409,
    "PROFILE_INCOMPLETE": 409,
    "DUPLICATE_PENDING_REQUEST": 409,
    "REQUEST_COOLDOWN": 409,
    "PENDING_LIMIT_REACHED": 409,
    "MENTOR_NOT_AVAILABLE": 409,
    "MENTOR_AT_CAPACITY": 409,
    "ACTIVE_MENTORSHIP_EXISTS": 409,
    "INVALID_STATE_TRANSITION": 409,
    "MENTORSHIP_NOT_ACTIVE": 409,
    "SLOT_UNAVAILABLE": 409,
    "SLOT_OVERLAP": 409,
    "SLOT_BOOKED": 409,
    "SESSION_CONFLICT": 409,
    "FEEDBACK_NOT_ALLOWED": 409,
    "FEEDBACK_ALREADY_SUBMITTED": 409,
    "VALIDATION_ERROR": 422,
    "RATE_LIMITED": 429,
}

DEFAULT_MESSAGES = {
    "BAD_REQUEST": "Malformed request or an invalid query parameter.",
    "INVALID_TOKEN": "Token is invalid or expired.",
    "UNAUTHENTICATED": "Authentication required. Please sign in again.",
    "INVALID_CREDENTIALS": "E-mail or password is incorrect.",
    "REFRESH_INVALID": "Session is no longer valid. Please sign in again.",
    "REFRESH_REUSED": "Session security error. Please sign in again.",
    "FORBIDDEN": "You do not have access to this action.",
    "ACCOUNT_SUSPENDED": "Your account is suspended. Contact the programme office.",
    "NOT_FOUND": "Resource does not exist or is not visible to you.",
    "EMAIL_ALREADY_REGISTERED": "An account with this e-mail already exists.",
    "DUPLICATE_ENTRY": "A catalogue entry with this name already exists.",
    "PROFILE_INCOMPLETE": "Complete your profile before performing this action.",
    "DUPLICATE_PENDING_REQUEST": "You already have a pending request with this mentor.",
    "REQUEST_COOLDOWN": "Re-requesting this mentor is blocked for the cooldown period.",
    "PENDING_LIMIT_REACHED": "You already have the maximum number of pending requests.",
    "MENTOR_NOT_AVAILABLE": "This mentor is not accepting requests right now.",
    "MENTOR_AT_CAPACITY": "This mentor already has the maximum number of active mentees.",
    "ACTIVE_MENTORSHIP_EXISTS": "An active mentorship between you already exists.",
    "INVALID_STATE_TRANSITION": "This action is not allowed in the current state.",
    "MENTORSHIP_NOT_ACTIVE": "Mentorship must be active to perform this action.",
    "SLOT_UNAVAILABLE": "This slot is already booked or in the past.",
    "SLOT_OVERLAP": "This slot overlaps another slot.",
    "SLOT_BOOKED": "This slot holds a scheduled session and cannot be changed.",
    "SESSION_CONFLICT": "A scheduled session already exists in this time range.",
    "FEEDBACK_NOT_ALLOWED": "Feedback is only allowed for completed sessions within 14 days.",
    "FEEDBACK_ALREADY_SUBMITTED": "You have already submitted feedback for this session.",
    "VALIDATION_ERROR": "One or more fields are invalid.",
    "RATE_LIMITED": "Too many requests. Please wait a moment.",
}


class DomainError(Exception):
    """Business error raised by the service layer; stable machine-readable code."""

    def __init__(self, code: str, message: str | None = None, details: list[dict] | None = None,
                 headers: dict[str, str] | None = None):
        status = ERROR_STATUS.get(code, 500)
        super().__init__(message or DEFAULT_MESSAGES.get(code, code))
        self.code = code
        self.status = status
        self.message = message or DEFAULT_MESSAGES.get(code, code)
        self.details = details or []
        self.headers = headers or {}


def envelope(request_id: str, code: str, message: str, details: list[dict] | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or [], "request_id": request_id}}


def _rid() -> str:
    return "req_" + uuid.uuid4().hex[:12]


def register_handlers(app):
    @app.exception_handler(DomainError)
    async def domain_handler(request: Request, exc: DomainError):
        rid = request.headers.get("x-request-id") or _rid()
        return JSONResponse(status_code=exc.status, content=envelope(rid, exc.code, exc.message, exc.details),
                            headers={"x-request-id": rid, **(exc.headers or {})})

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        details = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err.get("loc", []) if p != "body")
            details.append({"field": field or "*", "issue": err.get("msg", "invalid")})
        rid = _rid()
        return JSONResponse(status_code=422, content=envelope(rid, "VALIDATION_ERROR",
                            DEFAULT_MESSAGES["VALIDATION_ERROR"], details))

    @app.exception_handler(HTTPException)
    async def http_handler(request: Request, exc: HTTPException):
        code = HTTP_BY_STATUS.get(exc.status_code, "BAD_REQUEST")
        if exc.status_code == 404:
            code = "NOT_FOUND"
        message = DEFAULT_MESSAGES.get(code, "Request failed.")
        if code in ("UNAUTHENTICATED", "FORBIDDEN") and isinstance(exc.detail, str) and exc.detail:
            message = exc.detail
        rid = _rid()
        return JSONResponse(status_code=exc.status_code,
                            content=envelope(rid, code, message),
                            headers={"x-request-id": rid, **(exc.headers or {})})

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):  # pragma: no cover - safety net
        app.logger.error("Unhandled exception", exc_info=exc)
        rid = _rid()
        return JSONResponse(status_code=500, content=envelope(rid, "INTERNAL_ERROR",
                            "Something went wrong. Please try again."))
