"""User accounts and refresh tokens."""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import CHAR, Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import config
from app.extensions import db_provider  # noqa: F401 (keeps import graph obvious)
from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    account_status: Mapped[str] = mapped_column(String(20), default="active")
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    anonymised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, viewonly=True,
                                   foreign_keys="StudentProfile.user_id")
    mentor_profile = relationship("MentorProfile", back_populates="user", uselist=False, viewonly=True,
                                  foreign_keys="MentorProfile.user_id")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    token_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)

    @staticmethod
    def new(user_id, family_id, hashed: str) -> "RefreshToken":
        return RefreshToken(user_id=user_id, family_id=family_id, token_hash=hashed,
                            expires_at=datetime.now(tz=timedelta(0)).astimezone() + timedelta(days=config.cfg.REFRESH_TOKEN_DAYS))
