"""Deployment plumbing: serving the built SPA and configuring CORS."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import cors_origins, mount_frontend


def _build_frontend(tmp_path):
    root = tmp_path / "dist"
    (root / "assets").mkdir(parents=True)
    (root / "index.html").write_text("<!doctype html><title>app shell</title>")
    (root / "assets" / "app.js").write_text("console.log('built')")
    return root


def test_mount_frontend_serves_the_app_at_the_root(tmp_path):
    app = FastAPI()
    assert mount_frontend(app, _build_frontend(tmp_path)) is True
    resp = TestClient(app).get("/")
    assert resp.status_code == 200
    assert "app shell" in resp.text


def test_client_side_route_falls_back_to_the_app_shell(tmp_path):
    """A deep link like /results/47 must not 404 — the router needs the shell."""
    app = FastAPI()
    mount_frontend(app, _build_frontend(tmp_path))
    resp = TestClient(app).get("/results/47")
    assert resp.status_code == 200
    assert "app shell" in resp.text


def test_built_assets_are_served(tmp_path):
    app = FastAPI()
    mount_frontend(app, _build_frontend(tmp_path))
    resp = TestClient(app).get("/assets/app.js")
    assert resp.status_code == 200
    assert "built" in resp.text


def test_api_routes_still_take_priority(tmp_path):
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"status": "ok"}

    mount_frontend(app, _build_frontend(tmp_path))
    resp = TestClient(app).get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_mount_frontend_declines_a_missing_build(tmp_path):
    assert mount_frontend(FastAPI(), tmp_path / "missing") is False


def test_cors_origins_default_to_the_local_dev_servers(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert cors_origins() == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_cors_origins_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example, https://alt.example")
    assert cors_origins() == ["https://app.example", "https://alt.example"]
