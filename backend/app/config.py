"""Configuration from environment variables (defaults follow design report Section 11.5)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # backend/.env, if present


def _env(key: str, default=None, type=str):
    raw = os.environ.get(key)
    if raw is None or raw == "":
        return default
    if type is bool:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if type is int:
        return int(raw)
    if type is float:
        return float(raw)
    return raw


def _normalize_db_url(url: str) -> str:
    """Ensure SQLAlchemy-compatible driver prefix (postgresql+psycopg://)."""
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Config:
    # database
    _raw_db_url: str = _env(
        "DATABASE_URL",
        default="postgresql+psycopg://mentoring:mentoring_dev_pw@localhost:5432/mentoring")
    DATABASE_URL: str = _normalize_db_url(_raw_db_url)
    SQL_ECHO: bool = _env("SQL_ECHO", default=False, type=bool)

    # secrets / tokens
    JWT_SECRET_KEY: str = _env("JWT_SECRET_KEY", default="dev-only-insecure-secret-key-32bytes")  # required in production
    ACCESS_TOKEN_MINUTES: int = _env("ACCESS_TOKEN_MINUTES", default=15, type=int)
    REFRESH_TOKEN_DAYS: int = _env("REFRESH_TOKEN_DAYS", default=7, type=int)

    # rule parameters (R3, R4, R6, R15) - live in configuration, not in code
    REQUEST_EXPIRY_DAYS: int = _env("REQUEST_EXPIRY_DAYS", default=14, type=int)
    COOLDOWN_DAYS: int = _env("COOLDOWN_DAYS", default=30, type=int)
    FEEDBACK_WINDOW_DAYS: int = _env("FEEDBACK_WINDOW_DAYS", default=14, type=int)
    MAX_PENDING_REQUESTS: int = _env("MAX_PENDING_REQUESTS", default=3, type=int)
    SESSION_MAX_HOURS: int = _env("SESSION_MAX_HOURS", default=4, type=int)

    # matching weights (checked at start-up: must sum to 1.0)
    MATCH_W_SKILLS: float = _env("MATCH_W_SKILLS", default=0.50, type=float) or 0.50
    MATCH_W_INTERESTS: float = _env("MATCH_W_INTERESTS", default=0.30, type=float) or 0.30
    MATCH_W_AVAILABILITY: float = _env("MATCH_W_AVAILABILITY", default=0.20, type=float) or 0.20

    # misc
    CORS_ORIGINS: str = _env("CORS_ORIGINS", default="http://localhost:5173")
    EMAIL_ENABLED: bool = _env("EMAIL_ENABLED", default=False, type=bool)
    DEFAULT_PAGE_SIZE: int = _env("DEFAULT_PAGE_SIZE", default=10, type=int)
    MAX_PAGE_SIZE: int = _env("MAX_PAGE_SIZE", default=50, type=int)

    # seeded administrator (seed-admin CLI; admins cannot self-register)
    ADMIN_EMAIL: str = _env("ADMIN_EMAIL", default="admin@example.org")
    ADMIN_PASSWORD: str = _env("ADMIN_PASSWORD", default="admin-password-123")

    # run background job loop inside the app process (dev convenience; also `cli.py run-jobs`)
    JOBS_ENABLED: bool = _env("JOBS_ENABLED", default=True, type=bool)

    ENV: str = _env("ENV", default="local")


cfg = Config()

if abs(cfg.MATCH_W_SKILLS + cfg.MATCH_W_INTERESTS + cfg.MATCH_W_AVAILABILITY - 1.0) > 1e-9:
    raise RuntimeError("MATCH_W_SKILLS + MATCH_W_INTERESTS + MATCH_W_AVAILABILITY must sum to 1.0")
