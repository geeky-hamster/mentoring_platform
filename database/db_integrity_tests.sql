-- Database integrity tests for the proposed schema (run after schema.sql on an empty database).
-- Each test prints PASS/FAIL via RAISE NOTICE. Executed against PostgreSQL 16 while preparing the report.
\set ON_ERROR_STOP off
SET client_min_messages = notice;

CREATE OR REPLACE FUNCTION expect_fail(test_id text, stmt text, expected_state text) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE NOTICE 'FAIL % (statement succeeded but should have been rejected)', test_id;
EXCEPTION WHEN OTHERS THEN
  IF SQLSTATE = expected_state THEN RAISE NOTICE 'PASS % (rejected with SQLSTATE %)', test_id, SQLSTATE;
  ELSE RAISE NOTICE 'FAIL % (got SQLSTATE % - %)', test_id, SQLSTATE, SQLERRM; END IF;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION expect_ok(test_id text, stmt text) RETURNS void AS $$
BEGIN
  EXECUTE stmt;
  RAISE NOTICE 'PASS % (accepted)', test_id;
EXCEPTION WHEN OTHERS THEN
  RAISE NOTICE 'FAIL % (unexpected error % - %)', test_id, SQLSTATE, SQLERRM;
END; $$ LANGUAGE plpgsql;

-- ---- fixtures -------------------------------------------------------------
INSERT INTO users (user_id, full_name, email, password_hash, role) VALUES
 ('00000000-0000-4000-8000-000000000001','Admin One','admin@example.org','x','admin'),
 ('00000000-0000-4000-8000-0000000000a1','Student A','a@example.org','x','student'),
 ('00000000-0000-4000-8000-0000000000a2','Student B','b@example.org','x','student'),
 ('00000000-0000-4000-8000-0000000000a3','Student C','c@example.org','x','student'),
 ('00000000-0000-4000-8000-0000000000b1','Mentor X','x@example.org','x','mentor'),
 ('00000000-0000-4000-8000-0000000000b2','Mentor Y','y@example.org','x','mentor');
INSERT INTO student_profiles (user_id) VALUES
 ('00000000-0000-4000-8000-0000000000a1'),('00000000-0000-4000-8000-0000000000a2'),('00000000-0000-4000-8000-0000000000a3');
INSERT INTO mentor_profiles (user_id, professional_title, organisation, experience_years, bio, profile_status, reviewed_by, max_active_mentees) VALUES
 ('00000000-0000-4000-8000-0000000000b1','Data Scientist','Example Co',3,'bio','approved','00000000-0000-4000-8000-000000000001',1),
 ('00000000-0000-4000-8000-0000000000b2','Engineer','Example Co',5,'bio','approved','00000000-0000-4000-8000-000000000001',3);

-- ---- users ----------------------------------------------------------------
SELECT expect_fail('DB-01 duplicate e-mail', $$INSERT INTO users (full_name,email,password_hash,role) VALUES ('Dup','a@example.org','x','student')$$, '23505');
SELECT expect_fail('DB-02 upper-case e-mail rejected', $$INSERT INTO users (full_name,email,password_hash,role) VALUES ('Up','UP@Example.org','x','student')$$, '23514');
SELECT expect_fail('DB-03 invalid role', $$INSERT INTO users (full_name,email,password_hash,role) VALUES ('R','r@example.org','x','teacher')$$, '23514');

-- ---- role/profile consistency ---------------------------------------------
SELECT expect_fail('DB-04 student profile for a mentor user', $$INSERT INTO student_profiles (user_id) VALUES ('00000000-0000-4000-8000-0000000000b1')$$, '23503');
SELECT expect_fail('DB-05 second student profile for same user', $$INSERT INTO student_profiles (user_id) VALUES ('00000000-0000-4000-8000-0000000000a1')$$, '23505');
SELECT expect_fail('DB-06 mentor profile for a student user', $$INSERT INTO mentor_profiles (user_id) VALUES ('00000000-0000-4000-8000-0000000000a1')$$, '23503');
SELECT expect_fail('DB-07 approve incomplete mentor profile', $$UPDATE mentor_profiles SET professional_title = NULL WHERE user_id = '00000000-0000-4000-8000-0000000000b2'$$, '23514');

-- ---- requests -------------------------------------------------------------
SELECT expect_ok('DB-08 first pending request', $$INSERT INTO mentoring_requests (request_id, student_id, mentor_id, career_goal) VALUES ('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','I want to move into data science roles after graduating.')$$);
SELECT expect_fail('DB-09 duplicate pending request', $$INSERT INTO mentoring_requests (student_id, mentor_id, career_goal) VALUES ('00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','Second request to the same mentor, still pending.')$$, '23505');
SELECT expect_fail('DB-10 request to a student as mentor', $$INSERT INTO mentoring_requests (student_id, mentor_id, career_goal) VALUES ('00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000a2','Mentor id actually belongs to a student account.')$$, '23503');
SELECT expect_fail('DB-11 career_goal too short', $$INSERT INTO mentoring_requests (student_id, mentor_id, career_goal) VALUES ('00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1','short')$$, '23514');
SELECT expect_fail('DB-12 accepted without responded_at', $$UPDATE mentoring_requests SET status='accepted' WHERE request_id='10000000-0000-4000-8000-000000000001'$$, '23514');

-- ---- mentorship creation only after acceptance ----------------------------
SELECT expect_fail('DB-13 mentorship from a pending request', $$INSERT INTO mentorships (request_id, student_id, mentor_id) VALUES ('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1')$$, '23514');
UPDATE mentoring_requests SET status='accepted', responded_at=now() WHERE request_id='10000000-0000-4000-8000-000000000001';
SELECT expect_fail('DB-14 mentorship with mismatched student', $$INSERT INTO mentorships (request_id, student_id, mentor_id) VALUES ('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1')$$, '23503');
SELECT expect_ok('DB-15 mentorship from accepted request', $$INSERT INTO mentorships (mentorship_id, request_id, student_id, mentor_id) VALUES ('20000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1')$$);
UPDATE mentor_profiles SET max_active_mentees = 3 WHERE user_id = '00000000-0000-4000-8000-0000000000b1';  -- isolate the UNIQUE(request_id) rule from the capacity trigger
SELECT expect_fail('DB-16 second mentorship for the same request', $$INSERT INTO mentorships (request_id, student_id, mentor_id) VALUES ('10000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1')$$, '23505');

UPDATE mentor_profiles SET max_active_mentees = 1 WHERE user_id = '00000000-0000-4000-8000-0000000000b1';
-- ---- capacity (mentor X has max_active_mentees = 1) -----------------------
INSERT INTO mentoring_requests (request_id, student_id, mentor_id, career_goal, status, responded_at) VALUES ('10000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1','Second student wants the same mentor, who is full.','accepted',now());
SELECT expect_fail('DB-17 capacity exceeded', $$INSERT INTO mentorships (request_id, student_id, mentor_id) VALUES ('10000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1')$$, '23514');
SELECT expect_fail('DB-18 ended_at missing on ended mentorship', $$UPDATE mentorships SET status='ended' WHERE mentorship_id='20000000-0000-4000-8000-000000000001'$$, '23514');

-- ---- availability slots ---------------------------------------------------
SELECT expect_ok('DB-19 slot 1', $$INSERT INTO availability_slots (slot_id, mentor_id, start_time, end_time) VALUES ('30000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000b1','2030-01-07 10:00+00','2030-01-07 11:00+00')$$);
SELECT expect_fail('DB-20 overlapping slot', $$INSERT INTO availability_slots (mentor_id, start_time, end_time) VALUES ('00000000-0000-4000-8000-0000000000b1','2030-01-07 10:30+00','2030-01-07 11:30+00')$$, '23P01');
SELECT expect_ok('DB-21 adjacent slot allowed', $$INSERT INTO availability_slots (slot_id, mentor_id, start_time, end_time) VALUES ('30000000-0000-4000-8000-000000000002','00000000-0000-4000-8000-0000000000b1','2030-01-07 11:00+00','2030-01-07 12:00+00')$$);
SELECT expect_fail('DB-22 end before start', $$INSERT INTO availability_slots (mentor_id, start_time, end_time) VALUES ('00000000-0000-4000-8000-0000000000b1','2030-01-08 12:00+00','2030-01-08 11:00+00')$$, '23514');

-- ---- sessions -------------------------------------------------------------
SELECT expect_ok('DB-23 session booked on slot 1', $$INSERT INTO sessions (session_id, mentorship_id, student_id, mentor_id, slot_id, scheduled_start, scheduled_end) VALUES ('40000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','30000000-0000-4000-8000-000000000001','2030-01-07 10:00+00','2030-01-07 11:00+00')$$);
SELECT expect_fail('DB-24 same slot booked twice', $$INSERT INTO sessions (mentorship_id, student_id, mentor_id, slot_id, scheduled_start, scheduled_end) VALUES ('20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','30000000-0000-4000-8000-000000000001','2030-01-07 10:00+00','2030-01-07 11:00+00')$$, '23P01');
SELECT expect_fail('DB-25 overlapping ad-hoc session (mentor conflict)', $$INSERT INTO sessions (mentorship_id, student_id, mentor_id, scheduled_start, scheduled_end) VALUES ('20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','2030-01-07 10:30+00','2030-01-07 11:30+00')$$, '23P01');
SELECT expect_fail('DB-26 session parties differ from mentorship', $$INSERT INTO sessions (mentorship_id, student_id, mentor_id, scheduled_start, scheduled_end) VALUES ('20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a2','00000000-0000-4000-8000-0000000000b1','2030-02-01 10:00+00','2030-02-01 11:00+00')$$, '23503');
UPDATE sessions SET status='cancelled', cancelled_by='00000000-0000-4000-8000-0000000000a1', cancel_reason='clash' WHERE session_id='40000000-0000-4000-8000-000000000001';
SELECT expect_ok('DB-27 cancelled session frees the time and slot', $$INSERT INTO sessions (mentorship_id, student_id, mentor_id, slot_id, scheduled_start, scheduled_end) VALUES ('20000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-0000000000a1','00000000-0000-4000-8000-0000000000b1','30000000-0000-4000-8000-000000000001','2030-01-07 10:00+00','2030-01-07 11:00+00')$$);
SELECT expect_fail('DB-28 cancel data on non-cancelled session', $$UPDATE sessions SET cancel_reason='x' WHERE status='scheduled'$$, '23514');

-- ---- feedback -------------------------------------------------------------
UPDATE sessions SET status='completed' WHERE status='scheduled';
SELECT expect_ok('DB-29 feedback by student', $$INSERT INTO feedback (session_id, submitted_by, rating, comments) SELECT session_id, '00000000-0000-4000-8000-0000000000a1', 5, 'Helpful' FROM sessions WHERE status='completed' LIMIT 1$$);
SELECT expect_fail('DB-30 second feedback by same user', $$INSERT INTO feedback (session_id, submitted_by, rating) SELECT session_id, '00000000-0000-4000-8000-0000000000a1', 4 FROM sessions WHERE status='completed' LIMIT 1$$, '23505');
SELECT expect_fail('DB-31 rating out of range', $$INSERT INTO feedback (session_id, submitted_by, rating) SELECT session_id, '00000000-0000-4000-8000-0000000000b1', 6 FROM sessions WHERE status='completed' LIMIT 1$$, '23514');

-- ---- notifications, tokens ------------------------------------------------
SELECT expect_fail('DB-32 read flag without timestamp', $$INSERT INTO notifications (user_id,title,message,notification_type,is_read) VALUES ('00000000-0000-4000-8000-0000000000a1','t','m','request_received',true)$$, '23514');
SELECT expect_fail('DB-33 unknown notification type', $$INSERT INTO notifications (user_id,title,message,notification_type) VALUES ('00000000-0000-4000-8000-0000000000a1','t','m','spam')$$, '23514');
SELECT expect_ok('DB-34 refresh token stored as hash', $$INSERT INTO refresh_tokens (user_id, family_id, token_hash, expires_at) VALUES ('00000000-0000-4000-8000-0000000000a1', gen_random_uuid(), repeat('a',64), now() + interval '7 days')$$);
SELECT expect_fail('DB-35 duplicate token hash', $$INSERT INTO refresh_tokens (user_id, family_id, token_hash, expires_at) VALUES ('00000000-0000-4000-8000-0000000000a1', gen_random_uuid(), repeat('a',64), now() + interval '7 days')$$, '23505');

-- ---- junction tables ------------------------------------------------------
INSERT INTO skills (skill_name, category) VALUES ('Python','Programming');
INSERT INTO career_interests (interest_name) VALUES ('Data Science');
SELECT expect_ok('DB-36 student skill', $$INSERT INTO student_skills (student_profile_id, skill_id, proficiency_level) SELECT sp.student_profile_id, s.skill_id, 'intermediate' FROM student_profiles sp, skills s LIMIT 1$$);
SELECT expect_fail('DB-37 duplicate junction row (composite PK)', $$INSERT INTO student_skills (student_profile_id, skill_id, proficiency_level) SELECT student_profile_id, skill_id, 'advanced' FROM student_skills LIMIT 1$$, '23505');
SELECT expect_fail('DB-38 delete skill still referenced (RESTRICT)', $$DELETE FROM skills$$, '23503');
SELECT expect_ok('DB-39 mentor interest (added table)', $$INSERT INTO mentor_interests (mentor_profile_id, interest_id) SELECT mp.mentor_profile_id, ci.interest_id FROM mentor_profiles mp, career_interests ci LIMIT 1$$);
