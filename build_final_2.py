#!/usr/bin/env python3
"""Part 2: Front matter + Chapter 1."""
import docx
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = "/Users/himanshu/Downloads/LLM_Code_Reviewer_Final_Report.docx"
doc = Document(OUT)

def set_run(run, size=12, bold=False, italic=False, name="Times New Roman"):
    run.font.name = name; run.font.size = Pt(size); run.bold = bold; run.italic = italic
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn('w:rFonts'))
    if rfonts is None:
        rfonts = OxmlElement('w:rFonts'); rpr.append(rfonts)
    rfonts.set(qn('w:ascii'), name); rfonts.set(qn('w:hAnsi'), name); rfonts.set(qn('w:cs'), name)

def para(text="", size=12, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         space_after=12, space_before=0, indent_first=0.25, line_spacing=1.5,
         name="Times New Roman", caps=False, left_indent=0.0):
    p = doc.add_paragraph(); p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after); pf.space_before = Pt(space_before)
    pf.line_spacing = line_spacing; pf.left_indent = Inches(left_indent)
    if indent_first > 0: pf.first_line_indent = Inches(indent_first)
    run = p.add_run(text.upper() if caps else text)
    set_run(run, size=size, bold=bold, italic=italic, name=name); return p

def heading_chapter(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format; pf.space_before = Pt(24); pf.space_after = Pt(18); pf.line_spacing = 1.0
    run = p.add_run(text.upper()); set_run(run, size=18, bold=True, name="Times New Roman")

def heading_section(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format; pf.space_before = Pt(12); pf.space_after = Pt(6); pf.line_spacing = 1.0
    run = p.add_run(text.upper()); set_run(run, size=12, bold=True, name="Times New Roman")

def heading_sub(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format; pf.space_before = Pt(10); pf.space_after = Pt(4); pf.line_spacing = 1.0
    run = p.add_run(text); set_run(run, size=12, bold=True, name="Times New Roman")

def bullet(text, indent=0.5):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format; pf.left_indent = Inches(indent); pf.first_line_indent = Inches(-0.25)
    pf.space_after = Pt(6); pf.line_spacing = 1.5
    run = p.add_run("\u2022  " + text); set_run(run, size=12, name="Times New Roman"); return p

def table(headers, rows, caption=None):
    if caption:
        para(caption, size=12, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=6, space_before=6, indent_first=0.0)
    t = doc.add_table(rows=1, cols=len(headers)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]; cell.text = ""
        run = cell.paragraphs[0].add_run(h); set_run(run, size=11, bold=True, name="Times New Roman")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(val)); set_run(run, size=11, name="Times New Roman")
    para("", size=6, space_after=6, indent_first=0.0); return t

def page_break(): doc.add_page_break()

# ============ COVER PAGE ============
para("", space_after=30)
para("A PROJECT REPORT ON", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12, indent_first=0.0)
para("LLM-Powered Secure Code Review Assistant", size=18, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("SUBMITTED TO", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, indent_first=0.0)
para("MIT SCHOOL OF COMPUTING, LONI, PUNE IN PARTIAL FULFILLMENT OF THE REQUIREMENTS FOR THE AWARD OF THE DEGREE", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("BACHELOR OF TECHNOLOGY", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("(Computer Science & Engineering / Information Technology)", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("BY", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, indent_first=0.0)
para("Candidate Name\tPRN/ Enrollment No: -----", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("Under the guidance of", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, indent_first=0.0)
para("Prof./Dr/ \u2026\u2026\u2026.", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("DEPARTMENT OF COMPUTER SCIENCE AND ENGINEERING", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=8, indent_first=0.0)
para("MIT SCHOOL OF COMPUTING", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("MIT Art, Design and Technology University", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("Rajbaug Campus, Loni-Kalbhor, Pune 412201", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("20__- __", size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, indent_first=0.0)
page_break()

# ============ CERTIFICATE ============
heading_section("CERTIFICATE")
para("", space_after=10)
para("This is to certify that the project report entitled", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("LLM-Powered Secure Code Review Assistant", size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, indent_first=0.0)
para("Submitted by", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("Name of the Candidate\tPRN/ Enrollment No: -----", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16, indent_first=0.0)
para("is a bonafide work carried out by them under the supervision of Prof./Dr/ \u2026\u2026\u2026. and it is submitted towards the partial fulfillment of the requirement of MIT ADT University, Pune for the award of the degree of Bachelor of Technology (Computer Science and Engineering).", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=24, indent_first=0.0)
para("Place: PUNE" + "\t"*6 + "Guide" + "\t"*6 + "Head of Department", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
para("Date: __________" + "\t"*6 + "Prof./Dr/ \u2026\u2026\u2026." + "\t"*6 + "Dr/ \u2026\u2026\u2026.", size=12, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, indent_first=0.0)
page_break()

# ============ DECLARATION ============
heading_section("DECLARATION")
para("I hereby declare that the project report entitled \u201cLLM-Powered Secure Code Review Assistant\u201d submitted to MIT School of Computing, MIT ADT University, Pune, in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology is a bonafide record of work carried out by me under the supervision of Prof./Dr. \u2026\u2026\u2026. This report has not been submitted previously to any other university or institution for the award of any degree or diploma.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=24, indent_first=0.25)
para("Place: PUNE" + "\t"*8 + "Signature of Candidate", size=12, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent_first=0.25)
para("Date: __________" + "\t"*8 + "Name: -----", size=12, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4, indent_first=0.25)
page_break()

# ============ ACKNOWLEDGEMENT ============
heading_section("ACKNOWLEDGEMENT")
para("NOT FOUND IN CODEBASE \u2013 author to write. The repository does not contain an acknowledgement section. The author should acknowledge the project guide, department faculty, family, and friends who supported the project work.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=24, indent_first=0.25)
page_break()

# ============ ABSTRACT ============
heading_section("ABSTRACT")
para("This project presents the LLM-Powered Secure Code Review Assistant, a full-stack web application for automated code quality and security analysis. The system accepts source code submitted by users through paste or file upload, detects the programming language among Python, JavaScript, Java, C, and C++, and executes a built-in analysis engine comprising six passes: regex security rules, secret detection using Shannon entropy and known token prefixes, Python abstract syntax tree (AST) semantic checks, a per-language semantic pattern catalogue, interprocedural taint analysis, and maintainability quality metrics. The engine operates entirely offline using the Python standard library, requiring no API key and making no network calls during the review path. Findings are severity-ranked with confidence levels, accompanied by plain-English explanations, fix suggestions, and evidence snippets, and aggregated into a damped quality score from 0 to 100. Users register and authenticate using email/password with bcrypt hashing and JSON Web Token (JWT) bearer tokens. Each review is owned by the submitting user and stored in a SQLite database, with owner-only access enforced on review history and detail endpoints. The frontend is a React single-page application served by Vite in development and statically by FastAPI in production via a single-container Docker build. The technology stack includes FastAPI, SQLAlchemy, PyJWT, bcrypt, React, Tailwind CSS, and React Router. The outcome is a deterministic, locally-executable code review tool suitable for student project evaluation without dependence on external language model services.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=24, indent_first=0.25)
page_break()

# ============ LIST OF FIGURES ============
heading_section("LIST OF FIGURES")
figures = [
    ("Figure 1.1", "System Context Diagram"),
    ("Figure 2.1", "System Architecture Diagram"),
    ("Figure 2.2", "Entity-Relationship Diagram"),
    ("Figure 5.1", "Use Case Diagram"),
    ("Figure 5.2", "Data Flow Diagram Level 0"),
    ("Figure 5.3", "Data Flow Diagram Level 1 \u2013 Review Submission Flow"),
    ("Figure 5.4", "Sequence Diagram \u2013 Review Submission"),
    ("Figure 5.5", "Class Diagram"),
    ("Figure 6.1", "Landing Page with Pipeline and Rule Catalogue"),
    ("Figure 6.2", "Submit Page with Editor and Pipeline Sidebar"),
    ("Figure 6.3", "Results Page Showing Score Dial, Flagged Code, and Findings"),
    ("Figure 6.4", "History Page with Review Table"),
]
table(["Figure Number", "Title", "Page Number"], [(f[0], f[1], "-") for f in figures])
doc.add_paragraph()
page_break()

# ============ LIST OF TABLES ============
heading_section("LIST OF TABLES")
tables = [
    ("Table 2.1", "Database Schema"),
    ("Table 4.1", "Development Phases Inferred from Commit History"),
    ("Table 4.2", "Development and Deployment Tools"),
    ("Table 5.1", "User Classes and Capabilities"),
    ("Table 5.2", "Functional Requirements"),
    ("Table 5.3", "API Endpoints"),
    ("Table 7.1", "Backend Test Modules"),
    ("Table 7.2", "Frontend Test Modules"),
    ("Table 7.3", "Representative Test Cases (Sample)"),
    ("Table N.1", "Abbreviations and Acronyms"),
]
table(["Table Number", "Title", "Page Number"], [(t[0], t[1], "-") for t in tables])
doc.add_paragraph()
page_break()

# ============ CHAPTER 1 ============
heading_chapter("Chapter 1: Introduction")

heading_section("1.1 Introduction")
para("The LLM-Powered Secure Code Review Assistant is a web-based static code analysis system developed for automated review of source code submissions. The system operates in the domain of software development education and secure coding practice, where program code must be examined for security vulnerabilities, coding defects, and maintainability concerns before final submission. The application follows a client-server model. A React frontend provides the interface for user authentication, code submission, and result visualization. A FastAPI backend executes the analysis engine, manages authenticated user sessions, and persists review records in a SQLite database. The analysis is carried out by six local passes that function without external model endpoints, API keys, or network access during the review path [README.md; backend/app/main.py; backend/app/analysis/engine.py].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent_first=0.25)

heading_section("1.2 Existing Work")
para("NOT FOUND IN CODEBASE \u2013 author to write. The README and repository documentation do not describe or cite any existing systems, tools, or prior work that this project replaces or improves upon, beyond the general statement that an external LLM reviewer path was removed in favor of a built-in engine [docs/specs/2026-11-16-builtin-analysis-engine-design.md; README.md]. The author should describe existing approaches such as commercial static application security testing (SAST) tools, LLM-based code reviewers, and open-source linters that motivated this project.", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent_first=0.25)

heading_section("1.3 Motivation")
para("The system addresses the problem of dependence on external language model infrastructure for code review. The prior design called an external LLM endpoint, which required an API key, an internet connection, and a third-party service, and degraded silently when the key was missing or the endpoint failed [docs/specs/2026-11-16-builtin-analysis-engine-design.md lines 7-13; README.md lines 148-152]. The code implements a replacement built-in analysis engine written against the Python standard library, so that no network call, no API key, and no external model are involved at review time [README.md lines 148-152; backend/app/analysis/engine.py]. Additionally, the system provides user authentication and review history so that individual submissions are attributed to their owners and remain accessible on a dashboard [backend/app/auth/router.py; backend/app/reviews/router.py; frontend/src/pages/History.tsx].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent_first=0.25)

heading_section("1.4 Objectives")
objectives = [
    "To provide offline static analysis of source code using only the Python standard library, with no API key and no network calls in the review path [README.md lines 148-152; backend/app/analysis/pipeline.py].",
    "To detect the programming language of submitted code from filename extension and content signatures, supporting Python, JavaScript, Java, C, and C++ [backend/app/analysis/detect.py].",
    "To run six analysis passes: regex security rules, secret detection, Python AST checks, semantic pattern detection, taint tracking, and quality metrics [backend/app/analysis/engine.py lines 46-60].",
    "To return severity-ranked findings with confidence levels, plain-English explanations, fix suggestions, and evidence snippets [backend/app/analysis/rules.py; backend/app/analysis/secrets.py; backend/app/analysis/ast_analyzer.py; backend/app/analysis/sinks.py; backend/app/analysis/taint.py; backend/app/analysis/quality.py].",
    "To compute a damped quality score from 0 to 100 based on severity-weighted findings with reduced penalty for repeated findings [backend/app/analysis/scorer.py].",
    "To enable user registration and login with email/password, bcrypt password hashing, and JWT bearer authentication [backend/app/auth/router.py; backend/app/auth/security.py].",
    "To enforce owner-only access to submitted reviews and review history [backend/app/reviews/router.py lines 32-57].",
    "To serve a React frontend for code submission, results viewing, and history browsing, either from Vite in development or statically from FastAPI in production [frontend/src/App.tsx; backend/app/main.py lines 28-54; Dockerfile].",
]
for obj in objectives: bullet(obj)

heading_section("1.5 Scope")
para("The system implements the following features, as verified in the source code:", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent_first=0.25)
scope_impl = [
    "User registration, login, and JWT-based authentication [backend/app/auth/router.py; backend/app/auth/security.py].",
    "Source code submission by paste or file upload [frontend/src/pages/Submit.tsx].",
    "Automatic language detection for Python, JavaScript, Java, C, and C++ [backend/app/analysis/detect.py].",
    "Six-pass offline analysis engine producing severity-ranked findings with confidence labels [backend/app/analysis/engine.py].",
    "Quality score from 0 to 100 with damping for repeated findings [backend/app/analysis/scorer.py].",
    "Review history dashboard listing the authenticated user\u2019s reviews newest first [backend/app/reviews/router.py lines 32-42; frontend/src/pages/History.tsx].",
    "Owner-only access to individual review details including source code and findings [backend/app/reviews/router.py lines 45-57].",
    "Health endpoint reporting the analysis engines [backend/app/main.py lines 76-81].",
    "Single-container Docker deployment serving the built frontend from FastAPI [Dockerfile; render.yaml].",
]
for s in scope_impl: bullet(s)

para("The system does not implement the following, as no corresponding code or TODO markers were found:", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=8, indent_first=0.25)
scope_out = [
    "Any language model inference or external API call during review [README.md line 152].",
    "Pagination for review history [backend/app/reviews/router.py lines 32-42].",
    "Rate limiting on authentication or submission endpoints [backend/app/auth/router.py; backend/app/reviews/router.py].",
    "Password complexity requirements beyond length [backend/app/auth/router.py line 14].",
    "Token revocation or refresh mechanism [backend/app/auth/security.py; frontend/src/api.ts].",
    "Caching of analysis results [ASSUMPTION: no caching code found in backend/app or frontend/src].",
    "Dark mode theme; the design document lists it as optional and not in version 1 [docs/specs/2026-11-17-graded-paper-design.md line 32].",
    "Admin role or user management beyond self-service registration [backend/app/auth/dependencies.py; backend/app/db/models.py].",
]
for s in scope_out: bullet(s)

para("No TODO or FIXME markers were found in backend/app or frontend/src source files [grep of source trees].", size=12, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=12, indent_first=0.25)
page_break()

doc.save(OUT)
print("Part 2 saved. Paragraphs:", len(doc.paragraphs), "Tables:", len(doc.tables))