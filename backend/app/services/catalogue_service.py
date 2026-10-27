"""CatalogueService (component C03): E10 / E11 lists and admin CRUD (E55-E58)."""
from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import AuditLog, CareerInterest, Skill
from app.serializers import interest_row, skill_row
from app.services import audit_service


def list_skills(db: Session, *, q: str | None, category: str | None, page: int, page_size: int,
                include_inactive: bool = False, with_usage: bool = False) -> dict:
    stmt = select(Skill)
    if not include_inactive:
        stmt = stmt.where(Skill.is_active == True)  # noqa: E712
    if q:
        stmt = stmt.where(Skill.skill_name.ilike(f"%{q}%"))
    if category:
        stmt = stmt.where(Skill.category == category)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(Skill.skill_name).offset((page - 1) * page_size).limit(page_size)).all()
    usage = usage_counts(db)[0] if with_usage else None
    data = []
    for s in rows:
        row = skill_row(s)
        if usage is not None:
            row["usage_count"] = usage.get(str(s.skill_id), 0)
        data.append(row)
    return {"data": data, "meta": meta(page, page_size, total or 0)}


def list_interests(db: Session, *, page: int, page_size: int, include_inactive: bool = False,
                   with_usage: bool = False) -> dict:
    stmt = select(CareerInterest)
    if not include_inactive:
        stmt = stmt.where(CareerInterest.is_active == True)  # noqa: E712
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(CareerInterest.interest_name).offset((page - 1) * page_size).limit(page_size)).all()
    usage = usage_counts(db)[1] if with_usage else None
    data = []
    for c in rows:
        row = interest_row(c)
        if usage is not None:
            row["usage_count"] = usage.get(str(c.interest_id), 0)
        data.append(row)
    return {"data": data, "meta": meta(page, page_size, total or 0)}


# ------------------------------------------------------------------ admin (E55-E58)
def create_skill(db: Session, *, skill_name: str, category: str | None, actor, ip) -> dict:
    skill_name = (skill_name or "").strip()
    if not (1 <= len(skill_name) <= 100):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "skill_name", "issue": "must be 1-100 characters"}])
    if category and len(category) > 80:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "category", "issue": "must be at most 80 characters"}])
    if db.scalar(select(Skill.skill_id).where(func.lower(Skill.skill_name) == skill_name.lower())):
        raise DomainError("DUPLICATE_ENTRY", f'A skill named "{skill_name}" already exists.')
    s = Skill(skill_name=skill_name, category=category)
    db.add(s)
    db.flush()
    audit_service.record(db, actor.user_id, "catalogue.skill_added", "skill", s.skill_id, {"name": skill_name}, ip)
    return skill_row(s)


def update_skill(db: Session, skill_id, payload: dict, actor, ip) -> dict:
    s = db.get(Skill, skill_id)
    if s is None:
        raise DomainError("NOT_FOUND")
    if "skill_name" in payload and payload["skill_name"] is not None:
        name = str(payload["skill_name"]).strip()
        if not (1 <= len(name) <= 100):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "skill_name", "issue": "must be 1-100 characters"}])
        clash = db.scalar(select(Skill.skill_id).where(func.lower(Skill.skill_name) == name.lower(), Skill.skill_id != s.skill_id))
        if clash:
            raise DomainError("DUPLICATE_ENTRY", f'A skill named "{name}" already exists.')
        s.skill_name = name
    if "category" in payload:
        s.category = payload["category"]
    if "is_active" in payload and payload["is_active"] is not None:
        s.is_active = bool(payload["is_active"])
    audit_service.record(db, actor.user_id, "catalogue.skill_updated", "skill", s.skill_id,
                         {"name": s.skill_name, "is_active": s.is_active}, ip)
    return skill_row(s)


def create_interest(db: Session, *, interest_name: str, description: str | None, actor, ip) -> dict:
    interest_name = (interest_name or "").strip()
    if not (1 <= len(interest_name) <= 100):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "interest_name", "issue": "must be 1-100 characters"}])
    if description and len(description) > 500:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "description", "issue": "must be at most 500 characters"}])
    if db.scalar(select(CareerInterest.interest_id).where(func.lower(CareerInterest.interest_name) == interest_name.lower())):
        raise DomainError("DUPLICATE_ENTRY", f'A career interest named "{interest_name}" already exists.')
    c = CareerInterest(interest_name=interest_name, description=description)
    db.add(c)
    db.flush()
    audit_service.record(db, actor.user_id, "catalogue.interest_added", "career_interest", c.interest_id,
                         {"name": interest_name}, ip)
    return interest_row(c)


def update_interest(db: Session, interest_id, payload: dict, actor, ip) -> dict:
    c = db.get(CareerInterest, interest_id)
    if c is None:
        raise DomainError("NOT_FOUND")
    if "interest_name" in payload and payload["interest_name"] is not None:
        name = str(payload["interest_name"]).strip()
        if not (1 <= len(name) <= 100):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "interest_name", "issue": "must be 1-100 characters"}])
        clash = db.scalar(select(CareerInterest.interest_id)
                          .where(func.lower(CareerInterest.interest_name) == name.lower(),
                                 CareerInterest.interest_id != c.interest_id))
        if clash:
            raise DomainError("DUPLICATE_ENTRY", f'A career interest named "{name}" already exists.')
        c.interest_name = name
    if "description" in payload:
        c.description = payload["description"]
    if "is_active" in payload and payload["is_active"] is not None:
        c.is_active = bool(payload["is_active"])
    audit_service.record(db, actor.user_id, "catalogue.interest_updated", "career_interest", c.interest_id,
                         {"name": c.interest_name, "is_active": c.is_active}, ip)
    return interest_row(c)


def usage_counts(db: Session) -> tuple[dict, dict]:
    """Catalogue usage counters for admin page 23."""
    from app.models import MentorExpertise, MentorInterests, StudentInterests, StudentSkills
    skill_use = {str(s): int(c) for s, c in db.execute(
        select(StudentSkills.skill_id, func.count()).group_by(StudentSkills.skill_id)).all()}
    for s, c in db.execute(select(MentorExpertise.skill_id, func.count()).group_by(MentorExpertise.skill_id)):
        skill_use[str(s)] = skill_use.get(str(s), 0) + int(c)
    interest_use = {str(i): int(c) for i, c in db.execute(
        select(StudentInterests.interest_id, func.count()).group_by(StudentInterests.interest_id)).all()}
    for i, c in db.execute(select(MentorInterests.interest_id, func.count()).group_by(MentorInterests.interest_id)):
        interest_use[str(i)] = interest_use.get(str(i), 0) + int(c)
    return skill_use, interest_use
