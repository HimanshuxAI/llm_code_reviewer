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


def test_keyword_only_mutable_default_argument():
    code = "def f(*, items=[]):\n    return items\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "BUG001" for f in findings)


def test_chained_assignment_registers_client():
    code = "import requests\na = b = requests.Session()\na.get('http://x')\nb.get('http://x')\n"
    findings = analyse_python(code)
    assert sum(f["rule_id"] == "PY002" for f in findings) == 2


def test_annotated_assignment_registers_client():
    code = "import requests\ns: requests.Session = requests.Session()\ns.get('http://x')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "PY002" for f in findings)


def test_non_builtin_open_calls_are_not_flagged():
    code = (
        "import os\nimport tarfile\nimport gzip\nfrom pathlib import Path\n"
        "os.open('f', os.O_CREAT)\n"
        "tarfile.open('f.tar')\n"
        "gzip.open('f.gz')\n"
        "Path('f').open()\n"
    )
    assert not any(f["rule_id"] == "QUAL003" for f in analyse_python(code))


def test_assert_non_authorization_asserts_are_not_flagged():
    code = (
        "def f(payload, users, data, cfg, u):\n"
        "    assert is_valid(payload)\n"
        "    assert len(users) > 0\n"
        "    assert 'author' in data\n"
        "    assert cfg.oauth_url\n"
        "    assert isinstance(u, User)\n"
    )
    assert not any(f["rule_id"] == "PY001" for f in analyse_python(code))


def test_client_registration_is_scope_isolated():
    code = (
        "import requests\n"
        "def a():\n"
        "    s = requests.Session()\n"
        "    s.get('http://x')\n"
        "def b():\n"
        "    s = {}\n"
        "    s.get('key')\n"
    )
    findings = analyse_python(code)
    assert sum(f["rule_id"] == "PY002" for f in findings) == 1
    assert findings[0]["line"] == 4


def test_from_import_session_registers_client():
    code = "from requests import Session\ns = Session()\ns.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_from_import_bare_get_does_not_fire():
    # documented narrowness: `from requests import get` then bare get(url) is not tracked
    code = "from requests import get\nget('http://x')\n"
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_with_statement_registers_client():
    code = "import requests\nwith requests.Session() as s:\n    s.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_async_with_registers_client():
    code = (
        "import httpx\n"
        "async def f():\n"
        "    async with httpx.AsyncClient() as c:\n"
        "        c.get('http://x')\n"
    )
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_kwargs_timeout_is_not_reported():
    # **kwargs means we cannot see whether timeout is passed; skip the call
    code = "import requests\ndef f(**kwargs):\n    requests.get('http://x', **kwargs)\n"
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_instance_attribute_client_flagged_and_shadowing_clears():
    code = (
        "import httpx\n"
        "class C:\n"
        "    def f(self):\n"
        "        self.client = httpx.Client()\n"
        "        self.client.get('http://x')\n"
        "        self.client = {}\n"
        "        self.client.get('http://x')\n"
    )
    findings = analyse_python(code)
    assert sum(f["rule_id"] == "PY002" for f in findings) == 1


def test_open_positional_encoding_fourth_arg_is_fine():
    code = "f = open('out.txt', 'w', -1, 'utf-8')\n"
    assert not any(f["rule_id"] == "QUAL003" for f in analyse_python(code))


def test_bug001_reports_the_default_line():
    code = "def f(\n    items=[]\n):\n    return items\n"
    findings = analyse_python(code)
    bug001 = [f for f in findings if f["rule_id"] == "BUG001"]
    assert len(bug001) == 1
    assert bug001[0]["line"] == 2


def test_max_findings_is_capped_at_60():
    code = "".join(f"open('out{i}.txt', 'w')\n" for i in range(70))
    assert len(analyse_python(code)) == 60


def test_bug001_none_and_tuple_defaults_not_flagged():
    code = "def f(x=None, y=()):\n    return x\n"
    assert not any(f["rule_id"] == "BUG001" for f in analyse_python(code))


def test_qual002_negatives():
    code = (
        "try:\n    x = 1\nexcept ValueError:\n    pass\n"
        "try:\n    y = 1\nexcept Exception:\n    print('logged')\n"
    )
    assert not any(f["rule_id"] == "QUAL002" for f in analyse_python(code))


def test_except_tuple_with_broad_handler_still_fires():
    code = "try:\n    x = 1\nexcept (Exception, ValueError):\n    pass\n"
    assert any(f["rule_id"] == "QUAL002" for f in analyse_python(code))


def test_duplicate_mutable_defaults_report_twice():
    code = "def f(a=[], b=[]):\n    return a\n"
    assert sum(f["rule_id"] == "BUG001" for f in analyse_python(code)) == 2
