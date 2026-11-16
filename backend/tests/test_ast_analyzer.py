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


def test_class_scope_init_registration_visible_in_sibling_method():
    code = (
        "import httpx\n"
        "class C:\n"
        "    def __init__(self): self.client = httpx.Client()\n"
        "    def fetch(self):    self.client.get('http://x')\n"
    )
    findings = analyse_python(code)
    assert any(f["rule_id"] == "PY002" for f in findings)


def test_cross_method_reassignment_clears_binding_for_siblings():
    code = (
        "import httpx\n"
        "class C:\n"
        "    def __init__(self): self.client = httpx.Client()\n"
        "    def reset(self):    self.client = {}\n"
        "    def fetch(self):    self.client.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_module_level_client_shadowed_in_function_is_not_flagged():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "def f():\n"
        "    s = {}\n"
        "    s.get('k')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_module_level_client_shadowed_by_annotated_assignment_is_not_flagged():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "def f():\n"
        "    s: dict = {}\n"
        "    s.get('k')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_unrelated_session_source_is_not_flagged():
    # false positive guard: sqlalchemy's Session is not an HTTP client
    code = (
        "from sqlalchemy.orm import Session\n"
        "s = Session()\n"
        "s.get(1)\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_from_httpx_import_client_is_flagged():
    code = "from httpx import Client\nc = Client()\nc.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_aliased_requests_import_call_is_flagged():
    code = "import requests as rq\nrq.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_aliased_constructor_call_is_flagged():
    code = "import requests as rq\ns = rq.Session()\ns.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_with_binding_does_not_outlive_the_block():
    code = (
        "import requests\n"
        "with requests.Session() as s:\n"
        "    pass\n"
        "s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_async_with_binding_does_not_outlive_the_block():
    code = (
        "import httpx\n"
        "async def f():\n"
        "    async with httpx.AsyncClient() as c:\n"
        "        pass\n"
        "    c.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_starred_args_skip_timeout_check():
    code = "import requests\nargs = ()\nrequests.get('http://x', *args)\n"
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_aliased_import_shadowed_in_function_is_not_flagged():
    code = (
        "import requests as rq\n"
        "def f():\n"
        "    rq = {}\n"
        "    rq.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_aliased_import_shadowed_at_module_level_is_not_flagged():
    code = (
        "import requests as rq\n"
        "rq = {}\n"
        "rq.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_aliased_import_unblocked_alias_still_fires():
    # bare sanity: alias itself still fires when nothing was shadowed
    code = "import requests as rq\nrq.get('http://x')\n"
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_module_requests_name_shadowed_is_not_flagged():
    code = (
        "import requests\n"
        "requests = {}\n"
        "requests.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_function_dotted_key_does_not_leak_into_sibling_function():
    code = (
        "import httpx\n"
        "def make(cfg):\n"
        "    cfg.client = httpx.Client()\n"
        "def use(cfg):\n"
        "    cfg.client.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_function_dotted_tombstone_does_not_leak_into_module_frame():
    code = (
        "import httpx\n"
        "cfg = make_cfg()\n"
        "cfg.client = httpx.Client()\n"
        "def use(cfg):\n"
        "    cfg.client = {}\n"
        "use(cfg)\n"
        "cfg.client.get('http://x')\n"
    )
    # module-level cfg.client is a client; use()'s tombstone must not clear it
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_parameter_binding_tombstones_module_client():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "def f(s):\n"
        "    s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_comprehension_target_tombstones_module_client():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "x = [s.get('http://x') for s in ['a', 'b']]\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_for_target_tombstones_module_client():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "for s in ['a', 'b']:\n"
        "    s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_non_client_with_binding_tombstones():
    code = (
        "import requests\n"
        "s = requests.Session()\n"
        "with open('f') as s:\n"
        "    s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_from_import_star_constructor_is_flagged():
    code = (
        "from requests import *\n"
        "s = Session()\n"
        "s.get('http://x')\n"
    )
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_from_import_star_dotted_module_call_is_flagged():
    code = (
        "from requests import *\n"
        "api.get('http://x')\n"
    )
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_last_import_of_same_name_wins():
    code = (
        "from requests import Session\n"
        "from sqlalchemy.orm import Session\n"
        "s = Session()\n"
        "s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_last_import_of_same_name_wins_reversed_order():
    code = (
        "from sqlalchemy.orm import Session\n"
        "from requests import Session\n"
        "s = Session()\n"
        "s.get('http://x')\n"
    )
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_explicit_negative_import_wins_over_star():
    code = (
        "from requests import *\n"
        "from sqlalchemy.orm import Session\n"
        "s = Session()\n"
        "s.get('http://x')\n"
    )
    assert not any(f["rule_id"] == "PY002" for f in analyse_python(code))


def test_from_import_api_dotted_call_is_flagged():
    code = (
        "from requests import api\n"
        "api.get('http://x')\n"
    )
    assert any(f["rule_id"] == "PY002" for f in analyse_python(code))
