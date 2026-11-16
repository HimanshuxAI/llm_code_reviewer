from app.analysis.ast_analyzer import analyse_python


def test_mutable_default_argument():
    code = "def f(items=[]):\n    return items\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "BUG001" for f in findings)


def test_bare_except_not_double_counted_with_regex():
    # QUAL001 already catches bare except in rules.py; AST pass reports swallowing only
    code = "try:\n    x = 1\nexcept Exception:\n    pass\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "QUAL002" for f in findings)


def test_requests_call_without_timeout():
    code = "import requests\nrequests.get('http://x')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "PY002" for f in findings)


def test_requests_call_with_timeout_is_fine():
    code = "import requests\nrequests.get('http://x', timeout=10)\n"
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_open_without_encoding():
    code = "f = open('out.txt', 'w')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "QUAL003" for f in findings)


def test_open_with_encoding_is_fine():
    code = "f = open('out.txt', 'w', encoding='utf-8')\n"
    assert not any(f["rule_id"] == "QUAL003" for f in analyse_python(code))


def test_assert_used_for_authorization():
    code = "def delete(user):\n    assert user.is_admin\n    pass\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "PY001" for f in findings)


def test_assert_for_debugging_is_not_flagged():
    code = "def f(x):\n    assert isinstance(x, int)\n    return x\n"
    assert not any(f["rule_id"] == "PY001" for f in analyse_python(code))


def test_syntax_error_returns_empty_list():
    assert analyse_python("def f(: pass\n") == []


def test_findings_carry_source_and_evidence():
    for f in analyse_python("def f(items=[]):\n    return items\n"):
        assert f["source"] == "ast"
        assert f["evidence"]



def test_plain_dict_get_is_not_an_http_call():
    code = "d = {}\nd.get('k')\n"
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_session_derived_http_client_is_flagged():
    code = "import requests\ns = requests.Session()\ns.get('http://x')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "PY002" for f in findings)
