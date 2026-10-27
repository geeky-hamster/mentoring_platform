"""MatchingService (component C05) and DiscoveryService (C04).

The scoring rule is a faithful port of the report's reference implementation
(src/matching.py): Score = 0.50 S + 0.30 C + 0.20 A with weight renormalisation when a
dimension is missing, hard eligibility filters, deterministic tie-breaks and pagination.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import config
from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import (AvailabilitySlot, CareerInterest, Feedback, MentorExpertise, MentorInterests,
                        MentorProfile, Mentorship, MentoringRequest, Session as SessionModel, Skill,
                        StudentInterests, StudentProfile, StudentSkills, User)

cfg = config.cfg
W_S, W_C, W_A = cfg.MATCH_W_SKILLS, cfg.MATCH_W_INTERESTS, cfg.MATCH_W_AVAILABILITY
LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
Q_HIGHER, Q_EQUAL, Q_LOWER = 1.0, 0.6, 0.3
SLOT_TARGET = 6
MAX_FOCUS = 5


@dataclass
class MatchStudent:
    skills: dict[str, str] = field(default_factory=dict)   # skill_id -> level
    focus: set[str] = field(default_factory=set)
    interests: set[str] = field(default_factory=set)


@dataclass
class MatchMentor:
    mentor_id: str
    name: str
    full_name: str
    professional_title: str | None
    organisation: str | None
    experience_years: int | None
    mentor_type: str
    expertise: dict[str, str]
    interests: set[str]
    interest_names: list[str]
    open_slots_14d: int
    active_mentees: int
    max_active_mentees: int
    approved: bool = True
    is_available: bool = True
    account_active: bool = True
    blocked_for_student: bool = False


# ------------------------------------------------------------------ pure scoring (report Section 10)
def eligible(m: MatchMentor) -> bool:
    return (m.approved and m.is_available and m.account_active and not m.blocked_for_student
            and m.active_mentees < m.max_active_mentees)


def focus_skills(s: MatchStudent) -> list[str]:
    return sorted(s.focus)[:MAX_FOCUS] if s.focus else sorted(s.skills)[:MAX_FOCUS]


def skill_score(s: MatchStudent, m: MatchMentor) -> float | None:
    f = focus_skills(s)
    if not f:
        return None
    total = 0.0
    for k in f:
        if k in m.expertise:
            ms, ss = LEVEL_RANK[m.expertise[k]], LEVEL_RANK[s.skills[k]]
            total += Q_HIGHER if ms > ss else (Q_EQUAL if ms == ss else Q_LOWER)
    return 100.0 * total / len(f)


def interest_score(s: MatchStudent, m: MatchMentor) -> float | None:
    if not s.interests:
        return None
    return 100.0 * len(s.interests & m.interests) / len(s.interests)


def availability_score(m: MatchMentor) -> float:
    free = m.max_active_mentees - m.active_mentees
    return 70.0 * min(1.0, m.open_slots_14d / SLOT_TARGET) + 30.0 * free / m.max_active_mentees


def score(s: MatchStudent, m: MatchMentor) -> dict:
    S, C, A = skill_score(s, m), interest_score(s, m), availability_score(m)
    parts = [(W_S, S), (W_C, C), (W_A, A)]
    used = [(w, x) for w, x in parts if x is not None]
    total = sum(w * x for w, x in used) / sum(w for w, _ in used)  # missing-data rule
    r1 = lambda v: None if v is None else round(v + 1e-9, 1)  # noqa: E731
    return dict(mentor_id=m.mentor_id, name=m.name, S=r1(S), C=r1(C), A=r1(A), score=r1(total),
                free_capacity=m.max_active_mentees - m.active_mentees, open_slots=m.open_slots_14d)


def rank(s: MatchStudent, mentors: list[MatchMentor]) -> list[dict]:
    rows = [score(s, m) for m in mentors if eligible(m)]
    key = lambda r: (-r["score"], -(r["S"] or 0), -(r["C"] or 0), -r["open_slots"], -r["free_capacity"], r["mentor_id"])  # noqa: E731
    return sorted(rows, key=key)


def reasons_for(s: MatchStudent, m: MatchMentor, sc: dict) -> list[str]:
    """Human-readable reasons for the ranking (E23 contract)."""
    reasons = []
    f = focus_skills(s)
    covered = [(k, LEVEL_RANK[m.expertise[k]], LEVEL_RANK[s.skills[k]]) for k in f if k in m.expertise]
    higher = sum(1 for _, ms, ss in covered if ms > ss)
    equal = sum(1 for _, ms, ss in covered if ms == ss)
    if covered:
        parts = []
        if higher:
            parts.append(f"Covers {higher} of your focus skills at a higher level")
        if equal:
            parts.append(f"matches {equal} focus skill{'s' if equal != 1 else ''} at your level")
        reasons.append(" and ".join(parts))
    shared = len(s.interests & m.interests)
    if shared and s.interests:
        reasons.append(f"Advises on {shared} of your {len(s.interests)} career interests"
                       + (" (all of them)" if shared == len(s.interests) else ""))
    if sc["open_slots"] >= SLOT_TARGET:
        reasons.append(f"Wide availability: {sc['open_slots']} open slots in the next 14 days")
    else:
        reasons.append(f"{sc['free_capacity']} mentee spot{'s' if sc['free_capacity'] != 1 else ''} free, "
                       f"{sc['open_slots']} open slots in the next 14 days")
    return reasons


# ------------------------------------------------------------------ DB loaders
def load_student(db: Session, user_id) -> MatchStudent:
    p = db.scalars(select(StudentProfile).where(StudentProfile.user_id == user_id)).first()
    s = MatchStudent()
    if p is None:
        return s
    for ss, skill in db.execute(select(StudentSkills, Skill).join(Skill, Skill.skill_id == StudentSkills.skill_id)
                                .where(StudentSkills.student_profile_id == p.student_profile_id)):
        s.skills[str(ss.skill_id)] = ss.proficiency_level
        if ss.is_focus:
            s.focus.add(str(ss.skill_id))
    for ci, in db.execute(select(CareerInterest.interest_id)
                          .join(StudentInterests, StudentInterests.interest_id == CareerInterest.interest_id)
                          .where(StudentInterests.student_profile_id == p.student_profile_id)):
        s.interests.add(str(ci))
    return s


def load_mentors(db: Session, *, student_id=None, statuses=("approved",), accepting: bool | None = True) -> list[MatchMentor]:
    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=14)
    mentors = db.execute(
        select(MentorProfile, User)
        .join(User, User.user_id == MentorProfile.user_id)
        .where(MentorProfile.profile_status.in_(list(statuses)), User.account_status == "active")).all()
    out: list[MatchMentor] = []
    for p, u in mentors:
        expertise = {str(r): lvl for r, lvl in db.execute(
            select(MentorExpertise.skill_id, MentorExpertise.expertise_level)
            .where(MentorExpertise.mentor_profile_id == p.mentor_profile_id))}
        interests_rows = db.execute(
            select(CareerInterest.interest_id, CareerInterest.interest_name)
            .join(MentorInterests, MentorInterests.interest_id == CareerInterest.interest_id)
            .where(MentorInterests.mentor_profile_id == p.mentor_profile_id)).all()
        open_slots = db.scalar(select(func.count()).select_from(
            select(AvailabilitySlot.slot_id)
            .where(AvailabilitySlot.mentor_id == p.user_id, AvailabilitySlot.is_available == True,  # noqa: E712
                   AvailabilitySlot.start_time > now, AvailabilitySlot.start_time < horizon).subquery())) or 0
        active = db.scalar(select(func.count()).select_from(
            select(Mentorship.mentorship_id).where(Mentorship.mentor_id == p.user_id, Mentorship.status == "active").subquery())) or 0
        blocked = False
        if student_id is not None:
            blocked = bool(
                db.scalar(select(func.count()).select_from(
                    select(MentoringRequest.request_id).where(
                        MentoringRequest.student_id == student_id, MentoringRequest.mentor_id == p.user_id,
                        MentoringRequest.status == "pending").subquery()))
                or db.scalar(select(func.count()).select_from(
                    select(Mentorship.mentorship_id).where(
                        Mentorship.student_id == student_id, Mentorship.mentor_id == p.user_id,
                        Mentorship.status == "active").subquery()))
                or db.scalar(select(func.count()).select_from(
                    select(MentoringRequest.request_id).where(
                        MentoringRequest.student_id == student_id, MentoringRequest.mentor_id == p.user_id,
                        MentoringRequest.status == "declined",
                        MentoringRequest.responded_at > now - timedelta(days=cfg.COOLDOWN_DAYS)).subquery())))
        out.append(MatchMentor(
            mentor_id=str(p.user_id), name=u.full_name, full_name=u.full_name,
            professional_title=p.professional_title, organisation=p.organisation,
            experience_years=p.experience_years, mentor_type=p.mentor_type, expertise=expertise,
            interests={str(i) for i, _ in interests_rows}, interest_names=[n for _, n in interests_rows],
            open_slots_14d=int(open_slots), active_mentees=int(active), max_active_mentees=p.max_active_mentees,
            approved=p.profile_status == "approved", is_available=p.is_available,
            account_active=u.account_status == "active", blocked_for_student=blocked))
    return out


def top_skills(db: Session, mentor_id, limit: int = 3) -> list[str]:
    rows = db.execute(
        select(Skill.skill_name).join(MentorExpertise, MentorExpertise.skill_id == Skill.skill_id)
        .where(MentorExpertise.mentor_profile_id == (
            select(MentorProfile.mentor_profile_id).where(MentorProfile.user_id == mentor_id).scalar_subquery()))
        .order_by(MentorExpertise.expertise_level.desc(), Skill.skill_name).limit(limit)).scalars().all()
    return list(rows)


# ------------------------------------------------------------------ E23 / E22
def recommended(db: Session, student_user_id, *, page: int, page_size: int) -> dict:
    profile = db.scalars(select(StudentProfile).where(StudentProfile.user_id == student_user_id)).first()
    if profile is None or not profile.profile_completed:
        raise DomainError("PROFILE_INCOMPLETE")
    s = load_student(db, student_user_id)
    mentors = load_mentors(db, student_id=profile.user_id)
    ranked = rank(s, mentors)
    total = len(ranked)
    start = (max(1, page) - 1) * page_size
    page_rows = ranked[start:start + page_size]
    data = []
    mentor_map = {m.mentor_id: m for m in mentors}
    for row in page_rows:
        m = mentor_map[row["mentor_id"]]
        card = {
            "mentor_id": m.mentor_id, "full_name": m.full_name, "professional_title": m.professional_title,
            "organisation": m.organisation, "experience_years": m.experience_years, "mentor_type": m.mentor_type,
            "top_skills": list(top_skills(db, m.mentor_id)), "interests": m.interest_names,
            "accepting_mentees": m.is_available and m.active_mentees < m.max_active_mentees,
        }
        data.append({"mentor": card, "match_score": row["score"],
                     "breakdown": {"skills": row["S"], "interests": row["C"], "availability": row["A"]},
                     "reasons": reasons_for(s, m, row)})
    return {"data": data, "meta": meta(page, page_size, total)}


def search(db: Session, *, q: str | None, skill_ids: list[str] | None, interest_ids: list[str] | None,
           mentor_type: str | None, min_experience: int | None, accepting: bool, sort: str,
           page: int, page_size: int) -> dict:
    stmt = (select(MentorProfile, User)
            .join(User, User.user_id == MentorProfile.user_id)
            .where(MentorProfile.profile_status == "approved", User.account_status == "active"))
    if accepting:
        stmt = stmt.where(MentorProfile.is_available == True)  # noqa: E712
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(MentorProfile.professional_title.ilike(like), MentorProfile.organisation.ilike(like),
                              MentorProfile.bio.ilike(like)))
    if mentor_type:
        if mentor_type not in ("recent_graduate", "alumni"):
            raise DomainError("BAD_REQUEST", "mentor_type must be recent_graduate or alumni.")
        stmt = stmt.where(MentorProfile.mentor_type == mentor_type)
    if min_experience is not None:
        stmt = stmt.where(MentorProfile.experience_years >= min_experience)
    if skill_ids:
        stmt = stmt.where(MentorProfile.user_id.in_(
            select(MentorProfile.user_id)
            .join(MentorExpertise, MentorExpertise.mentor_profile_id == MentorProfile.mentor_profile_id)
            .where(MentorExpertise.skill_id.in_(skill_ids)).subquery()))
    if interest_ids:
        stmt = stmt.where(MentorProfile.user_id.in_(
            select(MentorProfile.user_id)
            .join(MentorInterests, MentorInterests.mentor_profile_id == MentorProfile.mentor_profile_id)
            .where(MentorInterests.interest_id.in_(interest_ids)).subquery()))
    if sort == "experience":
        stmt = stmt.order_by(MentorProfile.experience_years.desc().nullslast(), User.full_name)
    elif sort == "name":
        stmt = stmt.order_by(User.full_name)
    else:
        stmt = stmt.order_by(MentorProfile.created_at.desc())
    rows = db.execute(stmt).all()
    total = len(rows)
    start = (max(1, page) - 1) * page_size
    data = []
    for p, u in rows[start:start + page_size]:
        active = db.scalar(select(func.count()).select_from(
            select(Mentorship.mentorship_id).where(Mentorship.mentor_id == p.user_id, Mentorship.status == "active").subquery())) or 0
        open_slots = db.scalar(select(func.count()).select_from(
            select(AvailabilitySlot.slot_id).where(AvailabilitySlot.mentor_id == p.user_id,
                   AvailabilitySlot.is_available == True,  # noqa: E712
                   AvailabilitySlot.start_time > datetime.now(timezone.utc),
                   AvailabilitySlot.start_time < datetime.now(timezone.utc) + timedelta(days=14)).subquery())) or 0
        data.append({
            "mentor_id": str(p.user_id), "full_name": u.full_name, "professional_title": p.professional_title,
            "organisation": p.organisation, "experience_years": p.experience_years, "mentor_type": p.mentor_type,
            "top_skills": list(top_skills(db, p.user_id)),
            "interests": [n for n, in db.execute(
                select(CareerInterest.interest_name)
                .join(MentorInterests, MentorInterests.interest_id == CareerInterest.interest_id)
                .where(MentorInterests.mentor_profile_id == p.mentor_profile_id))],
            "accepting_mentees": p.is_available and active < p.max_active_mentees,
            "open_slots_14d": int(open_slots),
        })
    return {"data": data, "meta": meta(page, page_size, total)}
