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
    code = 'Cipher c = Cipher.getInstance("DES");\n'
    matches = detect_semantic_patterns(code, "java")
    assert matches
    for f in matches:
        assert set(f) >= {"rule_id", "title", "severity", "line",
                          "explanation", "suggestion", "source", "fixed_snippet"}
        assert f["source"] == "sinks"
        assert f["fixed_snippet"] is None


def test_strncat_does_not_match_c001():
    code = "strncat(dst, src, 5);\n"
    assert detect_semantic_patterns(code, "c") == []


def test_width_limited_scanf_is_not_flagged():
    code = 'scanf("%99s", buf);\n'
    findings = detect_semantic_patterns(code, "c")
    assert not any(f["rule_id"] == "C003" for f in findings)


def test_js004_requires_child_process():
    code = "const re = /x/; re.exec(`prefix-${x}`);\n"
    findings = detect_semantic_patterns(code, "javascript")
    assert not any(f["rule_id"] == "JS004" for f in findings)
    code = 'require("child_process"); exec(`ls ${x}`);\n'
    findings = detect_semantic_patterns(code, "javascript")
    assert any(f["rule_id"] == "JS004" for f in findings)


def test_text_language_yields_empty():
    assert detect_semantic_patterns("anything %s DES getInstance(\"MD5\")\n", "text") == []


def test_findings_are_capped_at_60():
    code = "".join("document.write(x);\n" for _ in range(70))
    findings = detect_semantic_patterns(code, "javascript")
    assert len(findings) == 60
    assert all(f["source"] == "sinks" for f in findings)


def test_multiline_trust_manager_fires():
    code = (
        "class T extends X509TrustManager {\n"
        "    public void checkServerTrusted(\n"
        "        X509Certificate[] chain,\n"
        "        String authType) {\n"
        "    }\n"
        "}\n"
    )
    findings = detect_semantic_patterns(code, "java")
    assert any(f["rule_id"] == "SEC016" for f in findings)


def test_trust_manager_in_comment_does_not_fire():
    code = "// checkServerTrusted(\n"
    findings = detect_semantic_patterns(code, "java")
    assert not any(f["rule_id"] == "SEC016" for f in findings)


def test_suffixed_crypto_instances_fire():
    for algo in ("DES", "DES/ECB/PKCS5Padding", "DESede/CBC/PKCS5Padding", "RC4",
                 "MD5", "MD5withRSA", "SHA1withRSA", "SHA-1"):
        code = f'Cipher.getInstance("{algo}");\n'
        findings = detect_semantic_patterns(code, "java")
        assert any(f["rule_id"] in ("SEC013", "SEC014") for f in findings), algo
    for algo in ("AES", "SHA-256"):
        code = f'Cipher.getInstance("{algo}");\n'
        findings = detect_semantic_patterns(code, "java")
        assert not any(f["rule_id"] in ("SEC013", "SEC014") for f in findings), algo
