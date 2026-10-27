"""Password hashing (Argon2id with hashlib.scrypt fallback per design Section 3),
JWT access tokens, signed time-limited tokens (reset / e-mail verify)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass

import jwt

from app import config

cfg = config.cfg

# ----------------------------------------------------------------------------- passwords
try:  # prefer Argon2id (wheels for every supported Python)
    from argon2 import PasswordHasher as _ArgonHasher
    from argon2.exceptions import VerifyMismatchError as _VerifyMismatch

    _argon = _ArgonHasher()
except Exception:  # pragma: no cover - fallback path
    _argon = None
    _VerifyMismatch = Exception


def hash_password(password: str) -> str:
    if _argon is not None:
        return _argon.hash(password)
    # fallback: scrypt (OpenSSL-backed, stdlib)
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    if stored.startswith("argon2id$") or stored.startswith("$argon2"):
        try:
            return _argon.verify(stored, password)
        except Exception:
            return False
    if stored.startswith("scrypt$"):
        try:
            _, salt_b64, key_hex = stored.split("$")
            dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=16384, r=8, p=1, dklen=32)
            return hmac.compare_digest(dk.hex(), key_hex)
        except Exception:
            return False
    return False


def password_issues(password: str) -> list[str]:
    problems = []
    if len(password) < 10:
        problems.append("must be at least 10 characters")
    if len(password) > 128:
        problems.append("must be at most 128 characters")
    return problems


# ----------------------------------------------------------------------------- JWT access token
ISSUER = "mentoring-platform"


def issue_access_token(user, family_id=None) -> str:
    now = int(time.time())
    payload = {"iss": ISSUER, "sub": str(user.user_id), "role": user.role, "iat": now,
               "exp": now + cfg.ACCESS_TOKEN_MINUTES * 60, "jti": secrets.token_hex(8)}
    if family_id:
        # lets endpoints identify the caller's refresh-token family even where the
        # cookie is not delivered (its Path is /api/v1/auth)
        payload["fam"] = str(family_id)
    return jwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=["HS256"], issuer=ISSUER)


# ----------------------------------------------------------------------------- signed tokens
@dataclass
class SignedToken:
    user_id: str
    purpose: str
    issued_at: int


def sign_token(user_id: str, purpose: str, minutes_valid: int = 30) -> str:
    payload = {"sub": user_id, "purpose": purpose, "iat": int(time.time()), "exp": int(time.time()) + minutes_valid * 60}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    sig = hmac.new(cfg.JWT_SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
    return body + "." + sig


def parse_token(token: str, purpose: str) -> SignedToken:
    try:
        body, sig = token.rsplit(".", 1)
        good = hmac.new(cfg.JWT_SECRET_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, good):
            raise ValueError
        payload = json.loads(base64.urlsafe_b64decode(body.encode()))
    except Exception as exc:  # malformed or bad signature
        raise ValueError("malformed") from exc
    if payload.get("purpose") != purpose:
        raise ValueError("wrong purpose")
    if payload.get("exp", 0) < time.time():
        raise ValueError("expired")
    return SignedToken(user_id=payload["sub"], purpose=purpose, issued_at=payload["iat"])
