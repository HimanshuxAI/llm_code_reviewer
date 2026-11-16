# LLM-Powered Secure Code Review Assistant

AI-powered automated code quality and security analysis for student projects. Students paste or upload source code and receive a review with severity-ranked findings, plain-English explanations, fix suggestions, and an overall code-quality score.

## What it does

The application accepts source code (pasted text or uploaded file), detects the programming language, runs a static heuristic scanner, optionally calls a language model for additional findings, merges and deduplicates the results, and returns a severity-weighted quality score from 0 to 100.

Users register with an email and password, authenticate with JWT tokens, and can view their review history on a dashboard. Each review is owned by the submitting user; other users cannot read another user's reviews.

## Features

- Email/password registration and login with JWT bearer tokens
- Submit source code by pasting or uploading a file
- Automatic language detection (Python, JavaScript, Java, C, C++)
- Static heuristic security scanner that runs without any API key
- Optional LLM-based review through an OpenAI-compatible endpoint, off by default
- Works fully offline with no API key and no internet connection
- Severity-ranked findings: critical, high, medium, low
- Plain-English explanations and fix suggestions per finding
- Corrected code snippets when available
- Overall code-quality score (0-100)
- Review history dashboard, newest first
- Owner-only access to individual reviews
- CORS enabled for local frontend development

## Tech stack

Backend:
- Python 3
- FastAPI
- SQLAlchemy 2 with SQLite
- PyJWT for authentication
- bcrypt for password hashing
- pydantic-settings for configuration
- httpx for LLM API calls
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
      detect.py        language detection from filename and content
      rules.py         static analysis rule definitions
      static_scanner.py line-by-line rule scanner
      llm_reviewer.py  OpenAI-compatible LLM client with strict JSON parsing
      scorer.py        severity-weighted 0-100 score
      pipeline.py      merge and deduplicate static and LLM findings
    tests/
      pytest test suite for auth, scanner, scorer, pipeline, app, and API
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
- `GET /api/health` — returns `{"status": "ok"}`

## Running without an API key

The application is fully functional with no API key and no internet connection. The static
scanner is a local regex engine over 14 rules, so a review completes in roughly 15
milliseconds and returns real findings with a real score.

An API key is optional and only adds a second opinion. When `LLM_API_KEY` is empty the
model is never contacted. When a key is set but the endpoint is unreachable, the request
fails over to static findings rather than erroring, so a bad key can never break a review.

To enable the LLM review, get a free key and set one variable:

```
LLM_API_KEY=your-key-here
```

That is the only change needed. The default endpoint is the Gemini free tier through its
OpenAI-compatible interface, so `LLM_BASE_URL` and `LLM_MODEL` can stay as they are. Any
other OpenAI-compatible endpoint works by changing those two values instead.

## Configuration

Copy `backend/.env.example` to `backend/.env` and edit the values:

```
SECRET_KEY=replace-with-a-random-32-byte-string
LLM_API_KEY=
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=gemini-2.0-flash
LLM_TIMEOUT_SECONDS=30
```

- `SECRET_KEY` — signing key for JWT tokens. Must be at least 32 bytes for HS256. Replace the default before any real use, otherwise anyone can forge tokens.
- `LLM_API_KEY` — API key for the language model. Leave empty to run static analysis only.
- `LLM_BASE_URL` — base URL of an OpenAI-compatible chat completions endpoint.
- `LLM_MODEL` — model name to request.
- `LLM_TIMEOUT_SECONDS` — how long to wait for the model before falling back to static findings.

## How to run

Backend:

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env if you want LLM review
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

- The static scanner uses pure-Python regex rules and requires no external binaries or API keys, so the tool produces results even without configuring an LLM.
- LLM responses are parsed as strict JSON; malformed responses are discarded safely and static findings are still returned.
- Findings from static scan and LLM review are merged and deduplicated by line, severity, and title before scoring.
- Score starts at 100 and is reduced per finding: critical -20, high -10, medium -5, low -2, floored at 0.
- Frontend styling avoids AI-template defaults: no purple gradients, no emoji icons, no generated look. Severity uses color semantics (red critical, orange high, amber medium, gray low) and all interactive elements have visible focus states.

## License

MIT