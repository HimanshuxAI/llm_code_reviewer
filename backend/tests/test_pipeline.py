from app.analysis.pipeline import merge_findings, run_review


def test_merge_dedupes_by_line_and_title():
    static = [{"rule_id": "S1", "title": "Use of eval()", "severity": "critical",
               "line": 3, "source": "static", "explanation": "e", "suggestion": "s", "fixed_snippet": None}]
    llm = [{"rule_id": "LLM", "title": "Use of eval()", "severity": "critical",
            "line": 3, "source": "llm", "explanation": "e", "suggestion": "s", "fixed_snippet": None}]
    merged = merge_findings(static, llm)
    assert len(merged) == 1
    assert merged[0]["source"] == "static"


def test_run_review_shape():
    result = run_review("x = eval(input())\n", None)
    assert result["language"] == "python"
    assert result["findings"][0]["rule_id"] == "SEC001"
    assert isinstance(result["score"], int)
