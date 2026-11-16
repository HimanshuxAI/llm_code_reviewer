from app.analysis.static_scanner import scan


def rule_ids(findings):
    return [f["rule_id"] for f in findings]


def test_detects_eval_in_python():
    findings = scan("x = eval(input())\n", "python")
    assert "SEC001" in rule_ids(findings)
    assert findings[0]["line"] == 1
    assert findings[0]["severity"] == "critical"


def test_detects_hardcoded_secret_any_language():
    findings = scan('api_key = "sk-123456abcdef"\n', "javascript")
    assert "SEC003" in rule_ids(findings)


def test_detects_sql_concat_python_only():
    assert scan('c.execute("SELECT * FROM u WHERE id=" + uid)\n', "python")
    assert not rule_ids(scan('c.execute("SELECT * FROM u WHERE id=" + uid)\n', "javascript"))


def test_detects_c_dangerous_functions():
    findings = scan("#include <stdio.h>\ngets(buf);\n", "c")
    assert "SEC009" in rule_ids(findings)
    assert findings[0]["line"] == 2


def test_detects_innerhtml_javascript():
    assert "SEC008" in rule_ids(scan('el.innerHTML = userInput;\n', "javascript"))


def test_clean_code_has_no_findings():
    assert scan("def add(a, b):\n    return a + b\n", "python") == []


def test_finding_shape():
    finding = scan("x = eval('1')\n", "python")[0]
    assert set(finding) == {"rule_id", "title", "severity", "line", "explanation", "suggestion", "source", "fixed_snippet"}
    assert finding["source"] == "static"
