-- Illustrative PostgreSQL DDL generated from the report's schema model (PostgreSQL 15+).
-- Requires: CREATE EXTENSION IF NOT EXISTS btree_gist;  (for EXCLUDE constraints)
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE users (
  user_id UUID NOT NULL DEFAULT gen_random_uuid(),
  full_name VARCHAR(120) NOT NULL CHECK (char_length(btrim(full_name)) > 0),
  email VARCHAR(255) NOT NULL UNIQUE CHECK (email = lower(email)),
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(20) NOT NULL CHECK (role IN ('student', 'mentor', 'admin')),
  account_status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (account_status IN ('active', 'suspended', 'deactivated')),
  email_verified BOOLEAN NOT NULL DEFAULT FALSE,
  last_login_at TIMESTAMPTZ,
  anonymised_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id),
  CONSTRAINT uq_users_id_role UNIQUE (user_id, role)
);
CREATE INDEX ix_users_role_status ON users (role, account_status);

CREATE TABLE student_profiles (
  student_profile_id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  user_role VARCHAR(20) NOT NULL DEFAULT 'student' CHECK (user_role = 'student'),
  programme_stage VARCHAR(50) CHECK (programme_stage IN ('foundation', 'diploma', 'bsc_degree', 'bs_degree')),
  expected_graduation_year INTEGER CHECK (expected_graduation_year BETWEEN 2024 AND 2100),
  career_goals TEXT CHECK (char_length(career_goals) <= 2000),
  guidance_needs TEXT CHECK (char_length(guidance_needs) <= 2000),
  bio TEXT CHECK (char_length(bio) <= 1000),
  profile_completed BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (student_profile_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_student_user_role FOREIGN KEY (user_id, user_role) REFERENCES users (user_id, role)
);

CREATE TABLE mentor_profiles (
  mentor_profile_id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE,
  user_role VARCHAR(20) NOT NULL DEFAULT 'mentor' CHECK (user_role = 'mentor'),
  mentor_type VARCHAR(20) NOT NULL DEFAULT 'alumni' CHECK (mentor_type IN ('recent_graduate', 'alumni')),
  professional_title VARCHAR(120),
  organisation VARCHAR(150),
  experience_years INTEGER CHECK (experience_years BETWEEN 0 AND 60),
  graduation_year INTEGER CHECK (graduation_year BETWEEN 2000 AND 2100),
  linkedin_url VARCHAR(255),
  bio TEXT CHECK (char_length(bio) <= 1500),
  is_available BOOLEAN NOT NULL DEFAULT TRUE,
  max_active_mentees INTEGER NOT NULL DEFAULT 3 CHECK (max_active_mentees BETWEEN 1 AND 10),
  profile_status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (profile_status IN ('draft', 'pending_review', 'approved', 'rejected', 'suspended')),
  reviewed_by UUID,
  reviewed_at TIMESTAMPTZ,
  review_note TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (mentor_profile_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE RESTRICT,
  FOREIGN KEY (reviewed_by) REFERENCES users (user_id) ON DELETE SET NULL,
  CONSTRAINT fk_mentor_user_role FOREIGN KEY (user_id, user_role) REFERENCES users (user_id, role),
  CONSTRAINT ck_mentor_complete CHECK (profile_status IN ('draft','rejected') OR (professional_title IS NOT NULL AND organisation IS NOT NULL AND experience_years IS NOT NULL AND bio IS NOT NULL)),
  CONSTRAINT ck_mentor_reviewed CHECK (profile_status IN ('draft','pending_review') OR reviewed_by IS NOT NULL)
);
CREATE INDEX ix_mentor_discoverable ON mentor_profiles (profile_status, is_available);
CREATE INDEX ix_mentor_fts ON mentor_profiles USING GIN (to_tsvector('english', coalesce(professional_title,'') || ' ' || coalesce(organisation,'') || ' ' || coalesce(bio,'')));

CREATE TABLE skills (
  skill_id UUID NOT NULL DEFAULT gen_random_uuid(),
  skill_name VARCHAR(100) NOT NULL UNIQUE,
  category VARCHAR(80),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (skill_id)
);

CREATE TABLE student_skills (
  student_profile_id UUID NOT NULL,
  skill_id UUID NOT NULL,
  proficiency_level VARCHAR(30) NOT NULL CHECK (proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
  is_focus BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (student_profile_id, skill_id),
  FOREIGN KEY (student_profile_id) REFERENCES student_profiles (student_profile_id) ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE RESTRICT
);
CREATE INDEX ix_student_skills_skill ON student_skills (skill_id);

CREATE TABLE mentor_expertise (
  mentor_profile_id UUID NOT NULL,
  skill_id UUID NOT NULL,
  expertise_level VARCHAR(30) NOT NULL CHECK (expertise_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
  PRIMARY KEY (mentor_profile_id, skill_id),
  FOREIGN KEY (mentor_profile_id) REFERENCES mentor_profiles (mentor_profile_id) ON DELETE CASCADE,
  FOREIGN KEY (skill_id) REFERENCES skills (skill_id) ON DELETE RESTRICT
);
CREATE INDEX ix_mentor_expertise_skill ON mentor_expertise (skill_id, mentor_profile_id);

CREATE TABLE career_interests (
  interest_id UUID NOT NULL DEFAULT gen_random_uuid(),
  interest_name VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (interest_id)
);

CREATE TABLE student_interests (
  student_profile_id UUID NOT NULL,
  interest_id UUID NOT NULL,
  PRIMARY KEY (student_profile_id, interest_id),
  FOREIGN KEY (student_profile_id) REFERENCES student_profiles (student_profile_id) ON DELETE CASCADE,
  FOREIGN KEY (interest_id) REFERENCES career_interests (interest_id) ON DELETE RESTRICT
);
CREATE INDEX ix_student_interests_interest ON student_interests (interest_id);

CREATE TABLE mentoring_requests (
  request_id UUID NOT NULL DEFAULT gen_random_uuid(),
  student_id UUID NOT NULL,
  mentor_id UUID NOT NULL,
  career_goal TEXT NOT NULL CHECK (char_length(career_goal) BETWEEN 20 AND 1000),
  message TEXT CHECK (char_length(message) <= 1500),
  status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'cancelled', 'expired')),
  status_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  responded_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ NOT NULL DEFAULT now() + interval '14 days',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (request_id),
  FOREIGN KEY (student_id) REFERENCES student_profiles (user_id) ON DELETE RESTRICT,
  FOREIGN KEY (mentor_id) REFERENCES mentor_profiles (user_id) ON DELETE RESTRICT,
  CONSTRAINT uq_request_parties UNIQUE (request_id, student_id, mentor_id),
  CONSTRAINT ck_request_responded CHECK ((status IN ('accepted','declined')) = (responded_at IS NOT NULL))
);
CREATE UNIQUE INDEX uq_pending_request ON mentoring_requests (student_id, mentor_id) WHERE status = 'pending';
CREATE INDEX ix_requests_mentor ON mentoring_requests (mentor_id, status, created_at DESC);
CREATE INDEX ix_requests_student ON mentoring_requests (student_id, status, created_at DESC);
CREATE INDEX ix_requests_expiry ON mentoring_requests (expires_at) WHERE status = 'pending';

CREATE TABLE mentorships (
  mentorship_id UUID NOT NULL DEFAULT gen_random_uuid(),
  request_id UUID NOT NULL UNIQUE,
  student_id UUID NOT NULL,
  mentor_id UUID NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'ended')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at TIMESTAMPTZ,
  ended_by UUID,
  end_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (mentorship_id),
  FOREIGN KEY (request_id) REFERENCES mentoring_requests (request_id) ON DELETE RESTRICT,
  FOREIGN KEY (student_id) REFERENCES student_profiles (user_id) ON DELETE RESTRICT,
  FOREIGN KEY (mentor_id) REFERENCES mentor_profiles (user_id) ON DELETE RESTRICT,
  FOREIGN KEY (ended_by) REFERENCES users (user_id) ON DELETE SET NULL,
  CONSTRAINT fk_mentorship_request FOREIGN KEY (request_id, student_id, mentor_id) REFERENCES mentoring_requests (request_id, student_id, mentor_id),
  CONSTRAINT uq_mentorship_parties UNIQUE (mentorship_id, student_id, mentor_id),
  CONSTRAINT ck_mentorship_ended CHECK ((status = 'active') = (ended_at IS NULL))
);
CREATE UNIQUE INDEX uq_active_pair ON mentorships (student_id, mentor_id) WHERE status = 'active';
CREATE INDEX ix_mentorship_mentor ON mentorships (mentor_id, status);
CREATE INDEX ix_mentorship_student ON mentorships (student_id, status);

CREATE TABLE availability_slots (
  slot_id UUID NOT NULL DEFAULT gen_random_uuid(),
  mentor_id UUID NOT NULL,
  start_time TIMESTAMPTZ NOT NULL,
  end_time TIMESTAMPTZ NOT NULL CHECK (end_time > start_time AND end_time - start_time <= interval '4 hours'),
  is_available BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (slot_id),
  FOREIGN KEY (mentor_id) REFERENCES mentor_profiles (user_id) ON DELETE RESTRICT,
  CONSTRAINT ex_slot_no_overlap EXCLUDE USING gist (mentor_id WITH =, tstzrange(start_time, end_time) WITH &&)
);
CREATE INDEX ix_slots_open ON availability_slots (mentor_id, start_time) WHERE is_available;

CREATE TABLE sessions (
  session_id UUID NOT NULL DEFAULT gen_random_uuid(),
  mentorship_id UUID NOT NULL,
  student_id UUID NOT NULL,
  mentor_id UUID NOT NULL,
  slot_id UUID,
  scheduled_start TIMESTAMPTZ NOT NULL,
  scheduled_end TIMESTAMPTZ NOT NULL CHECK (scheduled_end > scheduled_start),
  meeting_mode VARCHAR(20) NOT NULL DEFAULT 'online' CHECK (meeting_mode IN ('online', 'phone', 'in_person')),
  meeting_link TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
  notes TEXT CHECK (char_length(notes) <= 4000),
  cancelled_by UUID,
  cancel_reason TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (session_id),
  FOREIGN KEY (mentorship_id) REFERENCES mentorships (mentorship_id) ON DELETE RESTRICT,
  FOREIGN KEY (slot_id) REFERENCES availability_slots (slot_id) ON DELETE SET NULL,
  FOREIGN KEY (cancelled_by) REFERENCES users (user_id) ON DELETE SET NULL,
  CONSTRAINT fk_session_mentorship FOREIGN KEY (mentorship_id, student_id, mentor_id) REFERENCES mentorships (mentorship_id, student_id, mentor_id),
  CONSTRAINT ex_session_mentor_no_overlap EXCLUDE USING gist (mentor_id WITH =, tstzrange(scheduled_start, scheduled_end) WITH &&) WHERE (status = 'scheduled'),
  CONSTRAINT ex_session_student_no_overlap EXCLUDE USING gist (student_id WITH =, tstzrange(scheduled_start, scheduled_end) WITH &&) WHERE (status = 'scheduled'),
  CONSTRAINT ck_session_cancel CHECK (status = 'cancelled' OR (cancelled_by IS NULL AND cancel_reason IS NULL))
);
CREATE UNIQUE INDEX uq_session_slot_booked ON sessions (slot_id) WHERE status = 'scheduled';
CREATE INDEX ix_sessions_mentorship ON sessions (mentorship_id, scheduled_start);
CREATE INDEX ix_sessions_mentor_time ON sessions (mentor_id, scheduled_start) WHERE status = 'scheduled';
CREATE INDEX ix_sessions_student_time ON sessions (student_id, scheduled_start) WHERE status = 'scheduled';

CREATE TABLE feedback (
  feedback_id UUID NOT NULL DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL,
  submitted_by UUID NOT NULL,
  rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comments TEXT CHECK (char_length(comments) <= 1000),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (feedback_id),
  FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE RESTRICT,
  FOREIGN KEY (submitted_by) REFERENCES users (user_id) ON DELETE RESTRICT,
  CONSTRAINT uq_feedback_once UNIQUE (session_id, submitted_by)
);

CREATE TABLE notifications (
  notification_id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  title VARCHAR(150) NOT NULL,
  message TEXT NOT NULL,
  notification_type VARCHAR(50) NOT NULL CHECK (notification_type IN ('request_received', 'request_accepted', 'request_declined', 'request_cancelled', 'request_expired', 'mentorship_ended', 'session_scheduled', 'session_cancelled', 'session_reminder', 'feedback_requested', 'mentor_reviewed', 'account_status_changed')),
  related_entity_type VARCHAR(50),
  related_entity_id UUID,
  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (notification_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT ck_notification_read CHECK (is_read = (read_at IS NOT NULL))
);
CREATE INDEX ix_notifications_user ON notifications (user_id, is_read, created_at DESC);

CREATE TABLE audit_logs (
  audit_id UUID NOT NULL DEFAULT gen_random_uuid(),
  actor_user_id UUID,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  entity_id UUID NOT NULL,
  details JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (audit_id),
  FOREIGN KEY (actor_user_id) REFERENCES users (user_id) ON DELETE SET NULL
);
CREATE INDEX ix_audit_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX ix_audit_actor ON audit_logs (actor_user_id, created_at DESC);
CREATE INDEX ix_audit_time ON audit_logs (created_at);

CREATE TABLE mentor_interests (
  mentor_profile_id UUID NOT NULL,
  interest_id UUID NOT NULL,
  PRIMARY KEY (mentor_profile_id, interest_id),
  FOREIGN KEY (mentor_profile_id) REFERENCES mentor_profiles (mentor_profile_id) ON DELETE CASCADE,
  FOREIGN KEY (interest_id) REFERENCES career_interests (interest_id) ON DELETE RESTRICT
);
CREATE INDEX ix_mentor_interests_interest ON mentor_interests (interest_id);

CREATE TABLE refresh_tokens (
  token_id UUID NOT NULL DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  family_id UUID NOT NULL,
  token_hash CHAR(64) NOT NULL UNIQUE,
  issued_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL CHECK (expires_at > issued_at),
  revoked_at TIMESTAMPTZ,
  revoked_reason VARCHAR(30) CHECK (revoked_reason IS NULL OR revoked_reason IN ('rotated', 'logout', 'reuse_detected', 'password_change', 'admin_action')),
  PRIMARY KEY (token_id),
  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT ck_token_revoked CHECK ((revoked_at IS NULL) = (revoked_reason IS NULL))
);
CREATE INDEX ix_refresh_user_live ON refresh_tokens (user_id) WHERE revoked_at IS NULL;
CREATE INDEX ix_refresh_family ON refresh_tokens (family_id);

-- ---------------------------------------------------------------------------
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
