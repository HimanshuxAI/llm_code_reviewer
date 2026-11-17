from app.analysis.pipeline import run_review


def test_run_review_shape():
    result = run_review("import os\nos.system('ls ' + input())\n", "a.py")
    assert result["language"] == "python"
    assert result["findings"]
    assert isinstance(result["score"], int)


def test_run_review_vulnerable_python():
    result = run_review('import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n', "a.py")
    rule_ids = {f["rule_id"] for f in result["findings"]}
    assert "SEC003" in rule_ids
    assert "SEC010" in rule_ids
    assert result["score"] < 100


def test_run_review_clean_code():
    result = run_review("def add(a, b):\n    return a + b\n", "a.py")
    assert result["score"] == 100
    assert result["findings"] == []
