"""Reference implementation of the proposed rule-based mentor matching (Section 10).
Weights are proposed assumptions, not validated values. Pure functions: no database access.
Run this file to execute the self-tests that back the worked example in the report."""
from dataclasses import dataclass, field
from typing import Dict, Set, List, Optional

W_S, W_C, W_A = 0.50, 0.30, 0.20          # proposed weights (to be validated by user research)
LEVEL_RANK = {"beginner": 1, "intermediate": 2, "advanced": 3, "expert": 4}
Q_HIGHER, Q_EQUAL, Q_LOWER = 1.0, 0.6, 0.3   # mentor level above / equal / below the student's level
SLOT_TARGET = 6                               # open slots in the next 14 days that earn the full slot score
MAX_FOCUS = 5


@dataclass
class Student:
    skills: Dict[str, str]                    # skill_id -> proficiency_level
    focus: Set[str] = field(default_factory=set)
    interests: Set[str] = field(default_factory=set)


@dataclass
class Mentor:
    mentor_id: str
    name: str
    expertise: Dict[str, str]                 # skill_id -> expertise_level
    interests: Set[str]
    open_slots_14d: int
    active_mentees: int
    max_active_mentees: int
    approved: bool = True
    is_available: bool = True
    account_active: bool = True
    blocked_for_student: bool = False         # pending request, active mentorship or cooldown with this student


def eligible(m: Mentor) -> bool:
    """Hard filters applied before any scoring."""
    return (m.approved and m.is_available and m.account_active and not m.blocked_for_student
            and m.active_mentees < m.max_active_mentees)


def focus_skills(s: Student) -> List[str]:
    chosen = sorted(s.focus)[:MAX_FOCUS] if s.focus else sorted(s.skills)[:MAX_FOCUS]
    return chosen


def skill_score(s: Student, m: Mentor) -> Optional[float]:
    f = focus_skills(s)
    if not f:
        return None
    total = 0.0
    for k in f:
        if k in m.expertise:
            ms, ss = LEVEL_RANK[m.expertise[k]], LEVEL_RANK[s.skills[k]]
            total += Q_HIGHER if ms > ss else (Q_EQUAL if ms == ss else Q_LOWER)
    return 100.0 * total / len(f)


def interest_score(s: Student, m: Mentor) -> Optional[float]:
    if not s.interests:
        return None
    return 100.0 * len(s.interests & m.interests) / len(s.interests)


def availability_score(m: Mentor) -> float:
    free = m.max_active_mentees - m.active_mentees
    return 70.0 * min(1.0, m.open_slots_14d / SLOT_TARGET) + 30.0 * free / m.max_active_mentees


def score(s: Student, m: Mentor) -> dict:
    S, C, A = skill_score(s, m), interest_score(s, m), availability_score(m)
    parts = [(W_S, S), (W_C, C), (W_A, A)]
    used = [(w, x) for w, x in parts if x is not None]
    total = sum(w * x for w, x in used) / sum(w for w, _ in used)   # missing-data rule: renormalise weights
    r1 = lambda v: None if v is None else round(v + 1e-9, 1)
    return dict(mentor_id=m.mentor_id, name=m.name, S=r1(S), C=r1(C), A=r1(A), score=r1(total),
                free_capacity=m.max_active_mentees - m.active_mentees, open_slots=m.open_slots_14d)


def rank(s: Student, mentors: List[Mentor]) -> List[dict]:
    rows = [score(s, m) for m in mentors if eligible(m)]
    key = lambda r: (-r["score"], -(r["S"] or 0), -(r["C"] or 0), -r["open_slots"], -r["free_capacity"], r["mentor_id"])
    return sorted(rows, key=key)


def paginate(rows: List[dict], page: int = 1, page_size: int = 10):
    page_size = max(1, min(page_size, 50))
    total = len(rows)
    start = (page - 1) * page_size
    return rows[start:start + page_size], dict(page=page, page_size=page_size, total=total,
                                               total_pages=max(1, -(-total // page_size)))


# ---------------------------------------------------------------------------------------------
# Worked example used in the report (all identifiers are illustrative)
# ---------------------------------------------------------------------------------------------
SK = dict(python="a4c1e7d2-0b35-4f89-9a16-3d7e5b2c8f40", sql="5e9b3a7c-2d14-4c68-8f01-6a2d9e4b7c13",
          ml="d7f2b8e4-6a19-4e30-b5c7-1f3a9d0e2b65", stats="1b6d4f9a-8c27-4a53-9e0d-7c5b3a1f8d26")
IN = dict(ds="6c3e9a1f-4b72-4d58-a0e6-9b1d7f2c5a34", higher="f1a8d5c3-9e47-4b06-8c2a-3e6b0d7f1a59")

ASHA = Student(skills={SK["python"]: "intermediate", SK["sql"]: "beginner", SK["ml"]: "beginner"},
               focus={SK["python"], SK["sql"], SK["ml"]}, interests={IN["ds"], IN["higher"]})

MENTORS = [
    Mentor("9d4c7e52-1a3b-4f68-8c2d-5b7e0a9f3c21", "Rohan Iyer",
           {SK["python"]: "advanced", SK["sql"]: "advanced", SK["ml"]: "intermediate"}, {IN["ds"]}, 4, 1, 3),
    Mentor("a2f6c8d1-3e59-4b74-9d0a-5c1e7b3f9a68", "Meera Nair",
           {SK["python"]: "intermediate", SK["ml"]: "expert", SK["stats"]: "advanced"}, {IN["ds"], IN["higher"]}, 6, 0, 2),
    Mentor("c5b9e3a7-1d62-4f08-a4c9-8e2b6d0f7a31", "Karthik Rao",
           {SK["python"]: "advanced", SK["sql"]: "beginner"}, {IN["higher"]}, 2, 2, 3),
    Mentor("e0d4a8f2-7c13-4b95-b6e1-2a9c5f3d8b70", "Divya Sharma",            # excluded: at capacity
           {SK["python"]: "expert", SK["sql"]: "expert", SK["ml"]: "expert"}, {IN["ds"], IN["higher"]}, 5, 2, 2),
    Mentor("0b7e5c9d-4a21-4d86-8f3b-6c1a9e2d4f57", "Sanjay Patel",            # excluded: not accepting mentees
           {SK["python"]: "expert"}, {IN["ds"]}, 3, 0, 3, is_available=False),
    Mentor("7a3d1f6b-9c48-4e02-b5a7-4d8e2c0f6b19", "Lakshmi Pillai",          # excluded: profile not approved
           {SK["python"]: "advanced", SK["sql"]: "advanced"}, {IN["ds"]}, 4, 0, 3, approved=False),
]


def worked_example():
    return rank(ASHA, MENTORS)


def _selftest():
    res = worked_example()
    assert [r["name"] for r in res] == ["Rohan Iyer", "Meera Nair", "Karthik Rao"], res
    by = {r["name"]: r for r in res}
    assert (by["Rohan Iyer"]["S"], by["Rohan Iyer"]["C"], by["Rohan Iyer"]["A"], by["Rohan Iyer"]["score"]) == (100.0, 50.0, 66.7, 78.3)
    assert (by["Meera Nair"]["S"], by["Meera Nair"]["C"], by["Meera Nair"]["A"], by["Meera Nair"]["score"]) == (53.3, 100.0, 100.0, 76.7)
    assert (by["Karthik Rao"]["S"], by["Karthik Rao"]["C"], by["Karthik Rao"]["A"], by["Karthik Rao"]["score"]) == (53.3, 50.0, 33.3, 48.3)
    # exclusions
    assert not eligible(MENTORS[3]) and not eligible(MENTORS[4]) and not eligible(MENTORS[5])
    # missing-data rule: a student with no interests is scored on S and A only (weights renormalised)
    s2 = Student(skills=ASHA.skills, focus=ASHA.focus, interests=set())
    r = score(s2, MENTORS[0])
    assert r["C"] is None and r["score"] == round((0.5 * 100 + 0.2 * (70 * 4 / 6 + 30 * 2 / 3)) / 0.7 + 1e-9, 1)
    # tie-break: same score -> higher S first, then more open slots, then lower mentor_id
    a = Mentor("00000000-0000-4000-8000-00000000000a", "A", {SK["python"]: "advanced"}, set(), 6, 0, 1)
    b = Mentor("00000000-0000-4000-8000-00000000000b", "B", {SK["python"]: "advanced"}, set(), 6, 0, 1)
    s3 = Student(skills={SK["python"]: "intermediate"}, focus={SK["python"]})
    assert [x["name"] for x in rank(s3, [b, a])] == ["A", "B"]
    # pagination
    page, meta = paginate(res, 2, 2)
    assert [p["name"] for p in page] == ["Karthik Rao"] and meta["total"] == 3 and meta["total_pages"] == 2
    return True


if __name__ == "__main__":
    _selftest()
    for r in worked_example():
        print(r)
    print("matching self-tests passed")
