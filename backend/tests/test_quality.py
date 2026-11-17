from app.analysis.quality import detect_quality_issues


def test_long_function():
    body = "\n".join(f"    x{i} = {i}" for i in range(70))
    code = f"def big():\n{body}\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL007" for f in findings)


def test_high_complexity():
    code = "def f(x):\n    " + "\n    ".join(
        f"if x > {i}:\n        y{i} = {i}" for i in range(13)) + "\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL008" for f in findings)


def test_deep_nesting():
    # Five nested ifs (nesting depth 5 > MAX_NESTING=4). The innermost if
    # needs a real body, otherwise ast.parse raises SyntaxError and the
    # analyzer returns [] instead of reporting QUAL009.
    nested = "".join("    " * (i + 1) + f"if x > {i}:\n" for i in range(5))
    code = "def f(x):\n" + nested + "    " * 6 + "pass\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL009" for f in findings)


def test_too_many_parameters():
    code = "def f(a, b, c, d, e, f):\n    return a\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL010" for f in findings)


def test_leftover_print():
    code = "def h():\n    print('debug')\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL011" for f in findings)


def test_console_log_javascript():
    code = "function h() {\n  console.log('debug');\n}\n"
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL011" for f in findings)


def test_todo_comment():
    code = "x = 1\n# TODO: refactor this\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL012" for f in findings)


def test_no_findings_on_clean_code():
    code = "def add(a, b):\n    return a + b\n"
    assert detect_quality_issues(code, "python") == []


def test_javascript_long_function():
    body = "\n".join(f"  const x{i} = {i};" for i in range(70))
    code = f"function big() {{\n{body}\n}}\n"
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL007" for f in findings)


def test_javascript_high_complexity():
    body = "\n".join(f"  if (x > {i}) {{ y{i} = {i}; }}" for i in range(13))
    code = f"function f(x) {{\n{body}\n}}\n"
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL008" for f in findings)


def test_javascript_deep_nesting():
    code = ("function f(x) {\n"
            + "".join("  " * (i + 1) + f"if (x > {i}) {{\n" for i in range(5))
            + "      doIt();\n"
            + "    }\n" * 5
            + "}\n")
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL009" for f in findings)


def test_javascript_too_many_parameters():
    code = "function f(a, b, c, d, e, g) {\n  return a;\n}\n"
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL010" for f in findings)


def test_java_long_function():
    body = "\n".join(f"    int x{i} = {i};" for i in range(70))
    code = f"public void big() {{\n{body}\n}}\n"
    findings = detect_quality_issues(code, "java")
    assert any(f["rule_id"] == "QUAL007" for f in findings)


def test_c_too_many_parameters():
    code = "int f(int a, int b, int c, int d, int e, int g) {\n  return a;\n}\n"
    findings = detect_quality_issues(code, "c")
    assert any(f["rule_id"] == "QUAL010" for f in findings)


def test_javascript_clean_code_has_no_quality_findings():
    code = "function add(a, b) {\n  return a + b;\n}\n"
    assert detect_quality_issues(code, "javascript") == []
