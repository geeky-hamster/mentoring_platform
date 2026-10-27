"""Component catalogue C01-C12 (single source for Section 5, the dependency matrix and cross-references)."""
import api

AUD = "AUD"
COMPS = [
    dict(id="C01", key="c01", name="Authentication and authorisation", service="AuthenticationService",
         purpose="Proves who the caller is and decides what a role may do. Owns passwords, tokens and sessions.",
         resp=["Register students and mentors; hash passwords (Argon2id).", "Log in, issue 15-minute access tokens and rotating refresh tokens; log out; detect refresh-token reuse.",
               "Reset and change passwords; optional e-mail verification.", "Provide the role and ownership guards used by every other component.", "Block suspended or deactivated accounts."],
         inputs="E-mail, password, refresh cookie, signed reset/verification tokens.", outputs="Access token (JWT with user_id and role), rotated refresh cookie, user summary, 4xx errors.",
         rules=["Admin accounts are created only by a seed command (R16 for suspended accounts).", "Login errors never reveal whether the e-mail exists.", "Reuse of a rotated refresh token revokes the whole family.", "Password change or reset revokes all refresh tokens."],
         eps=["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09"], wtables=["users", "refresh_tokens"], rtables=[],
         deps=[AUD], ext="E-mail provider (optional) for verification and reset links."),
    dict(id="C02", key="c02", name="User and profile management", service="ProfileService (entity methods on StudentProfile and MentorProfile)",
         purpose="Keeps the student and mentor profiles that every other component reads.",
         resp=["Read and update the caller's own profile; replace skill, expertise and interest lists as a whole.", "Compute profile_completed for students server-side.",
               "Move a mentor profile through draft, pending_review, approved, rejected and suspended on the mentor's side (submit for review).", "Enforce that capacity cannot drop below the active mentee count.", "Flag edits to sensitive fields on approved mentor profiles."],
         inputs="Profile fields; skill and interest lists (ids from the catalogues).", outputs="Profile with skills and interests; completeness flag; review status.",
         rules=["A student profile must be complete before requesting (R1).", "At most five focus skills.", "A mentor cannot submit an incomplete profile (DB ck_mentor_complete).", "max_active_mentees between 1 and 10."],
         eps=["E12", "E13", "E14", "E15"], wtables=["student_profiles", "mentor_profiles", "student_skills", "student_interests", "mentor_expertise", "mentor_interests"], rtables=["users", "skills", "career_interests"],
         deps=["C01", "C03", AUD], ext=""),
    dict(id="C03", key="c03", name="Skill and career-interest management", service="CatalogueService (AdminService.saveCatalogueEntry)",
         purpose="Controlled vocabularies that make profiles comparable and matching reliable.",
         resp=["Serve active skills and career pathways to forms and filters.", "Let administrators add, rename, recategorise and retire entries.", "Prevent duplicate names; keep retired entries for history."],
         inputs="Entry name, category or description, is_active.", outputs="Catalogue lists; created or updated entry.",
         rules=["Names are unique (409 DUPLICATE_ENTRY).", "Retired entries stay referenced; they are hidden from new selections only.", "Only administrators may change catalogues."],
         eps=["E10", "E11", "E55", "E56", "E57", "E58"], wtables=["skills", "career_interests"], rtables=[], deps=[AUD], ext=""),
    dict(id="C04", key="c04", name="Mentor discovery and filtering", service="DiscoveryService (read-only queries; MatchingService.search)",
         purpose="Lets a student browse and filter approved mentors and open a mentor's profile.",
         resp=["Search approved mentors by keyword, skill, career pathway, experience range, mentor type and availability.", "Return paginated cards with top skills and an accepting-mentees flag.",
               "Return a single mentor profile with rating summary (small samples hidden).", "Hide mentors who are suspended, unapproved or unavailable."],
         inputs="Filters, sort, page and page_size.", outputs="Page of MentorCard; MentorProfile.",
         rules=["Only approved mentors are visible to students.", "Unavailable mentors are hidden unless accepting=false is requested.", "Ratings are shown only after at least three entries."],
         eps=["E16", "E22"], wtables=[], rtables=["mentor_profiles", "mentor_expertise", "mentor_interests", "skills", "career_interests", "availability_slots", "feedback"],
         deps=["C02", "C03", "C08"], ext=""),
    dict(id="C05", key="c05", name="Mentor matching service", service="MatchingService",
         purpose="Ranks eligible mentors for one student with an explainable score.",
         resp=["Apply hard eligibility filters; compute S, C and A scores and the weighted total.", "Order results deterministically and paginate them.", "Produce human-readable reasons from the score parts.", "Exclude mentors already pending, active or in cooldown with the student."],
         inputs="Student id from the token; page and page_size.", outputs="Page of MentorMatch: card, score, breakdown, reasons.",
         rules=["Score = 0.50 S + 0.30 C + 0.20 A (Section 10).", "Missing data renormalises weights.", "Ties break by S, C, open slots, free capacity, then id."],
         eps=["E23"], wtables=[], rtables=["student_profiles", "student_skills", "student_interests", "mentor_profiles", "mentor_expertise", "mentor_interests", "availability_slots", "mentoring_requests", "mentorships"],
         deps=["C04", "C03", "C06", "C07", "C08"], ext=""),
    dict(id="C06", key="c06", name="Mentoring request management", service="MentoringService (request operations)",
         purpose="Runs the life of a request from submission to its recorded outcome.",
         resp=["Validate and create a request taking the student from the token.", "Accept (creating the mentorship in the same transaction), decline with reason, cancel, and expire.", "List requests for the sender or addressee; show the student's profile summary to the mentor.", "Apply duplicate, limit and cooldown rules."],
         inputs="mentor_id, career_goal, message; decision and reason.", outputs="Request, or request plus mentorship on accept; notifications.",
         rules=["R1 to R8 in Section 2.8.", "Expiry after 14 days.", "Accept is one transaction with row locks."],
         eps=["E24", "E25", "E26", "E27", "E28", "E29"], wtables=["mentoring_requests"], rtables=["student_profiles", "mentor_profiles", "mentorships"], deps=["C02", "C07", "C10", AUD], ext=""),
    dict(id="C07", key="c07", name="Mentorship relationship management", service="MentoringService (mentorship operations)",
         purpose="Owns the active relationship between one student and one mentor and its closing.",
         resp=["Create the mentorship from an accepted request (called by accept).", "List and show mentorships with the counterpart summary and session statistics.", "Close a mentorship as completed or ended; raise the closed event so future sessions are cancelled; notify the other party.", "Provide capacity counts to other components."],
         inputs="Mentorship id; target status; reason.", outputs="Mentorship; cancelled sessions; notifications.",
         rules=["R14: either party or an administrator can close; closed is final.", "One active mentorship per pair; capacity never exceeded."],
         eps=["E30", "E31", "E32"], wtables=["mentorships"], rtables=["mentoring_requests", "mentor_profiles"], deps=["C10", AUD], ext="Publishes an internal 'mentorship closed' event that C08 handles by cancelling future sessions (no direct call, so no dependency cycle)."),
    dict(id="C08", key="c08", name="Availability and session scheduling", service="SessionService",
         purpose="Publishes mentor time and turns it into booked, completed or cancelled sessions.",
         resp=["Create, edit and delete availability slots (single or weekly helper).", "Show open slots to the mentor, the admin and mentees.", "Book sessions with conflict checks for both parties.", "Complete, cancel and annotate sessions; list sessions and calendar."],
         inputs="Slot times, recurrence helper, slot_id, meeting mode and link, notes, cancellation reason.", outputs="Slots, sessions, notifications (scheduled, cancelled, reminder).",
         rules=["R9 to R13.", "Slot at most 4 hours; slots of a mentor never overlap.", "Reminder job runs 24 hours before start (proposed)."],
         eps=["E17", "E18", "E19", "E20", "E21", "E33", "E34", "E35", "E36", "E37"], wtables=["availability_slots", "sessions"], rtables=["mentorships"], deps=["C07", "C10"], ext="iCalendar export (optional)."),
    dict(id="C09", key="c09", name="Feedback management", service="FeedbackService",
         purpose="Collects one rating and comment per participant per completed session.",
         resp=["Accept feedback within 14 days of completion.", "Show each party the entries they are allowed to see.", "Feed rating summaries to discovery and analytics."],
         inputs="session_id, rating 1-5, comment.", outputs="Feedback entry; visible feedback list.",
         rules=["R15: once per participant; only for completed sessions; only participants.", "Comments are not shown publicly."],
         eps=["E38", "E39"], wtables=["feedback"], rtables=["sessions"], deps=["C08"], ext=""),
    dict(id="C10", key="c10", name="Notifications", service="NotificationService",
         purpose="In-app messages that tell users something changed and where to look.",
         resp=["Create notifications for events raised by other components.", "List, mark read and mark all read; supply the unread count.", "Optional e-mail delivery behind an interface; purge read items after 90 days."],
         inputs="user_id, type, related entity.", outputs="Notification list and unread count.",
         rules=["Twelve notification types (schema CHECK).", "A user sees only their own notifications."],
         eps=["E42", "E43", "E44"], wtables=["notifications"], rtables=[], deps=[], ext="E-mail provider (optional)."),
    dict(id="C11", key="c11", name="Administration", service="AdminService and AuditService",
         purpose="Gives administrators the controls to keep the programme safe and orderly.",
         resp=["Search and filter users; suspend, reactivate or deactivate accounts.", "Review the mentor queue; approve, reject (note required) or suspend.", "Oversee all mentorships and requests; end a mentorship when needed.", "Search the append-only audit log; write audit entries for sensitive actions."],
         inputs="Filters; decisions with notes; status changes.", outputs="Admin lists, updated statuses, audit entries.",
         rules=["Admins cannot change their own status.", "Every decision records the actor; rejection needs a note.", "Audit log is append-only for the application role."],
         eps=["E45", "E46", "E47", "E48", "E49", "E50", "E54"], wtables=["audit_logs"], rtables=["users", "mentor_profiles", "mentorships", "mentoring_requests"], deps=["C01", "C02", "C06", "C07", "C10"], ext=""),
    dict(id="C12", key="c12", name="Analytics and reporting", service="AnalyticsService (and dashboard read models)",
         purpose="Turns the operational data into dashboards, trends and exports for the right audience.",
         resp=["Student and mentor dashboards (counts, next session, capacity, rating summary).", "Programme KPIs and time series for administrators; CSV export.", "Suppress groups smaller than five; never export free text."],
         inputs="Date range, metric, interval.", outputs="Dashboard objects, overview, trend series, CSV.",
         rules=["Counts only; small groups hidden.", "Read-only access to the data tables."],
         eps=["E40", "E41", "E51", "E52", "E53"], wtables=[], rtables=["users", "mentor_profiles", "mentoring_requests", "mentorships", "sessions", "feedback", "notifications"], deps=["C02", "C06", "C07", "C08", "C09", "C10"], ext=""),
]
BY = {c["id"]: c for c in COMPS}


def verify():
    seen = []
    for c in COMPS:
        seen += c["eps"]
        for e in c["eps"]:
            assert e in api.EP, e
    assert sorted(seen) == sorted(api.EP), set(api.EP) ^ set(seen)
    import schema
    for c in COMPS:
        for t in c["wtables"] + c["rtables"]:
            assert t in schema.TBL, t
        for d in c["deps"]:
            assert d == AUD or d in BY, d
    # acyclic over component deps
    state = {}

    def dfs(n, path):
        if state.get(n) == 1:
            raise AssertionError("cycle " + "->".join(path + [n]))
        if state.get(n) == 2:
            return
        state[n] = 1
        for d in BY[n]["deps"]:
            if d != AUD:
                dfs(d, path + [n])
        state[n] = 2
    for c in COMPS:
        dfs(c["id"], [])
    return True


if __name__ == "__main__":
    print(verify())
