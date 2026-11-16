from app.analysis.sinks import SOURCES, SINKS, detect_semantic_patterns


def test_sources_and_sinks_exist_for_all_languages():
    for lang in ("python", "javascript", "java", "c", "cpp", "text"):
        assert lang in SOURCES
        assert lang in SINKS


def test_python_sinks_include_os_system_and_eval():
    assert "system" in SINKS["python"]
    assert "eval" in SINKS["python"]


def test_detect_semantic_patterns_java_des():
    code = 'Cipher c = Cipher.getInstance("DES");\n'
    findings = detect_semantic_patterns(code, "java")
    assert any("DES" in f["explanation"] for f in findings)
    assert all(f["line"] == 1 for f in findings)


def test_detect_semantic_patterns_ignores_comment():
    code = '// Cipher.getInstance("DES")\nint x = 1;\n'
    findings = detect_semantic_patterns(code, "java")
    assert findings == []


def test_detect_semantic_patterns_javascript_document_write():
    code = "document.write(userInput);\n"
    findings = detect_semantic_patterns(code, "javascript")
    assert any("document.write" in f["explanation"] for f in findings)


def test_findings_have_required_keys():
    code = 'String q = "SELECT " + u; stmt.execute(q);\n'
    for f in detect_semantic_patterns(code, "java"):
        assert set(f) >= {"rule_id", "title", "severity", "line",
                          "explanation", "suggestion", "source", "fixed_snippet"}
        assert f["source"] == "sinks"
        assert f["fixed_snippet"] is None


def test_findings_have_required_keys_when_matched():
    code = 'Cipher c = Cipher.getInstance("DES");\n'
    matches = detect_semantic_patterns(code, "java")
    assert matches
    for f in matches:
        assert set(f) >= {"rule_id", "title", "severity", "line",
                          "explanation", "suggestion", "source", "fixed_snippet"}
        assert f["source"] == "sinks"
        assert f["fixed_snippet"] is None
