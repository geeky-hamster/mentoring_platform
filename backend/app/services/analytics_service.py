"""AnalyticsService (component C12): KPI overview (E51), trends (E52), CSV export (E53)."""
from __future__ import annotations

import csv
import io
import statistics
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.models import (Feedback, MentorProfile, Mentorship, MentoringRequest,
                        Session as SessionModel, User)


def _range(from_date, to_date) -> tuple[datetime, datetime]:
    try:
        start = datetime.fromisoformat(from_date).replace(tzinfo=timezone.utc)
        end = datetime.fromisoformat(to_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
    except Exception:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "from", "issue": "from/to must be ISO dates (YYYY-MM-DD)"}])
    if start >= end:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "to", "issue": "to must be after from"}])
    return start, end


def overview(db: Session, from_date: str, to_date: str) -> dict:
    start, end = _range(from_date, to_date)
    users_counts = dict(db.execute(select(User.role, func.count()).where(
        User.account_status == "active").group_by(User.role)).all())
    mentor_statuses = dict(db.execute(select(MentorProfile.profile_status, func.count())
                                      .group_by(MentorProfile.profile_status)).all())
    capacity_total = db.scalar(select(func.coalesce(func.sum(MentorProfile.max_active_mentees), 0))
                               .where(MentorProfile.profile_status == "approved")) or 0
    active_mentorships_now = db.scalar(select(func.count()).select_from(Mentorship).where(
        Mentorship.status == "active")) or 0
    requests_by_status = dict(db.execute(select(MentoringRequest.status, func.count()).where(
        MentoringRequest.created_at >= start, MentoringRequest.created_at < end)
        .group_by(MentoringRequest.status)).all())
    decided = requests_by_status.get("accepted", 0) + requests_by_status.get("declined", 0)
    acceptance_rate = round(requests_by_status.get("accepted", 0) / decided, 3) if decided else 0.0
    response_hours = [r[0] for r in db.execute(
        select(func.extract("epoch", MentoringRequest.responded_at - MentoringRequest.created_at) / 3600.0)
        .where(MentoringRequest.responded_at.isnot(None),
               MentoringRequest.created_at >= start, MentoringRequest.created_at < end)).all()]
    median_response = round(statistics.median(response_hours), 1) if response_hours else None
    mentorships_by_status = dict(db.execute(select(Mentorship.status, func.count()).where(
        Mentorship.created_at >= start, Mentorship.created_at < end).group_by(Mentorship.status)).all())
    with_three = db.scalar(select(func.count()).select_from(
        select(SessionModel.mentorship_id).where(SessionModel.status == "completed")
        .group_by(SessionModel.mentorship_id).having(func.count() >= 3).subquery())) or 0
    sessions_by_status = dict(db.execute(select(SessionModel.status, func.count()).where(
        SessionModel.created_at >= start, SessionModel.created_at < end).group_by(SessionModel.status)).all())
    finished = sessions_by_status.get("completed", 0) + sessions_by_status.get("cancelled", 0)
    completion_rate = round(sessions_by_status.get("completed", 0) / finished, 3) if finished else 0.0
    fb_count = db.scalar(select(func.count()).select_from(Feedback).where(
        Feedback.created_at >= start, Feedback.created_at < end)) or 0
    fb_avg = db.scalar(select(func.avg(Feedback.rating)).where(
        Feedback.created_at >= start, Feedback.created_at < end))
    distribution = {str(k): int(c) for k, c in db.execute(select(Feedback.rating, func.count()).where(
        Feedback.created_at >= start, Feedback.created_at < end).group_by(Feedback.rating)).all()}
    return {
        "period": {"from": from_date, "to": to_date},
        "users": {"students": int(users_counts.get("student", 0)), "mentors": int(users_counts.get("mentor", 0)),
                  "admins": int(users_counts.get("admin", 0))},
        "mentors": {"approved": int(mentor_statuses.get("approved", 0)),
                    "pending_review": int(mentor_statuses.get("pending_review", 0)),
                    "rejected": int(mentor_statuses.get("rejected", 0)),
                    "suspended": int(mentor_statuses.get("suspended", 0)),
                    "draft": int(mentor_statuses.get("draft", 0)),
                    "capacity_total": int(capacity_total),
                    "utilisation": round(active_mentorships_now / capacity_total, 3) if capacity_total else 0.0},
        "requests": {"total": sum(requests_by_status.values()),
                     "pending": requests_by_status.get("pending", 0), "accepted": requests_by_status.get("accepted", 0),
                     "declined": requests_by_status.get("declined", 0), "cancelled": requests_by_status.get("cancelled", 0),
                     "expired": requests_by_status.get("expired", 0),
                     "acceptance_rate": acceptance_rate, "median_response_hours": median_response},
        "mentorships": {"active": mentorships_by_status.get("active", 0),
                        "completed": mentorships_by_status.get("completed", 0),
                        "ended": mentorships_by_status.get("ended", 0),
                        "with_three_or_more_sessions": int(with_three)},
        "sessions": {"scheduled": sessions_by_status.get("scheduled", 0),
                     "completed": sessions_by_status.get("completed", 0),
                     "cancelled": sessions_by_status.get("cancelled", 0), "completion_rate": completion_rate},
        "feedback": {"count": int(fb_count), "average_rating": round(float(fb_avg), 2) if fb_avg else None,
                     "rating_distribution": {str(r): distribution.get(str(r), 0) for r in (1, 2, 3, 4, 5)}},
    }


TREND_METRICS = ("requests", "acceptances", "sessions", "active_users", "new_mentors", "avg_rating")


def trends(db: Session, *, metric: str, interval: str, from_date: str, to_date: str) -> dict:
    if metric not in TREND_METRICS:
        raise DomainError("VALIDATION_ERROR", details=[{"field": "metric", "issue": "must be one of " + ", ".join(TREND_METRICS)}])
    if interval not in ("week", "month"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "interval", "issue": "must be week or month"}])
    start, end = _range(from_date, to_date)
    step = timedelta(days=7) if interval == "week" else None
    buckets = []
    if step is None:
        # calendar months
        y, m = start.year, start.month
        while datetime(y, m, 1, tzinfo=timezone.utc) < end:
            buckets.append(datetime(y, m, 1, tzinfo=timezone.utc))
            m += 1
            if m > 12:
                y, m = y + 1, 1
        def bucket_of(d):  # noqa: E306
            return datetime(d.year, d.month, 1, tzinfo=timezone.utc)
        def next_b(b):
            return datetime(b.year + (1 if b.month == 12 else 0), 1 if b.month == 12 else b.month + 1, 1, tzinfo=timezone.utc)
    else:
        first = start - timedelta(days=start.weekday())
        buckets.append(first)
        while buckets[-1] + step < end:
            buckets.append(buckets[-1] + step)
        def bucket_of(d):
            return d - timedelta(days=d.weekday(), hours=d.hour, minutes=d.minute, seconds=d.seconds, microseconds=d.microseconds)
        def next_b(b):
            return b + step

    series = []
    for b in buckets:
        b_end = min(next_b(b), end)
        if b_end <= b:
            continue
        value = _metric_value(db, metric, b, b_end)
        series.append({"period_start": b.date().isoformat(), "value": value})
    return {"metric": metric, "interval": interval, "series": series}


def _metric_value(db: Session, metric: str, b_start: datetime, b_end: datetime):
    if metric == "requests":
        return db.scalar(select(func.count()).select_from(MentoringRequest).where(
            MentoringRequest.created_at >= b_start, MentoringRequest.created_at < b_end)) or 0
    if metric == "acceptances":
        return db.scalar(select(func.count()).select_from(MentoringRequest).where(
            MentoringRequest.status == "accepted", MentoringRequest.responded_at >= b_start,
            MentoringRequest.responded_at < b_end)) or 0
    if metric == "sessions":
        return db.scalar(select(func.count()).select_from(SessionModel).where(
            SessionModel.created_at >= b_start, SessionModel.created_at < b_end)) or 0
    if metric == "active_users":
        students = set(db.scalars(select(MentoringRequest.student_id).where(
            MentoringRequest.created_at >= b_start, MentoringRequest.created_at < b_end)).all())
        students |= set(db.scalars(select(SessionModel.student_id).where(
            SessionModel.created_at >= b_start, SessionModel.created_at < b_end)).all())
        mentors = set(db.scalars(select(SessionModel.mentor_id).where(
            SessionModel.created_at >= b_start, SessionModel.created_at < b_end)).all())
        mentors |= set(db.scalars(select(MentoringRequest.mentor_id).where(
            MentoringRequest.created_at >= b_start, MentoringRequest.created_at < b_end)).all())
        return len(students | mentors)
    if metric == "new_mentors":
        return db.scalar(select(func.count()).select_from(MentorProfile).where(
            MentorProfile.created_at >= b_start, MentorProfile.created_at < b_end)) or 0
    avg = db.scalar(select(func.avg(Feedback.rating)).where(
        Feedback.created_at >= b_start, Feedback.created_at < b_end))
    return round(float(avg), 2) if avg is not None else None


# ------------------------------------------------------------------ E53
def export_csv(db: Session, *, report: str, from_date: str, to_date: str) -> tuple[str, str]:
    if report not in ("mentorships", "requests", "sessions", "participation"):
        raise DomainError("VALIDATION_ERROR", details=[{"field": "report", "issue": "must be mentorships, requests, sessions or participation"}])
    start, end = _range(from_date, to_date)
    buf = io.StringIO()
    writer = csv.writer(buf)
    if report == "mentorships":
        writer.writerow(["mentorship_id", "student_id", "mentor_id", "status", "started_at", "ended_at", "sessions_completed"])
        for m in db.scalars(select(Mentorship).where(Mentorship.created_at >= start, Mentorship.created_at < end)).all():
            done = db.scalar(select(func.count()).select_from(SessionModel).where(
                SessionModel.mentorship_id == m.mentorship_id, SessionModel.status == "completed")) or 0
            writer.writerow([m.mentorship_id, m.student_id, m.mentor_id, m.status,
                             m.started_at.date().isoformat(), m.ended_at.date().isoformat() if m.ended_at else "", int(done)])
    elif report == "requests":
        writer.writerow(["request_id", "student_id", "mentor_id", "status", "created_at", "responded_at"])
        for r in db.scalars(select(MentoringRequest).where(
                MentoringRequest.created_at >= start, MentoringRequest.created_at < end)).all():
            writer.writerow([r.request_id, r.student_id, r.mentor_id, r.status,
                             r.created_at.date().isoformat(), r.responded_at.date().isoformat() if r.responded_at else ""])
    elif report == "sessions":
        writer.writerow(["session_id", "mentorship_id", "scheduled_start", "duration_minutes", "status"])
        for s in db.scalars(select(SessionModel).where(
                SessionModel.created_at >= start, SessionModel.created_at < end)).all():
            writer.writerow([s.session_id, s.mentorship_id, s.scheduled_start.isoformat(),
                             int((s.scheduled_end - s.scheduled_start).total_seconds() // 60), s.status])
    else:  # participation: per-mentor aggregate (counts only)
        writer.writerow(["mentor_id", "active_mentees", "sessions_completed", "average_rating"])
        rows = db.execute(select(MentorProfile.user_id)).all()
        for (mid,) in rows:
            active = db.scalar(select(func.count()).select_from(Mentorship).where(
                Mentorship.mentor_id == mid, Mentorship.status == "active")) or 0
            done = db.scalar(select(func.count()).select_from(SessionModel).where(
                SessionModel.mentor_id == mid, SessionModel.status == "completed")) or 0
            avg = db.scalar(select(func.avg(Feedback.rating)).select_from(Feedback)
                            .join(SessionModel, SessionModel.session_id == Feedback.session_id)
                            .where(SessionModel.mentor_id == mid))
            writer.writerow([mid, int(active), int(done), round(float(avg), 2) if avg is not None else ""])
    return buf.getvalue(), report
