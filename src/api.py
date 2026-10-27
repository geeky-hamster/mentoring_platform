"""Single source of truth for the REST API (base path /api/v1): endpoint table, error catalogue,
illustrative examples and the OpenAPI 3.0 generator. All identifiers in examples are illustrative."""
import json
import matching as M

BASE = "/api/v1"

ERRORS = {  # code: (http, meaning)
    "BAD_REQUEST": (400, "Malformed JSON or an invalid query parameter."),
    "INVALID_TOKEN": (400, "Signed e-mail or password-reset token is invalid or expired."),
    "UNAUTHENTICATED": (401, "Access token missing, expired or invalid."),
    "INVALID_CREDENTIALS": (401, "E-mail or password is wrong (message is deliberately generic)."),
    "REFRESH_INVALID": (401, "Refresh token unknown, expired or revoked."),
    "REFRESH_REUSED": (401, "A rotated refresh token was replayed; the whole token family is revoked."),
    "FORBIDDEN": (403, "Authenticated, but the role or ownership rules do not allow this action."),
    "ACCOUNT_SUSPENDED": (403, "Account is suspended or deactivated."),
    "NOT_FOUND": (404, "Resource does not exist or is not visible to the caller."),
    "EMAIL_ALREADY_REGISTERED": (409, "An account with this e-mail exists."),
    "DUPLICATE_ENTRY": (409, "A catalogue entry with this name exists."),
    "PROFILE_INCOMPLETE": (409, "The student profile must be completed before this action."),
    "DUPLICATE_PENDING_REQUEST": (409, "A pending request to this mentor already exists."),
    "REQUEST_COOLDOWN": (409, "Re-requesting a mentor who declined is blocked for 30 days (proposed); retry_after is returned."),
    "PENDING_LIMIT_REACHED": (409, "The student already has the maximum number of pending requests (proposed: 3)."),
    "MENTOR_NOT_AVAILABLE": (409, "Mentor is not approved, not accepting mentees or suspended."),
    "MENTOR_AT_CAPACITY": (409, "Mentor already has max_active_mentees active mentorships."),
    "ACTIVE_MENTORSHIP_EXISTS": (409, "An active mentorship between this pair already exists."),
    "INVALID_STATE_TRANSITION": (409, "The action is not allowed in the resource's current status."),
    "MENTORSHIP_NOT_ACTIVE": (409, "Sessions can only be scheduled in an active mentorship."),
    "SLOT_UNAVAILABLE": (409, "The slot is already booked, blocked or in the past."),
    "SLOT_OVERLAP": (409, "The slot overlaps another slot of the same mentor."),
    "SLOT_BOOKED": (409, "The slot is held by a scheduled session and cannot be changed or deleted."),
    "SESSION_CONFLICT": (409, "The mentor or the student already has a scheduled session in that time range."),
    "FEEDBACK_NOT_ALLOWED": (409, "Session is not completed or the 14-day feedback window has closed."),
    "FEEDBACK_ALREADY_SUBMITTED": (409, "This participant has already submitted feedback for the session."),
    "VALIDATION_ERROR": (422, "One or more fields failed validation; see error.details."),
    "RATE_LIMITED": (429, "Too many requests; see the Retry-After header."),
}

EPS = []


def E(eid, method, path, group, purpose, auth, roles, params, body, ok, errs, tables, note=""):
    EPS.append(dict(id=eid, method=method, path=path, group=group, purpose=purpose, auth=auth, roles=roles,
                    params=params, body=body, ok=ok, errs=errs, tables=tables, note=note))


# params: list of (name, type, description) query parameters. body: dict field -> DSL spec.
PAGING = [("page", "integer", "Page number, default 1."), ("page_size", "integer", "Items per page, default 10, max 50.")]

G = "Authentication and account"
E("E01", "POST", "/auth/register", G, "Create a student or mentor account. Admin accounts cannot self-register (created by a CLI seed command).",
  "public", ["public"], [], {"full_name": "string(1..120)!", "email": "email!", "password": "string(10..128)!", "role": "enum:student|mentor!"},
  ("201", "User", "Created user summary; an empty profile row is created in the same transaction."),
  ["409 EMAIL_ALREADY_REGISTERED", "422 VALIDATION_ERROR", "429 RATE_LIMITED"], ["users", "student_profiles / mentor_profiles", "audit_logs"])
E("E02", "POST", "/auth/login", G, "Authenticate and obtain a short-lived access token; sets the refresh token as an HttpOnly cookie.",
  "public", ["public"], [], {"email": "email!", "password": "string!"},
  ("200", "LoginResult", "access_token (15 min), token_type, expires_in, user."),
  ["401 INVALID_CREDENTIALS", "403 ACCOUNT_SUSPENDED", "429 RATE_LIMITED"], ["users", "refresh_tokens"])
E("E03", "POST", "/auth/refresh", G, "Exchange the refresh cookie for a new access token; the refresh token is rotated.",
  "refresh", ["any"], [], {},
  ("200", "LoginResult", "New access token and a rotated refresh cookie."),
  ["401 REFRESH_INVALID", "401 REFRESH_REUSED", "403 ACCOUNT_SUSPENDED"], ["refresh_tokens", "users"])
E("E04", "POST", "/auth/logout", G, "Revoke the current refresh-token family and clear the cookie.",
  "access", ["any"], [], {}, ("204", None, "No content."), ["401 UNAUTHENTICATED"], ["refresh_tokens"])
E("E05", "POST", "/auth/forgot-password", G, "Request a password-reset link. Always answers 202 to avoid revealing which e-mails exist. Needs the optional e-mail extension; in development the link is logged.",
  "public", ["public"], [], {"email": "email!"}, ("202", None, "Accepted (no content)."), ["422 VALIDATION_ERROR", "429 RATE_LIMITED"], ["users"])
E("E06", "POST", "/auth/reset-password", G, "Set a new password using the signed, time-limited token; revokes all refresh tokens of the user.",
  "signed_token", ["public"], [], {"token": "string!", "new_password": "string(10..128)!"},
  ("204", None, "No content."), ["400 INVALID_TOKEN", "422 VALIDATION_ERROR"], ["users", "refresh_tokens", "audit_logs"])
E("E07", "POST", "/auth/verify-email", G, "Confirm an e-mail address with a signed token (optional extension).",
  "signed_token", ["public"], [], {"token": "string!"}, ("204", None, "No content."), ["400 INVALID_TOKEN"], ["users"])
E("E08", "GET", "/users/me", G, "Return the authenticated user's identity, role and onboarding or review state.",
  "access", ["any"], [], {}, ("200", "User", "Current user with profile_completed and (for mentors) profile_status."),
  ["401 UNAUTHENTICATED"], ["users", "student_profiles", "mentor_profiles"])
E("E09", "POST", "/users/me/password", G, "Change the password; other refresh tokens are revoked.",
  "access", ["any"], [], {"current_password": "string!", "new_password": "string(10..128)!"},
  ("204", None, "No content."), ["401 UNAUTHENTICATED", "422 VALIDATION_ERROR"], ["users", "refresh_tokens", "audit_logs"])

G = "Catalogues"
E("E10", "GET", "/skills", G, "List active skills for profile forms and filters.", "access", ["any"],
  [("q", "string", "Name contains (case-insensitive)."), ("category", "string", "Exact category.")] + PAGING, {},
  ("200", "page:Skill", "Paginated skills."), ["401 UNAUTHENTICATED"], ["skills"])
E("E11", "GET", "/career-interests", G, "List active career pathways for profile forms and filters.", "access", ["any"],
  PAGING, {}, ("200", "page:CareerInterest", "Paginated career interests."), ["401 UNAUTHENTICATED"], ["career_interests"])

G = "Profiles"
E("E12", "GET", "/students/me/profile", G, "Read the caller's student profile including skills and interests.", "access", ["student"],
  [], {}, ("200", "StudentProfile", "Profile."), ["401 UNAUTHENTICATED", "403 FORBIDDEN"],
  ["users", "student_profiles", "student_skills", "student_interests", "skills", "career_interests"])
E("E13", "PATCH", "/students/me/profile", G, "Update profile fields; skill and interest lists are replaced as a whole. profile_completed is recomputed server-side.",
  "access", ["student"], [], {"full_name": "string(1..120)", "programme_stage": "enum:foundation|diploma|bsc_degree|bs_degree",
                              "expected_graduation_year": "integer", "career_goals": "string(0..2000)", "guidance_needs": "string(0..2000)",
                              "bio": "string(0..1000)", "skills": "array:object", "interest_ids": "array:uuid"},
  ("200", "StudentProfile", "Updated profile."), ["403 FORBIDDEN", "422 VALIDATION_ERROR"],
  ["users", "student_profiles", "student_skills", "student_interests"], "skills items: {skill_id, proficiency_level, is_focus}; at most 5 focus skills.")
E("E14", "GET", "/mentors/me/profile", G, "Read the caller's mentor profile including review status.", "access", ["mentor"], [], {},
  ("200", "MentorProfile", "Profile."), ["401 UNAUTHENTICATED", "403 FORBIDDEN"],
  ["users", "mentor_profiles", "mentor_expertise", "mentor_interests", "skills", "career_interests"])
E("E15", "PATCH", "/mentors/me/profile", G, "Update the mentor profile; submit_for_review moves draft/rejected to pending_review. Edits to title, organisation or LinkedIn on an approved profile are audit-logged and flagged to admins.",
  "access", ["mentor"], [], {"full_name": "string(1..120)", "mentor_type": "enum:recent_graduate|alumni", "professional_title": "string(1..120)",
                             "organisation": "string(1..150)", "experience_years": "integer", "graduation_year": "integer", "linkedin_url": "string(0..255)",
                             "bio": "string(0..1500)", "is_available": "boolean", "max_active_mentees": "integer", "expertise": "array:object",
                             "interest_ids": "array:uuid", "submit_for_review": "boolean"},
  ("200", "MentorProfile", "Updated profile."), ["403 FORBIDDEN", "409 INVALID_STATE_TRANSITION", "422 VALIDATION_ERROR"],
  ["users", "mentor_profiles", "mentor_expertise", "mentor_interests", "audit_logs"],
  "expertise items: {skill_id, expertise_level}; max_active_mentees cannot be lowered below the current active count.")
E("E16", "GET", "/mentors/:mentor_id", G, "View a mentor's profile. Students see approved mentors only; admins see any status. mentor_id is the mentor's users.user_id.",
  "access", ["student", "admin"], [], {}, ("200", "MentorProfile", "Public mentor profile with aggregate rating (shown when at least 3 ratings exist) and capacity indicator."),
  ["403 FORBIDDEN", "404 NOT_FOUND"], ["users", "mentor_profiles", "mentor_expertise", "mentor_interests", "feedback", "mentorships"])

G = "Availability"
E("E17", "GET", "/mentors/me/availability", G, "List the mentor's own slots.", "access", ["mentor"],
  [("from", "datetime", "Window start."), ("to", "datetime", "Window end."), ("is_available", "boolean", "Filter by open/blocked.")], {},
  ("200", "page:Slot", "Slots in the window."), ["403 FORBIDDEN"], ["availability_slots", "sessions"])
E("E18", "POST", "/mentors/me/availability", G, "Create individual slots, or expand a weekly recurrence helper into concrete slots (max 100 slots and 12 weeks per call).",
  "access", ["mentor"], [], {"slots": "array:object", "recurrence": "object"},
  ("201", "page:Slot", "Created slots."), ["403 FORBIDDEN", "409 SLOT_OVERLAP", "422 VALIDATION_ERROR"], ["availability_slots"],
  "slots item: {start_time, end_time}. recurrence: {weekdays[], start_time, end_time, weeks}.")
E("E19", "PATCH", "/mentors/me/availability/:slot_id", G, "Change the time or open/blocked state of an unbooked slot.", "access", ["mentor"], [],
  {"start_time": "datetime", "end_time": "datetime", "is_available": "boolean"}, ("200", "Slot", "Updated slot."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 SLOT_BOOKED", "409 SLOT_OVERLAP", "422 VALIDATION_ERROR"], ["availability_slots", "sessions"])
E("E20", "DELETE", "/mentors/me/availability/:slot_id", G, "Delete an unbooked slot.", "access", ["mentor"], [], {}, ("204", None, "No content."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 SLOT_BOOKED"], ["availability_slots", "sessions"])
E("E21", "GET", "/mentors/:mentor_id/availability", G, "Open future slots of a mentor. Allowed for the mentor, admins and students with an active mentorship with that mentor (exact times are not public).",
  "access", ["student", "mentor", "admin"], [("from", "datetime", "Window start."), ("to", "datetime", "Window end.")], {},
  ("200", "page:Slot", "Open slots."), ["403 FORBIDDEN", "404 NOT_FOUND"], ["availability_slots", "mentorships"])

G = "Discovery and matching"
E("E22", "GET", "/mentors", G, "Search and filter approved mentors. Unavailable mentors are hidden unless accepting=false is requested.", "access", ["student", "admin"],
  [("q", "string", "Keyword over title, organisation and bio."), ("skill_id", "uuid[]", "Repeatable; mentor has any of the skills."),
   ("interest_id", "uuid[]", "Repeatable; mentor advises on any of the pathways."), ("mentor_type", "string", "recent_graduate | alumni."),
   ("min_experience", "integer", "Minimum years of experience."), ("accepting", "boolean", "Default true."),
   ("sort", "string", "newest | experience | name; default newest.")] + PAGING, {},
  ("200", "page:MentorCard", "Paginated mentor cards."), ["400 BAD_REQUEST", "403 FORBIDDEN"],
  ["users", "mentor_profiles", "mentor_expertise", "mentor_interests", "mentorships"])
E("E23", "GET", "/mentors/recommended", G, "Ranked mentors for the calling student using the rule-based score (Section 10). Includes the score breakdown and human-readable reasons.",
  "access", ["student"], PAGING, {}, ("200", "page:MentorMatch", "Paginated matches, highest score first."),
  ["403 FORBIDDEN", "409 PROFILE_INCOMPLETE"],
  ["mentor_profiles", "mentor_expertise", "mentor_interests", "availability_slots", "mentorships", "mentoring_requests", "student_skills", "student_interests"])

G = "Mentoring requests"
E("E24", "POST", "/mentoring-requests", G, "Submit a request to a mentor. The student is taken from the access token, never from the body.", "access", ["student"], [],
  {"mentor_id": "uuid!", "career_goal": "string(20..1000)!", "message": "string(0..1500)"},
  ("201", "MentoringRequest", "Created request with status pending."),
  ["404 NOT_FOUND", "409 PROFILE_INCOMPLETE", "409 DUPLICATE_PENDING_REQUEST", "409 REQUEST_COOLDOWN", "409 PENDING_LIMIT_REACHED",
   "409 MENTOR_NOT_AVAILABLE", "409 MENTOR_AT_CAPACITY", "409 ACTIVE_MENTORSHIP_EXISTS", "422 VALIDATION_ERROR", "429 RATE_LIMITED"],
  ["mentoring_requests", "mentor_profiles", "mentorships", "notifications", "audit_logs"])
E("E25", "GET", "/mentoring-requests/mine", G, "Role-aware list: requests the caller sent (student) or received (mentor).", "access", ["student", "mentor"],
  [("status", "string", "pending | accepted | declined | cancelled | expired.")] + PAGING, {},
  ("200", "page:MentoringRequest", "Paginated requests, newest first."), ["403 FORBIDDEN"],
  ["mentoring_requests", "users", "student_profiles", "mentor_profiles"])
E("E26", "GET", "/mentoring-requests/:request_id", G, "Request detail. Mentors also receive a summary of the student's profile (goals, skills, interests).", "access",
  ["student", "mentor", "admin"], [], {}, ("200", "MentoringRequest", "Request detail."), ["403 FORBIDDEN", "404 NOT_FOUND"],
  ["mentoring_requests", "student_profiles", "student_skills", "student_interests", "users"])
E("E27", "POST", "/mentoring-requests/:request_id/accept", G, "Accept a pending request: one transaction that locks the request and mentor rows, checks capacity, creates the mentorship and notifies the student.",
  "access", ["mentor"], [], {}, ("200", "AcceptResult", "Updated request and the new mentorship."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION", "409 MENTOR_AT_CAPACITY", "409 ACTIVE_MENTORSHIP_EXISTS"],
  ["mentoring_requests", "mentorships", "mentor_profiles", "notifications", "audit_logs"])
E("E28", "POST", "/mentoring-requests/:request_id/decline", G, "Decline a pending request with an optional reason.", "access", ["mentor"], [],
  {"reason": "string(0..500)"}, ("200", "MentoringRequest", "Request with status declined."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION"], ["mentoring_requests", "notifications", "audit_logs"])
E("E29", "POST", "/mentoring-requests/:request_id/cancel", G, "Cancel the caller's own pending request.", "access", ["student"], [],
  {"reason": "string(0..500)"}, ("200", "MentoringRequest", "Request with status cancelled."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION"], ["mentoring_requests", "notifications", "audit_logs"])

G = "Mentorships, sessions and feedback"
E("E30", "GET", "/mentorships", G, "Role-aware list of the caller's mentorships.", "access", ["student", "mentor"],
  [("status", "string", "active | completed | ended.")] + PAGING, {}, ("200", "page:Mentorship", "Paginated mentorships."), ["403 FORBIDDEN"],
  ["mentorships", "users", "student_profiles", "mentor_profiles", "sessions"])
E("E31", "GET", "/mentorships/:mentorship_id", G, "Mentorship detail with the counterpart summary, originating request and session statistics.", "access",
  ["student", "mentor", "admin"], [], {}, ("200", "Mentorship", "Mentorship detail."), ["403 FORBIDDEN", "404 NOT_FOUND"],
  ["mentorships", "mentoring_requests", "sessions", "users"])
E("E32", "PATCH", "/mentorships/:mentorship_id", G, "Close an active mentorship as completed (natural end) or ended (early termination). Future scheduled sessions are cancelled and the other party is notified.",
  "access", ["student", "mentor", "admin"], [], {"status": "enum:completed|ended!", "reason": "string(0..500)"},
  ("200", "Mentorship", "Closed mentorship."), ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION", "422 VALIDATION_ERROR"],
  ["mentorships", "sessions", "availability_slots", "notifications", "audit_logs"])
E("E33", "GET", "/mentorships/:mentorship_id/sessions", G, "Session history of a mentorship with feedback flags.", "access", ["student", "mentor", "admin"],
  [("status", "string", "scheduled | completed | cancelled.")] + PAGING, {}, ("200", "page:Session", "Paginated sessions, newest first."),
  ["403 FORBIDDEN", "404 NOT_FOUND"], ["sessions", "feedback", "mentorships"])
E("E34", "POST", "/mentorships/:mentorship_id/sessions", G, "Schedule a session. Students must book an open slot (slot_id); mentors may book a slot or give explicit times.",
  "access", ["student", "mentor"], [], {"slot_id": "uuid", "scheduled_start": "datetime", "scheduled_end": "datetime",
                                         "meeting_mode": "enum:online|phone|in_person", "meeting_link": "string(0..2000)", "notes": "string(0..4000)"},
  ("201", "Session", "Created session with status scheduled."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 MENTORSHIP_NOT_ACTIVE", "409 SLOT_UNAVAILABLE", "409 SESSION_CONFLICT", "422 VALIDATION_ERROR"],
  ["sessions", "availability_slots", "mentorships", "notifications"])
E("E35", "GET", "/sessions", G, "Role-aware calendar list of the caller's sessions across mentorships.", "access", ["student", "mentor"],
  [("from", "datetime", "Window start."), ("to", "datetime", "Window end."), ("status", "string", "scheduled | completed | cancelled.")] + PAGING, {},
  ("200", "page:Session", "Paginated sessions."), ["403 FORBIDDEN"], ["sessions", "mentorships", "users"])
E("E36", "GET", "/sessions/:session_id", G, "Session detail including whether the caller has submitted feedback.", "access", ["student", "mentor", "admin"], [], {},
  ("200", "Session", "Session detail."), ["403 FORBIDDEN", "404 NOT_FOUND"], ["sessions", "feedback"])
E("E37", "PATCH", "/sessions/:session_id", G, "Cancel (either participant), complete (mentor, after the start time), or edit notes/link/mode.", "access", ["student", "mentor"], [],
  {"status": "enum:cancelled|completed", "cancel_reason": "string(0..500)", "notes": "string(0..4000)", "meeting_mode": "enum:online|phone|in_person",
   "meeting_link": "string(0..2000)"}, ("200", "Session", "Updated session."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION", "422 VALIDATION_ERROR"], ["sessions", "availability_slots", "notifications"])
E("E38", "POST", "/sessions/:session_id/feedback", G, "Submit one rating and optional comment for a completed session (within 14 days).", "access", ["student", "mentor"], [],
  {"rating": "integer!", "comments": "string(0..1000)"}, ("201", "Feedback", "Created feedback."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 FEEDBACK_NOT_ALLOWED", "409 FEEDBACK_ALREADY_SUBMITTED", "422 VALIDATION_ERROR"], ["feedback", "sessions", "notifications"])
E("E39", "GET", "/sessions/:session_id/feedback", G, "Feedback visible to the caller: own entry; the mentor also sees the student's entry; admins see all.", "access",
  ["student", "mentor", "admin"], [], {}, ("200", "page:Feedback", "Visible feedback entries."), ["403 FORBIDDEN", "404 NOT_FOUND"], ["feedback"])

G = "Dashboards and notifications"
E("E40", "GET", "/students/me/dashboard", G, "Aggregated data for the student dashboard (profile completeness, requests, active mentorships, next session, unread count).",
  "access", ["student"], [], {}, ("200", "StudentDashboard", "Dashboard summary."), ["403 FORBIDDEN"],
  ["student_profiles", "mentoring_requests", "mentorships", "sessions", "notifications"])
E("E41", "GET", "/mentors/me/dashboard", G, "Aggregated data for the mentor dashboard (review status, pending requests, capacity, upcoming sessions, rating summary).",
  "access", ["mentor"], [], {}, ("200", "MentorDashboard", "Dashboard summary."), ["403 FORBIDDEN"],
  ["mentor_profiles", "mentoring_requests", "mentorships", "sessions", "feedback", "notifications"])
E("E42", "GET", "/notifications", G, "List the caller's notifications, newest first.", "access", ["any"],
  [("is_read", "boolean", "Filter by read state.")] + PAGING, {}, ("200", "page:Notification", "Paginated notifications; meta.unread_count included."),
  ["401 UNAUTHENTICATED"], ["notifications"])
E("E43", "PATCH", "/notifications/:notification_id", G, "Mark one notification as read.", "access", ["any"], [], {"is_read": "boolean!"},
  ("200", "Notification", "Updated notification."), ["403 FORBIDDEN", "404 NOT_FOUND"], ["notifications"])
E("E44", "POST", "/notifications/mark-all-read", G, "Mark all the caller's notifications as read.", "access", ["any"], [], {}, ("204", None, "No content."),
  ["401 UNAUTHENTICATED"], ["notifications"])

G = "Administration"
E("E45", "GET", "/admin/users", G, "Search and filter all users.", "access", ["admin"],
  [("role", "string", "student | mentor | admin."), ("account_status", "string", "active | suspended | deactivated."), ("q", "string", "Name or e-mail contains.")] + PAGING, {},
  ("200", "page:AdminUser", "Paginated users."), ["403 FORBIDDEN"], ["users", "mentor_profiles", "student_profiles"])
E("E46", "PATCH", "/admin/users/:user_id/status", G, "Suspend, reactivate or deactivate an account. Suspension revokes the user's refresh tokens; for a mentor it also cancels pending requests.",
  "access", ["admin"], [], {"account_status": "enum:active|suspended|deactivated!", "reason": "string(0..500)"},
  ("200", "AdminUser", "Updated user."), ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION"],
  ["users", "refresh_tokens", "mentoring_requests", "notifications", "audit_logs"], "An admin cannot change their own status.")
E("E47", "GET", "/admin/mentors", G, "Review queue and mentor directory for admins (default filter: pending_review).", "access", ["admin"],
  [("profile_status", "string", "draft | pending_review | approved | rejected | suspended."), ("q", "string", "Name, organisation or title contains.")] + PAGING, {},
  ("200", "page:MentorProfile", "Paginated mentor profiles with review fields."), ["403 FORBIDDEN"], ["mentor_profiles", "users", "mentor_expertise"])
E("E48", "PATCH", "/admin/mentors/:mentor_id/approval", G, "Approve, reject or suspend a mentor profile. Rejection requires a note. Approving a suspended mentor reinstates them.",
  "access", ["admin"], [], {"decision": "enum:approve|reject|suspend!", "note": "string(0..1000)"},
  ("200", "MentorProfile", "Updated profile with reviewed_by and reviewed_at."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 INVALID_STATE_TRANSITION", "422 VALIDATION_ERROR"],
  ["mentor_profiles", "mentoring_requests", "notifications", "audit_logs"])
E("E49", "GET", "/admin/mentorships", G, "Oversee all mentoring relationships.", "access", ["admin"],
  [("status", "string", "active | completed | ended."), ("mentor_id", "uuid", "Filter by mentor."), ("student_id", "uuid", "Filter by student.")] + PAGING, {},
  ("200", "page:Mentorship", "Paginated mentorships with session counts and last activity."), ["403 FORBIDDEN"], ["mentorships", "sessions", "users"])
E("E50", "GET", "/admin/mentoring-requests", G, "Oversee requests, e.g. long-pending ones.", "access", ["admin"],
  [("status", "string", "Request status."), ("older_than_days", "integer", "Only requests older than N days.")] + PAGING, {},
  ("200", "page:MentoringRequest", "Paginated requests."), ["403 FORBIDDEN"], ["mentoring_requests", "users"])
E("E51", "GET", "/admin/analytics/overview", G, "Programme KPIs for a date range (counts only; small groups are suppressed).", "access", ["admin"],
  [("from", "date", "Start date."), ("to", "date", "End date.")], {}, ("200", "AnalyticsOverview", "KPI summary."), ["403 FORBIDDEN", "422 VALIDATION_ERROR"],
  ["users", "mentor_profiles", "mentoring_requests", "mentorships", "sessions", "feedback"])
E("E52", "GET", "/admin/analytics/trends", G, "Time series for one metric.", "access", ["admin"],
  [("metric", "string", "requests | acceptances | sessions | active_users | new_mentors | avg_rating."), ("interval", "string", "week | month."),
   ("from", "date", "Start date."), ("to", "date", "End date.")], {}, ("200", "AnalyticsTrend", "Series of {period_start, value}."),
  ["403 FORBIDDEN", "422 VALIDATION_ERROR"], ["mentoring_requests", "mentorships", "sessions", "feedback", "users"])
E("E53", "GET", "/admin/analytics/export", G, "Download a CSV report (no free-text fields).", "access", ["admin"],
  [("report", "string", "mentorships | requests | sessions | participation."), ("from", "date", "Start date."), ("to", "date", "End date.")], {},
  ("200", "csv", "text/csv attachment."), ["403 FORBIDDEN", "422 VALIDATION_ERROR"], ["mentorships", "mentoring_requests", "sessions", "users"])
E("E54", "GET", "/admin/audit-logs", G, "Search the audit trail.", "access", ["admin"],
  [("entity_type", "string", "Entity type."), ("entity_id", "uuid", "Entity id."), ("actor_user_id", "uuid", "Actor."), ("action", "string", "Action prefix."),
   ("from", "datetime", "Start."), ("to", "datetime", "End.")] + PAGING, {}, ("200", "page:AuditLog", "Paginated audit entries."), ["403 FORBIDDEN"], ["audit_logs", "users"])
E("E55", "POST", "/admin/skills", G, "Add a skill to the catalogue.", "access", ["admin"], [], {"skill_name": "string(1..100)!", "category": "string(0..80)"},
  ("201", "Skill", "Created skill."), ["403 FORBIDDEN", "409 DUPLICATE_ENTRY", "422 VALIDATION_ERROR"], ["skills", "audit_logs"])
E("E56", "PATCH", "/admin/skills/:skill_id", G, "Rename, recategorise or retire a skill.", "access", ["admin"], [],
  {"skill_name": "string(1..100)", "category": "string(0..80)", "is_active": "boolean"}, ("200", "Skill", "Updated skill."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 DUPLICATE_ENTRY"], ["skills", "audit_logs"])
E("E57", "POST", "/admin/career-interests", G, "Add a career pathway to the catalogue.", "access", ["admin"], [],
  {"interest_name": "string(1..100)!", "description": "string(0..500)"}, ("201", "CareerInterest", "Created interest."),
  ["403 FORBIDDEN", "409 DUPLICATE_ENTRY", "422 VALIDATION_ERROR"], ["career_interests", "audit_logs"])
E("E58", "PATCH", "/admin/career-interests/:interest_id", G, "Rename, describe or retire a career pathway.", "access", ["admin"], [],
  {"interest_name": "string(1..100)", "description": "string(0..500)", "is_active": "boolean"}, ("200", "CareerInterest", "Updated interest."),
  ["403 FORBIDDEN", "404 NOT_FOUND", "409 DUPLICATE_ENTRY"], ["career_interests", "audit_logs"])

EP = {e["id"]: e for e in EPS}

# Components (schemas) for OpenAPI, same compact DSL.
COMP = {
    "Error": {"error": "object!"},
    "Meta": {"page": "integer", "page_size": "integer", "total": "integer", "total_pages": "integer"},
    "User": {"user_id": "uuid", "full_name": "string", "email": "email", "role": "enum:student|mentor|admin", "account_status": "enum:active|suspended|deactivated",
             "email_verified": "boolean", "profile_completed": "boolean", "profile_status": "string", "created_at": "datetime"},
    "LoginResult": {"access_token": "string", "token_type": "string", "expires_in": "integer", "user": "ref:User"},
    "Skill": {"skill_id": "uuid", "skill_name": "string", "category": "string", "is_active": "boolean"},
    "CareerInterest": {"interest_id": "uuid", "interest_name": "string", "description": "string", "is_active": "boolean"},
    "StudentProfile": {"student_profile_id": "uuid", "user_id": "uuid", "full_name": "string", "programme_stage": "string", "expected_graduation_year": "integer",
                       "career_goals": "string", "guidance_needs": "string", "bio": "string", "profile_completed": "boolean", "skills": "array:object", "interests": "array:object"},
    "MentorProfile": {"mentor_id": "uuid", "full_name": "string", "mentor_type": "string", "professional_title": "string", "organisation": "string",
                      "experience_years": "integer", "graduation_year": "integer", "bio": "string", "is_available": "boolean", "max_active_mentees": "integer",
                      "profile_status": "string", "expertise": "array:object", "interests": "array:object", "rating": "object"},
    "MentorCard": {"mentor_id": "uuid", "full_name": "string", "professional_title": "string", "organisation": "string", "experience_years": "integer",
                   "mentor_type": "string", "top_skills": "array:string", "interests": "array:string", "accepting_mentees": "boolean"},
    "MentorMatch": {"mentor": "ref:MentorCard", "match_score": "number", "breakdown": "object", "reasons": "array:string"},
    "Slot": {"slot_id": "uuid", "start_time": "datetime", "end_time": "datetime", "is_available": "boolean"},
    "MentoringRequest": {"request_id": "uuid", "student_id": "uuid", "mentor_id": "uuid", "career_goal": "string", "message": "string",
                         "status": "enum:pending|accepted|declined|cancelled|expired", "status_reason": "string", "created_at": "datetime",
                         "responded_at": "datetime", "expires_at": "datetime"},
    "Mentorship": {"mentorship_id": "uuid", "request_id": "uuid", "student_id": "uuid", "mentor_id": "uuid", "status": "enum:active|completed|ended",
                   "started_at": "datetime", "ended_at": "datetime", "end_reason": "string"},
    "AcceptResult": {"request": "ref:MentoringRequest", "mentorship": "ref:Mentorship"},
    "Session": {"session_id": "uuid", "mentorship_id": "uuid", "slot_id": "uuid", "scheduled_start": "datetime", "scheduled_end": "datetime",
                "meeting_mode": "enum:online|phone|in_person", "meeting_link": "string", "status": "enum:scheduled|completed|cancelled", "notes": "string",
                "my_feedback_submitted": "boolean"},
    "Feedback": {"feedback_id": "uuid", "session_id": "uuid", "submitted_by": "uuid", "rating": "integer", "comments": "string", "created_at": "datetime"},
    "Notification": {"notification_id": "uuid", "title": "string", "message": "string", "notification_type": "string", "related_entity_type": "string",
                     "related_entity_id": "uuid", "is_read": "boolean", "created_at": "datetime"},
    "StudentDashboard": {"profile_completed": "boolean", "pending_requests": "integer", "active_mentorships": "integer", "next_session": "ref:Session", "unread_notifications": "integer"},
    "MentorDashboard": {"profile_status": "string", "pending_requests": "integer", "active_mentees": "integer", "max_active_mentees": "integer",
                        "upcoming_sessions": "array:object", "rating_summary": "object", "unread_notifications": "integer"},
    "AdminUser": {"user_id": "uuid", "full_name": "string", "email": "email", "role": "string", "account_status": "string", "last_login_at": "datetime", "created_at": "datetime"},
    "AuditLog": {"audit_id": "uuid", "actor_user_id": "uuid", "action": "string", "entity_type": "string", "entity_id": "uuid", "details": "object", "created_at": "datetime"},
    "AnalyticsOverview": {"period": "object", "users": "object", "mentors": "object", "requests": "object", "mentorships": "object", "sessions": "object", "feedback": "object"},
    "AnalyticsTrend": {"metric": "string", "interval": "string", "series": "array:object"},
}

# --------------------------------------------------------------------------------------------
# Illustrative identifiers and examples
# --------------------------------------------------------------------------------------------
STUDENT_ID = "3f2b8a1e-6c47-4d0a-9b53-1e8d2a7c4f10"
MENTOR_ID = "9d4c7e52-1a3b-4f68-8c2d-5b7e0a9f3c21"       # same as matching.MENTORS[0]
ADMIN_ID = "c1a5e9d3-7b24-4e86-a0f1-2d6b8c4e7a39"
REQUEST_ID = "7e1d3b9a-4c58-4a27-b6e0-9f2a5c8d1b43"
MENTORSHIP_ID = "5a9c2e7f-8d13-4b60-a4e7-3c1f6b0d9a82"
SLOT_ID = "b3e6f1a4-2d97-4c05-8a1b-7e4d9c2f6a50"
SESSION_ID = "e8d2a6c1-5f39-4b74-9c0e-1a7b3d5f8e26"
FEEDBACK_ID = "2c7f4b9e-3a81-4d56-b0c2-6e9a1d8f4b37"
ALL_IDS = [STUDENT_ID, MENTOR_ID, ADMIN_ID, REQUEST_ID, MENTORSHIP_ID, SLOT_ID, SESSION_ID, FEEDBACK_ID]


def js(o):
    return json.dumps(o, indent=2, ensure_ascii=False)


def examples():
    ex = []
    ex.append(("Registration", "E01", "POST /api/v1/auth/register",
               js({"full_name": "Asha Menon", "email": "asha.menon@example.org", "password": "correct-horse-battery-9", "role": "student"}),
               "201 Created",
               js({"data": {"user_id": STUDENT_ID, "full_name": "Asha Menon", "email": "asha.menon@example.org", "role": "student",
                            "account_status": "active", "email_verified": False, "profile_completed": False, "created_at": "2026-10-20T09:12:44Z"}})))
    ex.append(("Login", "E02", "POST /api/v1/auth/login",
               js({"email": "asha.menon@example.org", "password": "correct-horse-battery-9"}),
               "200 OK  (also sets: Set-Cookie: refresh_token=<opaque>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth; Max-Age=604800)",
               js({"data": {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<payload>.<signature>", "token_type": "Bearer", "expires_in": 900,
                            "user": {"user_id": STUDENT_ID, "full_name": "Asha Menon", "role": "student", "profile_completed": False}}})))
    res = M.worked_example()
    cards = {"Rohan Iyer": ("Senior Data Scientist", "Example Analytics Pvt Ltd", 6, ["Python", "SQL", "Machine Learning"], ["Data Science"]),
             "Meera Nair": ("Research Engineer", "Example Research Lab", 5, ["Machine Learning", "Statistics", "Python"], ["Data Science", "Higher Studies"]),
             "Karthik Rao": ("Software Engineer", "Example Software Ltd", 4, ["Python", "SQL"], ["Higher Studies"])}
    reasons = {"Rohan Iyer": ["Covers 3 of your 3 focus skills at a higher level", "Advises on Data Science", "2 mentee spots free, 4 open slots in the next 14 days"],
               "Meera Nair": ["Covers 2 of your 3 focus skills", "Advises on both of your career interests", "2 mentee spots free, 6 open slots in the next 14 days"]}
    data = []
    for r in res[:2]:
        t, o, y, sk, it = cards[r["name"]]
        data.append({"mentor": {"mentor_id": r["mentor_id"], "full_name": r["name"], "professional_title": t, "organisation": o, "experience_years": y,
                                "mentor_type": "alumni", "top_skills": sk, "interests": it, "accepting_mentees": True},
                     "match_score": r["score"], "breakdown": {"skills": r["S"], "interests": r["C"], "availability": r["A"]}, "reasons": reasons[r["name"]]})
    ex.append(("Mentor discovery (recommended)", "E23", "GET /api/v1/mentors/recommended?page=1&page_size=2", "(no body; student token in the Authorization header)",
               "200 OK", js({"data": data, "meta": {"page": 1, "page_size": 2, "total": len(res), "total_pages": 2}})))
    ex.append(("Submitting a mentoring request", "E24", "POST /api/v1/mentoring-requests",
               js({"mentor_id": MENTOR_ID, "career_goal": "I want to move into a data science role after graduation and need advice on building a portfolio.",
                   "message": "Hello Rohan, your path from the programme into industry matches what I am aiming for."}),
               "201 Created",
               js({"data": {"request_id": REQUEST_ID, "student_id": STUDENT_ID, "mentor_id": MENTOR_ID, "status": "pending",
                            "career_goal": "I want to move into a data science role after graduation and need advice on building a portfolio.",
                            "created_at": "2026-10-21T10:03:12Z", "expires_at": "2026-11-04T10:03:12Z"}})))
    ex.append(("Accepting a request", "E27", f"POST /api/v1/mentoring-requests/{REQUEST_ID}/accept", "(no body; mentor token)", "200 OK",
               js({"data": {"request": {"request_id": REQUEST_ID, "status": "accepted", "responded_at": "2026-10-22T14:41:05Z"},
                            "mentorship": {"mentorship_id": MENTORSHIP_ID, "request_id": REQUEST_ID, "student_id": STUDENT_ID, "mentor_id": MENTOR_ID,
                                           "status": "active", "started_at": "2026-10-22T14:41:05Z", "ended_at": None}}})))
    ex.append(("Scheduling a session (student books a slot)", "E34", f"POST /api/v1/mentorships/{MENTORSHIP_ID}/sessions",
               js({"slot_id": SLOT_ID, "meeting_mode": "online", "meeting_link": "https://meet.example.org/abc-defg-hij", "notes": "Agenda: portfolio review and project ideas."}),
               "201 Created",
               js({"data": {"session_id": SESSION_ID, "mentorship_id": MENTORSHIP_ID, "slot_id": SLOT_ID, "scheduled_start": "2026-11-02T12:30:00Z",
                            "scheduled_end": "2026-11-02T13:30:00Z", "meeting_mode": "online", "meeting_link": "https://meet.example.org/abc-defg-hij",
                            "status": "scheduled", "notes": "Agenda: portfolio review and project ideas."}})))
    ex.append(("Submitting feedback", "E38", f"POST /api/v1/sessions/{SESSION_ID}/feedback",
               js({"rating": 5, "comments": "Clear, practical advice on structuring a data science portfolio."}), "201 Created",
               js({"data": {"feedback_id": FEEDBACK_ID, "session_id": SESSION_ID, "submitted_by": STUDENT_ID, "rating": 5,
                            "comments": "Clear, practical advice on structuring a data science portfolio.", "created_at": "2026-11-02T14:05:30Z"}})))
    rq = dict(pending=20, accepted=54, declined=31, cancelled=9, expired=6)
    total = sum(rq.values())
    decided = rq["accepted"] + rq["declined"]
    ms = dict(active=38, completed=9, ended=7)
    assert sum(ms.values()) == rq["accepted"], "every accepted request creates exactly one mentorship"
    assert total == 120
    ses = dict(scheduled=41, completed=133, cancelled=22)
    ex.append(("Administrator analytics (sample values)", "E51", "GET /api/v1/admin/analytics/overview?from=2026-07-01&to=2026-09-30", "(no body; admin token)", "200 OK",
               js({"data": {"period": {"from": "2026-07-01", "to": "2026-09-30"}, "note": "SAMPLE VALUES FOR ILLUSTRATION ONLY - not real programme statistics",
                            "users": {"students": 310, "mentors": 56, "admins": 3},
                            "mentors": {"approved": 42, "pending_review": 6, "rejected": 3, "suspended": 1, "draft": 4, "capacity_total": 104, "utilisation": round(ms["active"] / 104, 3)},
                            "requests": {"total": total, **rq, "acceptance_rate": round(rq["accepted"] / decided, 3), "median_response_hours": 21.5},
                            "mentorships": {**ms, "with_three_or_more_sessions": 29},
                            "sessions": {**ses, "completion_rate": round(ses["completed"] / (ses["completed"] + ses["cancelled"]), 3)},
                            "feedback": {"count": 97, "average_rating": 4.5, "rating_distribution": {"1": 1, "2": 2, "3": 9, "4": 31, "5": 54}}}})))
    # sanity: distribution sums to count
    return ex


EXAMPLE_ERRORS = [
    ("Validation error (422)", "POST /api/v1/mentoring-requests", js({"error": {"code": "VALIDATION_ERROR", "message": "One or more fields are invalid.",
        "details": [{"field": "career_goal", "issue": "must be between 20 and 1000 characters"}], "request_id": "req_01HZX3K8M2"}})),
    ("State conflict (409)", f"POST /api/v1/mentoring-requests/{REQUEST_ID}/accept", js({"error": {"code": "MENTOR_AT_CAPACITY",
        "message": "You already have the maximum number of active mentees.", "details": [], "request_id": "req_01HZX3K9QW"}})),
]


# --------------------------------------------------------------------------------------------
# OpenAPI generator
# --------------------------------------------------------------------------------------------
def _schema(spec):
    req = spec.endswith("!")
    s = spec.rstrip("!")
    out = {}
    if s.startswith("ref:"):
        out = {"$ref": "#/components/schemas/" + s[4:]}
    elif s.startswith("enum:"):
        out = {"type": "string", "enum": s[5:].split("|")}
    elif s.startswith("array:"):
        inner = s[6:]
        items = {"type": "string", "format": "uuid"} if inner == "uuid" else ({"type": "object"} if inner == "object" else {"type": "string"})
        out = {"type": "array", "items": items}
    elif s.startswith("string("):
        lo, hi = s[7:-1].split("..")
        out = {"type": "string", "minLength": int(lo), "maxLength": int(hi)}
    else:
        out = {"string": {"type": "string"}, "text": {"type": "string"}, "integer": {"type": "integer"}, "number": {"type": "number"},
               "boolean": {"type": "boolean"}, "uuid": {"type": "string", "format": "uuid"}, "email": {"type": "string", "format": "email"},
               "datetime": {"type": "string", "format": "date-time"}, "date": {"type": "string", "format": "date"}, "object": {"type": "object"}}[s]
    return out, req


def _obj(fields):
    props, required = {}, []
    for k, v in fields.items():
        sch, req = _schema(v)
        props[k] = sch
        if req:
            required.append(k)
    o = {"type": "object", "properties": props}
    if required:
        o["required"] = required
    return o


class Flow(dict):
    pass


class FlowList(list):
    pass


def _yaml_dumper():
    import yaml

    class D(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True
    D.add_representer(Flow, lambda d, x: d.represent_mapping("tag:yaml.org,2002:map", dict(x), flow_style=True))
    D.add_representer(FlowList, lambda d, x: d.represent_sequence("tag:yaml.org,2002:seq", list(x), flow_style=True))
    return D


def _flow(sch):
    """Mark leaf schemas as flow style (one line each) for a compact, readable YAML."""
    if isinstance(sch, dict):
        if "enum" in sch:
            sch = dict(sch, enum=FlowList(sch["enum"]))
        return Flow(sch)
    return sch


def _obj_flow(fields):
    o = _obj(fields)
    o["properties"] = {k: _flow(v) for k, v in o["properties"].items()}
    if "required" in o:
        o["required"] = FlowList(o["required"])
    return o


STATUS_RESP = {"400": "BadRequest", "401": "Unauthorized", "403": "Forbidden", "404": "NotFound", "409": "Conflict",
               "422": "ValidationError", "429": "RateLimited"}
STATUS_DESC = {"400": "Bad request", "401": "Authentication required or failed", "403": "Not allowed for this role or owner", "404": "Not found",
               "409": "State conflict (see x-error-codes)", "422": "Validation failed", "429": "Rate limit exceeded"}


def openapi(compact=False):
    import yaml, re
    paths = {}
    ok_resp = {}
    req_bodies, req_schemas = {}, {}
    for e in EPS:
        oapi_path = re.sub(r":(\w+)", r"{\1}", e["path"])
        params = [Flow({"name": n, "in": "path", "required": True, "schema": Flow({"type": "string", "format": "uuid"})})
                  for n in re.findall(r":(\w+)", e["path"])]
        for n, t, d in e["params"]:
            sch = {"integer": {"type": "integer"}, "boolean": {"type": "boolean"}, "uuid": {"type": "string", "format": "uuid"},
                   "uuid[]": {"type": "array", "items": {"type": "string", "format": "uuid"}}, "datetime": {"type": "string", "format": "date-time"},
                   "date": {"type": "string", "format": "date"}}.get(t, {"type": "string"})
            p = {"name": n, "in": "query", "schema": Flow(sch)}
            if not compact:
                p["description"] = d
            params.append(Flow(p))
        op = {"summary": e["purpose"].split(". ")[0].rstrip("."), "operationId": e["id"], "tags": FlowList([e["group"]])}
        if not compact:
            op["description"] = e["purpose"]
        op["security"] = ([] if e["auth"] in ("public", "signed_token") else [Flow({"refreshCookie": FlowList()})] if e["auth"] == "refresh"
                          else [Flow({"bearerAuth": FlowList()})])
        if params:
            op["parameters"] = params
        if e["body"]:
            req_schemas[e["id"] + "Request"] = _obj_flow(e["body"])
            req_bodies[e["id"]] = Flow({"required": True, "content": Flow({"application/json": Flow({"schema": Flow({"$ref": "#/components/schemas/" + e["id"] + "Request"})})})})
            op["requestBody"] = Flow({"$ref": "#/components/requestBodies/" + e["id"]})
        code, schema, desc = e["ok"]
        if schema is None:
            op_ok = Flow({"description": desc})
        else:
            name = ("Page" + schema[5:]) if schema.startswith("page:") else ("Csv" if schema == "csv" else schema)
            ok_resp[name] = (schema, desc)
            op_ok = Flow({"$ref": "#/components/responses/" + name})
        responses = {code: op_ok}
        codes = []
        for er in e["errs"]:
            c, nm = er.split(" ", 1)
            responses[c] = Flow({"$ref": "#/components/responses/" + STATUS_RESP[c]})
            codes.append(nm)
        op["responses"] = dict(sorted(responses.items()))
        if codes:
            op["x-error-codes"] = FlowList(codes)
        paths.setdefault(oapi_path, {})[e["method"].lower()] = op
    resp_comp = {}
    for c, nm in STATUS_RESP.items():
        resp_comp[nm] = Flow({"description": STATUS_DESC[c], "content": Flow({"application/json": Flow({"schema": Flow({"$ref": "#/components/schemas/Error"})})})})
    for name, (schema, desc) in ok_resp.items():
        if schema == "csv":
            resp_comp[name] = Flow({"description": desc, "content": Flow({"text/csv": Flow({"schema": Flow({"type": "string"})})})})
        elif schema.startswith("page:"):
            sch = {"type": "object", "properties": {"data": Flow({"type": "array", "items": Flow({"$ref": "#/components/schemas/" + schema[5:]})}),
                                                    "meta": Flow({"$ref": "#/components/schemas/Meta"})}}
            resp_comp[name] = {"description": "Paginated " + schema[5:] + " list", "content": Flow({"application/json": Flow({"schema": sch})})}
        else:
            sch = {"type": "object", "properties": {"data": Flow({"$ref": "#/components/schemas/" + schema})}}
            resp_comp[name] = {"description": schema, "content": Flow({"application/json": Flow({"schema": sch})})}
    schemas = {k: _obj_flow(v) for k, v in COMP.items()}
    schemas.update(req_schemas)
    doc = {"openapi": "3.0.3",
           "info": {"title": "Student Mentoring and Career Support Platform API", "version": "1.0.0-draft",
                    **({} if compact else {"description": "Proposed REST API (design draft). All examples and identifiers are illustrative."})},
           "servers": [Flow({"url": "/api/v1"})],
           "paths": paths,
           "components": {"securitySchemes": {"bearerAuth": Flow({"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}),
                                              "refreshCookie": Flow({"type": "apiKey", "in": "cookie", "name": "refresh_token"})},
                          "requestBodies": req_bodies, "responses": resp_comp, "schemas": schemas}}
    return yaml.dump(doc, Dumper=_yaml_dumper(), sort_keys=False, width=200, allow_unicode=True, default_flow_style=False)


def verify():
    ids = [e["id"] for e in EPS]
    assert len(ids) == len(set(ids))
    for e in EPS:
        for er in e["errs"]:
            c, name = er.split(" ", 1)
            assert name in ERRORS and ERRORS[name][0] == int(c), (e["id"], er)
        code, schema, _ = e["ok"]
        if schema and schema != "csv":
            base = schema.split(":")[-1]
            assert base in COMP, (e["id"], schema)
    keys = set()
    for e in EPS:
        k = (e["method"], e["path"])
        assert k not in keys
        keys.add(k)
    for _t, eid, *_ in examples():
        assert eid in EP
    return True


if __name__ == "__main__":
    verify()
    print(len(EPS), "endpoints;", len(ERRORS), "error codes")
    y = openapi()
    open("/home/claude/report_build/api-spec.yaml", "w").write(y)
    print(len(y.splitlines()), "yaml lines (full);", len(openapi(True).splitlines()), "(compact for print)")
