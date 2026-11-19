#!/usr/bin/env python3
"""Part 3: Chapters 3-5."""
import docx
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_PATH = "/Users/himanshu/Downloads/LLM_Code_Reviewer_Project_Report.docx"

doc = Document(OUT_PATH)

def set_run_font(run, size=12, bold=False, italic=False, name="Times New Roman"):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts')
        rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), name)
    rfonts.set(qn('w:hAnsi'), name)
    rfonts.set(qn('w:cs'), name)

def add_para(text="", size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
             space_after=6, space_before=0, indent=0.25, line_spacing=1.5, name="Times New Roman"):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing
    if indent > 0:
        pf.left_indent = Inches(indent)
    if text:
        run = p.add_run(text)
        set_run_font(run, size=size, bold=bold, italic=italic, name=name)
    return p

def add_heading_chapter(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(24)
    pf.space_after = Pt(18)
    pf.line_spacing = 1.0
    run = p.add_run(text.upper())
    set_run_font(run, size=18, bold=True, name="Times New Roman")
    return p

def add_heading_section(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(12)
    pf.space_after = Pt(6)
    pf.line_spacing = 1.0
    run = p.add_run(text.upper())
    set_run_font(run, size=12, bold=True, name="Times New Roman")
    return p

def add_heading_sub(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(10)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.0
    run = p.add_run(text)
    set_run_font(run, size=12, bold=True, name="Times New Roman")
    return p

def add_table(headers, rows, caption=None):
    if caption:
        add_para(caption, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        set_run_font(run, size=11, bold=True, name="Times New Roman")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val))
            set_run_font(run, size=11, name="Times New Roman")
    doc.add_paragraph()
    return t

def add_mermaid_block(title, mermaid_code):
    add_para(title, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_after = Pt(10)
    pf.line_spacing = 1.0
    run = p.add_run(mermaid_code)
    set_run_font(run, size=9, bold=False, name="Consolas")
    pPr = p._element.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), 'F2F2F2')
    pPr.append(shd)
    return p

def add_page_break():
    doc.add_page_break()

def add_bullet(text, indent=0.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Inches(indent)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    run = p.add_run(text)
    set_run_font(run, size=12, name="Times New Roman")
    return p

# ---------- CHAPTER 3 ----------
add_heading_chapter("CHAPTER 3: LITERATURE SURVEY")
add_para("NOT FOUND IN CODEBASE \u2013 author to write. The README, source code comments, configuration files, and documentation files in this repository do not cite any research papers, technical articles, books, URLs, or prior systems. No references to existing static analysis tools, taint analysis literature, secret detection methods, or related work are present in the codebase. The author should prepare this chapter based on external research into static application security testing (SAST), taint analysis, secret detection, and code quality assessment tools.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=24, indent=0.25)
add_page_break()

# ---------- CHAPTER 4 ----------
add_heading_chapter("CHAPTER 4: PROJECT PLAN")

add_heading_section("4.1 Development Model")
add_para("The commit history indicates an incremental, feature-driven development model. Commits are organized around discrete features (authentication, analysis engine passes, taint analysis, quality metrics, frontend design, deployment) with accompanying fix commits addressing issues in previously implemented features. This supports an incremental or agile-like process rather than a strict sequential waterfall model. Evidence includes commit messages such as feat: Python interprocedural taint analysis, fix: taint engine call-shaped sources, feat: apply the Graded Paper design, and feat: make the app deployable as one container [git log output]. No formal sprint boards, issue trackers, milestones, or release tags were found in the repository.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("4.2 Timeline")
add_para("Table 4.1: Development phases inferred from commit history", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
phase_rows = [
    ("Initial setup", "Earliest commits", "Repository initialization, backend and frontend project structure"),
    ("Authentication", "Early commits", "Email/password registration, login, JWT authentication, token namespacing"),
    ("Core analysis engine", "Mid commits", "Analysis engine orchestrator, pipeline rewrite, damped scoring"),
    ("Taint analysis", "Mid-late commits", "Python and token-language interprocedural taint analysis"),
    ("AST and quality checks", "Mid-late commits", "Python AST checks, scope-aware analysis, correctness bug rules"),
    ("Frontend design", "Later commits", "Graded Paper visual design, score dial, landing page pipeline copy"),
    ("Deployment", "Later commits", "Single-container Docker build, Render blueprint, API base fallback"),
    ("Testing and documentation", "Throughout", "Test suites, README, design specifications"),
]
add_table(["Phase", "Approx. Dates", "What was built"], phase_rows)
add_para("NOT FOUND IN CODEBASE \u2013 exact commit dates are not included in the git log output provided. The author should run git log --format=\"%ad %s\" to supply actual dates for each phase.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("4.3 Team Contribution")
add_para("NOT FOUND IN CODEBASE \u2013 author to write. The git log output does not include author names or email addresses, only commit hashes and messages [git log output]. Individual contributor attribution cannot be extracted from the repository. The author should run git log --format=\"%an %s\" to list contributors and map them to modules.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("4.4 Tools")
add_para("Table 4.2: Development and deployment tools", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
tool_rows = [
    ("Git", "Version control", ".git/ directory; commit history"),
    ("Docker", "Containerized build and runtime", "Dockerfile"),
    ("Render", "Cloud deployment target", "render.yaml"),
    ("pip", "Python package installation", "backend/requirements.txt"),
    ("npm", "Node package installation", "frontend/package.json"),
    ("pytest", "Backend testing", "backend/requirements.txt line 10"),
    ("vitest", "Frontend testing", "frontend/package.json line 27"),
]
add_table(["Tool", "Purpose", "Evidence"], tool_rows)
add_para("NOT FOUND IN CODEBASE \u2013 specific IDE and CI/CD platform usage are not visible in the repository. The author should supply if applicable.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)
add_page_break()

# ---------- CHAPTER 5 ----------
add_heading_chapter("CHAPTER 5: SOFTWARE REQUIREMENTS SPECIFICATION")

add_heading_section("5.1 Project Scope")
add_para("The system is a web application that performs offline static analysis of source code submitted by authenticated users. It supports Python, JavaScript, Java, C, and C++. It provides user registration/login, code submission, severity-ranked findings with confidence levels, a 0\u2013100 quality score, and an owner-only review history. The analysis engine operates entirely offline using the Python standard library, requiring no API key and making no network calls during the review path [README.md; backend/app/analysis/engine.py].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("5.2 User Classes and Characteristics")
add_para("Table 5.1: User classes and capabilities", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
uc_rows = [
    ("Unauthenticated visitor", "Access landing page, register, login", "[frontend/src/pages/Landing.tsx; frontend/src/pages/Login.tsx; frontend/src/pages/Register.tsx]"),
    ("Authenticated user", "Submit code, view own review results, view own review history, sign out", "[frontend/src/pages/Submit.tsx; frontend/src/pages/Results.tsx; frontend/src/pages/History.tsx; backend/app/auth/dependencies.py]"),
    ("Review owner", "Access own review detail including source code", "[backend/app/reviews/router.py lines 45-57]"),
]
add_table(["User class", "Capabilities", "Source"], uc_rows)
add_para("No admin role or moderation capability exists in the code [backend/app/auth/dependencies.py; backend/app/db/models.py].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("5.3 Functional Requirements")
add_para("Table 5.2: Functional requirements", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
fr_rows = [
    ("FR1", "User registration with email and password (min 8 chars)", "[backend/app/auth/router.py lines 22-30]"),
    ("FR2", "User login returning JWT access token", "[backend/app/auth/router.py lines 33-38]"),
    ("FR3", "Password hashing with bcrypt", "[backend/app/auth/security.py lines 9-17]"),
    ("FR4", "JWT token creation and verification", "[backend/app/auth/security.py lines 20-31]"),
    ("FR5", "Authenticated source code submission by paste or file upload", "[frontend/src/pages/Submit.tsx; backend/app/reviews/router.py lines 13-29]"),
    ("FR6", "Language detection from filename and content", "[backend/app/analysis/detect.py]"),
    ("FR7", "Regex security rule scanning", "[backend/app/analysis/static_scanner.py; backend/app/analysis/rules.py]"),
    ("FR8", "Secret detection via entropy and known prefixes", "[backend/app/analysis/secrets.py]"),
    ("FR9", "Python AST semantic analysis", "[backend/app/analysis/ast_analyzer.py]"),
    ("FR10", "Per-language semantic pattern detection", "[backend/app/analysis/sinks.py]"),
    ("FR11", "Python correctness bug detection", "[backend/app/analysis/bugs.py]"),
    ("FR12", "Interprocedural taint analysis", "[backend/app/analysis/taint.py]"),
    ("FR13", "Quality metrics computation", "[backend/app/analysis/quality.py]"),
    ("FR14", "Finding merge, deduplication, and cap at 80", "[backend/app/analysis/engine.py lines 15-29]"),
    ("FR15", "Damped quality score 0-100", "[backend/app/analysis/scorer.py]"),
    ("FR16", "Review persistence in SQLite", "[backend/app/db/models.py; backend/app/reviews/router.py lines 19-29]"),
    ("FR17", "Owner-only review listing and detail access", "[backend/app/reviews/router.py lines 32-57]"),
    ("FR18", "Health endpoint reporting analysis engines", "[backend/app/main.py lines 76-81]"),
    ("FR19", "Frontend served statically from FastAPI in production", "[backend/app/main.py lines 28-54; Dockerfile]"),
]
add_table(["ID", "Requirement", "File"], fr_rows)

add_heading_section("5.4 Non-Functional Requirements")
add_para("Security: Passwords hashed with bcrypt [backend/app/auth/security.py line 10]; JWT HS256 signing [backend/app/auth/security.py line 23]; owner-only authorization on review endpoints [backend/app/reviews/router.py lines 45-57]; CORS origins configurable [backend/app/main.py lines 17-25]. Rate limiting is NOT FOUND IN CODEBASE. Password complexity beyond length is NOT FOUND IN CODEBASE.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, indent=0.25)
add_para("Performance: Findings capped per pass (60) and merged output capped (80) [backend/app/analysis/engine.py line 12]; source code limited to 50,000 characters [backend/app/reviews/schemas.py line 7]; taint analysis bounded to 50 propagation passes [backend/app/analysis/taint.py line 220]. Performance test asserts <2 seconds for 50,000-character input [backend/tests/test_engine.py lines 45-51].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, indent=0.25)
add_para("Reliability: Fail-open parsing\u2014passes return no findings rather than raising on syntax errors [README.md line 306; backend/app/analysis/tokenizer.py lines 247-269].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, indent=0.25)
add_para("Usability: React SPA with React Router navigation [frontend/src/App.tsx]; form validation on register/login [frontend/src/pages/Login.tsx; frontend/src/pages/Register.tsx].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=6, indent=0.25)
add_para("Portability: Docker single-container build [Dockerfile]; Render deployment configuration [render.yaml].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("5.5 API Specification")
add_para("Table 5.3: API endpoints", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.0)
api_rows = [
    ("POST", "/api/auth/register", "Register a new user", "No", "{email, password}", "{id, email}, 201"),
    ("POST", "/api/auth/login", "Authenticate and receive JWT", "No", "{email, password}", "{access_token, token_type}, 200"),
    ("POST", "/api/reviews", "Create a code review", "Yes", "{source_code, filename?}", "ReviewOut, 201"),
    ("GET", "/api/reviews", "List authenticated user\u2019s reviews", "Yes", "None", "[ReviewSummary], 200"),
    ("GET", "/api/reviews/{id}", "Get a single review (owner only)", "Yes", "None", "ReviewDetail, 200"),
    ("GET", "/api/health", "Health check with engine list", "No", "None", "{status, engines}, 200"),
]
add_table(["Method", "Endpoint", "Purpose", "Auth required", "Request body", "Response"], api_rows)
add_para("[backend/app/auth/router.py; backend/app/reviews/router.py; backend/app/main.py]", size=11, italic=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=12, indent=0.25)

add_heading_section("5.6 System Requirements")
add_para("Software:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.25)
sys_sw = [
    "Python 3.12+ (Dockerfile uses python:3.12-slim) [Dockerfile line 13]",
    "Node.js 22+ for frontend build [Dockerfile line 5]",
    "pip and npm package managers [backend/requirements.txt; frontend/package.json]",
]
for s in sys_sw:
    add_bullet(s)
add_para("Setup and run steps:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent=0.25)
add_para("Backend:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, indent=0.5)
add_para("cd backend\npython3 -m venv .venv\nsource .venv/bin/activate\npip install -r requirements.txt\ncp .env.example .env\nuvicorn app.main:app --reload --port 8000", size=11, name="Consolas", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6, indent=0.5)
add_para("Frontend:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=2, indent=0.5)
add_para("cd frontend\nnpm install\nnpm run dev", size=11, name="Consolas", align=WD_ALIGN_PARAGRAPH.LEFT, space_after=12, indent=0.5)
add_para("NOT FOUND IN CODEBASE \u2013 exact hardware specifications (RAM, CPU, disk) are not specified in the repository.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent=0.25)

add_heading_section("5.7 Diagrams")
add_para("Figure 5.1: Use Case Diagram", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
uc_mermaid = """graph LR
    Actor((User))
    Actor -->|Register/Login| Auth[Authentication]
    Actor -->|Submit code| Submit[Submit Review]
    Actor -->|View results| Results[View Review Results]
    Actor -->|View history| History[Review History]
    Auth -->|JWT token| Backend[Backend API]
    Submit --> Backend
    Results --> Backend
    History --> Backend"""
add_mermaid_block("Figure 5.1: Use Case Diagram", uc_mermaid)

add_para("Figure 5.2: Data Flow Diagram Level 0", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
dfd0_mermaid = """graph TD
    User((User)) -->|Submit code + JWT| Backend[FastAPI Backend]
    Backend -->|Run analysis| Engine[Analysis Engine]
    Engine -->|Findings + score| DB[(SQLite Database)]
    DB -->|Store review| Backend
    Backend -->|Return results| User"""
add_mermaid_block("Figure 5.2: Data Flow Diagram Level 0", dfd0_mermaid)

add_para("Figure 5.3: Data Flow Diagram Level 1 \u2013 Review Submission Flow", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
dfd1_mermaid = """graph TD
    User((User)) -->|POST /api/reviews| API[API Gateway]
    API -->|Authenticate| Auth[Auth Service]
    Auth -->|Validate JWT| Pipeline[Review Pipeline]
    Pipeline -->|Detect language| Detect[Language Detection]
    Pipeline -->|Run 6 passes| Passes[Analysis Passes]
    Passes -->|Merge + dedup| Merge[Merge Engine]
    Merge -->|Score| Score[Quality Scorer]
    Score -->|Persist| DB[(SQLite)]
    DB -->|ReviewOut| API
    API -->|JSON response| User"""
add_mermaid_block("Figure 5.3: Data Flow Diagram Level 1 \u2013 Review Submission Flow", dfd1_mermaid)

add_para("Figure 5.4: Sequence Diagram \u2013 Review Submission", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
seq_mermaid = """sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant D as SQLite
    U->>F: Enter code and click Run review
    F->>B: POST /api/reviews (JWT)
    B->>B: Authenticate user
    B->>B: run_review() pipeline
    B->>D: INSERT review
    D-->>B: Review row
    B-->>F: ReviewOut JSON
    F-->>U: Render Results page"""
add_mermaid_block("Figure 5.4: Sequence Diagram \u2013 Review Submission", seq_mermaid)

add_para("Figure 5.5: Class Diagram", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
cls_mermaid = """classDiagram
    class User {
        int id
        string email
        string hashed_password
        datetime created_at
    }
    class Review {
        int id
        int owner_id
        string language
        text source_code
        json findings
        int score
        datetime created_at
    }
    class Finding {
        string rule_id
        string title
        string severity
        int line
        string explanation
        string suggestion
        string source
        string evidence
        string confidence
    }
    User "1" -- "many" Review : owns"""
add_mermaid_block("Figure 5.5: Class Diagram", cls_mermaid)

doc.save(OUT_PATH)
print(f"Part 3 saved to {OUT_PATH}")