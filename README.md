# LLM-Powered Secure Code Review Assistant

Automated code quality and security analysis for student projects. Students paste or upload source code and receive a review with severity-ranked findings, plain-English explanations, fix suggestions, and an overall code-quality score.

## What it does

The application accepts source code (pasted text or uploaded file), detects the programming language, runs a built-in analysis engine over it, and returns a severity-ranked set of findings plus a quality score from 0 to 100. Nothing leaves the machine: there is no model endpoint, no API key, and no network call in the review path.

Users register with an email and password, authenticate with JWT tokens, and can view their review history on a dashboard. Each review is owned by the submitting user; other users cannot read another user's reviews.

## Analysis engine

Reviews are produced entirely by a built-in engine. It runs six analysis passes over the source, sharing one tokenizer:

1. **Regex rules** — 14 security patterns over every line. Comments are masked before matching, so a commented-out credential is not reported.
2. **Taint tracking** — untrusted input is followed to dangerous calls, across function boundaries. Python uses the `ast` module; JavaScript, Java, C and C++ use a token-based function inventory with brace matching.
3. **Secret detection** — Shannon entropy plus known token prefixes (AWS keys, Stripe keys, GitHub tokens). Secret values are redacted in reports.
4. **Python AST analysis** — semantic checks such as mutable default arguments, bare `except` clauses, and HTTP clients created without a timeout.
5. **Semantic catalogue** — per-language dangerous patterns (weak ciphers, `Runtime.exec`, `strcat`, `document.write`).
6. **Quality metrics** — function length, cyclomatic complexity, nesting depth, parameter count, leftover debug output, and TODO comments.

Taint findings are reported as **high** confidence when the flow stays inside one function and **medium** confidence when it crosses a function boundary or comes from the token-based path. The call graph for non-Python languages is inferred from brace matching, so a medium finding is a prompt to look, not a proof.

Findings from every pass are merged and deduplicated by line, severity and title, then capped at 80.

## Features

- Email/password registration and login with JWT bearer tokens
- Submit source code by pasting or uploading a file
- Automatic language detection (Python, JavaScript, Java, C, C++)
- Six-pass built-in analysis engine, with no API key and no network access
- Severity-ranked findings: critical, high, medium, low
- Confidence label on every finding: high or medium
- Plain-English explanations and fix suggestions per finding
- Evidence snippet showing the code that triggered the finding
- Overall code-quality score with damping for repeated findings
- Review history dashboard, newest first
- Owner-only access to individual reviews
- CORS enabled for local frontend development

## Tech stack

Backend:
- Python 3 (standard library analysis engine; `ast` for Python, a hand-written tokenizer otherwise)
- FastAPI
- SQLAlchemy 2 with SQLite
- PyJWT for authentication
- bcrypt for password hashing
- pydantic-settings for configuration
- httpx, used only by the test client
- pytest for tests

Frontend:
- React
- Vite
- Tailwind CSS
- React Router
- lucide-react icons
- vitest and Testing Library for tests

## Repository layout

```
llm_code_reviewer/
Dockerfile            builds the frontend and serves it from FastAPI
.dockerignore
backend/
  app/
    main.py            FastAPI app, CORS, lifespan startup, health endpoint, router mounting
    config.py          settings loaded from .env
    db/
      session.py       SQLite engine, session dependency, Base
      models.py        User and Review SQLAlchemy models
    auth/
      router.py        POST /api/auth/register, POST /api/auth/login
      security.py      bcrypt hashing, JWT encode/decode
      dependencies.py  get_current_user dependency
    reviews/
      router.py        POST /api/reviews, GET /api/reviews, GET /api/reviews/{id}
      schemas.py       Pydantic request/response models
    analysis/
      tokenizer.py     shared tokenizer; comment and string masking
      detect.py        language detection from filename and content
      rules.py         static analysis rule definitions
      static_scanner.py line-by-line rule scanner
      ast_analyzer.py  scope-aware Python AST checks
      taint.py         two-phase interprocedural taint analysis
      tokens.py        brace-matched function inventory for non-Python languages
      secrets.py       entropy and prefix secret detection
      sinks.py         per-language sources, sinks and semantic patterns
      quality.py       maintainability metrics
      engine.py        runs every pass, merges and deduplicates findings
      scorer.py        damped severity-weighted 0-100 score
      pipeline.py      detect language, run engine, score
  tests/
      pytest suite for auth, tokenizer, sinks, secrets, AST, taint, quality,
      scoring, engine, pipeline and the API
frontend/
  src/
    main.tsx           entry point
    App.tsx            router shell
    api.ts             fetch client with JWT interceptor
    index.css          design system and workspace layout
    components/        Workspace, ErrorBoundary, ProtectedRoute, CodeEditor, ScoreDial,
                       SeverityBadge, FindingCard, DiffPreview, CopyButton, ScanLoader,
                       EmptyState
    pages/             Landing, Login, Register, Submit, Results, History
    test/setup.ts      vitest setup
  vite.config.ts
```

## API endpoints

All backend endpoints are prefixed with `/api`.

Authentication:
- `POST /api/auth/register` — body `{email, password}`, returns `{id, email}`, status 201. Password must be at least 8 characters.
- `POST /api/auth/login` — body `{email, password}`, returns `{access_token, token_type}`

Reviews:
- `POST /api/reviews` — body `{source_code, filename?}`, requires auth, returns the created review
- `GET /api/reviews` — requires auth, returns list of the current user's reviews newest first
- `GET /api/reviews/{id}` — requires auth and ownership, returns the full review including `source_code` and findings

Other:
- `GET /api/health` — returns `{"status": "ok", "engines": ["rules", "taint", "secrets", "ast", "sinks", "quality"]}`

A finding is returned as:

```json
{
  "rule_id": "TAINT001",
  "title": "Untrusted data reaches a dangerous call",
  "severity": "high",
  "line": 3,
  "explanation": "...",
  "suggestion": "...",
  "source": "taint",
  "fixed_snippet": null,
  "evidence": "os.system(user_input)",
  "confidence": "high",
  "related_lines": []
}
```

`source` is one of `static`, `taint`, `secrets`, `ast`, `sinks` or `quality`, which lets the UI label where a finding came from.

## No API key required

There is nothing to configure and nothing to download. The engine is pure Python standard library: `ast` for Python parsing and a hand-written tokenizer for everything else. A review of a few hundred lines completes in milliseconds and is deterministic for a given input.

The project name is kept for continuity, but no language model is involved at review time.

## Configuration

Copy `backend/.env.example` to `backend/.env` and edit the value:

```
SECRET_KEY=replace-with-a-random-32-byte-string
```

- `SECRET_KEY` — signing key for JWT tokens. Must be at least 32 bytes for HS256. Replace the default before any real use, otherwise anyone can forge tokens.

That is the only setting for local development. `DATABASE_URL` and `TOKEN_EXPIRE_DAYS` also exist in `app/config.py` with working defaults and can be overridden through the environment.

### Environment variables

| Variable | Default | What it does |
| --- | --- | --- |
| `SECRET_KEY` | a dev placeholder | JWT signing key. Set this in any deployment. |
| `DATABASE_URL` | `sqlite:///./reviews.db` | SQLAlchemy URL. Point it at a mounted volume so reviews survive a restart. |
| `CORS_ORIGINS` | the two local dev servers | Comma-separated browser origins. Only needed when the frontend is served from a different host than the API. |
| `STATIC_DIR` | unset | Directory of the built frontend to serve from the same origin. Unset in development. |
| `PORT` | `8000` | Port the server listens on. |
| `TOKEN_EXPIRE_DAYS` | `30` | How long a login stays valid. |

## Deploying

The app is a FastAPI server and a static frontend. Two ways to put it online.

### Option 1 — one container (recommended)

The `Dockerfile` builds the React app and serves it from FastAPI, so the whole
thing runs on one origin and there is no CORS to configure.

```
docker build -t code-reviewer .
docker run -d -p 8000:8000 \
  -e SECRET_KEY="a-real-random-32-byte-secret-key" \
  -v code-reviewer-data:/app/data \
  code-reviewer
```

Then open `http://localhost:8000`.

The `/app/data` volume holds the SQLite file. Without a volume the reviews are
lost when the container is replaced.

That image runs as-is on **Render**, **Railway**, **Fly.io**, **Google Cloud Run**,
**AWS ECS**, or any VPS with Docker. On Render and Railway, point the service at
the `Dockerfile` in the repository root, add a disk mounted at `/app/data`, and
set `SECRET_KEY`.

### Option 2 — frontend and backend on separate hosts

Deploy the frontend to **Vercel** or **Netlify** and the backend to **Render**,
**Railway** or **Fly.io**.

Frontend build settings:

```
Build command:       npm run build
Output directory:    dist
Environment:         VITE_API_BASE=https://your-backend.example.com
```

Backend settings:

```
Environment:         SECRET_KEY=<random 32+ bytes>
                     CORS_ORIGINS=https://your-frontend.vercel.app
                     DATABASE_URL=sqlite:////data/reviews.db
```

`VITE_API_BASE` is baked into the frontend bundle at build time, so set it
before the build runs. `CORS_ORIGINS` must list the frontend's exact origin.

### Before you go live

- Set `SECRET_KEY` to a random value of at least 32 bytes. The default in the
  repository is a placeholder, and anyone who knows it can forge tokens.
- Mount a persistent disk for the database, or point `DATABASE_URL` at a hosted
  Postgres and add the driver to `backend/requirements.txt`.
- The review source code is stored verbatim. If you deploy this for other
  people, that is their code sitting in your database — worth saying in your
  privacy note.

### Checking a deployment

```
curl https://your-app.example.com/api/health
```

Expected:

```json
{"status": "ok", "engines": ["rules", "taint", "secrets", "ast", "sinks", "quality"]}
```

## How to run

Backend:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`.

Frontend:

```
cd frontend
npm install
npm run dev
```

The app is available at `http://localhost:5173` and calls the backend at `http://localhost:8000`.

To run the built frontend from the backend on one port, as a deployment does:

```
cd frontend && npm run build && cd ..
cd backend && STATIC_DIR=../frontend/dist .venv/bin/uvicorn app.main:app --port 8000
```

Run backend tests:

```
cd backend
source .venv/bin/activate
pytest
```

Run frontend tests:

```
cd frontend
npm test
```

Build frontend for production:

```
cd frontend
npm run build
```

## Design notes

- Every pass is deterministic and offline. No pass can fail a review: a pass that cannot parse the source returns no findings rather than raising.
- Taint analysis runs in two phases. The first works bottom-up and computes, per function, whether data flows to a sink or a return value, without assuming any parameter is tainted. The second walks top-down from real sources, so a helper called with a constant does not produce a false positive.
- The score starts at 100 and is reduced per finding: critical 20, high 10, medium 5, low 2. Repeated findings of the same severity are damped — full weight, then 70%, 50%, 35%, and 30% for everything after — because a linear penalty drove any realistic file to 0 and made the number meaningless.
- Frontend styling avoids AI-template defaults: no purple gradients, no emoji icons, no generated look. The interface uses a "Graded Paper" palette — warm paper background, cobalt accent, a dark code panel — with severity rendered as rubber-stamp badges, flagged lines underlined in red pen, and the score drawn as a circled grade.
- All interactive elements have visible focus states.

## License

MIT
