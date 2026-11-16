def test_register_creates_user(client):
    resp = client.post("/api/auth/register", json={"email": "a@b.com", "password": "longenough1"})
    assert resp.status_code == 201
    assert resp.json() == {"id": 1, "email": "a@b.com"}


def test_register_duplicate_email_rejected(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "longenough1"})
    resp = client.post("/api/auth/register", json={"email": "a@b.com", "password": "longenough1"})
    assert resp.status_code == 400


def test_register_invalid_email_rejected(client):
    resp = client.post("/api/auth/register", json={"email": "not-an-email", "password": "longenough1"})
    assert resp.status_code == 422


def test_login_returns_token(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "longenough1"})
    resp = client.post("/api/auth/login", json={"email": "a@b.com", "password": "longenough1"})
    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert len(resp.json()["access_token"]) > 20


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={"email": "a@b.com", "password": "longenough1"})
    resp = client.post("/api/auth/login", json={"email": "a@b.com", "password": "wrong-pass-1"})
    assert resp.status_code == 401
