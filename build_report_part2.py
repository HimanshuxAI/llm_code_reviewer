#!/usr/bin/env python3
"""Part 2: Chapters 2-5."""
import docx
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
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

# ---------- CHAPTER 2 ----------
add_heading_chapter("CHAPTER 2: CONCEPTS AND METHODS")

add_heading_section("2.1 Definitions")
add_para("The following technologies, frameworks, libraries, databases, and algorithms are used in the system, as verified from the dependency files and source code.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent=0.25)

add_heading_sub("Backend (Python)")
backend_defs = [
    ("Python 3", "The backend is written in Python 3. The Dockerfile specifies python:3.12-slim as the runtime image [Dockerfile line 13]."),
    ("FastAPI", "A Python web framework used to build the REST API. Unpinned in backend/requirements.txt line 1. Used for route definition, dependency injection, request validation, and middleware [backend/app/main.py]."),
    ("Uvicorn", "The ASGI server used to run the FastAPI application. Specified as uvicorn[standard] in backend/requirements.txt line 2 [Dockerfile line 31]."),
    ("SQLAlchemy 2", "The object-relational mapper used for database access. Uses the 2.0-style Mapped and mapped_column typing [backend/app/db/models.py lines 4-33]. Unpinned in backend/requirements.txt line 3."),
    ("SQLite", "The relational database engine. Configured via SQLAlchemy with URL sqlite:///./reviews.db by default [backend/app/config.py line 7; backend/app/db/session.py line 12]."),
    ("Pydantic and pydantic-settings", "Used for request/response schema validation and environment-variable-based configuration. pydantic[email] is in backend/requirements.txt line 4; pydantic-settings line 5. Settings are defined in backend/app/config.py."),
    ("PyJWT", "Used to encode and decode JSON Web Tokens for authentication [backend/app/auth/security.py lines 20-29]. Specified as pyjwt in backend/requirements.txt line 6."),
    ("bcrypt", "Used to hash and verify user passwords [backend/app/auth/security.py lines 9-17]. Specified in backend/requirements.txt line 7."),
    ("pytest", "The test framework for the backend. Specified in backend/requirements.txt line 10. Tests reside in backend/tests/."),
    ("httpx", "A test-only dependency used by Starlette\u2019s TestClient [backend/requirements.txt line 9; backend/tests/conftest.py line 2]."),
    ("Analysis algorithms", "Six analysis passes implemented purely in the Python standard library (ast, tokenize, re, math, io, collections, datetime, contextlib, pathlib). No external machine-learning or analysis libraries are used [README.md lines 148-152; backend/app/analysis/engine.py]."),
]
for term, desc in backend_defs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Inches(0.25)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    run = p.add_run(term + ": ")
    set_run_font(run, size=12, bold=True, name="Times New Roman")
    run2 = p.add_run(desc)
    set_run_font(run2, size=12, name="Times New Roman")

add_heading_sub("Frontend (TypeScript / React)")
frontend_defs = [
    ("React", "Version ^19 (indicated by @types/react ^19.3.0 in frontend/package.json line 18). Used for the user interface [frontend/src/App.tsx]."),
    ("Vite", "Version ^8.3.6 [frontend/package.json line 26]. Used as the build tool and development server [frontend/vite.config.ts]."),
    ("Tailwind CSS", "Version ^4.3.5 [frontend/package.json line 24]. Used as the utility-first CSS framework, integrated via @tailwindcss/vite [frontend/vite.config.ts line 4; frontend/src/index.css line 1]."),
    ("React Router DOM", "Version ^7.18.5 [frontend/package.json line 31]. Used for client-side routing [frontend/src/App.tsx]."),
    ("lucide-react", "Version ^1.73.0 [frontend/package.json line 30]. Used for icons [frontend/src/pages/Login.tsx line 2; multiple components]."),
    ("vitest", "Version ^5.1.0 [frontend/package.json line 27]. Used for frontend unit testing [frontend/src/pages/Results.test.tsx]."),
    ("jsdom", "Version ^29.1.1 [frontend/package.json line 22]. Used as the test environment for vitest [frontend/vite.config.ts line 9]."),
    ("TypeScript", "Version ~7.0.2 [frontend/package.json line 25]. Used for type-safe frontend development [frontend/tsconfig.json]."),
]
for term, desc in frontend_defs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Inches(0.25)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    run = p.add_run(term + ": ")
    set_run_font(run, size=12, bold=True, name="Times New Roman")
    run2 = p.add_run(desc)
    set_run_font(run2, size=12, name="Times New Roman")

add_heading_sub("DevOps and Deployment")
devops_defs = [
    ("Docker", "Used for single-container deployment. The Dockerfile builds the React frontend in a Node 22-alpine stage and serves it from the Python runtime [Dockerfile lines 5-31]."),
    ("Render", "A deployment target documented in render.yaml, which configures a web service using the Dockerfile with a persistent disk mounted at /app/data [render.yaml lines 1-21]."),
]
for term, desc in devops_defs:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Inches(0.25)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    run = p.add_run(term + ": ")
    set_run_font(run, size=12, bold=True, name="Times New Roman")
    run2 = p.add_run(desc)
    set_run_font(run2, size=12, name="Times New Roman")

add_heading_section("2.2 Architecture")
add_para("The system follows a client-server, RESTful architecture. The frontend is a React single-page application that communicates with the FastAPI backend over HTTP using JSON. Authentication is stateless, using JWT bearer tokens stored in browser localStorage. The backend persists data to a SQLite database via SQLAlchemy. In production, the frontend is built statically and served from the same FastAPI process on one origin, eliminating cross-origin resource sharing (CORS) requirements [Dockerfile; backend/app/main.py lines 28-54; README.md lines 181-192].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent=0.25)

add_para("Folder structure:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6, indent=0.25)
folder_items = [
    "backend/app/main.py: FastAPI application entry point, CORS middleware, router mounting, health endpoint, SPA static-file serving, and database initialization on startup [backend/app/main.py lines 63-88].",
    "backend/app/config.py: Pydantic settings loaded from .env [backend/app/config.py lines 1-12].",
    "backend/app/db/session.py: SQLAlchemy engine, session factory, and get_db dependency [backend/app/db/session.py lines 1-22].",
    "backend/app/db/models.py: User and Review SQLAlchemy models [backend/app/db/models.py lines 13-34].",
    "backend/app/auth/router.py: Registration and login endpoints [backend/app/auth/router.py lines 22-38].",
    "backend/app/auth/security.py: Password hashing and JWT encode/decode [backend/app/auth/security.py lines 9-31].",
    "backend/app/auth/dependencies.py: get_current_user authentication dependency [backend/app/auth/dependencies.py lines 12-21].",
    "backend/app/reviews/router.py: Review create, list, and get endpoints [backend/app/reviews/router.py lines 13-57].",
    "backend/app/reviews/schemas.py: Pydantic schemas for review requests and responses [backend/app/reviews/schemas.py lines 1-44].",
    "backend/app/analysis/: The analysis engine containing tokenizer, language detection, rules, secret detection, AST analysis, taint analysis, semantic patterns, quality metrics, bugs, engine orchestrator, scorer, and pipeline [backend/app/analysis/].",
    "frontend/src/: React source code including pages, components, API client, and styles [frontend/src/].",
]
for item in folder_items:
    add_bullet(item)

add_para("Figure 2.1: System Architecture Diagram", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
arch_mermaid = """graph TD
    subgraph Client [Client: React SPA]
        UI[UI: Landing, Login, Register, Submit, Results, History]
        API[api.ts: fetch client with JWT interceptor]
    end

    subgraph Server [Server: FastAPI + SQLite]
        MW[CORS Middleware]
        AR[Auth Router /api/auth]
        RR[Reviews Router /api/reviews]
        HEALTH[/api/health]
        PIPE[pipeline.run_review()]
        ENG[engine.analyse(): 6 passes]
        SCOR[scorer.compute_score()]
        DB[(SQLite: users, reviews)]
    end

    Client -->|HTTP/JSON + Bearer JWT| Server
    UI --> API
    API --> MW
    MW --> AR
    MW --> RR
    MW --> HEALTH
    RR --> PIPE
    PIPE --> ENG
    PIPE --> SCOR
    AR --> DB
    RR --> DB"""
add_mermaid_block("Figure 2.1: System Architecture Diagram", arch_mermaid)

add_heading_section("2.3 Methods / Algorithms")
add_para("The analysis pipeline executes in the following order [backend/app/analysis/pipeline.py lines 5-9; backend/app/analysis/engine.py lines 46-60]:", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent=0.25)
steps = [
    "Language detection: The filename extension is checked first; if absent or unknown, content signatures are matched (def , import , #include, function , public class, etc.). Defaults to \"text\" if no match is found [backend/app/analysis/detect.py lines 15-23].",
    "Regex security rules: Comment-masked source is scanned line-by-line against 14 compiled regex rules (SEC001\u2013SEC012, QUAL001). Findings are capped at 60 per pass [backend/app/analysis/static_scanner.py lines 7-25; backend/app/analysis/rules.py lines 16-58].",
    "Secret detection: Shannon entropy is computed on string literals adjacent to credential-like names; known token prefixes (AWS AKIA, Stripe sk-, GitHub ghp_, JWT eyJ, etc.) are matched. Secrets are redacted to their first four characters in evidence output [backend/app/analysis/secrets.py lines 64-155].",
    "Python AST analysis (Python only): The source is parsed with ast.parse. Checks include mutable default arguments, broad except clauses, HTTP calls without timeout, open() without encoding, assert-as-authorization, undefined names, and others [backend/app/analysis/ast_analyzer.py lines 514-523].",
    "Semantic pattern catalogue: Per-language regex patterns detect dangerous constructs such as Java weak ciphers, JavaScript document.write() / new Function(), and C strcat() / scanf() [backend/app/analysis/sinks.py lines 106-135].",
    "Bug detection (Python only): Scope-aware detection of unused variables, unreachable code, list/dict mutation during iteration, unused imports, builtin shadowing, and incorrect comparisons [backend/app/analysis/bugs.py lines 99-413].",
    "Taint analysis: Two-phase interprocedural dataflow analysis. Phase 1 (bottom-up) computes, per function, which parameters can reach a sink or return value without assuming any parameter is tainted. Phase 2 (top-down) propagates taint from real sources through call sites and reports a sink only when tainted data reaches it. Python uses the AST; JavaScript, Java, C, and C++ use a token-based function inventory from brace matching [backend/app/analysis/taint.py lines 1-357; backend/app/analysis/tokens.py lines 1-118].",
    "Quality metrics: Maintainability checks for function length (>60 lines), cyclomatic complexity (>12), nesting depth (>4), parameter count (>5), leftover print() / console.log(), and TODO/FIXME/HACK/XXX comments [backend/app/analysis/quality.py lines 178-183].",
    "Merge and deduplicate: Findings from all passes are merged and deduplicated by line, severity, and title prefix, keeping the first pass that reports them. Capped at 80 total [backend/app/analysis/engine.py lines 15-29].",
    "Normalize: Missing evidence, confidence, and related_lines fields are filled with defaults [backend/app/analysis/engine.py lines 32-43].",
    "Score: A damped severity-weighted score from 0 to 100 is computed. Weights are critical 20, high 10, medium 5, low 2. Repeated findings of the same severity receive diminishing multipliers (1.0, 0.7, 0.5, 0.35, 0.3) [backend/app/analysis/scorer.py lines 2-23].",
]
for s in steps:
    add_bullet(s)

add_para("Taint analysis (token languages) step by step [backend/app/analysis/taint.py lines 360-702]:", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6, indent=0.25)
taint_steps = [
    "Tokens are generated and functions are identified by brace matching. Control-flow keywords are excluded to avoid phantom definitions [backend/app/analysis/tokens.py lines 33-97].",
    "A __module__ pseudo-function holds depth-0 statements so top-level code is scanned [backend/app/analysis/taint.py lines 632-655].",
    "Phase 1 anchors which locals hold external data from source calls or output-parameter calls [backend/app/analysis/taint.py lines 483-511].",
    "Phase 2 propagates taint through assignments and call arguments for up to 50 iterations, reporting sink hits with high or medium confidence [backend/app/analysis/taint.py lines 514-599].",
]
for s in taint_steps:
    add_bullet(s)

add_heading_section("2.4 Database Design")
add_para("The system uses two tables in SQLite, defined with SQLAlchemy ORM [backend/app/db/models.py lines 13-34].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent=0.25)

db_rows = [
    ("users", "id", "Integer", "Primary Key", "User identifier"),
    ("users", "email", "String(255)", "Unique, Indexed", "User email address"),
    ("users", "hashed_password", "String(255)", "Not null", "Bcrypt password hash"),
    ("users", "created_at", "DateTime", "Default utcnow", "Account creation timestamp"),
    ("reviews", "id", "Integer", "Primary Key", "Review identifier"),
    ("reviews", "owner_id", "Integer", "Foreign Key users.id, Indexed", "Owning user"),
    ("reviews", "language", "String(30)", "Not null", "Detected programming language"),
    ("reviews", "source_code", "Text", "Not null", "Submitted source code"),
    ("reviews", "findings", "JSON", "Default list", "Analysis findings"),
    ("reviews", "score", "Integer", "Not null", "Quality score 0-100"),
    ("reviews", "created_at", "DateTime", "Default utcnow", "Review creation timestamp"),
]
add_table(["Table", "Field", "Type", "Constraints", "Description"], db_rows, caption="Table 2.1: Database Schema")

add_para("Relationship: Review.owner references User.id (many-to-one); User.reviews is the inverse one-to-many relationship [backend/app/db/models.py lines 21, 35].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent=0.25)

add_para("Figure 2.2: Entity-Relationship Diagram", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6, indent=0.0)
er_mermaid = """erDiagram
    USER ||--o{ REVIEW : owns
    USER {
        int id PK
        string email UK
        string hashed_password
        datetime created_at
    }
    REVIEW {
        int id PK
        int owner_id FK
        string language
        text source_code
        json findings
        int score
        datetime created_at
    }"""
add_mermaid_block("Figure 2.2: Entity-Relationship Diagram", er_mermaid)

doc.save(OUT_PATH)
print(f"Part 2 saved to {OUT_PATH}")