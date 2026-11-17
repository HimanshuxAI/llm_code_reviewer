import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth.router import router as auth_router
from app.db.session import Base, engine
from app.reviews.router import router as reviews_router

DEFAULT_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


def cors_origins() -> list[str]:
    """Allowed browser origins, from the CORS_ORIGINS environment variable.

    Comma-separated. Unset means the local dev servers only; a deployment
    sets it to the frontend's public URL.
    """
    raw = os.getenv("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or DEFAULT_ORIGINS


def mount_frontend(app: FastAPI, directory: str | Path) -> bool:
    """Serve the built SPA from the same origin as the API.

    One container, one URL, and no CORS to configure. Returns False when the
    directory has no index.html, so a source checkout without a frontend
    build still starts.
    """
    root = Path(directory).resolve()
    index = root / "index.html"
    if not index.is_file():
        return False

    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        # A real file under the root is served as-is; anything else is a
        # client-side route, which gets the app shell.
        if full_path:
            candidate = (root / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(root):
                return FileResponse(candidate)
        return FileResponse(index)

    return True


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="LLM Code Reviewer", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engines": ["rules", "taint", "secrets", "ast", "sinks", "quality"],
    }


# A single-container deployment sets STATIC_DIR to the built frontend. In
# development it stays unset and Vite serves the frontend on its own port.
_static_dir = os.getenv("STATIC_DIR", "")
if _static_dir:
    mount_frontend(app, _static_dir)
