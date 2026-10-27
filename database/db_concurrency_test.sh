#!/usr/bin/env bash
# Concurrent request acceptance: two mentors' pending requests are accepted at the same moment for a mentor
# whose capacity is 1. Exactly one mentorship must be created (row lock on mentor_profiles + capacity check).
# Usage: PSQL="psql -h <socket-dir> -p <port> -U postgres -q" ./db_concurrency_test.sh <database>
set -u
DB=${1:-mp}; PSQL=${PSQL:-psql}
$PSQL -d "$DB" <<'SQL'
TRUNCATE feedback, sessions, availability_slots, mentorships, mentoring_requests, mentor_interests, mentor_expertise, mentor_profiles, student_interests, student_skills, student_profiles, notifications, audit_logs, refresh_tokens, users CASCADE;
INSERT INTO users (user_id, full_name, email, password_hash, role) VALUES
 ('00000000-0000-4000-8000-000000000001','Admin','admin@example.org','x','admin'),
 ('00000000-0000-4000-8000-0000000000a1','Student A','a@example.org','x','student'),
 ('00000000-0000-4000-8000-0000000000a2','Student B','b@example.org','x','student'),
 ('00000000-0000-4000-8000-0000000000b1','Mentor X','x@example.org','x','mentor');
INSERT INTO student_profiles (user_id) VALUES ('00000000-0000-4000-8000-0000000000a1'),('00000000-0000-4000-8000-0000000000a2');
INSERT INTO mentor_profiles (user_id, professional_title, organisation, experience_years, bio, profile_status, reviewed_by, max_active_mentees)
 VALUES ('00000000-0000-4000-8000-0000000000b1','T','O',3,'b','approved','00000000-0000-4000-8000-000000000001',1);
INSERT INTO mentoring_requests (request_id, student_id, mentor_id, career_goal) VALUES
 ('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','Student A wants guidance on data science careers.'),
 ('10000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1','Student B wants guidance on research careers.');
SQL
accept() {  # $1 = request id; mirrors the service-layer transaction described in Section 7.5
$PSQL -d "$DB" <<SQL 2>&1 | sed "s/^/[$1] /"
BEGIN;
SELECT 1 FROM mentoring_requests WHERE request_id='$1' AND status='pending' FOR UPDATE;
SELECT 1 FROM mentor_profiles WHERE user_id='00000000-0000-4000-8000-0000000000b1' FOR UPDATE;
SELECT pg_sleep(1.5);
DO \$\$ DECLARE cur int; cap int; BEGIN
  SELECT max_active_mentees INTO cap FROM mentor_profiles WHERE user_id='00000000-0000-4000-8000-0000000000b1';
  SELECT count(*) INTO cur FROM mentorships WHERE mentor_id='00000000-0000-4000-8000-0000000000b1' AND status='active';
  IF cur >= cap THEN RAISE NOTICE 'REJECTED: mentor at capacity (409 MENTOR_AT_CAPACITY)'; RETURN; END IF;
  UPDATE mentoring_requests SET status='accepted', responded_at=now() WHERE request_id='$1';
  INSERT INTO mentorships (request_id, student_id, mentor_id) SELECT request_id, student_id, mentor_id FROM mentoring_requests WHERE request_id='$1';
  RAISE NOTICE 'ACCEPTED: mentorship created';
END \$\$;
COMMIT;
SQL
}
accept 10000000-0000-4000-8000-000000000001 &
accept 10000000-0000-4000-8000-000000000002 &
wait
$PSQL -d "$DB" -At -c "SELECT 'active mentorships for mentor X (capacity 1) = ' || count(*) FROM mentorships WHERE status='active'"
