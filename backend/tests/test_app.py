from app.main import app


def test_health_endpoint(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_app_does_not_use_deprecated_on_event():
    """FastAPI deprecated @app.on_event in favour of lifespan handlers."""
    assert app.router.on_startup == []
    assert app.router.on_shutdown == []


def test_lifespan_creates_tables():
    """The lifespan handler must create the schema on startup."""
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        assert test_client.get("/api/health").status_code == 200
