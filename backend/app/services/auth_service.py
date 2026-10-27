"""AuthenticationService (component C01): register, login, refresh rotation with reuse
detection, logout, password change, signed reset / verify tokens (E01-E09, rules R16)."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import config
from app.core import security
from app.core.errors import DomainError
from app.models import MentorProfile, RefreshToken, StudentProfile, User
from app.services import audit_service

EMAIL_RE = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"


def _norm_email(email: str) -> str:
    return (email or "").strip().lower()


def register(db: Session, *, full_name: str, email: str, password: str, role: str, ip: str | None) -> dict:
    import re
    full_name = (full_name or "").strip()
    if not (1 <= len(full_name) <= 120):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "full_name", "issue": "must be 1-120 characters"}])
    if not re.match(EMAIL_RE, email or ""):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "email", "issue": "must be a valid e-mail address"}])
    issues = security.password_issues(password)
    if issues:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "password", "issue": issues[0]}])
    if role not in ("student", "mentor"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "role", "issue": "must be student or mentor"}])
    email = _norm_email(email)
    if db.scalar(select(User.user_id).where(User.email == email)):
        raise DomainError("EMAIL_ALREADY_REGISTERED")
    user = User(full_name=full_name, email=email, password_hash=security.hash_password(password),
                role=role, account_status="active")
    db.add(user)
    db.flush()
    if role == "student":
        db.add(StudentProfile(user_id=user.user_id, user_role="student"))
    else:
        db.add(MentorProfile(user_id=user.user_id, user_role="mentor"))
    audit_service.record(db, user.user_id, "account.registered", "user", user.user_id, {"role": role}, ip)
    return user


def authenticate(db: Session, *, email: str, password: str, ip: str | None) -> User:
    user = db.scalars(select(User).where(User.email == _norm_email(email))).first()
    if user is None or not security.verify_password(password or "", user.password_hash):
        raise DomainError("INVALID_CREDENTIALS")
    if user.account_status != "active":
        raise DomainError("ACCOUNT_SUSPENDED")
    user.last_login_at = datetime.now(timezone.utc)
    return user


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _family_id() -> str:
    return str(uuid.uuid4())


def start_session(db: Session, user) -> tuple[str, str]:
    """Create a refresh-token family; returns (access_token, refresh_plain)."""
    family = uuid.uuid4()
    plain = secrets.token_urlsafe(48)
    db.add(RefreshToken(user_id=user.user_id, family_id=family, token_hash=_hash_token(plain),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=config.cfg.REFRESH_TOKEN_DAYS)))
    return security.issue_access_token(user, family), plain


def rotate_refresh(db: Session, cookie_token: str | None) -> tuple[User, str, str]:
    """E03: exchange the refresh cookie for a new access token; rotate the family.

    Reuse of a rotated token revokes the whole family (REFRESH_REUSED)."""
    if not cookie_token:
        raise DomainError("REFRESH_INVALID")
    row = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == _hash_token(cookie_token))).first()
    if row is None:
        raise DomainError("REFRESH_INVALID")
    if row.revoked_at is not None:
        # replayed token -> revoke the whole family (must survive the 401 rollback)
        now = datetime.now(timezone.utc)
        db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id, RefreshToken.revoked_at.is_(None))
                   .values(revoked_at=now, revoked_reason="reuse_detected"))
        db.commit()
        raise DomainError("REFRESH_REUSED")
    if row.expires_at <= datetime.now(timezone.utc):
        row.revoked_at = datetime.now(timezone.utc)
        row.revoked_reason = "rotated"
        raise DomainError("REFRESH_INVALID")
    user = db.get(User, row.user_id)
    if user is None:
        raise DomainError("REFRESH_INVALID")
    if user.account_status != "active":
        raise DomainError("ACCOUNT_SUSPENDED")
    row.revoked_at = datetime.now(timezone.utc)
    row.revoked_reason = "rotated"
    new_plain = secrets.token_urlsafe(48)
    db.add(RefreshToken(user_id=user.user_id, family_id=row.family_id, token_hash=_hash_token(new_plain),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=config.cfg.REFRESH_TOKEN_DAYS)))
    return user, security.issue_access_token(user, row.family_id), new_plain


def revoke_family(db: Session, cookie_token: str | None, user_id) -> None:
    """Logout: revoke the cookie's family (or all of the user's when the cookie is gone)."""
    now = datetime.now(timezone.utc)
    if cookie_token:
        row = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == _hash_token(cookie_token))).first()
        if row is not None:
            db.execute(update(RefreshToken).where(RefreshToken.family_id == row.family_id,
                      RefreshToken.revoked_at.is_(None)).values(revoked_at=now, revoked_reason="logout"))
            return
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
               .values(revoked_at=now, revoked_reason="logout"))


def change_password(db: Session, user: User, *, current_password: str, new_password: str,
                    current_family=None) -> None:
    """E09: change the password; every refresh-token family except the caller's is revoked."""
    if not security.verify_password(current_password or "", user.password_hash):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "current_password", "issue": "current password is incorrect"}])
    issues = security.password_issues(new_password)
    if issues:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "new_password", "issue": issues[0]}])
    user.password_hash = security.hash_password(new_password)
    now = datetime.now(timezone.utc)
    stmt = update(RefreshToken).where(RefreshToken.user_id == user.user_id, RefreshToken.revoked_at.is_(None))
    if current_family:
        stmt = stmt.where(RefreshToken.family_id != current_family)
    db.execute(stmt.values(revoked_at=now, revoked_reason="password_change"))


# ------------------------------------------------------------------ reset / verify (E05-E07)
def forgot_password(db: Session, email: str) -> None:
    """Always answers 202 upstream; the link is logged when e-mail is disabled (dev)."""
    import re
    if not re.match(EMAIL_RE, email or ""):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "email", "issue": "must be a valid e-mail address"}])
    user = db.scalars(select(User).where(User.email == _norm_email(email))).first()
    if user is None:
        return
    token = security.sign_token(str(user.user_id), "password_reset", minutes_valid=30)
    if config.cfg.EMAIL_ENABLED:
        # real delivery is an optional extension; not wired in this build
        print(f"[email] password reset for {user.email}: /reset-password?token={token}")
    else:
        print(f"[dev] PASSWORD RESET LINK for {user.email}: /reset-password?token={token}")


def reset_password(db: Session, *, token: str, new_password: str, ip: str | None) -> None:
    issues = security.password_issues(new_password)
    if issues:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "new_password", "issue": issues[0]}])
    try:
        signed = security.parse_token(token, "password_reset")
    except ValueError:
        raise DomainError("INVALID_TOKEN", "The link is expired or was already used.")
    user = db.get(User, signed.user_id)
    if user is None:
        raise DomainError("INVALID_TOKEN", "The link is expired or was already used.")
    user.password_hash = security.hash_password(new_password)
    now = datetime.now(timezone.utc)
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.user_id, RefreshToken.revoked_at.is_(None))
               .values(revoked_at=now, revoked_reason="password_change"))
    audit_service.record(db, user.user_id, "account.password_reset", "user", user.user_id, {}, ip)


def verify_email(db: Session, *, token: str) -> None:
    try:
        signed = security.parse_token(token, "email_verify")
    except ValueError:
        raise DomainError("INVALID_TOKEN", "The verification link is invalid or expired.")
    user = db.get(User, signed.user_id)
    if user is None:
        raise DomainError("INVALID_TOKEN", "The verification link is invalid or expired.")
    user.email_verified = True


def me(db: Session, user: User) -> dict:
    from app.serializers import user_row
    profile_completed = False
    profile_status = None
    if user.role == "student" and (p := db.scalars(select(StudentProfile).where(StudentProfile.user_id == user.user_id)).first()):
        profile_completed = p.profile_completed
    if user.role == "mentor" and (p := db.scalars(select(MentorProfile).where(MentorProfile.user_id == user.user_id)).first()):
        profile_completed = p.profile_status == "approved"
        profile_status = p.profile_status
    return user_row(user, profile_completed=profile_completed, profile_status=profile_status)
