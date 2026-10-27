"""Single source of truth for the database design (PostgreSQL).
Everything in the report (data dictionary, ER diagrams, DDL appendix, class attributes) derives from here."""

ROLES = ["student", "mentor", "admin"]
ACCOUNT_STATUS = ["active", "suspended", "deactivated"]
PROFILE_STATUS = ["draft", "pending_review", "approved", "rejected", "suspended"]
REQUEST_STATUS = ["pending", "accepted", "declined", "cancelled", "expired"]
MENTORSHIP_STATUS = ["active", "completed", "ended"]
SESSION_STATUS = ["scheduled", "completed", "cancelled"]
MEETING_MODE = ["online", "phone", "in_person"]
LEVELS = ["beginner", "intermediate", "advanced", "expert"]
STAGES = ["foundation", "diploma", "bsc_degree", "bs_degree"]
MENTOR_TYPES = ["recent_graduate", "alumni"]
NOTIF_TYPES = ["request_received", "request_accepted", "request_declined", "request_cancelled",
               "request_expired", "mentorship_ended", "session_scheduled", "session_cancelled",
               "session_reminder", "feedback_requested", "mentor_reviewed", "account_status_changed"]
TOKEN_REVOKE_REASONS = ["rotated", "logout", "reuse_detected", "password_change", "admin_action"]


def inlist(vals):
    return "IN (" + ", ".join(f"'{v}'" for v in vals) + ")"


def C(name, typ, key="", null=False, default="", unique="", check="", purpose=""):
    return dict(name=name, type=typ, key=key, null=null, default=default, unique=unique, check=check, purpose=purpose)


T = []  # ordered list of tables


def add(num, name, group, purpose, cols, constraints=(), indexes=(), pk=None):
    T.append(dict(num=num, name=name, group=group, purpose=purpose, cols=cols,
                  constraints=list(constraints), indexes=list(indexes), pk=pk))


NOW = "now()"
UUID_DEF = "gen_random_uuid()"

add(1, "users", "baseline", "Every account (student, mentor or admin); authentication identity and account state.", [
    C("user_id", "UUID", "PK", False, UUID_DEF, "", "", "Surrogate identifier; appears in tokens and APIs."),
    C("full_name", "VARCHAR(120)", "", False, "", "", "char_length(btrim(full_name)) > 0", "Display name."),
    C("email", "VARCHAR(255)", "", False, "", "UQ", "email = lower(email)", "Login identifier, stored lower-case so UNIQUE is case-insensitive."),
    C("password_hash", "VARCHAR(255)", "", False, "", "", "", "Argon2id encoded hash. Plaintext is never stored or logged."),
    C("role", "VARCHAR(20)", "", False, "", "", "role " + inlist(ROLES), "Single role per account: student, mentor or admin."),
    C("account_status", "VARCHAR(20)", "", False, "'active'", "", "account_status " + inlist(ACCOUNT_STATUS), "Controls whether the account may sign in."),
    C("email_verified", "BOOLEAN", "", False, "FALSE", "", "", "Set after e-mail verification (optional extension)."),
    C("last_login_at", "TIMESTAMPTZ", "", True, "", "", "", "Last successful login; used for activity analytics."),
    C("anonymised_at", "TIMESTAMPTZ", "", True, "", "", "", "Set when personal data is erased but the row is kept for integrity."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change (maintained by trigger)."),
], constraints=[
    ("uq_users_id_role", "UNIQUE (user_id, role)", "Target of the composite foreign keys that tie profiles to the correct role (D-03)."),
], indexes=[
    ("ix_users_role_status", "(role, account_status)", "Admin user lists and role-filtered counts."),
])

add(2, "student_profiles", "baseline", "Career-related profile of a student user (one per student account).", [
    C("student_profile_id", "UUID", "PK", False, UUID_DEF, "", "", "Profile identifier."),
    C("user_id", "UUID", "FK", False, "", "UQ", "", "Owning user (1:1). Also the key other tables reference (see D-09)."),
    C("user_role", "VARCHAR(20)", "FK", False, "'student'", "", "user_role = 'student'", "Discriminator; composite FK (user_id, user_role) to users forces role 'student'."),
    C("programme_stage", "VARCHAR(50)", "", True, "", "", "programme_stage " + inlist(STAGES), "Programme level (Foundation, Diploma, BSc, BS). Proposed enumeration."),
    C("expected_graduation_year", "INTEGER", "", True, "", "", "expected_graduation_year BETWEEN 2024 AND 2100", "Used to prioritise students approaching graduation."),
    C("career_goals", "TEXT", "", True, "", "", "char_length(career_goals) <= 2000", "Free-text career goals."),
    C("guidance_needs", "TEXT", "", True, "", "", "char_length(guidance_needs) <= 2000", "What guidance the student is looking for."),
    C("bio", "TEXT", "", True, "", "", "char_length(bio) <= 1000", "Short self-introduction."),
    C("profile_completed", "BOOLEAN", "", False, "FALSE", "", "", "True once onboarding minimum fields are filled; gates mentor requests."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change."),
], constraints=[
    ("fk_student_user_role", "FOREIGN KEY (user_id, user_role) REFERENCES users (user_id, role)", "Role/profile consistency (D-03)."),
])

add(3, "mentor_profiles", "baseline", "Professional profile of a mentor (recent graduate or alumnus) with review state.", [
    C("mentor_profile_id", "UUID", "PK", False, UUID_DEF, "", "", "Profile identifier."),
    C("user_id", "UUID", "FK", False, "", "UQ", "", "Owning user (1:1). Public 'mentor_id' in the API."),
    C("user_role", "VARCHAR(20)", "FK", False, "'mentor'", "", "user_role = 'mentor'", "Discriminator; composite FK forces role 'mentor'."),
    C("mentor_type", "VARCHAR(20)", "", False, "'alumni'", "", "mentor_type " + inlist(MENTOR_TYPES), "Recent graduate or alumnus."),
    C("professional_title", "VARCHAR(120)", "", True, "", "", "", "Current role title."),
    C("organisation", "VARCHAR(150)", "", True, "", "", "", "Employer, university or venture."),
    C("experience_years", "INTEGER", "", True, "", "", "experience_years BETWEEN 0 AND 60", "Years of relevant experience."),
    C("graduation_year", "INTEGER", "", True, "", "", "graduation_year BETWEEN 2000 AND 2100", "Year the mentor completed the programme (verification input)."),
    C("linkedin_url", "VARCHAR(255)", "", True, "", "", "", "Public profile link used by admins to verify background."),
    C("bio", "TEXT", "", True, "", "", "char_length(bio) <= 1500", "What the mentor can help with."),
    C("is_available", "BOOLEAN", "", False, "TRUE", "", "", "Mentor-controlled switch for accepting new mentees."),
    C("max_active_mentees", "INTEGER", "", False, "3", "", "max_active_mentees BETWEEN 1 AND 10", "Capacity limit for concurrent active mentorships."),
    C("profile_status", "VARCHAR(20)", "", False, "'draft'", "", "profile_status " + inlist(PROFILE_STATUS), "Review lifecycle; only 'approved' mentors are discoverable."),
    C("reviewed_by", "UUID", "FK", True, "", "", "", "Admin who last reviewed the profile."),
    C("reviewed_at", "TIMESTAMPTZ", "", True, "", "", "", "Time of last review decision."),
    C("review_note", "TEXT", "", True, "", "", "", "Reason or note given with the decision."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change."),
], constraints=[
    ("fk_mentor_user_role", "FOREIGN KEY (user_id, user_role) REFERENCES users (user_id, role)", "Role/profile consistency (D-03)."),
    ("ck_mentor_complete", "CHECK (profile_status IN ('draft','rejected') OR (professional_title IS NOT NULL AND organisation IS NOT NULL AND experience_years IS NOT NULL AND bio IS NOT NULL))", "Incomplete profiles cannot enter review or be approved."),
    ("ck_mentor_reviewed", "CHECK (profile_status IN ('draft','pending_review') OR reviewed_by IS NOT NULL)", "Every decision records who made it."),
], indexes=[
    ("ix_mentor_discoverable", "(profile_status, is_available)", "Discovery query filters approved + available mentors."),
    ("ix_mentor_fts", "GIN (to_tsvector('english', coalesce(professional_title,'') || ' ' || coalesce(organisation,'') || ' ' || coalesce(bio,'')))", "Full-text keyword search in discovery."),
])

add(4, "skills", "baseline", "Admin-managed catalogue of skills used by profiles and matching.", [
    C("skill_id", "UUID", "PK", False, UUID_DEF, "", "", "Skill identifier."),
    C("skill_name", "VARCHAR(100)", "", False, "", "UQ", "", "Unique skill name (e.g. Python)."),
    C("category", "VARCHAR(80)", "", True, "", "", "", "Grouping used for filters (e.g. Programming, Data)."),
    C("is_active", "BOOLEAN", "", False, "TRUE", "", "", "Retire a skill without breaking history."),
])

add(5, "student_skills", "baseline", "Junction: skills a student has or wants to build, with level and focus flag.", [
    C("student_profile_id", "UUID", "PK,FK", False, "", "", "", "Student profile."),
    C("skill_id", "UUID", "PK,FK", False, "", "", "", "Skill."),
    C("proficiency_level", "VARCHAR(30)", "", False, "", "", "proficiency_level " + inlist(LEVELS), "Student's current level in the skill."),
    C("is_focus", "BOOLEAN", "", False, "FALSE", "", "", "Marks up to five skills the student most wants guidance on (matching input)."),
], pk=["student_profile_id", "skill_id"], indexes=[
    ("ix_student_skills_skill", "(skill_id)", "Reverse lookup and analytics by skill."),
])

add(6, "mentor_expertise", "baseline", "Junction: skills a mentor can guide on, with expertise level.", [
    C("mentor_profile_id", "UUID", "PK,FK", False, "", "", "", "Mentor profile."),
    C("skill_id", "UUID", "PK,FK", False, "", "", "", "Skill."),
    C("expertise_level", "VARCHAR(30)", "", False, "", "", "expertise_level " + inlist(LEVELS), "Mentor's level in the skill."),
], pk=["mentor_profile_id", "skill_id"], indexes=[
    ("ix_mentor_expertise_skill", "(skill_id, mentor_profile_id)", "Find mentors by skill filter."),
])

add(7, "career_interests", "baseline", "Admin-managed catalogue of career pathways (industry, research, higher studies, ...).", [
    C("interest_id", "UUID", "PK", False, UUID_DEF, "", "", "Career interest identifier."),
    C("interest_name", "VARCHAR(100)", "", False, "", "UQ", "", "Unique pathway name (e.g. Higher Studies)."),
    C("description", "TEXT", "", True, "", "", "", "Short explanation shown in forms."),
    C("is_active", "BOOLEAN", "", False, "TRUE", "", "", "Retire an interest without breaking history."),
])

add(8, "student_interests", "baseline", "Junction: career pathways a student is interested in.", [
    C("student_profile_id", "UUID", "PK,FK", False, "", "", "", "Student profile."),
    C("interest_id", "UUID", "PK,FK", False, "", "", "", "Career interest."),
], pk=["student_profile_id", "interest_id"], indexes=[
    ("ix_student_interests_interest", "(interest_id)", "Reverse lookup and analytics."),
])

add(9, "mentoring_requests", "baseline", "A student's request to be mentored by one mentor.", [
    C("request_id", "UUID", "PK", False, UUID_DEF, "", "", "Request identifier."),
    C("student_id", "UUID", "FK", False, "", "", "", "Requesting student (value = users.user_id of a student profile)."),
    C("mentor_id", "UUID", "FK", False, "", "", "", "Target mentor (value = users.user_id of a mentor profile)."),
    C("career_goal", "TEXT", "", False, "", "", "char_length(career_goal) BETWEEN 20 AND 1000", "What the student wants to achieve."),
    C("message", "TEXT", "", True, "", "", "char_length(message) <= 1500", "Optional personal note to the mentor."),
    C("status", "VARCHAR(20)", "", False, "'pending'", "", "status " + inlist(REQUEST_STATUS), "Lifecycle state."),
    C("status_reason", "TEXT", "", True, "", "", "", "Decline or cancel reason."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Submission time."),
    C("responded_at", "TIMESTAMPTZ", "", True, "", "", "", "Time the mentor accepted or declined."),
    C("expires_at", "TIMESTAMPTZ", "", False, "now() + interval '14 days'", "", "", "Pending requests expire automatically (proposed 14 days)."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change."),
], constraints=[
    ("uq_request_parties", "UNIQUE (request_id, student_id, mentor_id)", "Target of the composite FK from mentorships."),
    ("ck_request_responded", "CHECK ((status IN ('accepted','declined')) = (responded_at IS NOT NULL))", "responded_at is set exactly for mentor decisions."),
], indexes=[
    ("uq_pending_request", "UNIQUE (student_id, mentor_id) WHERE status = 'pending'", "Duplicate pending request prevention."),
    ("ix_requests_mentor", "(mentor_id, status, created_at DESC)", "Mentor inbox."),
    ("ix_requests_student", "(student_id, status, created_at DESC)", "Student 'my requests' list."),
    ("ix_requests_expiry", "(expires_at) WHERE status = 'pending'", "Expiry job scans only pending rows."),
])

add(10, "mentorships", "baseline", "Active or finished mentoring relationship created from an accepted request.", [
    C("mentorship_id", "UUID", "PK", False, UUID_DEF, "", "", "Mentorship identifier."),
    C("request_id", "UUID", "FK", False, "", "UQ", "", "Accepted request that created it (1:1)."),
    C("student_id", "UUID", "FK", False, "", "", "", "Student (must match the request)."),
    C("mentor_id", "UUID", "FK", False, "", "", "", "Mentor (must match the request)."),
    C("status", "VARCHAR(20)", "", False, "'active'", "", "status " + inlist(MENTORSHIP_STATUS), "active, completed (natural conclusion) or ended (early termination)."),
    C("started_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Start of the relationship."),
    C("ended_at", "TIMESTAMPTZ", "", True, "", "", "", "Set when the mentorship stops being active."),
    C("ended_by", "UUID", "FK", True, "", "", "", "User (participant or admin) who closed it."),
    C("end_reason", "TEXT", "", True, "", "", "", "Optional closing note."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change."),
], constraints=[
    ("fk_mentorship_request", "FOREIGN KEY (request_id, student_id, mentor_id) REFERENCES mentoring_requests (request_id, student_id, mentor_id)", "Parties cannot differ from the accepted request."),
    ("uq_mentorship_parties", "UNIQUE (mentorship_id, student_id, mentor_id)", "Target of the composite FK from sessions."),
    ("ck_mentorship_ended", "CHECK ((status = 'active') = (ended_at IS NULL))", "ended_at present exactly when not active."),
], indexes=[
    ("uq_active_pair", "UNIQUE (student_id, mentor_id) WHERE status = 'active'", "One active mentorship per student-mentor pair."),
    ("ix_mentorship_mentor", "(mentor_id, status)", "Capacity count and mentee list."),
    ("ix_mentorship_student", "(student_id, status)", "Student's mentorships."),
])

add(11, "availability_slots", "baseline", "Concrete time windows in which a mentor can be booked.", [
    C("slot_id", "UUID", "PK", False, UUID_DEF, "", "", "Slot identifier."),
    C("mentor_id", "UUID", "FK", False, "", "", "", "Owning mentor (users.user_id of a mentor profile)."),
    C("start_time", "TIMESTAMPTZ", "", False, "", "", "", "Slot start."),
    C("end_time", "TIMESTAMPTZ", "", False, "", "", "end_time > start_time AND end_time - start_time <= interval '4 hours'", "Slot end."),
    C("is_available", "BOOLEAN", "", False, "TRUE", "", "", "FALSE once booked or blocked."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
], constraints=[
    ("ex_slot_no_overlap", "EXCLUDE USING gist (mentor_id WITH =, tstzrange(start_time, end_time) WITH &&)", "A mentor cannot publish overlapping slots."),
], indexes=[
    ("ix_slots_open", "(mentor_id, start_time) WHERE is_available", "Open-slot lookup for matching and booking."),
])

add(12, "sessions", "baseline", "A scheduled, completed or cancelled mentoring meeting inside a mentorship.", [
    C("session_id", "UUID", "PK", False, UUID_DEF, "", "", "Session identifier."),
    C("mentorship_id", "UUID", "FK", False, "", "", "", "Parent mentorship."),
    C("student_id", "UUID", "FK", False, "", "", "", "Student (denormalised from the mentorship, enforced by composite FK)."),
    C("mentor_id", "UUID", "FK", False, "", "", "", "Mentor (denormalised from the mentorship, enforced by composite FK)."),
    C("slot_id", "UUID", "FK", True, "", "", "", "Booked availability slot; NULL for ad-hoc sessions."),
    C("scheduled_start", "TIMESTAMPTZ", "", False, "", "", "", "Planned start."),
    C("scheduled_end", "TIMESTAMPTZ", "", False, "", "", "scheduled_end > scheduled_start", "Planned end."),
    C("meeting_mode", "VARCHAR(20)", "", False, "'online'", "", "meeting_mode " + inlist(MEETING_MODE), "online, phone or in_person."),
    C("meeting_link", "TEXT", "", True, "", "", "", "Video-call link or location detail."),
    C("status", "VARCHAR(20)", "", False, "'scheduled'", "", "status " + inlist(SESSION_STATUS), "Lifecycle state."),
    C("notes", "TEXT", "", True, "", "", "char_length(notes) <= 4000", "Agenda and outcome notes shared by both participants."),
    C("cancelled_by", "UUID", "FK", True, "", "", "", "Participant who cancelled."),
    C("cancel_reason", "TEXT", "", True, "", "", "", "Cancellation reason."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
    C("updated_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Last change."),
], constraints=[
    ("fk_session_mentorship", "FOREIGN KEY (mentorship_id, student_id, mentor_id) REFERENCES mentorships (mentorship_id, student_id, mentor_id)", "Session parties always equal the mentorship parties."),
    ("ex_session_mentor_no_overlap", "EXCLUDE USING gist (mentor_id WITH =, tstzrange(scheduled_start, scheduled_end) WITH &&) WHERE (status = 'scheduled')", "No double-booking of a mentor."),
    ("ex_session_student_no_overlap", "EXCLUDE USING gist (student_id WITH =, tstzrange(scheduled_start, scheduled_end) WITH &&) WHERE (status = 'scheduled')", "No double-booking of a student."),
    ("ck_session_cancel", "CHECK (status = 'cancelled' OR (cancelled_by IS NULL AND cancel_reason IS NULL))", "Cancellation data only on cancelled sessions."),
], indexes=[
    ("uq_session_slot_booked", "UNIQUE (slot_id) WHERE status = 'scheduled'", "A slot is held by at most one scheduled session."),
    ("ix_sessions_mentorship", "(mentorship_id, scheduled_start)", "Session history."),
    ("ix_sessions_mentor_time", "(mentor_id, scheduled_start) WHERE status = 'scheduled'", "Mentor calendar."),
    ("ix_sessions_student_time", "(student_id, scheduled_start) WHERE status = 'scheduled'", "Student calendar."),
])

add(13, "feedback", "baseline", "Rating and comment given by one participant about one completed session.", [
    C("feedback_id", "UUID", "PK", False, UUID_DEF, "", "", "Feedback identifier."),
    C("session_id", "UUID", "FK", False, "", "", "", "Session being rated."),
    C("submitted_by", "UUID", "FK", False, "", "", "", "Participant who wrote it (verified against the mentorship in the service)."),
    C("rating", "INTEGER", "", False, "", "", "rating BETWEEN 1 AND 5", "1 (poor) to 5 (excellent)."),
    C("comments", "TEXT", "", True, "", "", "char_length(comments) <= 1000", "Optional comment."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Submission time."),
], constraints=[
    ("uq_feedback_once", "UNIQUE (session_id, submitted_by)", "One feedback entry per participant per session."),
], indexes=[])

add(14, "notifications", "baseline", "In-app notification addressed to one user.", [
    C("notification_id", "UUID", "PK", False, UUID_DEF, "", "", "Notification identifier."),
    C("user_id", "UUID", "FK", False, "", "", "", "Recipient."),
    C("title", "VARCHAR(150)", "", False, "", "", "", "Short headline."),
    C("message", "TEXT", "", False, "", "", "", "Body text."),
    C("notification_type", "VARCHAR(50)", "", False, "", "", "notification_type " + inlist(NOTIF_TYPES), "Event type; drives icon and deep link."),
    C("related_entity_type", "VARCHAR(50)", "", True, "", "", "", "Entity the notification points to (e.g. mentoring_request)."),
    C("related_entity_id", "UUID", "", True, "", "", "", "Identifier of that entity, for deep links."),
    C("is_read", "BOOLEAN", "", False, "FALSE", "", "", "Read flag."),
    C("read_at", "TIMESTAMPTZ", "", True, "", "", "", "Time it was read."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Creation time."),
], constraints=[
    ("ck_notification_read", "CHECK (is_read = (read_at IS NOT NULL))", "Read flag and timestamp stay consistent."),
], indexes=[
    ("ix_notifications_user", "(user_id, is_read, created_at DESC)", "Bell badge count and list."),
])

add(15, "audit_logs", "baseline", "Append-only record of sensitive actions for accountability.", [
    C("audit_id", "UUID", "PK", False, UUID_DEF, "", "", "Audit entry identifier."),
    C("actor_user_id", "UUID", "FK", True, "", "", "", "Acting user; NULL for system events (e.g. expiry job)."),
    C("action", "VARCHAR(100)", "", False, "", "", "", "Verb, e.g. mentor.approved, request.accepted."),
    C("entity_type", "VARCHAR(50)", "", False, "", "", "", "Type of the affected record."),
    C("entity_id", "UUID", "", False, "", "", "", "Identifier of the affected record (polymorphic, no FK)."),
    C("details", "JSONB", "", True, "", "", "", "Before/after values or reason; never secrets."),
    C("ip_address", "INET", "", True, "", "", "", "Client address for security-relevant events."),
    C("created_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Event time."),
], indexes=[
    ("ix_audit_entity", "(entity_type, entity_id)", "History of one record."),
    ("ix_audit_actor", "(actor_user_id, created_at DESC)", "Actions by one user."),
    ("ix_audit_time", "(created_at)", "Retention purge and time-range reports."),
])

add(16, "mentor_interests", "added", "Junction: career pathways a mentor can advise on (needed by the matching score C).", [
    C("mentor_profile_id", "UUID", "PK,FK", False, "", "", "", "Mentor profile."),
    C("interest_id", "UUID", "PK,FK", False, "", "", "", "Career interest."),
], pk=["mentor_profile_id", "interest_id"], indexes=[
    ("ix_mentor_interests_interest", "(interest_id)", "Filter mentors by career pathway."),
])

add(17, "refresh_tokens", "added", "Server-side record of issued refresh tokens (hash only) enabling rotation and revocation.", [
    C("token_id", "UUID", "PK", False, UUID_DEF, "", "", "Token identifier (JWT jti)."),
    C("user_id", "UUID", "FK", False, "", "", "", "Token owner."),
    C("family_id", "UUID", "", False, "", "", "", "Groups tokens issued from one login; reuse revokes the family."),
    C("token_hash", "CHAR(64)", "", False, "", "UQ", "", "SHA-256 hex of the opaque token; the raw token is never stored."),
    C("issued_at", "TIMESTAMPTZ", "", False, NOW, "", "", "Issue time."),
    C("expires_at", "TIMESTAMPTZ", "", False, "", "", "expires_at > issued_at", "Absolute expiry (proposed 7 days)."),
    C("revoked_at", "TIMESTAMPTZ", "", True, "", "", "", "Set on rotation, logout or security revocation."),
    C("revoked_reason", "VARCHAR(30)", "", True, "", "", "revoked_reason IS NULL OR revoked_reason " + inlist(TOKEN_REVOKE_REASONS), "Why it was revoked."),
], constraints=[
    ("ck_token_revoked", "CHECK ((revoked_at IS NULL) = (revoked_reason IS NULL))", "Revocation data stays consistent."),
], indexes=[
    ("ix_refresh_user_live", "(user_id) WHERE revoked_at IS NULL", "Revoke all live tokens of a user."),
    ("ix_refresh_family", "(family_id)", "Revoke a whole token family on reuse."),
])

TBL = {t["name"]: t for t in T}

# Foreign keys: (child, child_cols, parent, parent_cols, on_delete, cardinality, child_optional, label)
# cardinality describes child:parent as seen from the parent: "1:1" (child.unique) or "1:N".
FKS = [
    ("student_profiles", ["user_id"], "users", ["user_id"], "RESTRICT", "1:1", False, "has student profile"),
    ("mentor_profiles", ["user_id"], "users", ["user_id"], "RESTRICT", "1:1", False, "has mentor profile"),
    ("mentor_profiles", ["reviewed_by"], "users", ["user_id"], "SET NULL", "1:N", True, "reviewed by (admin)"),
    ("student_skills", ["student_profile_id"], "student_profiles", ["student_profile_id"], "CASCADE", "1:N", False, ""),
    ("student_skills", ["skill_id"], "skills", ["skill_id"], "RESTRICT", "1:N", False, ""),
    ("mentor_expertise", ["mentor_profile_id"], "mentor_profiles", ["mentor_profile_id"], "CASCADE", "1:N", False, ""),
    ("mentor_expertise", ["skill_id"], "skills", ["skill_id"], "RESTRICT", "1:N", False, ""),
    ("student_interests", ["student_profile_id"], "student_profiles", ["student_profile_id"], "CASCADE", "1:N", False, ""),
    ("student_interests", ["interest_id"], "career_interests", ["interest_id"], "RESTRICT", "1:N", False, ""),
    ("mentor_interests", ["mentor_profile_id"], "mentor_profiles", ["mentor_profile_id"], "CASCADE", "1:N", False, ""),
    ("mentor_interests", ["interest_id"], "career_interests", ["interest_id"], "RESTRICT", "1:N", False, ""),
    ("mentoring_requests", ["student_id"], "student_profiles", ["user_id"], "RESTRICT", "1:N", False, "sends"),
    ("mentoring_requests", ["mentor_id"], "mentor_profiles", ["user_id"], "RESTRICT", "1:N", False, "receives"),
    ("mentorships", ["request_id"], "mentoring_requests", ["request_id"], "RESTRICT", "1:1", False, "created from"),
    ("mentorships", ["student_id"], "student_profiles", ["user_id"], "RESTRICT", "1:N", False, "learns in"),
    ("mentorships", ["mentor_id"], "mentor_profiles", ["user_id"], "RESTRICT", "1:N", False, "guides in"),
    ("mentorships", ["ended_by"], "users", ["user_id"], "SET NULL", "1:N", True, "ended by"),
    ("availability_slots", ["mentor_id"], "mentor_profiles", ["user_id"], "RESTRICT", "1:N", False, "publishes"),
    ("sessions", ["mentorship_id"], "mentorships", ["mentorship_id"], "RESTRICT", "1:N", False, "contains"),
    ("sessions", ["slot_id"], "availability_slots", ["slot_id"], "SET NULL", "1:N", True, "booked into"),
    ("sessions", ["cancelled_by"], "users", ["user_id"], "SET NULL", "1:N", True, "cancelled by"),
    ("feedback", ["session_id"], "sessions", ["session_id"], "RESTRICT", "1:N", False, "rates"),
    ("feedback", ["submitted_by"], "users", ["user_id"], "RESTRICT", "1:N", False, "written by"),
    ("notifications", ["user_id"], "users", ["user_id"], "CASCADE", "1:N", False, "addressed to"),
    ("audit_logs", ["actor_user_id"], "users", ["user_id"], "SET NULL", "1:N", True, "performed by"),
    ("refresh_tokens", ["user_id"], "users", ["user_id"], "CASCADE", "1:N", False, "issued to"),
]
# Composite FKs documented through constraints (not repeated above): profiles->users(user_id, role),
# mentorships->requests(request_id, student_id, mentor_id), sessions->mentorships(mentorship_id, student_id, mentor_id).


def fk_cols_set():
    import re
    s = {}
    for child, cols, *_ in FKS:
        for c in cols:
            s.setdefault(child, set()).add(c)
    for t in T:  # columns covered by composite FOREIGN KEY constraints
        for _, d, _ in t["constraints"]:
            m = re.search(r"FOREIGN KEY \(([^)]*)\)", d)
            if m:
                for c in m.group(1).split(","):
                    s.setdefault(t["name"], set()).add(c.strip())
    return s


def verify():
    """Internal consistency checks; raises AssertionError on any mismatch."""
    names = {t["name"] for t in T}
    assert len(T) == 17 and len(names) == 17
    fkset = fk_cols_set()
    for t in T:
        cn = [c["name"] for c in t["cols"]]
        assert len(cn) == len(set(cn)), t["name"]
        for c in t["cols"]:
            if "FK" in c["key"]:
                # every FK column must be declared in FKS or be the discriminator of a composite FK
                if c["name"] == "user_role":
                    continue
                assert c["name"] in fkset.get(t["name"], set()), (t["name"], c["name"])
        for col in t["pk"] or []:
            assert col in cn
    for child, cols, parent, pcols, *_ in FKS:
        assert child in names and parent in names
        for c in cols:
            assert c in [x["name"] for x in TBL[child]["cols"]], (child, c)
        for c in pcols:
            assert c in [x["name"] for x in TBL[parent]["cols"]], (parent, c)
    return True


def ddl():
    out = ["-- Illustrative PostgreSQL DDL generated from the report's schema model (PostgreSQL 15+).",
           "-- Requires: CREATE EXTENSION IF NOT EXISTS btree_gist;  (for EXCLUDE constraints)",
           "CREATE EXTENSION IF NOT EXISTS btree_gist;", ""]
    fk_by_child = {}
    for child, cols, parent, pcols, ond, card, opt, label in FKS:
        fk_by_child.setdefault(child, []).append((cols, parent, pcols, ond))
    for t in T:
        lines = []
        for c in t["cols"]:
            s = f"  {c['name']} {c['type']}"
            if not c["null"]:
                s += " NOT NULL"
            if c["default"]:
                s += f" DEFAULT {c['default']}"
            if c["unique"] == "UQ":
                s += " UNIQUE"
            if c["check"]:
                s += f" CHECK ({c['check']})"
            lines.append(s)
        pk = t["pk"] or [c["name"] for c in t["cols"] if c["key"] == "PK"]
        lines.append(f"  PRIMARY KEY ({', '.join(pk)})")
        for cols, parent, pcols, ond in fk_by_child.get(t["name"], []):
            lines.append(f"  FOREIGN KEY ({', '.join(cols)}) REFERENCES {parent} ({', '.join(pcols)}) ON DELETE {ond}")
        for name, d, _ in t["constraints"]:
            if d.startswith("CHECK"):
                lines.append(f"  CONSTRAINT {name} {d}")
            else:
                lines.append(f"  CONSTRAINT {name} {d}")
        out.append(f"CREATE TABLE {t['name']} (\n" + ",\n".join(lines) + "\n);")
        for name, d, _ in t["indexes"]:
            if d.startswith("UNIQUE"):
                body = d[len("UNIQUE "):]
                out.append(f"CREATE UNIQUE INDEX {name} ON {t['name']} {body};")
            elif d.startswith("GIN"):
                out.append(f"CREATE INDEX {name} ON {t['name']} USING {d};")
            else:
                out.append(f"CREATE INDEX {name} ON {t['name']} {d};")
        out.append("")
    out.append(EXTRA_SQL)
    return "\n".join(out)


EXTRA_SQL = """-- ---------------------------------------------------------------------------
-- Triggers (defence in depth; the service layer enforces the same rules first)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_student_profiles_updated BEFORE UPDATE ON student_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_mentor_profiles_updated BEFORE UPDATE ON mentor_profiles FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_requests_updated BEFORE UPDATE ON mentoring_requests FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_mentorships_updated BEFORE UPDATE ON mentorships FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_sessions_updated BEFORE UPDATE ON sessions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- A mentorship may only be created from an accepted request.
CREATE OR REPLACE FUNCTION mentorship_requires_accepted() RETURNS trigger AS $$
BEGIN
  IF (SELECT status FROM mentoring_requests WHERE request_id = NEW.request_id) <> 'accepted' THEN
    RAISE EXCEPTION 'mentorship requires an accepted request' USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_mentorship_requires_accepted BEFORE INSERT ON mentorships
  FOR EACH ROW EXECUTE FUNCTION mentorship_requires_accepted();

-- Mentor capacity: refuse an extra active mentorship beyond max_active_mentees.
-- The service locks the mentor_profiles row first (SELECT ... FOR UPDATE); this trigger is the safety net.
CREATE OR REPLACE FUNCTION mentorship_capacity_guard() RETURNS trigger AS $$
DECLARE cap integer; cur integer;
BEGIN
  IF NEW.status = 'active' THEN
    SELECT max_active_mentees INTO cap FROM mentor_profiles WHERE user_id = NEW.mentor_id;
    SELECT count(*) INTO cur FROM mentorships WHERE mentor_id = NEW.mentor_id AND status = 'active';
    IF cur >= cap THEN
      RAISE EXCEPTION 'mentor at capacity' USING ERRCODE = '23514';
    END IF;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
CREATE TRIGGER trg_mentorship_capacity BEFORE INSERT ON mentorships
  FOR EACH ROW EXECUTE FUNCTION mentorship_capacity_guard();

-- Audit log is append-only for the application role.
-- REVOKE UPDATE, DELETE ON audit_logs FROM app_role;
"""

IMPROVEMENTS = [
    ("D-01", "Identifiers", "UUID primary keys on principal entities; defaults use gen_random_uuid().",
     "Baseline left defaults unspecified. A database-side default lets any writer (API, seed script, test) create rows without coordinating IDs."),
    ("D-02", "users", "E-mail stored lower-case with CHECK + UNIQUE; CHECK on role and account_status; NOT NULL timestamps with defaults; added last_login_at and anonymised_at.",
     "Makes UNIQUE e-mail case-insensitive without extensions, rejects invalid states at the lowest layer, and supports activity analytics and erasure requests."),
    ("D-03", "Role/profile consistency", "users gets UNIQUE (user_id, role); profile tables carry a discriminator column (user_role) and a composite FK to it.",
     "A student_profiles row can only point to a user whose role is 'student' (same for mentors) with no trigger needed."),
    ("D-04", "student_profiles", "Constrained programme_stage; added expected_graduation_year, profile_completed, created_at.",
     "Stage values follow the four programme levels named on the programme website (Foundation, Diploma, BSc, BS) - treated as a proposed enumeration. profile_completed gates mentor requests."),
    ("D-05", "mentor_profiles", "Added mentor_type, graduation_year, linkedin_url, reviewed_by/at/note; CHECKs for status, capacity (1-10, default 3), experience and completeness.",
     "Supports the admin approval workflow and verification of alumni claims; prevents incomplete profiles from being approved."),
    ("D-06", "Catalogues", "skills and career_interests get is_active; names unique.",
     "Retire a catalogue entry without deleting history; a controlled vocabulary keeps matching reliable."),
    ("D-07", "student_skills", "Added is_focus flag; level CHECK.",
     "The matching score S uses the (up to five) skills the student most wants guidance on instead of diluting over every listed skill."),
    ("D-08", "NEW mentor_interests", "Added junction table mentor_interests (mentor_profile_id, interest_id).",
     "The baseline has student_interests but no mentor-side career pathways, so the career-interest score C could not be computed. This is the first of two added tables."),
    ("D-09", "mentoring_requests", "student_id and mentor_id reference student_profiles(user_id) and mentor_profiles(user_id); career_goal NOT NULL; status CHECK incl. 'expired'; added status_reason and expires_at; responded_at CHECK; partial UNIQUE index for pending pairs; UNIQUE (request_id, student_id, mentor_id).",
     "Referencing profile tables guarantees correct roles. The partial unique index prevents duplicate pending requests even under concurrent submissions. Values are still users.user_id, so the API stays simple."),
    ("D-10", "mentorships", "Composite FK to the request; added ended_by, end_reason, updated_at; CHECK active <=> ended_at IS NULL; partial UNIQUE (student_id, mentor_id) WHERE active; creation trigger requires an accepted request.",
     "Parties cannot diverge from the accepted request, only one active mentorship per pair exists, and a mentorship cannot exist without acceptance."),
    ("D-11", "Mentor capacity", "Capacity enforced in one transaction with row locks, plus a trigger as safety net.",
     "Two simultaneous acceptances must not exceed max_active_mentees (see Section 7.5)."),
    ("D-12", "availability_slots", "CHECKs on duration; EXCLUDE constraint forbids overlapping slots per mentor; added created_at; individual slots, no recurrence table.",
     "Concrete slots keep booking and overlap checks simple. A UI 'repeat weekly' helper expands into slots (Section 7.7)."),
    ("D-13", "sessions", "Added student_id and mentor_id (denormalised, composite FK to mentorships); two partial EXCLUDE constraints; partial UNIQUE on slot_id; cancelled_by, cancel_reason; meeting_mode CHECK.",
     "Overlap prevention for both parties needs the party IDs on the session row. The composite FK guarantees they cannot disagree with the mentorship."),
    ("D-14", "feedback", "UNIQUE (session_id, submitted_by); rating CHECK 1-5; comment length CHECK.",
     "One entry per participant per session, as suggested in the baseline; participation and 'completed' status are verified in the service."),
    ("D-15", "notifications", "Added related_entity_type/id and read_at; type CHECK; consistent read flag; index for the bell badge.",
     "Notifications can deep-link to the entity and the unread count query stays fast."),
    ("D-16", "audit_logs", "Added details (JSONB) and ip_address; actor FK is ON DELETE SET NULL; append-only for the app role.",
     "Audit entries keep their meaning after user changes and cannot be edited by application code."),
    ("D-17", "NEW refresh_tokens", "Added refresh_tokens (hash only, family_id, revoked_at/reason).",
     "Refresh-token rotation, logout and reuse detection require server-side state. This is the second added table."),
    ("D-18", "Indexes", "Added the indexes listed per table (Section 7.4).",
     "Support the inbox, discovery, calendar, notification and analytics queries."),
    ("D-19", "Retention", "No hard deletes of users; anonymisation and scheduled purges (Section 7.9).",
     "Preserves referential integrity and analytics while honouring erasure requests."),
    ("D-20", "Timestamps", "updated_at maintained by a trigger; all timestamps TIMESTAMPTZ stored in UTC.",
     "Prevents stale updated_at values and time-zone bugs (users are in several regions)."),
]

CASCADE_POLICY = [
    ("Profile -> junction tables", "ON DELETE CASCADE", "Junction rows have no meaning without the profile."),
    ("Junction -> catalogue (skills, career_interests)", "ON DELETE RESTRICT", "Catalogue entries are retired with is_active, never deleted while referenced."),
    ("Domain tables -> profiles/users (requests, mentorships, sessions, feedback)", "ON DELETE RESTRICT", "History must not vanish; users are anonymised, not deleted."),
    ("Optional actor columns (reviewed_by, ended_by, cancelled_by, audit actor)", "ON DELETE SET NULL", "Keep the record, lose only the pointer."),
    ("notifications.user_id, refresh_tokens.user_id", "ON DELETE CASCADE", "Operational data owned by the user."),
]

RETENTION = [
    ("users / profiles", "Kept while the account exists. On an erasure request: full_name and e-mail replaced by placeholders, password_hash cleared, bio/goals cleared, anonymised_at set, account deactivated.", "Preserves referential integrity and aggregate analytics."),
    ("mentoring_requests (declined, cancelled, expired)", "Retained 12 months, then personal text fields (career_goal, message) cleared.", "Proposed value; confirm with IITM data-governance policy."),
    ("mentorships, sessions, feedback", "Retained for the life of the programme record; personal text anonymised on erasure.", "Needed for programme-effectiveness analysis."),
    ("notifications", "Read notifications purged after 90 days; unread kept.", "Operational data with little long-term value."),
    ("audit_logs", "Retained 24 months, then purged by a scheduled job.", "Proposed value; accountability versus data minimisation."),
    ("refresh_tokens", "Expired or revoked rows purged after 30 days.", "Keeps the table small; reuse detection needs only recent rows."),
]

if __name__ == "__main__":
    verify()
    print("tables", len(T), "columns", sum(len(t["cols"]) for t in T), "fks", len(FKS))
