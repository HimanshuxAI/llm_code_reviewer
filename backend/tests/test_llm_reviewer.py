from app.analysis.llm_reviewer import parse_llm_json, review_with_llm

RAW = '''Here are the issues:
```json
{"findings": [{"type": "SQL Injection", "severity": "HIGH", "line": 12,
 "explanation": "Query is built from user input.", "suggestion": "Use parameters.",
 "fixed_snippet": "c.execute(q, (uid,))"}]}
```
'''


def test_parses_fenced_json():
    findings = parse_llm_json(RAW)
    assert len(findings) == 1
    f = findings[0]
    assert f["rule_id"] == "LLM"
    assert f["severity"] == "high"
    assert f["line"] == 12
    assert f["source"] == "llm"
    assert f["fixed_snippet"].startswith("c.execute")


def test_malformed_json_returns_empty():
    assert parse_llm_json("no json here at all") == []
    assert parse_llm_json('{"findings": "not-a-list"}') == []


def test_bad_severity_normalizes_to_medium():
    f = parse_llm_json('{"findings": [{"type": "x", "severity": "urgent", "line": 1}]}')[0]
    assert f["severity"] == "medium"


def test_disabled_without_api_key(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "llm_api_key", "")
    assert review_with_llm("print(1)", "python") == []


def test_timeout_is_bounded_by_settings(monkeypatch):
    """A hanging endpoint must not block the review for a full minute."""
    import httpx

    from app.config import settings

    monkeypatch.setattr(settings, "llm_api_key", "sk-test")
    monkeypatch.setattr(settings, "llm_timeout_seconds", 12)

    captured = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        raise httpx.ConnectError("boom")

    monkeypatch.setattr(httpx, "post", fake_post)
    review_with_llm("print(1)", "python")

    timeout = captured["timeout"]
    assert timeout.connect == 5
    assert timeout.read == 12
    assert timeout.write == 12
    assert timeout.pool == 12


def test_network_failure_returns_empty_findings(monkeypatch):
    """A dead endpoint degrades to static-only, it does not raise."""
    import httpx

    from app.config import settings

    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    def fake_post(url, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)
    assert review_with_llm("print(1)", "python") == []


def test_pipeline_still_scores_when_llm_fails(monkeypatch):
    """The whole review must still succeed when the model is unreachable."""
    import httpx

    from app.analysis.pipeline import run_review
    from app.config import settings

    monkeypatch.setattr(settings, "llm_api_key", "sk-test")

    def fake_post(url, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(httpx, "post", fake_post)
    result = run_review('import os\npassword = "hunter2hunter2"\n', "a.py")

    assert result["score"] < 100
    assert {f["rule_id"] for f in result["findings"]} == {"SEC003"}
    assert all(f["source"] == "static" for f in result["findings"])
