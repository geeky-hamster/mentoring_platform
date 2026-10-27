"""Static outline: gives every H1/H2 a stable number so text can cross-reference sections ('R(key)')."""
OUT = [
    ("1", "exec", "Executive summary and scope", [
        ("purpose", "Purpose and audience"), ("context", "Context: the official IITM Mentor Mentee Portal"),
        ("verified", "Verified facts and sources"), ("proposal", "What this report proposes"),
        ("scope", "Scope, non-goals and discovery items"), ("decisions", "Key design decisions at a glance"),
        ("conventions", "Conventions used in this report")]),
    ("2", "workflows", "System workflows", [
        ("arch", "Architecture overview"), ("e2e", "End-to-end flow"), ("student", "Student flow"), ("mentor", "Mentor flow"),
        ("admin", "Administrator flow"), ("states", "State models"), ("sequences", "Key interaction sequences"),
        ("rules", "Business rules and edge cases"), ("errors", "Error states and recovery")]),
    ("3", "stack", "Technology stack and justification", [
        ("frontend", "Frontend"), ("backend", "Backend"), ("database", "Database"), ("apitools", "API contract, testing and quality tools"),
        ("collab", "Design and collaboration tools"), ("deploy", "Deployment"), ("risks", "Technology risks and mitigations")]),
    ("4", "wireframes", "Wireframes and page specifications", [
        ("inventory", "Page inventory and role access"), ("nav", "Navigation maps"), ("shared", "Shared components and state patterns"),
        ("pub", "Public and shared pages (1-4)"), ("stu", "Student pages (5-14)"), ("men", "Mentor pages (15-21)"),
        ("adm", "Administrator pages (22-26)"), ("stories", "User stories and traceability")]),
    ("5", "components", "Software components", [
        ("overview", "Component overview"), ("c01", "C01 Authentication and authorisation"), ("c02", "C02 User and profile management"),
        ("c03", "C03 Skill and career-interest management"), ("c04", "C04 Mentor discovery and filtering"), ("c05", "C05 Mentor matching service"),
        ("c06", "C06 Mentoring request management"), ("c07", "C07 Mentorship relationship management"),
        ("c08", "C08 Availability and session scheduling"), ("c09", "C09 Feedback management"), ("c10", "C10 Notifications"),
        ("c11", "C11 Administration"), ("c12", "C12 Analytics and reporting"), ("depmatrix", "Component dependency matrix")]),
    ("6", "uml", "UML class diagram", [
        ("identity", "Identity and catalogue classes"), ("lifecycle", "Mentoring lifecycle classes"), ("services", "Service layer"),
        ("relations", "Reading the relationships"), ("mapping", "Class-to-table mapping")]),
    ("7", "database", "Database design", [
        ("principles", "Design principles"), ("improvements", "Improvements over the baseline schema"), ("dictionary", "Data dictionary"),
        ("indexes", "Indexes"), ("concurrency", "Concurrency and integrity rules"), ("fkpolicy", "Foreign keys and delete policy"),
        ("slots", "Availability slots and recurrence"), ("dbtests", "Verification on PostgreSQL 16"), ("retention", "Retention and privacy"),
        ("migrations", "Migrations and seed data")]),
    ("8", "er", "Entity-relationship diagrams", [
        ("legend", "How to read the diagrams"), ("accounts", "Accounts and operations"), ("catalogue", "Skills and career interests"),
        ("lifecycleer", "Mentoring lifecycle"), ("cards", "Relationship and cardinality summary")]),
    ("9", "api", "REST API design", [
        ("conventions", "Conventions: versioning, envelopes, pagination and validation"), ("authn", "Authentication, JWT and refresh-token revocation"),
        ("rbac", "Authorisation and ownership rules"), ("security", "CORS, rate limiting and transport security"),
        ("catalogue", "Endpoint catalogue"), ("errorcat", "Error catalogue"), ("examples", "Flow examples"), ("errex", "Error examples"),
        ("openapi", "OpenAPI contract and Postman")]),
    ("10", "matching", "Mentor matching algorithm", [
        ("inputs", "Inputs and hard eligibility filters"), ("formula", "Score definition"), ("missing", "Missing data, ties and ordering"),
        ("worked", "Worked example"), ("explain", "Explanations shown to students"), ("impl", "Implementation and performance"),
        ("validate", "Validating the weights"), ("limits", "Limitations and fairness")]),
    ("11", "structure", "Project structure", [
        ("repo", "Repository layout"), ("backendlayers", "Backend layering"), ("frontendlayout", "Frontend organisation"),
        ("config", "Configuration and environments"), ("workflow", "Branching, reviews and CI")]),
    ("12", "testing", "Testing strategy", [
        ("levels", "Test levels and tools"), ("cases", "Sample test cases"), ("dbev", "Database test evidence"),
        ("gates", "Quality gates"), ("uat", "Acceptance testing")]),
    ("13", "roadmap", "Development roadmap", [
        ("phases", "Phase overview"), ("detail", "Phase details"), ("critical", "Dependencies and critical path"), ("rrisks", "Delivery risks")]),
    ("14", "team", "Team roles and responsibilities", [
        ("roles", "Role definitions"), ("shared", "Shared requirements and design activities"), ("raci", "Responsibility matrix"),
        ("handoffs", "Handoffs and definition of done"), ("agreements", "Working agreements")]),
    ("15", "quality", "Assumptions, open questions and references", [
        ("assume", "Assumptions"), ("open", "Open questions for the client"), ("glossary", "Glossary"), ("refs", "References"),
        ("control", "Document control")]),
    ("A", "appA", "Appendix A - OpenAPI 3.0 contract", []),
    ("B", "appB", "Appendix B - PostgreSQL schema (DDL)", []),
    ("C", "appC", "Appendix C - Matching reference implementation", []),
    ("D", "appD", "Appendix D - Database test evidence", []),
]

NUM = {}      # key -> "7.5"
TITLE = {}    # key -> title
ORDER = []
for n, k, t, subs in OUT:
    NUM[k] = n
    TITLE[k] = t
    ORDER.append((1, k))
    for i, (sk, st) in enumerate(subs, 1):
        full = f"{k}.{sk}"
        NUM[full] = f"{n}.{i}" if n.isdigit() else f"{n}.{i}"
        TITLE[full] = st
        ORDER.append((2, full))


def R(key):
    """Cross-reference text, e.g. R('database.concurrency') -> 'Section 7.5'."""
    if "." not in key and not NUM[key][0].isdigit():
        return "Appendix " + NUM[key]
    return "Section " + NUM[key]
