VULNERABLE = 'import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n'


def test_unknown_user_requires_auth(client):
    assert client.get("/api/reviews").status_code == 401
    assert client.post("/api/reviews", json={"source_code": "x=1\n"}).status_code == 401


def test_submit_review(client, auth_headers):
    resp = client.post("/api/reviews", json={"source_code": VULNERABLE}, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["language"] == "python"
    assert body["score"] < 100
    assert {f["rule_id"] for f in body["findings"]} >= {"SEC003", "SEC010"}


def test_review_requires_auth(client):
    assert client.post("/api/reviews", json={"source_code": "x=1\n"}).status_code == 401


def test_empty_code_rejected(client, auth_headers):
    assert client.post("/api/reviews", json={"source_code": ""}, headers=auth_headers).status_code == 422


def test_history_lists_newest_first(client, auth_headers):
    for i in range(2):
        client.post("/api/reviews", json={"source_code": f"x = {i}\n"}, headers=auth_headers)
    resp = client.get("/api/reviews", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    assert items[0]["id"] > items[1]["id"]


def test_foreign_review_is_404(client, auth_headers):
    client.post("/api/auth/register", json={"email": "other@b.com", "password": "longenough1"})
    other = client.post("/api/auth/login", json={"email": "other@b.com", "password": "longenough1"}).json()
    review = client.post("/api/reviews", json={"source_code": "x=1\n"}, headers=auth_headers).json()
    resp = client.get(f"/api/reviews/{review['id']}", headers={"Authorization": f"Bearer {other['access_token']}"})
    assert resp.status_code == 404


def test_get_single_review(client, auth_headers):
    created = client.post("/api/reviews", json={"source_code": VULNERABLE}, headers=auth_headers).json()
    resp = client.get(f"/api/reviews/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["language"] == "python"
    assert resp.json()["score"] < 100
