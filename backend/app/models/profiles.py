"""Student and mentor profiles, and their skill / interest links."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    student_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), unique=True)
    user_role: Mapped[str] = mapped_column(String(20), server_default=text("'student'"))
    programme_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    expected_graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    career_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidance_needs: Mapped[str | None] = mapped_column(Text, nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="student_profile", uselist=False, viewonly=True,
                        foreign_keys=[user_id])


class MentorProfile(Base):
    __tablename__ = "mentor_profiles"
    mentor_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), unique=True)
    user_role: Mapped[str] = mapped_column(String(20), server_default=text("'mentor'"))
    mentor_type: Mapped[str] = mapped_column(String(20), server_default=text("'alumni'"))
    professional_title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    organisation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    max_active_mentees: Mapped[int] = mapped_column(Integer, default=3)
    profile_status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="mentor_profile", uselist=False, viewonly=True,
                        foreign_keys=[user_id])

    def required_fields_complete(self) -> bool:
        return bool(self.professional_title and self.organisation and self.experience_years is not None
                    and self.bio and str(self.bio).strip())


class StudentSkills(Base):
    __tablename__ = "student_skills"
    student_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.student_profile_id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.skill_id", ondelete="RESTRICT"), primary_key=True)
    proficiency_level: Mapped[str] = mapped_column(String(30))   # beginner|intermediate|advanced|expert
    is_focus: Mapped[bool] = mapped_column(Boolean, default=False)


class MentorExpertise(Base):
    __tablename__ = "mentor_expertise"
    mentor_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mentor_profiles.mentor_profile_id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("skills.skill_id", ondelete="RESTRICT"), primary_key=True)
    expertise_level: Mapped[str] = mapped_column(String(30))


class StudentInterests(Base):
    __tablename__ = "student_interests"
    student_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("student_profiles.student_profile_id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_interests.interest_id", ondelete="RESTRICT"), primary_key=True)


class MentorInterests(Base):
    __tablename__ = "mentor_interests"
    mentor_profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("mentor_profiles.mentor_profile_id", ondelete="CASCADE"), primary_key=True)
    interest_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("career_interests.interest_id", ondelete="RESTRICT"), primary_key=True)
