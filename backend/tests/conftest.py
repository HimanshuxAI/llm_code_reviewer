import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base
from app.db.session import get_db
from app.main import app

_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(_test_engine)
    yield
    Base.metadata.drop_all(_test_engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = lambda: _TestSession()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/api/auth/register", json={"email": "student@edu.in", "password": "s3cret-pass"})
    resp = client.post("/api/auth/login", json={"email": "student@edu.in", "password": "s3cret-pass"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
