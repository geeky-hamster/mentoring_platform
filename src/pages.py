"""Page inventory (26 pages), shared components, workflow step catalogue and user stories.
Single source for: Section 4 page specs, the navigation map, and the traceability matrix."""

# ---------------- workflow step catalogue (Section 2) ----------------
WF = {
    "S1": ("Student", "Register an account (and verify the e-mail when the optional extension is on)", ["E01", "E07"]),
    "S3": ("Student", "Complete onboarding profile (stage, skills, interests, goals)", ["E10", "E11", "E12", "E13"]),
    "S4": ("Student", "Discover mentors: search, filter, view recommendations", ["E22", "E23"]),
    "S5": ("Student", "View a mentor's profile", ["E16"]),
    "S6": ("Student", "Submit a mentoring request", ["E24"]),
    "S7": ("Student", "Track requests, cancel a pending request, receive decisions", ["E25", "E26", "E29", "E42"]),
    "S8": ("Student", "Begin mentorship (accepted request becomes a mentorship)", ["E30", "E31"]),
    "S9": ("Student", "Schedule a session in an open slot", ["E21", "E34"]),
    "S10": ("Student", "Attend, review history, cancel, give feedback", ["E33", "E36", "E37", "E38", "E39"]),
    "S11": ("Student", "End or complete a mentorship", ["E32"]),
    "S12": ("Student", "Maintain account: edit profile, change password, read notifications", ["E13", "E09", "E42", "E43", "E44"]),
    "M1": ("Mentor", "Register an account", ["E01"]),
    "M2": ("Mentor", "Complete professional profile", ["E14", "E15"]),
    "M3": ("Mentor", "Configure expertise, pathways and availability", ["E10", "E11", "E15", "E17", "E18", "E19", "E20"]),
    "M4": ("Mentor", "Submit profile for review and see the decision", ["E15", "E41"]),
    "M5": ("Mentor", "Review incoming requests", ["E25", "E26"]),
    "M6": ("Mentor", "Accept or decline a request", ["E27", "E28"]),
    "M7": ("Mentor", "Manage mentees and close mentorships", ["E30", "E31", "E32"]),
    "M8": ("Mentor", "Manage sessions: schedule, complete, cancel, notes", ["E34", "E35", "E37"]),
    "M9": ("Mentor", "Give session feedback", ["E38"]),
    "M10": ("Mentor", "Adjust capacity and accepting-mentees switch", ["E15"]),
    "A2": ("Administrator", "Review and approve or reject mentor applications", ["E47", "E48", "E16"]),
    "A3": ("Administrator", "Manage users (suspend, reactivate)", ["E45", "E46"]),
    "A4": ("Administrator", "Oversee mentoring relationships and stale requests", ["E49", "E50", "E32", "E31"]),
    "A5": ("Administrator", "Review participation metrics", ["E51", "E52"]),
    "A6": ("Administrator", "Analyse programme effectiveness and export reports", ["E51", "E52", "E53"]),
    "A7": ("Administrator", "Maintain skill and career-interest catalogues", ["E55", "E56", "E57", "E58"]),
    "A8": ("Administrator", "Review the audit trail", ["E54"]),
    "X0": ("Shared", "Sign in, keep the session alive (refresh) and sign out; admins use a seeded account", ["E02", "E03", "E04", "E08"]),
    "X1": ("Shared", "Recover a forgotten password", ["E05", "E06"]),
    "X2": ("Shared", "Handle expired sessions, denied access and errors", ["E03", "E08"]),
}

# ---------------- shared UI components / modals ----------------
SHARED = [
    ("AppShell", "Top bar (product name, notification bell with unread badge, user menu with Sign out) plus a role-specific left sidebar; wraps every authenticated page."),
    ("StatusBadge", "Colour + text label for statuses (pending, accepted, declined, cancelled, expired, active, completed, ended, scheduled, approved ...). Never colour alone."),
    ("FilterBar / Pagination", "Reusable list controls bound to the page, page_size, filter and sort query parameters."),
    ("DataTable / CardGrid", "Responsive list presentations: table on desktop, stacked cards on mobile."),
    ("ReasonDialog", "Modal asking for an optional or required reason (decline, cancel, end, suspend, reject) before calling the API."),
    ("ConfirmDialog", "Modal for irreversible actions (accept request, end mentorship, delete slot)."),
    ("FeedbackDialog", "Modal with 1-5 star rating and optional comment (students and mentors)."),
    ("BookingDialog", "Modal listing a mentor's open slots (E21) with meeting mode and link fields; creates a session (E34)."),
    ("SlotEditorDialog", "Modal to add single slots or a weekly recurrence (E18) or edit one slot (E19)."),
    ("RequestDrawer", "Side drawer showing request detail for students (E26); mentors use the full page 17."),
    ("EmptyState / ErrorState / Skeleton", "Standard placeholders: icon + message + primary action; error banner with retry; grey skeleton rows while loading."),
    ("Toast", "Transient confirmation or non-blocking error message."),
]

# ---------------- sidebars per role ----------------
SIDEBAR = {
    "student": [("Dashboard", 6), ("Find mentors", 7), ("My requests", 10), ("My mentorship", 11), ("Notifications", 14), ("Profile", 13)],
    "mentor": [("Dashboard", 15), ("Requests", 16), ("My mentees", 18), ("Schedule", 19), ("Profile", 20), ("Notifications", 21)],
    "admin": [("Dashboard", 22), ("Users", 23), ("Mentor reviews", 24), ("Mentorships", 25), ("Analytics", 26)],
}

# ---------------- pages ----------------
PAGES = []


def pg(num, title, role, route, purpose, elements, actions, endpoints, empty, error, tabs=None, group=None):
    PAGES.append(dict(num=num, title=title, role=role, route=route, purpose=purpose, elements=elements, actions=actions,
                      endpoints=endpoints, empty=empty, error=error, tabs=tabs or [], group=group))


# action tuple: (label, kind, target, endpoints, workflow_step)   kind: nav | modal | api
pg(1, "Login", "Public", "/login", "Authenticate an existing user and send them to the correct home page.",
   [("E-mail field", "Required, valid e-mail format; focus on load."),
    ("Password field", "Required; show/hide toggle."),
    ("Sign in button", "Calls E02; shows a spinner and disables itself while the request runs."),
    ("Forgot password link", "Opens page 3."),
    ("Create account link", "Opens page 2."),
    ("Error banner", "Shows INVALID_CREDENTIALS, ACCOUNT_SUSPENDED or RATE_LIMITED messages without revealing which field was wrong.")],
   [("Sign in", "api", None, ["E02", "E08"], "X0"), ("Forgot password", "nav", 3, [], "X1"), ("Create account", "nav", 2, [], "S1"),
    ("Verify e-mail link (optional extension)", "api", None, ["E07"], "S1")],
   ["E02", "E08", "E07"], "Not applicable.", "401 generic banner; 403 'account suspended, contact the programme office'; 429 'too many attempts, try again later'; network error banner with retry.",
   group="Shared")
pg(2, "Registration", "Public", "/register", "Create a student or mentor account.",
   [("Full name field", "Required, 1-120 characters."),
    ("E-mail field", "Required; uniqueness is checked by the server (E01)."),
    ("Password field", "Minimum 10 characters; strength hint; show/hide."),
    ("Role selector", "Segmented control: Student or Mentor (admin is not offered)."),
    ("Privacy notice checkbox", "Required before submitting."),
    ("Create account button", "Calls E01, then signs in (E02) and redirects: student to page 5, mentor to page 20."),
    ("Mentor approval hint", "Informational text: mentor profiles appear in search only after admin approval.")],
   [("Create account", "api", None, ["E01", "E02"], "S1"), ("Already registered? Sign in", "nav", 1, [], "X0")],
   ["E01", "E02"], "Not applicable.", "409 'e-mail already registered' under the e-mail field; 422 field-level messages; 429 banner.", group="Shared")
pg(3, "Forgot / reset password", "Public", "/forgot-password and /reset-password?token=", "Recover access: request a reset link, then set a new password.",
   [("Step 1: e-mail field", "Valid e-mail required."),
    ("Send reset link button", "Calls E05; always shows the same confirmation text."),
    ("Confirmation message", "'If the address is registered, a link has been sent' (no account enumeration)."),
    ("Step 2: new password field", "Minimum 10 characters; shown when the page is opened with a token."),
    ("Confirm password field", "Must match the new password."),
    ("Set password button", "Calls E06; on success redirects to page 1 with a toast.")],
   [("Send reset link", "api", None, ["E05"], "X1"), ("Set password", "api", None, ["E06"], "X1"), ("Back to sign in", "nav", 1, [], "X0")],
   ["E05", "E06"], "Not applicable.", "400 INVALID_TOKEN shows 'link expired or already used' with a button to request a new one; 422 inline; 429 banner.",
   tabs=["Request link (no token)", "Set new password (token present)"], group="Shared")
pg(4, "Access denied / error", "Any", "/403, /404, /500, /session-expired", "One ErrorPage component for all dead ends, with a safe way out.",
   [("Status code and heading", "401 session expired, 403 access denied, 404 not found, 500 or network error."),
    ("Explanation text", "Plain-language reason and what the user can do."),
    ("Primary button", "Sign in again (401) or Go to my dashboard (403/404/500)."),
    ("Secondary button", "Go back (browser history) or Retry (network error)."),
    ("Reference line", "Shows the request_id from the error response for support.")],
   [("Go to my dashboard", "nav", None, ["E08"], "X2"), ("Sign in again", "nav", 1, ["E03"], "X2")],
   ["E08", "E03"], "Not applicable.", "If E08 itself fails the button falls back to the login page.", group="Shared")

pg(5, "Student onboarding and profile setup", "Student", "/student/onboarding",
   "Collect the minimum profile needed for matching and for requests; gates the request feature until complete.",
   [("Step indicator", "Three steps: About you, Skills, Career interests and goals; completed steps are clickable."),
    ("Programme stage and graduation year", "Select from the four programme levels; year is optional."),
    ("Bio field", "Optional, up to 1000 characters with counter."),
    ("Skill picker", "Search the catalogue (E10), choose a level per skill, star up to 5 focus skills."),
    ("Career interest chips", "Multi-select from E11 (at least one required to finish)."),
    ("Goals and guidance needs", "Free text up to 2000 characters each; career goals required to finish."),
    ("Back / Save and continue", "Saves the step with E13; Finish sets profile_completed and opens page 6.")],
   [("Save and continue", "api", None, ["E13"], "S3"), ("Finish", "nav", 6, ["E13"], "S3")],
   ["E12", "E13", "E10", "E11", "E08"], "Empty catalogue: 'No skills available yet. Please contact the programme office.'",
   "422 messages next to fields; draft is kept if the request fails; leaving the page asks for confirmation when there are unsaved changes.",
   tabs=["Step 1 About you", "Step 2 Skills", "Step 3 Interests and goals"], group="Student")
pg(6, "Student dashboard", "Student", "/student/dashboard", "At-a-glance status: next steps, requests, mentorship, sessions and recommendations.",
   [("Profile completeness banner", "Shown until profile_completed; links to page 5."),
    ("Summary cards", "Pending requests, active mentorships, upcoming sessions (each links to its page)."),
    ("Next session card", "Date, mentor, mode, join link; button opens page 11."),
    ("Recommended mentors", "Top three matches with score and reasons; 'See all' opens page 7."),
    ("My requests list", "Latest three requests with status badges; opens page 10."),
    ("Notification peek", "Latest three notifications; opens page 14.")],
   [("Complete profile", "nav", 5, [], "S3"), ("Sign out (user menu)", "nav", 1, ["E04"], "X0"), ("See all recommendations", "nav", 7, ["E23"], "S4"), ("View my requests", "nav", 10, ["E25"], "S7"),
    ("Open mentorship", "nav", 11, ["E31"], "S8"), ("View notifications", "nav", 14, ["E42"], "S12")],
   ["E40", "E23", "E25"], "No mentorship yet: card 'Find your first mentor' with button to page 7. No recommendations: prompt to add skills and interests.",
   "Each panel loads independently with a skeleton; a failed panel shows a retry link instead of blocking the page.", group="Student")
pg(7, "Mentor discovery and search", "Student", "/student/mentors", "Find suitable mentors by recommendation or by searching and filtering the directory.",
   [("Tabs", "Recommended (ranked by match score) and All mentors (directory)."),
    ("Keyword search", "Searches title, organisation and bio (E22 q)."),
    ("Filter panel", "Skills, career pathways, mentor type, minimum experience, 'accepting mentees' switch; Apply and Clear."),
    ("Sort control", "Newest, experience or name (All tab); the Recommended tab is always score-ordered."),
    ("Mentor card", "Name, title and organisation, experience, top skills, accepting badge; match score badge (0-100, not a probability) on the Recommended tab."),
    ("View profile button", "Opens page 8."),
    ("Request button", "Opens page 9 directly."),
    ("Pagination", "Page controls and page size (default 10).")],
   [("Apply filters", "api", None, ["E22"], "S4"), ("View profile", "nav", 8, ["E16"], "S5"), ("Request mentoring", "nav", 9, [], "S6"),
    ("Open Recommended tab", "api", None, ["E23"], "S4")],
   ["E22", "E23", "E10", "E11"], "'No mentors match your filters' with a Clear filters button. Recommended tab with incomplete profile: banner to page 5; no eligible mentors: suggest widening interests.",
   "Failed search shows an inline error with Retry and keeps the filters; 409 PROFILE_INCOMPLETE on Recommended shows the banner.",
   tabs=["Recommended", "All mentors"], group="Student")
pg(8, "Mentor details", "Student", "/student/mentors/:mentor_id", "Let the student judge fit before requesting: background, expertise, pathways, ratings and capacity.",
   [("Header", "Name, title, organisation, mentor type, years of experience, accepting badge."),
    ("About section", "Mentor bio."),
    ("Expertise chips", "Skills with level labels."),
    ("Career pathway chips", "Pathways the mentor can advise on."),
    ("Rating summary", "Average rating shown only when at least 3 ratings exist; otherwise 'Not enough ratings yet'."),
    ("Availability and capacity note", "Open slots in the next 14 days (count only) and free mentee spots; exact times appear after a mentorship starts."),
    ("Request mentoring button", "Opens page 9; disabled with an explanation when a pending request, active mentorship, cooldown or full capacity applies."),
    ("Back to results", "Returns to page 7 with filters preserved.")],
   [("Request mentoring", "nav", 9, [], "S6"), ("Back to results", "nav", 7, [], "S4")],
   ["E16"], "Not applicable.", "404 (mentor not visible) shows page 4 variant 'This mentor is not available'; load failure shows retry.", group="Student")
pg(9, "Send mentoring request", "Student", "/student/mentors/:mentor_id/request", "Compose and submit one request to one mentor.",
   [("Mentor summary card", "Read-only name, title, organisation, free spots."),
    ("Career goal field", "Required, 20-1000 characters with live counter."),
    ("Message field", "Optional personal note, up to 1500 characters."),
    ("Profile preview", "What the mentor will see (stage, skills, interests) with an 'Edit profile' link to page 13."),
    ("Rules note", "Requests expire after 14 days; maximum 3 pending requests at a time."),
    ("Send request button", "Calls E24; on success opens page 10 with a toast."),
    ("Cancel link", "Returns to page 8 without saving.")],
   [("Send request", "api", 10, ["E24"], "S6"), ("Edit profile", "nav", 13, [], "S12"), ("Cancel", "nav", 8, [], "S5")],
   ["E24", "E16", "E12"], "Not applicable.",
   "409 codes shown as a banner: DUPLICATE_PENDING_REQUEST, REQUEST_COOLDOWN (with date), PENDING_LIMIT_REACHED, MENTOR_AT_CAPACITY, MENTOR_NOT_AVAILABLE, PROFILE_INCOMPLETE (link to page 5); 422 under the fields.",
   group="Student")
pg(10, "My mentoring requests", "Student", "/student/requests", "Track every request and cancel pending ones.",
   [("Status tabs", "All, Pending, Accepted, Declined, Cancelled or expired, each with a count."),
    ("Requests table", "Mentor, goal excerpt, sent date, status badge and the decision date or expiry."),
    ("View button", "Opens the RequestDrawer (E26) with full goal, message and decline reason."),
    ("Cancel button", "Pending rows only; opens ReasonDialog then calls E29."),
    ("Open mentorship button", "Accepted rows only; opens page 11."),
    ("Pagination", "Standard list pagination.")],
   [("View request", "modal", "RequestDrawer", ["E26"], "S7"), ("Cancel request", "api", None, ["E29"], "S7"), ("Open mentorship", "nav", 11, ["E31"], "S8"),
    ("Find a mentor", "nav", 7, [], "S4")],
   ["E25", "E26", "E29"], "Per tab: 'No pending requests' / 'You have not sent any requests yet' with a Find a mentor button (page 7).",
   "409 INVALID_STATE_TRANSITION on cancel (already decided) refreshes the row and shows a toast; load failure shows retry.",
   tabs=["All", "Pending", "Accepted", "Declined", "Cancelled / expired"], group="Student")
pg(11, "Mentorship details", "Student", "/student/mentorships/:mentorship_id", "Overview of one mentoring relationship and the entry point for scheduling and ending it.",
   [("Mentorship selector", "Dropdown when the student has more than one mentorship (E30)."),
    ("Header", "Mentor card, status badge, start date, link to mentor profile."),
    ("Goal card", "Career goal from the originating request."),
    ("Progress summary", "Sessions completed, sessions scheduled, last session date."),
    ("Upcoming sessions list", "Next sessions with date, mode, join link and a Cancel action."),
    ("Schedule session button", "Opens BookingDialog with the mentor's open slots (E21, E34); disabled when the mentorship is not active."),
    ("End mentorship button", "Opens ReasonDialog; choose 'Completed' or 'Ended early' (E32)."),
    ("Tabs", "Overview and Sessions and feedback (page 12).")],
   [("Schedule session", "modal", "BookingDialog", ["E21", "E34"], "S9"), ("End mentorship", "modal", "ReasonDialog", ["E32"], "S11"),
    ("Sessions and feedback tab", "nav", 12, ["E33"], "S10"), ("View mentor profile", "nav", 8, [], "S5")],
   ["E30", "E31", "E33", "E21", "E34", "E32"], "No open slots: 'Your mentor has no open slots; ask them to add availability'. No mentorship: redirect to page 10 with a message.",
   "409 SLOT_UNAVAILABLE or SESSION_CONFLICT in the dialog refreshes slots; 409 MENTORSHIP_NOT_ACTIVE disables actions; 404 opens page 4.",
   tabs=["Overview", "Sessions and feedback"], group="Student")
pg(12, "Session history and feedback", "Student", "/student/mentorships/:mentorship_id/sessions", "Review past and upcoming sessions, cancel, read notes and rate completed sessions.",
   [("Status filter", "All, Scheduled, Completed, Cancelled."),
    ("Sessions table", "Date and time, mode, status badge, notes preview."),
    ("Notes expander", "Shows shared agenda and outcome notes."),
    ("Cancel button", "Scheduled sessions only; ReasonDialog then E37."),
    ("Rate session button", "Completed sessions within 14 days without feedback; opens FeedbackDialog (E38)."),
    ("Feedback status", "Shows 'Rated 5/5' once submitted; students see their own entry only."),
    ("Schedule session button", "Opens BookingDialog.")],
   [("Cancel session", "api", None, ["E37"], "S10"), ("Rate session", "modal", "FeedbackDialog", ["E38"], "S10"), ("Schedule session", "modal", "BookingDialog", ["E21", "E34"], "S9"),
    ("Back to overview", "nav", 11, [], "S8")],
   ["E33", "E36", "E37", "E38", "E39"], "'No sessions yet' with a Schedule session button.",
   "409 FEEDBACK_NOT_ALLOWED / FEEDBACK_ALREADY_SUBMITTED shown in the dialog; 409 INVALID_STATE_TRANSITION on cancel refreshes the row.", group="Student")
pg(13, "Edit student profile", "Student", "/student/profile", "Maintain profile data used by matching and shown to mentors you request; manage the password.",
   [("Tabs", "Profile, Skills and interests, Account."),
    ("Profile fields", "Name, programme stage, graduation year, bio, career goals, guidance needs."),
    ("Skill editor", "Add or remove skills, set level, star up to 5 focus skills."),
    ("Interest chips", "Add or remove career pathways."),
    ("Password form", "Current password, new password, confirmation (E09)."),
    ("Save changes button", "Calls E13; disabled until something changes; toast on success.")],
   [("Save changes", "api", None, ["E13"], "S12"), ("Change password", "api", None, ["E09"], "S12")],
   ["E12", "E13", "E09", "E10", "E11"], "Not applicable.", "422 inline; wrong current password shown under that field; unsaved-changes warning on navigation.",
   tabs=["Profile", "Skills and interests", "Account"], group="Student")
pg(14, "Notifications (student)", "Student", "/student/notifications", "Read events about requests, sessions and feedback.",
   [("Filter tabs", "All and Unread."),
    ("Notification list", "Unread rows highlighted; icon by type, title, message, time."),
    ("Row click", "Marks the item read (E43) and opens its target (request, mentorship or session)."),
    ("Mark all as read", "Calls E44."),
    ("Pagination", "Standard list pagination.")],
   [("Open notification", "nav", 10, ["E43"], "S7"), ("Mark all as read", "api", None, ["E44"], "S12")],
   ["E42", "E43", "E44"], "'You're all caught up' (Unread tab) / 'No notifications yet' (All tab).", "Load failure shows retry; failed mark-as-read reverts the highlight and shows a toast.",
   tabs=["All", "Unread"], group="Student")

pg(15, "Mentor dashboard", "Mentor", "/mentor/dashboard", "Show review status, workload and what needs attention.",
   [("Profile status banner", "Draft: complete profile; Pending: awaiting approval; Rejected: shows the note and links to page 20; Suspended: contact the office."),
    ("Summary cards", "Pending requests, active mentees against capacity, upcoming sessions, average rating (when at least 3)."),
    ("Accepting mentees switch", "Toggles is_available (E15)."),
    ("Incoming requests preview", "Latest pending requests; opens page 16."),
    ("Upcoming sessions list", "Next sessions with mentee and mode; opens page 19."),
    ("Capacity indicator", "Bar showing active mentees out of max_active_mentees; link to edit in page 20.")],
   [("Sign out (user menu)", "nav", 1, ["E04"], "X0"), ("Review requests", "nav", 16, ["E25"], "M5"), ("View schedule", "nav", 19, ["E35"], "M8"), ("Edit profile", "nav", 20, [], "M2"),
    ("Toggle accepting mentees", "api", None, ["E15"], "M10")],
   ["E41", "E25", "E35", "E15"], "No requests: 'No pending requests'. No sessions: 'Nothing scheduled'. Not yet approved: cards are shown but the banner explains why requests cannot arrive.",
   "Panels load independently with retry; E15 failure reverts the switch and shows a toast.", group="Mentor")
pg(16, "Incoming requests", "Mentor", "/mentor/requests", "Work through mentoring requests addressed to the mentor.",
   [("Status tabs", "Pending, Accepted, Declined, All with counts."),
    ("Requests table", "Student name, programme stage, goal excerpt, received date, time left before expiry."),
    ("View button", "Opens page 17."),
    ("Accept button", "ConfirmDialog then E27; shows capacity after acceptance."),
    ("Decline button", "ReasonDialog (optional reason) then E28."),
    ("Capacity indicator", "'2 of 3 mentee spots used' above the table.")],
   [("View request", "nav", 17, ["E26"], "M5"), ("Accept", "api", None, ["E27"], "M6"), ("Decline", "modal", "ReasonDialog", ["E28"], "M6")],
   ["E25", "E27", "E28", "E41"], "'No pending requests'.",
   "409 MENTOR_AT_CAPACITY banner with link to page 20; 409 INVALID_STATE_TRANSITION (cancelled or expired meanwhile) refreshes the row.",
   tabs=["Pending", "Accepted", "Declined", "All"], group="Mentor")
pg(17, "Request details", "Mentor", "/mentor/requests/:request_id", "Give the mentor enough context about the student to decide.",
   [("Request header", "Student name, status badge, received date, expiry countdown."),
    ("Goal and message", "Full career goal and optional message."),
    ("Student profile summary", "Stage, expected graduation year, bio, goals and guidance needs."),
    ("Skills and interests", "Skills with levels (focus skills marked) and career pathways; overlaps with the mentor highlighted."),
    ("Capacity note", "Free spots now and after accepting."),
    ("Accept button", "ConfirmDialog then E27; on success opens page 18."),
    ("Decline button", "ReasonDialog then E28; returns to page 16.")],
   [("Accept", "nav", 18, ["E27"], "M6"), ("Decline", "nav", 16, ["E28"], "M6"), ("Back to requests", "nav", 16, [], "M5")],
   ["E26", "E27", "E28"], "Not applicable.", "409 MENTOR_AT_CAPACITY and INVALID_STATE_TRANSITION banners; 404 opens page 4.", group="Mentor")
pg(18, "My mentees / active mentorships", "Mentor", "/mentor/mentees", "Manage ongoing mentorships in a list-detail layout.",
   [("Status tabs", "Active and Closed (completed or ended)."),
    ("Mentee list", "Name, stage, start date, sessions completed, next session."),
    ("Detail panel header", "Mentee summary and the goal from the request."),
    ("Sessions list", "Sessions of the selected mentorship with status and notes."),
    ("Schedule session button", "Opens the scheduling dialog (E34 with slot or explicit times)."),
    ("Mark session completed", "Enabled after the start time (E37); then 'Rate' opens FeedbackDialog (E38)."),
    ("Close mentorship button", "ReasonDialog; choose Completed or Ended (E32).")],
   [("Schedule session", "modal", "BookingDialog", ["E34"], "M8"), ("Mark completed", "api", None, ["E37"], "M8"), ("Rate session", "modal", "FeedbackDialog", ["E38"], "M9"),
    ("Close mentorship", "modal", "ReasonDialog", ["E32"], "M7")],
   ["E30", "E31", "E33", "E34", "E37", "E38", "E32"], "'No active mentees yet' with a link to page 16.",
   "409 SESSION_CONFLICT or SLOT_UNAVAILABLE in the dialog; 409 MENTORSHIP_NOT_ACTIVE disables scheduling.",
   tabs=["Active", "Closed"], group="Mentor")
pg(19, "Session and availability management", "Mentor", "/mentor/schedule", "Publish availability and run the session calendar.",
   [("Tabs", "Sessions and Availability."),
    ("Week navigator", "Previous, next and today; shows the selected week."),
    ("Availability grid", "Open slots outlined, booked slots filled; click a slot to edit or delete."),
    ("Add slots button", "SlotEditorDialog: single slot or weekly recurrence (E18)."),
    ("Sessions list", "Upcoming and past sessions with mentee, mode, link and status."),
    ("Session actions", "Mark completed, cancel (ReasonDialog), edit link and notes (E37)."),
    ("Legend", "Open, booked, blocked.")],
   [("Add slots", "modal", "SlotEditorDialog", ["E18"], "M3"), ("Edit slot", "modal", "SlotEditorDialog", ["E19"], "M3"), ("Delete slot", "api", None, ["E20"], "M3"),
    ("Cancel session", "modal", "ReasonDialog", ["E37"], "M8"), ("Mark completed", "api", None, ["E37"], "M8")],
   ["E17", "E18", "E19", "E20", "E35", "E37"], "No slots: 'Add availability so mentees can book you'. No sessions: 'Nothing scheduled'.",
   "409 SLOT_OVERLAP and SLOT_BOOKED shown in the dialog; booked slots cannot be deleted (button disabled with tooltip).",
   tabs=["Sessions", "Availability"], group="Mentor")
pg(20, "Mentor profile editing", "Mentor", "/mentor/profile", "Maintain the professional profile, capacity and review submission.",
   [("Status badge and review note", "Draft, Pending review, Approved, Rejected (with the admin's note) or Suspended."),
    ("Tabs", "Professional, Expertise and interests, Capacity and availability, Account."),
    ("Professional fields", "Type (recent graduate or alumnus), title, organisation, experience, graduation year, LinkedIn URL, bio."),
    ("Expertise editor", "Skills with levels (E10) and career pathways (E11)."),
    ("Capacity and accepting switch", "Max active mentees 1-10 (cannot go below current active mentees) and is_available."),
    ("Save draft button", "Calls E15."),
    ("Submit for review button", "Calls E15 with submit_for_review; enabled when required fields are complete.")],
   [("Save draft", "api", None, ["E15"], "M2"), ("Submit for review", "api", 15, ["E15"], "M4"), ("Change password", "api", None, ["E09"], "M10")],
   ["E14", "E15", "E10", "E11", "E09"], "Not applicable.", "422 field errors; submit disabled with a checklist of missing fields; capacity below active count rejected with a message.",
   tabs=["Professional", "Expertise and interests", "Capacity and availability", "Account"], group="Mentor")
pg(21, "Notifications (mentor)", "Mentor", "/mentor/notifications", "Read events about requests, sessions, feedback and profile review.",
   [("Filter tabs", "All and Unread."),
    ("Notification list", "Same component as page 14 with mentor event types."),
    ("Row click", "Marks read (E43) and opens the target (request, mentee or session)."),
    ("Mark all as read", "Calls E44."),
    ("Pagination", "Standard list pagination.")],
   [("Open notification", "nav", 16, ["E43"], "M5"), ("Mark all as read", "api", None, ["E44"], "M10")],
   ["E42", "E43", "E44"], "'You're all caught up' / 'No notifications yet'.", "Same as page 14.", tabs=["All", "Unread"], group="Mentor")

pg(22, "Admin dashboard", "Admin", "/admin/dashboard", "Programme health at a glance and the work queue.",
   [("KPI cards", "Pending mentor reviews, active mentorships, requests in period, average rating."),
    ("Trend chart", "Requests and sessions per week (E52)."),
    ("Review queue preview", "Oldest pending mentor applications; opens page 24."),
    ("Stale requests alert", "Requests pending for more than 10 days; opens page 25."),
    ("Recent activity", "Latest audit entries (E54)."),
    ("Date range control", "Applies to KPIs and the chart.")],
   [("Sign out (user menu)", "nav", 1, ["E04"], "X0"), ("Review applications", "nav", 24, ["E47"], "A2"), ("View stale requests", "nav", 25, ["E50"], "A4"), ("Open analytics", "nav", 26, ["E51"], "A5")],
   ["E51", "E52", "E47", "E50", "E54"], "No pending reviews: 'Queue is empty'. No data in range: charts show 'No activity in this period'.",
   "Each panel loads independently with retry; counts below 5 in a group are shown as '<5'.", group="Admin")
pg(23, "User management", "Admin", "/admin/users", "Search users, change account status, maintain the skill and career-interest catalogues.",
   [("Tabs", "Users and Catalogue."),
    ("Filters", "Role, account status, search by name or e-mail."),
    ("Users table", "Name, e-mail, role, status badge, last login."),
    ("Suspend / Reactivate button", "ReasonDialog then E46; admins cannot act on their own account."),
    ("Catalogue lists", "Skills and career interests with category, active flag and usage count."),
    ("Add / Edit / Retire", "CatalogueDialog calling E55-E58; retired entries stay on existing profiles.")],
   [("Suspend or reactivate", "modal", "ReasonDialog", ["E46"], "A3"), ("Add skill or interest", "modal", "CatalogueDialog", ["E55", "E57"], "A7"),
    ("Edit or retire", "modal", "CatalogueDialog", ["E56", "E58"], "A7")],
   ["E45", "E46", "E10", "E11", "E55", "E56", "E57", "E58"], "'No users match the filters'. Empty catalogue: 'Add the first skill'.",
   "409 DUPLICATE_ENTRY in the catalogue dialog; 409 INVALID_STATE_TRANSITION or 403 for self-suspension shown as a toast.",
   tabs=["Users", "Catalogue"], group="Admin")
pg(24, "Mentor approval / review", "Admin", "/admin/mentors", "Verify mentor applications and decide.",
   [("Status tabs", "Pending review, Approved, Rejected, Suspended with counts."),
    ("Applicant list", "Name, organisation, mentor type, submitted date."),
    ("Profile detail panel", "All profile fields, LinkedIn link, graduation year, expertise and pathways (E16)."),
    ("Verification checklist", "Background verified, details complete, no policy concerns (UI aid; stored in the note)."),
    ("Approve button", "ConfirmDialog then E48 (approve); mentor is notified."),
    ("Reject button", "ReasonDialog with a required note then E48 (reject)."),
    ("Suspend button", "ReasonDialog then E48 (suspend); pending requests to the mentor are cancelled.")],
   [("Approve", "api", None, ["E48"], "A2"), ("Reject", "modal", "ReasonDialog", ["E48"], "A2"), ("Suspend", "modal", "ReasonDialog", ["E48"], "A2")],
   ["E47", "E48", "E16"], "'No applications waiting'.", "409 INVALID_STATE_TRANSITION (already decided) refreshes the list; 422 when the rejection note is missing.",
   tabs=["Pending review", "Approved", "Rejected", "Suspended"], group="Admin")
pg(25, "Mentorship management", "Admin", "/admin/mentorships", "Oversee relationships and long-pending requests.",
   [("Tabs", "Mentorships and Requests."),
    ("Filters", "Status, mentor, student; for requests also 'older than N days'."),
    ("Mentorships table", "Student, mentor, status, started, sessions completed, last activity."),
    ("Detail drawer", "Mentorship summary and session list (E31, E33); no access to private feedback comments beyond the admin view rules."),
    ("End mentorship button", "ReasonDialog then E32 for cases such as complaints."),
    ("Requests table", "Request age highlighted when pending longer than 10 days.")],
   [("View details", "modal", "RequestDrawer", ["E31", "E33"], "A4"), ("End mentorship", "modal", "ReasonDialog", ["E32"], "A4")],
   ["E49", "E50", "E31", "E33", "E32"], "'No mentorships match the filters'.", "409 INVALID_STATE_TRANSITION when already closed refreshes the row.",
   tabs=["Mentorships", "Requests"], group="Admin")
pg(26, "Programme analytics and reports", "Admin", "/admin/analytics", "Analyse participation and programme effectiveness; export CSV reports.",
   [("Date range and presets", "Last 30 days, last term, custom."),
    ("KPI row", "Acceptance rate, median response time, mentor utilisation, average rating."),
    ("Funnel chart", "Requests, accepted, mentorships, with at least one completed session, with feedback."),
    ("Trend chart", "Metric selector (requests, acceptances, sessions, active users) by week or month."),
    ("Rating distribution", "Bar chart of ratings 1-5."),
    ("Export button", "Choose report and range; downloads CSV (E53)."),
    ("Privacy note", "Counts only; groups smaller than 5 are suppressed.")],
   [("Apply range", "api", None, ["E51", "E52"], "A6"), ("Export CSV", "api", None, ["E53"], "A6")],
   ["E51", "E52", "E53"], "'No data for this period'.", "422 invalid range message; export failure toast; chart panels retry independently.", group="Admin")

PAGE = {p["num"]: p for p in PAGES}
MODALS = {"RequestDrawer", "BookingDialog", "ReasonDialog", "FeedbackDialog", "SlotEditorDialog", "CatalogueDialog"}

# ---------------- user stories ----------------
STORIES = [
    # id, role, story, pages, endpoints, workflow steps
    ("US-S01", "Student", "register with my e-mail and a password so that I can use the platform", [2, 1], ["E01", "E02"], ["S1", "X0"]),
    ("US-S02", "Student", "complete a profile with stage, skills, interests and goals so that mentors and matching understand my needs", [5, 13], ["E10", "E11", "E12", "E13"], ["S3", "S12"]),
    ("US-S03", "Student", "search and filter mentors by skill, career pathway, experience and availability", [7], ["E22"], ["S4"]),
    ("US-S04", "Student", "see mentors ranked for me with the reasons for the ranking", [6, 7], ["E23"], ["S4"]),
    ("US-S05", "Student", "read a mentor's profile, expertise and rating before asking", [8], ["E16"], ["S5"]),
    ("US-S06", "Student", "send a mentoring request that states my career goal", [9], ["E24"], ["S6"]),
    ("US-S07", "Student", "track my requests and cancel a pending one", [10], ["E25", "E26", "E29"], ["S7"]),
    ("US-S08", "Student", "be notified when a request is accepted or declined", [14], ["E42", "E43", "E44"], ["S7", "S12"]),
    ("US-S09", "Student", "see my mentorship and my mentor's details once a request is accepted", [11], ["E30", "E31"], ["S8"]),
    ("US-S10", "Student", "book a session in my mentor's open availability", [11, 12], ["E21", "E34"], ["S9"]),
    ("US-S11", "Student", "review my session history and notes and cancel a session", [12], ["E33", "E36", "E37"], ["S10"]),
    ("US-S12", "Student", "rate a completed session", [12], ["E38", "E39"], ["S10"]),
    ("US-S13", "Student", "end a mentorship that is complete or no longer useful", [11], ["E32"], ["S11"]),
    ("US-S14", "Student", "reset my password if I forget it", [3], ["E05", "E06"], ["X1"]),
    ("US-M01", "Mentor", "register as a mentor and build a professional profile", [2, 20], ["E01", "E14", "E15"], ["M1", "M2"]),
    ("US-M02", "Mentor", "state my expertise and the career pathways I can advise on", [20], ["E10", "E11", "E15"], ["M3"]),
    ("US-M03", "Mentor", "submit my profile for approval and see the decision", [20, 15], ["E15", "E41"], ["M4"]),
    ("US-M04", "Mentor", "set how many mentees I can take and pause new requests", [20, 15], ["E15"], ["M10"]),
    ("US-M05", "Mentor", "publish availability as single slots or a weekly pattern", [19], ["E17", "E18", "E19", "E20"], ["M3"]),
    ("US-M06", "Mentor", "review incoming requests together with the student's profile", [16, 17], ["E25", "E26"], ["M5"]),
    ("US-M07", "Mentor", "accept or decline a request", [16, 17], ["E27", "E28"], ["M6"]),
    ("US-M08", "Mentor", "see and manage my active mentees", [18], ["E30", "E31"], ["M7"]),
    ("US-M09", "Mentor", "schedule, complete and cancel sessions and keep shared notes", [18, 19], ["E34", "E35", "E37"], ["M8"]),
    ("US-M10", "Mentor", "close a mentorship when it has run its course", [18], ["E32"], ["M7"]),
    ("US-M11", "Mentor", "give feedback on a completed session", [18], ["E38"], ["M9"]),
    ("US-A01", "Administrator", "review and approve or reject mentor applications", [24], ["E47", "E48", "E16"], ["A2"]),
    ("US-A02", "Administrator", "suspend or reactivate user accounts", [23], ["E45", "E46"], ["A3"]),
    ("US-A03", "Administrator", "oversee all mentorships and long-pending requests", [25], ["E49", "E50"], ["A4"]),
    ("US-A04", "Administrator", "end a mentorship when a problem is reported", [25], ["E32"], ["A4"]),
    ("US-A05", "Administrator", "see participation metrics at a glance", [22], ["E51", "E52"], ["A5"]),
    ("US-A06", "Administrator", "analyse trends and export reports to judge programme effectiveness", [26], ["E51", "E52", "E53"], ["A6"]),
    ("US-A07", "Administrator", "maintain the skill and career-interest catalogues", [23], ["E55", "E56", "E57", "E58"], ["A7"]),
    ("US-A08", "Administrator", "review an audit trail of sensitive actions", [22], ["E54"], ["A8"]),
    ("US-X01", "Any user", "be told clearly when my session has expired or I lack access", [4], ["E03", "E08"], ["X2"]),
]


def verify(EP):
    """Cross-check pages, actions, workflow steps, stories and endpoints against the API table."""
    nums = {p["num"] for p in PAGES}
    assert nums == set(range(1, 27)), nums
    for p in PAGES:
        for e in p["endpoints"]:
            assert e in EP, (p["num"], e)
        for label, kind, target, eps, wf in p["actions"]:
            assert wf in WF, (p["num"], label, wf)
            for e in eps:
                assert e in EP, (p["num"], label, e)
            if kind == "nav" and target is not None:
                assert target in nums, (p["num"], label, target)
            if kind == "modal":
                assert target in MODALS, (p["num"], label, target)
        assert 4 <= len(p["elements"]) <= 9, p["num"]
    for k, (role, text, eps) in WF.items():
        for e in eps:
            assert e in EP, (k, e)
    for sid, role, text, pages, eps, wfs in STORIES:
        for n in pages:
            assert n in nums, sid
        for e in eps:
            assert e in EP, (sid, e)
        for w in wfs:
            assert w in WF, (sid, w)
    # every endpoint is used by at least one page, and every page endpoint is covered by a story
    used = set()
    for p in PAGES:
        used |= set(p["endpoints"])
        for a in p["actions"]:
            used |= set(a[3])
    unused = set(EP) - used
    return unused


if __name__ == "__main__":
    import api
    api.verify()
    un = verify(api.EP)
    print(len(PAGES), "pages;", len(STORIES), "stories;", len(WF), "workflow steps; endpoints not referenced by any page:", sorted(un))
