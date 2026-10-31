# Charts & Metrics Catalogue — IITM Mentoring Platform

**Companion to:** [`DATABASE-SPEC.md`](./DATABASE-SPEC.md) · [`DFD.md`](./DFD.md)
**Database:** PostgreSQL 16 · all queries run against `database/schema.sql` · timestamps are UTC

---

## 1. How to use this catalogue

Each chart has a stable ID (`C01`…`C20`), a question it answers, a chart type, and a **runnable SQL query**. The SQL is the specification: if a BI tool, a dashboard component or an AI generator needs to rebuild the chart, it needs nothing else.

All queries are read-only, use no extensions beyond `btree_gist` (already required by the schema), and are safe to run on the demo dataset.

### Output contract

Every chart endpoint/component should return the same envelope, regardless of chart type:

```json
{
  "chart_id": "C07",
  "title": "Request outcomes by week",
  "unit": "requests",
  "generated_at": "2026-10-31T09:00:00Z",
  "labels": ["2026-09-07", "2026-09-14", "2026-09-21"],
  "series": [
    { "name": "accepted", "data": [0, 1, 0] },
    { "name": "declined", "data": [0, 0, 1] }
  ],
  "meta": { "source": "mentoring_requests", "row_count": 3 }
}
```

Mapping rules: the first selected column is `labels` (cast to text); every remaining numeric column becomes a series named after its alias; `NULL` becomes `null` (rendered as a gap, never as zero).

### Global filters

| Filter | Default | Applies to |
| --- | --- | --- |
| `from` / `to` | last 90 days | all time-series charts |
| `role`, `status` | none | user/request charts |
| `mentor_id` | none | mentor dashboard variants |
| `student_id` | none | student dashboard variants |
| timezone | UTC (pass `AT TIME ZONE` for IST days) | daily/weekly buckets |

---

## 2. Metric dictionary (define once, reuse everywhere)

| Metric | Definition | Formula | Caveats |
| --- | --- | --- | --- |
| **Registered students** | Non-anonymised users with `role='student'` | `count(*) users WHERE role='student' AND anonymised_at IS NULL` | Includes deactivated accounts unless filtered |
| **Available mentors** | Approved mentors accepting mentees | `profile_status='approved' AND is_available` | Capacity may still be full |
| **Active mentorship** | `status='active'` | count of `mentorships` | One per pair; unique partial index guarantees it |
| **Pending request** | `status='pending'` | count | Excludes expired by definition |
| **Stale request** | Pending longer than 7 days | `status='pending' AND created_at < now()-interval '7 days'` | Reporting definition, not a DB state |
| **Response time** | Time from request creation to mentor decision | `responded_at - created_at` | Only for accepted/declined |
| **Response rate** | Decided requests ÷ all requests created in window | `(accepted+declined) / total` | Pending and cancelled depress the rate; publish the window |
| **Acceptance rate** | Accepted ÷ decided | `accepted / (accepted+declined)` | Excludes cancelled/expired by design |
| **Capacity utilisation** | Active mentees ÷ `max_active_mentees` | per mentor | Can be 100% while `is_available` is still true |
| **Session completion rate** | Completed ÷ (completed+cancelled) past sessions | per window | Excludes still-scheduled future sessions |
| **Attendance** | Sessions completed (proxy; no attendance flag exists) | count | Document the proxy |
| **Average rating** | Mean star rating | `avg(rating)` | Decide whether to include mentor-side feedback; this catalogue uses student-side for mentor leaderboards |
| **Read rate** | Read notifications ÷ sent | per window | Only meaningful once users open the app |
| **Mentor review latency** | Time from submission to decision | `reviewed_at - created_at` (or status change time) | `reviewed_at` exists; submission time is approximated by `created_at` |
| **Programme conversion** | Stage-to-stage ratios in the funnel | see C14 | Cohort the window consistently |

---

## 3. Chart catalogue

### C01 · Registrations over time

**Question:** Is the programme growing, and which side of the marketplace is lagging?
**Type:** line / area · **Grain:** week · **Dashboard:** admin > participation tab

```sql
SELECT date_trunc('week', created_at)::date AS week,
       count(*) FILTER (WHERE role = 'student') AS students,
       count(*) FILTER (WHERE role = 'mentor')  AS mentors
FROM users
WHERE anonymised_at IS NULL
  AND created_at >= now() - interval '12 weeks'
GROUP BY 1
ORDER BY 1;
```

**Notes.** Seed data creates all users in one batch, so the demo shows a single spike; that is expected.

---

### C02 · Role mix

**Question:** What is the student-to-mentor ratio right now?
**Type:** donut · **Grain:** snapshot

```sql
SELECT role,
       count(*) AS users
FROM users
WHERE anonymised_at IS NULL
GROUP BY role
ORDER BY users DESC;
```

**Notes.** Do not filter `account_status` here; C03 shows status separately. A 1:8 mentor ratio is the planning assumption.

---

### C03 · Account status by role

**Question:** How many accounts are suspended or deactivated, and on which side?
**Type:** stacked bar · **Grain:** snapshot

```sql
SELECT role,
       count(*) FILTER (WHERE account_status = 'active')      AS active,
       count(*) FILTER (WHERE account_status = 'suspended')   AS suspended,
       count(*) FILTER (WHERE account_status = 'deactivated') AS deactivated
FROM users
WHERE anonymised_at IS NULL
GROUP BY role
ORDER BY role;
```

---

### C04 · Mentor review pipeline

**Question:** How large is the approval queue, and how old is it?
**Type:** funnel + age column · **Grain:** snapshot

```sql
SELECT profile_status,
       count(*) AS profiles,
       round(avg(extract(epoch FROM (now() - created_at)) / 86400)::numeric, 1) AS avg_age_days
FROM mentor_profiles
GROUP BY profile_status
ORDER BY CASE profile_status
           WHEN 'draft' THEN 1
           WHEN 'pending_review' THEN 2
           WHEN 'approved' THEN 3
           WHEN 'rejected' THEN 4
           WHEN 'suspended' THEN 5
         END;
```

**Notes.** `ck_mentor_reviewed` guarantees approved/rejected/suspended rows have a reviewer, so this pipeline is auditable.

---

### C05 · Skill supply vs student demand

**Question:** Which skills have more students wanting them than mentors offering them?
**Type:** horizontal grouped bar · **Grain:** skill · **Dashboard:** admin > participation

```sql
WITH supply AS (
  SELECT me.skill_id, count(*) AS available_mentors
  FROM mentor_expertise me
  JOIN mentor_profiles mp ON mp.mentor_profile_id = me.mentor_profile_id
  WHERE mp.profile_status = 'approved' AND mp.is_available
  GROUP BY me.skill_id
), demand AS (
  SELECT ss.skill_id,
         count(*) AS students,
         count(*) FILTER (WHERE ss.is_focus) AS focus_students
  FROM student_skills ss
  GROUP BY ss.skill_id
)
SELECT s.skill_name,
       s.category,
       coalesce(sup.available_mentors, 0) AS available_mentors,
       coalesce(d.students, 0)            AS students,
       coalesce(d.focus_students, 0)      AS focus_students,
       coalesce(d.focus_students, 0) - coalesce(sup.available_mentors, 0) AS gap
FROM skills s
LEFT JOIN supply sup USING (skill_id)
LEFT JOIN demand d   USING (skill_id)
WHERE s.is_active
ORDER BY gap DESC, students DESC
LIMIT 15;
```

**Reading it.** Positive `gap` = under-supplied skill. Use `focus_students` for the demand bar, not all students, when prioritising mentor recruitment.

---

### C06 · Request status mix

**Question:** What share of requests is still unanswered or lost?
**Type:** bar + percentage labels · **Grain:** snapshot or window

```sql
SELECT status,
       count(*) AS requests,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM mentoring_requests
WHERE created_at >= now() - interval '90 days'
GROUP BY status
ORDER BY requests DESC;
```

---

### C07 · Request outcomes by week

**Question:** Are mentors responding faster or ignoring more requests over time?
**Type:** stacked bar · **Grain:** week · **Dashboard:** admin home

```sql
SELECT date_trunc('week', created_at)::date AS week,
       count(*) FILTER (WHERE status = 'accepted')  AS accepted,
       count(*) FILTER (WHERE status = 'declined')  AS declined,
       count(*) FILTER (WHERE status = 'cancelled') AS cancelled,
       count(*) FILTER (WHERE status = 'expired')   AS expired,
       count(*) FILTER (WHERE status = 'pending')   AS pending
FROM mentoring_requests
WHERE created_at >= now() - interval '12 weeks'
GROUP BY 1
ORDER BY 1;
```

**Caveat.** A request is counted in the week it was *created*, not the week it was decided. For decision-cohort charts, group by `date_trunc('week', responded_at)` and filter `responded_at IS NOT NULL`.

---

### C08 · Mentor response-time distribution

**Question:** How long do students wait for a decision?
**Type:** histogram (bucketed) · **Grain:** request

```sql
WITH decided AS (
  SELECT responded_at - created_at AS latency
  FROM mentoring_requests
  WHERE responded_at IS NOT NULL
)
SELECT CASE
         WHEN latency < interval '24 hours' THEN '0–24 h'
         WHEN latency < interval '3 days'   THEN '1–3 d'
         WHEN latency < interval '7 days'   THEN '3–7 d'
         ELSE '7 d+'
       END AS bucket,
       count(*) AS requests,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct
FROM decided
GROUP BY bucket
ORDER BY min(latency);
```

Median in one line:

```sql
SELECT round(percentile_cont(0.5) WITHIN GROUP (
         ORDER BY extract(epoch FROM (responded_at - created_at)) / 3600
       )::numeric, 1) AS median_hours
FROM mentoring_requests
WHERE responded_at IS NOT NULL;
```

---

### C09 · Response SLA by mentor

**Question:** Which mentors consistently answer within 48 hours?
**Type:** table with inline bars · **Grain:** mentor

```sql
SELECT u.full_name AS mentor,
       count(*) AS decided_requests,
       round(avg(extract(epoch FROM (r.responded_at - r.created_at)) / 3600)::numeric, 1) AS avg_hours,
       round(100.0 * count(*) FILTER (
         WHERE r.responded_at - r.created_at <= interval '48 hours'
       ) / count(*), 1) AS pct_within_48h
FROM mentoring_requests r
JOIN users u ON u.user_id = r.mentor_id
WHERE r.status IN ('accepted', 'declined')
  AND r.responded_at IS NOT NULL
GROUP BY u.user_id, u.full_name
ORDER BY pct_within_48h DESC, decided_requests DESC;
```

**Threshold.** With `HAVING count(*) >= 3` this becomes a fair league table; the demo set has too few requests, so it is omitted by default.

---

### C10 · Stale pending requests (work queue)

**Question:** Which students have been waiting more than a week?
**Type:** table · **Grain:** request · **Dashboard:** admin home

```sql
SELECT r.request_id,
       su.full_name AS student,
       mu.full_name AS mentor,
       r.created_at,
       now() - r.created_at AS age,
       r.expires_at
FROM mentoring_requests r
JOIN users su ON su.user_id = r.student_id
JOIN users mu ON mu.user_id = r.mentor_id
WHERE r.status = 'pending'
  AND r.created_at < now() - interval '7 days'
ORDER BY r.created_at;
```

**Notes.** The expiry job flips pending rows at `expires_at` (14 days by default), so a request can only appear here for about a week. If the job has run recently, the demo shows zero rows — that is correct, not a bug.

---

### C11 · Active mentorships over time

**Question:** Is the active caseload growing, flat or declining?
**Type:** area · **Grain:** week · **Dashboard:** admin > participation

```sql
WITH weeks AS (
  SELECT generate_series(
           date_trunc('week', now()) - interval '11 weeks',
           date_trunc('week', now()),
           interval '1 week') AS wk
)
SELECT w.wk::date AS week,
       (SELECT count(*)
          FROM mentorships m
         WHERE m.started_at < w.wk + interval '1 week'
           AND (m.ended_at IS NULL OR m.ended_at >= w.wk)) AS active_mentorships
FROM weeks w
ORDER BY 1;
```

**Notes.** This is a point-in-time count, not a flow. It includes mentorships that started before the window and are still active — the correct way to show a caseload.

---

### C12 · Sessions per week by status

**Question:** Is mentoring actually happening, or are relationships idle?
**Type:** stacked bar · **Grain:** week

```sql
SELECT date_trunc('week', scheduled_start)::date AS week,
       count(*) FILTER (WHERE status = 'scheduled') AS scheduled,
       count(*) FILTER (WHERE status = 'completed') AS completed,
       count(*) FILTER (WHERE status = 'cancelled') AS cancelled
FROM sessions
WHERE scheduled_start >= now() - interval '12 weeks'
GROUP BY 1
ORDER BY 1;
```

---

### C13 · Session completion rate

**Question:** What proportion of sessions that reached a decision actually happened?
**Type:** gauge / KPI · **Grain:** trailing 90 days

```sql
SELECT count(*) FILTER (WHERE status = 'completed') AS completed,
       count(*) FILTER (WHERE status = 'cancelled') AS cancelled,
       round(100.0 * count(*) FILTER (WHERE status = 'completed')
             / nullif(count(*) FILTER (WHERE status IN ('completed', 'cancelled')), 0), 1) AS completion_pct
FROM sessions
WHERE scheduled_end < now();
```

**Caveat.** Excludes future scheduled sessions by design. A high completion rate with very few sessions is not a healthy signal — always show C12 next to it.

---

### C14 · Programme funnel

**Question:** Where do students drop out between registration and a completed session?
**Type:** funnel · **Grain:** snapshot (or cohort window)

```sql
WITH stages(stage_no, stage, n) AS (
  SELECT 1, 'Registered students', count(*)
    FROM users WHERE role = 'student' AND anonymised_at IS NULL
  UNION ALL
  SELECT 2, 'Completed profile', count(*)
    FROM student_profiles WHERE profile_completed
  UNION ALL
  SELECT 3, 'Sent a request', count(DISTINCT student_id)
    FROM mentoring_requests
  UNION ALL
  SELECT 4, 'Request accepted', count(DISTINCT student_id)
    FROM mentoring_requests WHERE status = 'accepted'
  UNION ALL
  SELECT 5, 'Active mentorship', count(DISTINCT student_id)
    FROM mentorships WHERE status = 'active'
  UNION ALL
  SELECT 6, 'Attended a session', count(DISTINCT student_id)
    FROM sessions WHERE status = 'completed'
)
SELECT stage, n FROM stages ORDER BY stage_no;
```

**Notes.** Stages are cumulative sets of *students*, not request counts, so the funnel never widens. For cohort analysis, add `AND created_at >= :cohort_start` to stages 1–2 and join through the request's student.

---

### C15 · Feedback rating distribution

**Question:** Are students and mentors rating sessions similarly?
**Type:** grouped bar · **Grain:** rating

```sql
SELECT f.rating,
       count(*) FILTER (WHERE f.submitted_by = s.student_id) AS from_students,
       count(*) FILTER (WHERE f.submitted_by = s.mentor_id)  AS from_mentors
FROM feedback f
JOIN sessions s ON s.session_id = f.session_id
GROUP BY f.rating
ORDER BY f.rating;
```

**Notes.** `uq_feedback_once (session_id, submitted_by)` guarantees at most two rows per session, so the two series are comparable.

---

### C16 · Mentor leaderboard

**Question:** Who is delivering sessions and earning good ratings?
**Type:** table · **Grain:** mentor · **Dashboard:** admin > reviews tab

```sql
SELECT u.full_name AS mentor,
       mp.professional_title,
       coalesce(s.completed_sessions, 0) AS completed_sessions,
       s.avg_rating,
       coalesce(m.active_mentees, 0) AS active_mentees,
       mp.max_active_mentees
FROM mentor_profiles mp
JOIN users u ON u.user_id = mp.user_id
LEFT JOIN LATERAL (
  SELECT count(*) AS completed_sessions,
         round(avg(f.rating)::numeric, 2) AS avg_rating
  FROM sessions se
  LEFT JOIN feedback f
    ON f.session_id = se.session_id
   AND f.submitted_by = se.student_id      -- student-side ratings only
  WHERE se.mentor_id = mp.user_id
    AND se.status = 'completed'
) s ON TRUE
LEFT JOIN LATERAL (
  SELECT count(*) AS active_mentees
  FROM mentorships me
  WHERE me.mentor_id = mp.user_id AND me.status = 'active'
) m ON TRUE
WHERE mp.profile_status = 'approved'
ORDER BY s.avg_rating DESC NULLS LAST, s.completed_sessions DESC;
```

**Why laterals.** Joining sessions and mentorships directly multiplies rows and silently weights the average by the number of mentorships. The lateral subqueries keep each aggregate at its own grain.

---

### C17 · Capacity utilisation

**Question:** Which mentors are full, and who has room for a new mentee?
**Type:** bar with capacity line · **Grain:** mentor

```sql
SELECT u.full_name AS mentor,
       count(*) FILTER (WHERE m.status = 'active') AS active_mentees,
       mp.max_active_mentees,
       round(100.0 * count(*) FILTER (WHERE m.status = 'active')
             / mp.max_active_mentees, 0) AS utilisation_pct
FROM mentor_profiles mp
JOIN users u ON u.user_id = mp.user_id
LEFT JOIN mentorships m ON m.mentor_id = mp.user_id
WHERE mp.profile_status = 'approved'
GROUP BY u.user_id, u.full_name, mp.max_active_mentees
ORDER BY utilisation_pct DESC, active_mentees DESC;
```

**Notes.** 100% utilisation with `is_available=true` means the discovery UI must still show "at capacity"; the service checks the count before accepting.

---

### C18 · Notification engagement

**Question:** Are users reading what the platform sends?
**Type:** line + read-rate · **Grain:** day

```sql
SELECT date_trunc('day', created_at)::date AS day,
       count(*) AS sent,
       count(*) FILTER (WHERE is_read) AS read,
       round(100.0 * count(*) FILTER (WHERE is_read) / count(*), 1) AS read_pct
FROM notifications
WHERE created_at >= now() - interval '30 days'
GROUP BY 1
ORDER BY 1;
```

**Notes.** Notification types are enumerated (12 values), so the same query can be split by `notification_type` with one extra column.

---

### C19 · Admin work queue

**Question:** What needs an administrator's attention right now?
**Type:** table · **Grain:** item · **Dashboard:** admin home

```sql
SELECT 'Mentor review' AS item,
       u.full_name AS subject,
       'submitted ' || to_char(mp.created_at, 'DD Mon') AS detail,
       mp.created_at AS since
FROM mentor_profiles mp
JOIN users u ON u.user_id = mp.user_id
WHERE mp.profile_status = 'pending_review'

UNION ALL

SELECT 'Stale request' AS item,
       su.full_name || ' → ' || mu.full_name AS subject,
       'pending for ' || extract(day FROM now() - r.created_at)::int || ' days' AS detail,
       r.created_at AS since
FROM mentoring_requests r
JOIN users su ON su.user_id = r.student_id
JOIN users mu ON mu.user_id = r.mentor_id
WHERE r.status = 'pending'
  AND r.created_at < now() - interval '7 days'

ORDER BY since
LIMIT 20;
```

---

### C20 · Session heatmap (weekday × hour)

**Question:** When do sessions actually happen, and when should reminders go out?
**Type:** heatmap · **Grain:** weekday × hour · **Dashboard:** admin > sessions tab

```sql
SELECT extract(isodow FROM scheduled_start)::int AS weekday,  -- 1 = Monday
       extract(hour FROM scheduled_start)::int   AS hour,     -- UTC
       count(*) AS sessions
FROM sessions
WHERE status <> 'cancelled'
GROUP BY 1, 2
ORDER BY 1, 2;
```

**Notes.** Hours are UTC. For programme-local time use
`extract(hour FROM scheduled_start AT TIME ZONE 'Asia/Kolkata')` and label the axis IST.

---

## 4. KPI snapshot (admin header cards)

```sql
SELECT
  (SELECT count(*) FROM users
    WHERE role = 'student' AND account_status = 'active' AND anonymised_at IS NULL) AS active_students,
  (SELECT count(*) FROM mentor_profiles
    WHERE profile_status = 'approved' AND is_available)                            AS available_mentors,
  (SELECT count(*) FROM mentoring_requests WHERE status = 'pending')               AS pending_requests,
  (SELECT count(*) FROM mentorships WHERE status = 'active')                       AS active_mentorships,
  (SELECT count(*) FROM mentor_profiles WHERE profile_status = 'pending_review')   AS mentor_reviews,
  (SELECT round(avg(rating)::numeric, 2) FROM feedback
    WHERE created_at >= now() - interval '30 days')                                AS avg_rating_30d;
```

Each column maps to one tile; trend deltas compare the same query with `now() - interval '60 days'` and a 30-day window.

---

## 5. Dashboard composition

### Admin dashboard (P22)

| Slot | Content | Chart |
| --- | --- | --- |
| KPI row | students, available mentors, pending requests, active mentorships | §4 snapshot |
| Primary panel | needs attention | C19 |
| Tab: Participation | registrations + active mentorships | C01, C11 |
| Tab: Requests | outcomes by week + response distribution | C07, C08 |
| Tab: Sessions | volume by week + completion | C12, C13 |
| Tab: Reviews | rating split + leaderboard | C15, C16 |
| Export | CSV of the active tab | query result, `COPY ... CSV HEADER` |

### Mentor dashboard (P15)

Add `WHERE mentor_id = :mentor_id` (or join through `users`) to C10, C12, C16, C17. Show capacity and next session, not programme-wide charts.

### Student dashboard (P06)

No analytics beyond personal progress: request statuses (filtered C06), next session (C12 filtered), feedback pending (C15 filtered). Resist adding programme charts here; they are noise for the role.

---

## 6. Demo dataset — expected results

Two reference points: the **fresh seed** (deterministic, 27 Oct 2026) and the **live verification run** (31 Oct 2026, after manual testing). Values are for verification, not contractual.

| Chart | Expected output | Caveat |
| --- | --- | --- |
| C01 | one weekly bucket with 3 students + 6 mentors | all seed rows share a timestamp |
| C02 | admin 1 · mentor 6 · student 3 | |
| C03 | all 10 active | |
| C04 | approved 5 · pending_review 1 | Lakshmi pending |
| C05 | top skills Python, SQL, Data Science | counts small |
| C06 | accepted 2 · pending 1 (or expired 1) | expiry job may have run |
| C07 | single week, accepted 2, pending/expired 1 | |
| C08 | one decided pair at ~24 h; one outlier | |
| C09 | Divya 2 decided, ~24 h avg, 100% within 48 h | threshold omitted |
| C10 | Asha → Rohan, 12+ days old | becomes 0 after expiry |
| C11 | 2 active for every week since 19 days ago | |
| C12 | one completed session ~5 days before seed | |
| C13 | 100% (1 completed, 0 cancelled) | tiny sample |
| C14 | 3 → 3 → 3 → 2 → 2 → 1 | Vikram attended; Ravi has no session |
| C15 | rating 5 ×2 (1 student, 1 mentor) | |
| C16 | Divya 1 session, 5.00, 2 active mentees; others 0 | |
| C17 | Divya 100%; others 0% | |
| C18 | 0 rows | seed creates no notifications |
| C19 | Lakshmi review (+ stale request if not expired) | |
| C20 | one cell (weekday/hour of the completed session) | |

**Live verification (31 Oct 2026).** All 22 SELECT queries in this document were executed against the Neon `production` branch with zero failures. The live database has drifted from the fresh seed through manual testing: **11 users** (1 admin, 6 mentors, 4 students), 4 accepted + 1 pending request, 4 active mentorships, 1 completed + 1 cancelled session, 2 feedback rows, 7 notifications (2 `request_accepted`, 2 `request_received`, 1 each `session_cancelled`/`session_scheduled`/`mentor_reviewed`), 6 approved mentor profiles, 16 slots (15 available). Magnitudes in the table above scale accordingly; the cancelled session is why C13 reads 50% live instead of 100% on the fresh seed.

**Sanity check.** A fresh seed has exactly 10 users; the live dataset has 11. Check `SELECT role, count(*) FROM users GROUP BY role;` before comparing any number above.

---

## 7. Performance notes

| Chart | Main table | Index used | Note |
| --- | --- | --- | --- |
| C01, C02, C03 | `users` | `ix_users_role_status` | small table; seq scan is fine under 100k rows |
| C04 | `mentor_profiles` | `ix_mentor_discoverable` | partial predicate helps |
| C05 | `mentor_expertise`, `student_skills` | `ix_mentor_expertise_skill`, `ix_student_skills_skill` | aggregate per skill |
| C06, C07 | `mentoring_requests` | `ix_requests_*` | use `created_at` range |
| C08, C09 | `mentoring_requests` | `ix_requests_mentor` | filter `responded_at IS NOT NULL` |
| C10 | `mentoring_requests` | `ix_requests_expiry` (partial pending) | 7-day predicate is not indexed; fine at this scale |
| C11 | `mentorships` | `ix_mentorship_mentor`, `ix_mentorship_student` | point-in-time count is O(weeks × mentorships) |
| C12, C13, C20 | `sessions` | `ix_sessions_mentor_time` | range on `scheduled_start` |
| C14 | several | PK/unique indexes | six independent counts |
| C15 | `feedback` | PK + `uq_feedback_once` | small |
| C16, C17 | `mentor_profiles`, `mentorships` | `ix_mentorship_mentor` | laterals avoid row multiplication |
| C18 | `notifications` | `ix_notifications_user` | add `(created_at)` index if volume grows |
| C19 | mixed | as above | union of two small queries |

At demo scale (< 10k rows) every query is sub-50 ms. At 1M+ notifications, materialise C18 nightly:

```sql
CREATE MATERIALIZED VIEW mv_notification_daily AS
SELECT date_trunc('day', created_at)::date AS day,
       notification_type,
       count(*) AS sent,
       count(*) FILTER (WHERE is_read) AS read
FROM notifications
GROUP BY 1, 2;

CREATE UNIQUE INDEX ON mv_notification_daily (day, notification_type);
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_notification_daily;  -- nightly
```

---

## 8. Chart implementation checklist

- [ ] Query runs on a clean schema with seed data
- [ ] Output can be expressed in the §1 envelope
- [ ] Empty result renders an empty state, not a broken axis
- [ ] Units and timezone are labelled on the axis
- [ ] Percentages state their denominator
- [ ] Small samples are disclosed (n < 10) rather than hidden
- [ ] No chart queries the API; analytics read the database directly
- [ ] Every chart has a stable ID used in code, tests and the dashboard map

---

*Last verified against `database/schema.sql` on 2026-10-31. Queries target PostgreSQL 16.*
