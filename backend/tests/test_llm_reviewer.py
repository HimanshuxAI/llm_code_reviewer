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
