"""UML class diagrams for Section 6 (three figures)."""
from uml import UML, fig

UUID = "UUID"


def identity():
    u = UML(739, 312)
    u.add("User", 290, 4, 160, "User", [
        "+ userId: UUID", "+ fullName: String", "+ email: String", "- passwordHash: String", "+ role: Role", "+ accountStatus: AccountStatus"],
        ["+ verifyPassword(raw: String): Boolean", "+ hasRole(role: Role): Boolean", "+ suspend(): void", "+ reactivate(): void"])
    u.add("Notification", 570, 4, 165, "Notification", [
        "+ notificationId: UUID", "+ title: String", "+ message: Text", "+ notificationType: NotificationType", "+ relatedEntityType: String",
        "+ relatedEntityId: UUID", "+ isRead: Boolean", "+ readAt: DateTime"], ["+ markRead(): void"])
    u.add("StudentProfile", 4, 150, 178, "StudentProfile", [
        "+ studentProfileId: UUID", "+ programmeStage: ProgrammeStage", "+ expectedGraduationYear: Integer", "+ careerGoals: Text",
        "+ guidanceNeeds: Text", "+ bio: Text", "+ profileCompleted: Boolean"],
        ["+ addSkill(skill: Skill, level: Level, isFocus: Boolean): void", "+ removeSkill(skillId: UUID): void", "+ setInterests(ids: List<UUID>): void", "+ isComplete(): Boolean"])
    u.add("MentorProfile", 557, 150, 178, "MentorProfile", [
        "+ mentorProfileId: UUID", "+ mentorType: MentorType", "+ professionalTitle: String", "+ organisation: String", "+ experienceYears: Integer",
        "+ isAvailable: Boolean", "+ maxActiveMentees: Integer", "+ profileStatus: ProfileStatus", "+ reviewNote: Text"],
        ["+ submitForReview(): void", "+ addExpertise(skill: Skill, level: Level): void", "+ hasCapacity(activeCount: Integer): Boolean", "+ acceptingMentees(): Boolean"])
    u.add("Skill", 290, 150, 160, "Skill", ["+ skillId: UUID", "+ skillName: String", "+ category: String", "+ isActive: Boolean"], ["+ retire(): void"])
    u.add("CareerInterest", 290, 236, 160, "CareerInterest", ["+ interestId: UUID", "+ interestName: String", "+ description: Text", "+ isActive: Boolean"], ["+ retire(): void"])
    U, S, M, K, C = u.cls["User"], u.cls["StudentProfile"], u.cls["MentorProfile"], u.cls["Skill"], u.cls["CareerInterest"]
    ux = 370
    u.edge([(ux, U.y + U.h), (ux, 133), (S.x + 90, 133), (S.x + 90, S.y)], "assoc", "1", "0..1", "has", lseg=1, lpos=0.5, ldy=-1)
    u.edge([(ux, U.y + U.h), (ux, 133), (M.x + 90, 133), (M.x + 90, M.y)], "assoc", None, "0..1", "has", lseg=1, lpos=0.5, ldy=-1)
    u.edge([(U.x + U.w, 40), (570, 40)], "assoc", "1", "0..*", "receives", m2off=(-16, -8), m1off=(3, -8))
    # catalogue associations
    u.edge([(S.x + S.w, 160), (K.x, 160)], "assoc", "*", "*", "skills", ldy=-8, m1off=(3, -8), m2off=(-8, -8))
    u.edge([(S.x + S.w, 245), (C.x, 245)], "assoc", "*", "*", "interests", ldy=-8, m1off=(3, -8), m2off=(-8, -8))
    u.edge([(M.x, 160), (K.x + K.w, 160)], "assoc", "*", "*", "expertise", ldy=-8, m1off=(-9, -8), m2off=(3, -8))
    u.edge([(M.x, 245), (C.x + C.w, 245)], "assoc", "*", "*", "interests", ldy=-8, m1off=(-9, -8), m2off=(3, -8))
    u.note(190, 182, 94, "association class\nStudentSkill\nproficiencyLevel: Level\nisFocus: Boolean")
    u.note(456, 182, 94, "association class\nMentorExpertise\nexpertiseLevel: Level")
    u.note(4, 274, 270, "Interest links are plain many-to-many tables\n(student_interests, mentor_interests) with no extra attributes.")
    return u


def lifecycle():
    u = UML(739, 482)
    u.add("S", 4, 4, 160, "StudentProfile", ["+ userId: UUID (referenced key)"], [], kind="stub")
    u.add("M", 575, 4, 160, "MentorProfile", ["+ userId: UUID (referenced key)"], [], kind="stub")
    u.add("Req", 290, 66, 160, "MentoringRequest", [
        "+ requestId: UUID", "+ careerGoal: Text", "+ message: Text", "+ status: RequestStatus", "+ createdAt: DateTime", "+ expiresAt: DateTime"],
        ["+ accept(): Mentorship", "+ decline(reason: Text): void", "+ cancel(): void", "+ expire(): void"])
    u.add("Men", 290, 224, 160, "Mentorship", [
        "+ mentorshipId: UUID", "+ status: MentorshipStatus", "+ startedAt: DateTime", "+ endedAt: DateTime", "+ endReason: Text"],
        ["+ end(by: UUID, reason: Text): void", "+ complete(): void", "+ isActive(): Boolean"])
    u.add("Ses", 290, 362, 160, "Session", [
        "+ sessionId: UUID", "+ scheduledStart: DateTime", "+ scheduledEnd: DateTime", "+ meetingMode: MeetingMode", "+ meetingLink: String", "+ status: SessionStatus", "+ notes: Text"],
        ["+ complete(notes: Text): void", "+ cancel(by: UUID, reason: Text): void", "+ conflictsWith(o: Session): Boolean"])
    u.add("Slot", 575, 362, 160, "AvailabilitySlot", ["+ slotId: UUID", "+ startTime: DateTime", "+ endTime: DateTime", "+ isAvailable: Boolean"],
          ["+ overlaps(o: AvailabilitySlot): Boolean", "+ markBooked(): void", "+ release(): void"])
    u.add("Fb", 4, 374, 160, "Feedback", ["+ feedbackId: UUID", "+ rating: Integer [1..5]", "+ comments: Text", "+ createdAt: DateTime"], ["+ withinWindow(s: Session): Boolean"])
    S, M, R, N, E, L, F = (u.cls[k] for k in ("S", "M", "Req", "Men", "Ses", "Slot", "Fb"))
    u.edge([(130, S.y + S.h), (130, 100), (R.x, 100)], "assoc", "1", "0..*", "sends", lseg=1, lpos=0.55, ldy=-6, m1off=(3, 2), m2off=(-18, -8))
    u.edge([(620, M.y + M.h), (620, 100), (R.x + R.w, 100)], "assoc", "1", "0..*", "receives", lseg=1, lpos=0.5, ldy=-6, m1off=(3, 2), m2off=(3, -8))
    u.edge([(50, S.y + S.h), (50, 262), (N.x, 262)], "assoc", "1", "0..*", "learns in", lseg=1, lpos=0.5, ldy=-6, m1off=(3, 2), m2off=(-18, -8))
    u.edge([(675, M.y + M.h), (675, 262), (N.x + N.w, 262)], "assoc", "1", "0..*", "guides in", lseg=1, lpos=0.5, ldy=-6, m1off=(3, 2), m2off=(3, -8))
    u.edge([(370, R.y + R.h), (370, N.y)], "assoc", "1", "0..1", "results in", ldx=24, m1off=(4, 4), m2off=(4, -10))
    u.edge([(370, N.y + N.h), (370, E.y)], "comp", "1", "0..*", "contains", ldx=24, m1off=(5, 10), m2off=(4, -10))
    u.edge([(722, M.y + M.h), (722, L.y)], "assoc", "1", "0..*", "publishes", lseg=0, lpos=0.5, ldx=-24, m1off=(3, 3), m2off=(3, -10))
    u.edge([(L.x, 406), (E.x + E.w, 406)], "assoc", "0..1", "0..1", "booked into", ldy=-8, m1off=(-18, -9), m2off=(3, -9))
    u.edge([(E.x, 420), (F.x + F.w, 420)], "comp", "1", "0..2", "rated by", ldy=-8, m1off=(-15, -9), m2off=(3, -9))
    u.note(4, 282, 232, "A request that is accepted creates exactly one\nmentorship (Mentorship.request_id is unique).\nStudent and mentor on both objects must match.")
    u.note(4, 326, 232, "Feedback: at most one entry per participant\nper session, within 14 days of completion.")
    return u


SERVICES = [
    ("Auth", "AuthenticationService", ["uses: User, RefreshToken"], [
        "+ register(dto): User", "+ login(email, password): TokenPair", "+ refresh(token): TokenPair", "+ logout(token): void",
        "+ requestPasswordReset(email): void", "+ resetPassword(token, password): void"]),
    ("Match", "MatchingService", ["uses: StudentProfile, MentorProfile, Skill,", "CareerInterest, AvailabilitySlot (read only)"], [
        "+ search(filters, page): Page<MentorCard>", "+ recommend(studentId, page): List<MatchResult>", "+ score(student, mentor): MatchResult"]),
    ("Ana", "AnalyticsService", ["uses: aggregate queries (read only)"], [
        "+ overview(range): Overview", "+ trends(range, bucket): Trends", "+ exportCsv(range): Stream"]),
    ("Men", "MentoringService", ["uses: MentoringRequest, Mentorship"], [
        "+ createRequest(studentId, mentorId, dto)", "+ accept(requestId, mentorId): Mentorship", "+ decline(requestId, mentorId, reason): void",
        "+ cancel(requestId, studentId): void", "+ endMentorship(id, actorId, reason): void", "+ expireStaleRequests(): Integer"]),
    ("Ses", "SessionService", ["uses: AvailabilitySlot, Session"], [
        "+ addSlots(mentorId, slots): List<AvailabilitySlot>", "+ book(mentorshipId, actorId, slotId, dto): Session",
        "+ complete(sessionId, mentorId, notes): void", "+ cancel(sessionId, actorId, reason): void"]),
    ("Fb", "FeedbackService", ["uses: Feedback"], [
        "+ submit(sessionId, userId, rating, comments): Feedback", "+ listForSession(sessionId, userId): List<Feedback>"]),
    ("Aud", "AuditService", ["uses: AuditLog"], ["+ record(actorId, action, entity, details): void", "+ list(filters, page): Page<AuditLog>"]),
    ("Not", "NotificationService", ["uses: Notification"], [
        "+ notify(userId, type, entity): Notification", "+ list(userId, page): Page<Notification>", "+ markRead(id, userId): void", "+ markAllRead(userId): void"]),
    ("Adm", "AdminService", ["uses: User, MentorProfile, Skill, CareerInterest"], [
        "+ reviewMentor(mentorId, decision, note): MentorProfile", "+ setUserStatus(userId, status, reason): void",
        "+ saveCatalogueEntry(kind, dto): CatalogueEntry", "+ listMentorships(filters, page): Page<Mentorship>"]),
]


def services():
    u = UML(739, 480)
    xs = [4, 267, 530]
    ys = [4, 160, 330]
    for i, (id, name, uses, meths) in enumerate(SERVICES):
        r, c = divmod(i, 3)
        u.add(id, xs[c], ys[r], 205, name, uses, meths, kind="service")
    g = u.cls
    # dependencies (dashed, open arrow): consumer -> provider
    mid = lambda k: g[k].x + g[k].w / 2
    ses, men, fb, notf, adm, aud = g["Ses"], g["Men"], g["Fb"], g["Not"], g["Adm"], g["Aud"]
    u.edge([(ses.x, ses.y + 40), (men.x + men.w, ses.y + 40)], "dep", label="checks active", ldy=-8)
    u.edge([(fb.x, fb.y + 40), (ses.x + ses.w, fb.y + 40)], "dep", label="checks completed", ldy=-8)
    ybus = 300
    u.edge([(mid("Men"), men.y + men.h), (mid("Men"), ybus), (mid("Not"), ybus), (mid("Not"), notf.y)], "dep", label="notify", lseg=1, lpos=0.5, ldy=-6)
    u.edge([(mid("Ses"), ses.y + ses.h), (mid("Not"), notf.y)], "dep")
    u.edge([(mid("Fb"), fb.y + fb.h), (mid("Fb"), ybus), (mid("Not"), ybus), (mid("Not"), notf.y)], "dep")
    u.edge([(adm.x, adm.y + 50), (notf.x + notf.w, adm.y + 50)], "dep", label="notify", ldy=-8)
    u.note(267, 112, 205, "Dashed arrow = depends on (calls) the service it points to.")
    ylow = u.H - 6
    u.edge([(mid("Adm"), adm.y + adm.h), (mid("Adm"), ylow), (mid("Aud"), ylow), (mid("Aud"), aud.y + aud.h)], "dep", label="record audit entry", lseg=1, lpos=0.5, ldy=-6)
    return u


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "/home/claude/report_build/src")
    from reportlab.pdfgen import canvas
    c = canvas.Canvas("/home/claude/report_build/uml_test.pdf", pagesize=(760, 500))
    for fn in (identity, lifecycle, services):
        u = fn()
        c.saveState(); c.translate(10, 500 - u.H - 10); u.draw(c); c.restoreState(); c.showPage()
    c.save()
