"""SessionService (component C08): availability (E17-E21) and sessions (E33-E37). Rules R9-R13."""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import config
from app.core.errors import DomainError
from app.core.pagination import meta
from app.models import (AvailabilitySlot, MentorProfile, Mentorship, Session as SessionModel, Feedback, User)
from app.serializers import session_row, slot_row
from app.services import notification_service

cfg = config.cfg


def _utc(dt):
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ------------------------------------------------------------------ E17/E18/E19/E20 (R11)
def my_slots(db: Session, mentor_user_id, *, from_dt, to_dt, is_available: bool | None) -> dict:
    now = datetime.now(timezone.utc)
    stmt = select(AvailabilitySlot).where(AvailabilitySlot.mentor_id == mentor_user_id)
    if from_dt:
        stmt = stmt.where(AvailabilitySlot.end_time > from_dt)
    else:
        stmt = stmt.where(AvailabilitySlot.end_time > now)
    if to_dt:
        stmt = stmt.where(AvailabilitySlot.start_time < to_dt)
    if is_available is not None:
        stmt = stmt.where(AvailabilitySlot.is_available == is_available)
    rows = db.scalars(stmt.order_by(AvailabilitySlot.start_time)).all()
    booked_ids = {str(b) for b, in db.execute(
        select(SessionModel.slot_id).where(SessionModel.mentor_id == mentor_user_id,
                                           SessionModel.status == "scheduled", SessionModel.slot_id.isnot(None)))}
    return {"data": [slot_row(s, booked=str(s.slot_id) in booked_ids) for s in rows],
            "meta": meta(1, max(1, len(rows)), len(rows))}


def _overlap_exists(db: Session, mentor_id, start, end, exclude_slot=None) -> bool:
    stmt = select(func.count()).select_from(AvailabilitySlot).where(
        AvailabilitySlot.mentor_id == mentor_id,
        AvailabilitySlot.start_time < end, AvailabilitySlot.end_time > start)
    if exclude_slot is not None:
        stmt = stmt.where(AvailabilitySlot.slot_id != exclude_slot)
    return bool(db.scalar(stmt))


def _validate_times(start, end, field_prefix: str = "") -> tuple[datetime, datetime]:
    details = []
    if start is None or end is None:
        raise DomainError("VALIDATION_ERROR", details=[{"field": field_prefix + "start_time", "issue": "start_time and end_time are required"}])
    start, end = _utc(start), _utc(end)
    if end <= start:
        details.append({"field": field_prefix + "end_time", "issue": "end_time must be after start_time"})
    elif end - start > timedelta(hours=cfg.SESSION_MAX_HOURS):
        details.append({"field": field_prefix + "end_time", "issue": f"duration must be at most {cfg.SESSION_MAX_HOURS} hours"})
    if details:
        raise DomainError("VALIDATION_ERROR", details=details)
    return start, end


def create_slots(db: Session, mentor_user: User, *, slots: list | None, recurrence: dict | None) -> dict:
    to_create: list[tuple[datetime, datetime]] = []
    if slots:
        if len(slots) > 100:
            raise DomainError("VALIDATION_ERROR", details=[{"field": "slots", "issue": "at most 100 slots per call"}])
        for s in slots:
            start, end = _validate_times(s.get("start_time"), s.get("end_time"))
            to_create.append((start, end))
    if recurrence:
        weekdays = recurrence.get("weekdays") or []
        weeks = recurrence.get("weeks")
        try:
            t_start = str(recurrence["start_time"])
            t_end = str(recurrence["end_time"])
        except KeyError:
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence", "issue": "weekdays, start_time, end_time and weeks are required"}])
        if not isinstance(weeks, int) or not (1 <= weeks <= 12):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.weeks", "issue": "between 1 and 12 weeks"}])
        if not weekdays or not all(isinstance(w, int) and 0 <= w <= 6 for w in weekdays):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.weekdays", "issue": "0=Monday .. 6=Sunday"}])
        zone_name = recurrence.get("zone")
        try:
            zone = ZoneInfo(zone_name) if zone_name else timezone.utc
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.zone", "issue": "unknown IANA time zone"}])
        try:
            start_h, start_m = (int(part) for part in t_start.split(":"))
            end_h, end_m = (int(part) for part in t_end.split(":"))
        except (ValueError, TypeError):
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.start_time", "issue": "use HH:MM"}])
        # Expand in the mentor's zone (report Section 7.7): 18:00 local stays 18:00
        # across DST changes, while storage is UTC. Weekly patterns start next Monday.
        base = datetime.now(zone).date() + timedelta(days=1)
        next_monday = base + timedelta(days=(7 - base.weekday()) % 7)
        for week in range(weeks):
            monday = next_monday + timedelta(weeks=week)
            for wd in sorted(set(weekdays)):
                day = monday + timedelta(days=wd)
                local_start = datetime.combine(day, time(start_h, start_m), tzinfo=zone)
                local_end = datetime.combine(day, time(end_h, end_m), tzinfo=zone)
                if local_end <= local_start:
                    raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.end_time", "issue": "end_time must be after start_time"}])
                if local_end - local_start > timedelta(hours=cfg.SESSION_MAX_HOURS):
                    raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence.end_time", "issue": f"duration must be at most {cfg.SESSION_MAX_HOURS} hours"}])
                to_create.append((local_start.astimezone(timezone.utc), local_end.astimezone(timezone.utc)))
        if len(to_create) > 100:
            raise DomainError("VALIDATION_ERROR", details=[{"field": "recurrence", "issue": "at most 100 slots per call"}])
    if not to_create:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "slots", "issue": "provide slots or a recurrence"}])
    now = datetime.now(timezone.utc)
    details = []
    created = []
    for start, end in to_create:
        if end <= now:
            details.append({"field": "slots", "issue": "slots must be in the future"})
            continue
        if _overlap_exists(db, mentor_user.user_id, start, end):
            details.append({"field": "slots", "issue": f"a slot overlaps {start.isoformat()}"})
            continue
        created.append((start, end))
    if details:
        raise DomainError("VALIDATION_ERROR", details=details[:3])
    rows = [AvailabilitySlot(mentor_id=mentor_user.user_id, start_time=s, end_time=e, is_available=True)
            for s, e in created]
    db.add_all(rows)
    db.flush()
    return {"data": [slot_row(s) for s in rows], "meta": meta(1, max(1, len(rows)), len(rows))}


def _booked(db: Session, slot_id) -> bool:
    return bool(db.scalar(select(func.count()).select_from(SessionModel).where(
        SessionModel.slot_id == slot_id, SessionModel.status == "scheduled")))


def update_slot(db: Session, mentor_user: User, slot_id, payload: dict) -> dict:
    s = db.get(AvailabilitySlot, slot_id)
    if s is None or s.mentor_id != mentor_user.user_id:
        raise DomainError("NOT_FOUND")
    if _booked(db, s.slot_id):
        raise DomainError("SLOT_BOOKED")
    start = _utc(payload["start_time"]) if payload.get("start_time") is not None else s.start_time
    end = _utc(payload["end_time"]) if payload.get("end_time") is not None else s.end_time
    start, end = _validate_times(start, end)
    if _overlap_exists(db, s.mentor_id, start, end, exclude_slot=s.slot_id):
        raise DomainError("SLOT_OVERLAP")
    s.start_time, s.end_time = start, end
    if payload.get("is_available") is not None:
        s.is_available = bool(payload["is_available"])
    return slot_row(s)


def delete_slot(db: Session, mentor_user: User, slot_id) -> None:
    s = db.get(AvailabilitySlot, slot_id)
    if s is None or s.mentor_id != mentor_user.user_id:
        raise DomainError("NOT_FOUND")
    if _booked(db, s.slot_id):
        raise DomainError("SLOT_BOOKED")
    db.delete(s)


def open_slots(db: Session, viewer: User, mentor_id, *, from_dt, to_dt) -> dict:
    """E21: mentor self, admins, or students with an active mentorship with that mentor."""
    now = datetime.now(timezone.utc)
    if viewer.role == "mentor" and str(viewer.user_id) != str(mentor_id):
        raise DomainError("FORBIDDEN")
    if viewer.role == "student":
        allowed = db.scalar(select(func.count()).select_from(Mentorship).where(
            Mentorship.student_id == viewer.user_id, Mentorship.mentor_id == mentor_id,
            Mentorship.status == "active"))
        if not allowed:
            raise DomainError("FORBIDDEN")
    mentor = db.scalars(select(MentorProfile).where(MentorProfile.user_id == mentor_id)).first()
    if mentor is None:
        raise DomainError("NOT_FOUND")
    stmt = select(AvailabilitySlot).where(AvailabilitySlot.mentor_id == mentor_id,
                                          AvailabilitySlot.is_available == True,  # noqa: E712
                                          AvailabilitySlot.start_time > now)
    if from_dt:
        stmt = stmt.where(AvailabilitySlot.end_time > from_dt)
    if to_dt:
        stmt = stmt.where(AvailabilitySlot.start_time < to_dt)
    rows = db.scalars(stmt.order_by(AvailabilitySlot.start_time)).all()
    booked_ids = {str(b) for b, in db.execute(
        select(SessionModel.slot_id).where(SessionModel.mentor_id == mentor_id,
                                           SessionModel.status == "scheduled", SessionModel.slot_id.isnot(None)))}
    return {"data": [slot_row(s, booked=str(s.slot_id) in booked_ids) for s in rows],
            "meta": meta(1, max(1, len(rows)), len(rows))}


# ------------------------------------------------------------------ E33/E34/E35/E36/E37 (R9-R13)
def _mentorship(db: Session, mentorship_id, viewer: User) -> Mentorship:
    m = db.get(Mentorship, mentorship_id)
    if m is None:
        raise DomainError("NOT_FOUND")
    if viewer.user_id not in (m.student_id, m.mentor_id) and viewer.role != "admin":
        raise DomainError("NOT_FOUND")
    return m


def list_sessions(db: Session, user: User, *, mentorship_id, status: str | None, page: int, page_size: int,
                  include_feedback_flag: bool = True) -> dict:
    stmt = select(SessionModel)
    if user.role == "student":
        stmt = stmt.where(SessionModel.student_id == user.user_id)
    elif user.role == "mentor":
        stmt = stmt.where(SessionModel.mentor_id == user.user_id)
    elif mentorship_id is None:
        raise DomainError("FORBIDDEN")
    if mentorship_id is not None:
        m = _mentorship(db, mentorship_id, user)
        stmt = stmt.where(SessionModel.mentorship_id == m.mentorship_id)
    if status:
        if status not in ("scheduled", "completed", "cancelled"):
            raise DomainError("BAD_REQUEST", "Unknown session status filter.")
        stmt = stmt.where(SessionModel.status == status)
    rows = db.scalars(stmt.order_by(SessionModel.scheduled_start.desc())).all()
    mine = {str(f.session_id) for f in db.scalars(select(Feedback).where(Feedback.submitted_by == user.user_id)).all()}
    data = [session_row(s, my_feedback_submitted=str(s.session_id) in mine) for s in rows]
    start = (max(1, page) - 1) * page_size
    return {"data": data[start:start + page_size], "meta": meta(page, page_size, len(data))}


def calendar_sessions(db: Session, user: User, *, from_dt, to_dt, status: str | None,
                      page: int, page_size: int) -> dict:
    result = list_sessions(db, user, mentorship_id=None, status=status, page=page, page_size=page_size)
    if from_dt or to_dt:
        rows = [r for r in result["data"]
                if (not from_dt or r["scheduled_end"] > from_dt.isoformat())
                and (not to_dt or r["scheduled_start"] < to_dt.isoformat())]
        result["data"] = rows
        result["meta"] = meta(page, page_size, len(rows))
    return result


def get_session(db: Session, user: User, session_id) -> dict:
    s = db.get(SessionModel, session_id)
    if s is None:
        raise DomainError("NOT_FOUND")
    if user.user_id not in (s.student_id, s.mentor_id) and user.role != "admin":
        raise DomainError("NOT_FOUND")
    mine = db.scalar(select(func.count()).select_from(Feedback).where(
        Feedback.session_id == s.session_id, Feedback.submitted_by == user.user_id))
    student = db.get(User, s.student_id)
    mentor = db.get(User, s.mentor_id)
    return session_row(s, my_feedback_submitted=bool(mine),
                       extra={"student_name": student.full_name if student else None,
                              "mentor_name": mentor.full_name if mentor else None})


def schedule_session(db: Session, user: User, mentorship_id, *, slot_id=None, scheduled_start=None,
                     scheduled_end=None, meeting_mode: str = "online", meeting_link: str | None = None,
                     notes: str | None = None) -> dict:
    m = _mentorship(db, mentorship_id, user)
    if m.status != "active":
        raise DomainError("MENTORSHIP_NOT_ACTIVE")
    is_mentor = user.user_id == m.mentor_id
    if meeting_mode not in ("online", "phone", "in_person"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "meeting_mode", "issue": "must be online, phone or in_person"}])
    if meeting_link and len(meeting_link) > 2000:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "meeting_link", "issue": "must be at most 2000 characters"}])
    if notes and len(notes) > 4000:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "notes", "issue": "must be at most 4000 characters"}])
    now = datetime.now(timezone.utc)
    slot = None
    if slot_id:
        slot = db.get(AvailabilitySlot, slot_id)
        if slot is None or str(slot.mentor_id) != str(m.mentor_id):
            raise DomainError("SLOT_UNAVAILABLE")
        if not slot.is_available or slot.start_time <= now or _slot_held(db, slot.slot_id):
            raise DomainError("SLOT_UNAVAILABLE")
        start, end = slot.start_time, slot.end_time
    else:
        if not is_mentor:  # R9: a student must pick an open slot
            raise DomainError("VALIDATION_ERROR", details=[{"field": "slot_id", "issue": "students must book an open slot"}])
        start, end = _validate_times(scheduled_start, scheduled_end)
        if start <= now:
            raise DomainError("VALIDATION_ERROR", details=[{"field": "scheduled_start", "issue": "start must be in the future"}])
    if _mentor_conflict(db, m.mentor_id, start, end, exclude_session=None):
        raise DomainError("SESSION_CONFLICT")
    if _student_conflict(db, m.student_id, start, end, exclude_session=None):
        raise DomainError("SESSION_CONFLICT")
    s = SessionModel(mentorship_id=m.mentorship_id, student_id=m.student_id, mentor_id=m.mentor_id,
                     slot_id=slot.slot_id if slot else None, scheduled_start=start, scheduled_end=end,
                     meeting_mode=meeting_mode, meeting_link=meeting_link, status="scheduled", notes=notes)
    db.add(s)
    db.flush()
    counterpart_id = m.student_id if is_mentor else m.mentor_id
    counterpart = db.get(User, counterpart_id)
    notification_service.notify(db, counterpart_id, "Session scheduled",
                                f"A session with {user.full_name} is scheduled for {start.strftime('%Y-%m-%d %H:%M UTC')}.",
                                "session_scheduled", "session", s.session_id)
    student = db.get(User, m.student_id)
    mentor_u = db.get(User, m.mentor_id)
    return session_row(s, extra={"student_name": student.full_name if student else None,
                                 "mentor_name": mentor_u.full_name if mentor_u else None})


def _slot_held(db: Session, slot_id) -> bool:
    return bool(db.scalar(select(func.count()).select_from(SessionModel).where(
        SessionModel.slot_id == slot_id, SessionModel.status == "scheduled")))


def _mentor_conflict(db: Session, mentor_id, start, end, *, exclude_session) -> bool:
    stmt = select(func.count()).select_from(SessionModel).where(
        SessionModel.mentor_id == mentor_id, SessionModel.status == "scheduled",
        SessionModel.scheduled_start < end, SessionModel.scheduled_end > start)
    if exclude_session is not None:
        stmt = stmt.where(SessionModel.session_id != exclude_session)
    return bool(db.scalar(stmt))


def _student_conflict(db: Session, student_id, start, end, *, exclude_session) -> bool:
    stmt = select(func.count()).select_from(SessionModel).where(
        SessionModel.student_id == student_id, SessionModel.status == "scheduled",
        SessionModel.scheduled_start < end, SessionModel.scheduled_end > start)
    if exclude_session is not None:
        stmt = stmt.where(SessionModel.session_id != exclude_session)
    return bool(db.scalar(stmt))


def update_session(db: Session, user: User, session_id, payload: dict) -> dict:
    s = db.get(SessionModel, session_id)
    if s is None:
        raise DomainError("NOT_FOUND")
    is_mentor = user.user_id == s.mentor_id
    if user.user_id not in (s.student_id, s.mentor_id):
        raise DomainError("NOT_FOUND")
    details = []
    if payload.get("status") is not None:
        new_status = payload["status"]
        if new_status == "cancelled":
            if s.status != "scheduled":
                raise DomainError("INVALID_STATE_TRANSITION", f"The session is already {s.status}.")
            s.status = "cancelled"
            s.cancelled_by = user.user_id
            s.cancel_reason = (payload.get("cancel_reason") or "").strip() or None
            other_id = s.mentor_id if is_mentor else s.student_id
            notification_service.notify(db, other_id, "Session cancelled",
                                        f"The session on {s.scheduled_start.strftime('%Y-%m-%d %H:%M')} was cancelled"
                                        + (f": {s.cancel_reason}" if s.cancel_reason else "."),
                                        "session_cancelled", "session", s.session_id)
        elif new_status == "completed":
            if s.status != "scheduled":
                raise DomainError("INVALID_STATE_TRANSITION", f"The session is {s.status}; only scheduled sessions can be completed.")
            if not is_mentor:
                raise DomainError("FORBIDDEN", "Only the mentor can mark a session completed.")
            if datetime.now(timezone.utc) < s.scheduled_start:
                raise DomainError("INVALID_STATE_TRANSITION", "A session can be completed only after its start time.")
            s.status = "completed"
            other_id = s.student_id
            notification_service.notify(db, other_id, "Feedback requested",
                                        "How was the session? Rate it within 14 days.",
                                        "feedback_requested", "session", s.session_id)
        else:
            details.append({"field": "status", "issue": "must be cancelled or completed"})
    if details:
        raise DomainError("VALIDATION_ERROR", details=details)
    if payload.get("notes") is not None:
        if len(payload["notes"]) > 4000:
            details.append({"field": "notes", "issue": "must be at most 4000 characters"})
        else:
            s.notes = payload["notes"] or None
    if payload.get("meeting_mode") is not None:
        if payload["meeting_mode"] not in ("online", "phone", "in_person"):
            details.append({"field": "meeting_mode", "issue": "must be online, phone or in_person"})
        else:
            s.meeting_mode = payload["meeting_mode"]
    if payload.get("meeting_link") is not None:
        if len(payload["meeting_link"]) > 2000:
            details.append({"field": "meeting_link", "issue": "must be at most 2000 characters"})
        else:
            s.meeting_link = payload["meeting_link"] or None
    if details:
        raise DomainError("VALIDATION_ERROR", details=details)
    return get_session(db, user, s.session_id)


def session_feedback_flags(db: Session, user: User, rows: list[dict]) -> list[dict]:
    mine = {str(f.session_id) for f in db.scalars(select(Feedback).where(Feedback.submitted_by == user.user_id)).all()}
    for r in rows:
        r["my_feedback_submitted"] = str(r["session_id"]) in mine
    return rows
