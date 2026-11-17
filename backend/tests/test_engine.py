import time

from app.analysis.engine import analyse


VULNERABLE = 'import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n'


def test_analyse_python_finds_multiple_classes():
    findings = analyse(VULNERABLE, "python")
    assert any(f["rule_id"] == "SEC003" for f in findings)
    assert any(f["rule_id"] == "SEC010" for f in findings)


def test_analyse_comments_are_not_flagged():
    findings = analyse('# password = "hunter2hunter2"\nx = 1\n', "python")
    # commented-out secret must not be flagged; only the unused variable remains
    assert not any(f["rule_id"].startswith("SEC") for f in findings)
    assert any(f["rule_id"] == "PY004" for f in findings)


def test_analyse_finds_aws_key():
    findings = analyse('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "python")
    assert any(f["source"] == "secrets" for f in findings)


def test_findings_have_evidence_and_confidence():
    for f in analyse(VULNERABLE, "python"):
        assert "evidence" in f
        assert f["confidence"] in ("high", "medium")
        assert "related_lines" in f


def test_deduped_by_line_severity_title():
    findings = analyse(VULNERABLE, "python")
    keys = [(f["line"], f["severity"], f["title"].lower()) for f in findings]
    assert len(keys) == len(set(keys))


def test_analyser_handles_garbage_input():
    assert isinstance(analyse("\x00\x01 def (", "python"), list)
    assert isinstance(analyse("}", "text"), list)


def test_performance_budget():
    code = (VULNERABLE * 2000)[:50000]  # under the 50k limit
    t0 = time.perf_counter()
    findings = analyse(code, "python")
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0
    assert findings


def test_unused_variable_is_flagged():
    findings = analyse("x = 1\ny = 2\nprint(y)\n", "python")
    assert any(f["rule_id"] == "PY004" and "x" in f["title"] for f in findings)


def test_used_variable_is_not_flagged():
    findings = analyse("x = 1\nprint(x)\n", "python")
    assert not any(f["rule_id"] == "PY004" for f in findings)


def test_unreachable_code_after_return_is_flagged():
    findings = analyse("def f():\n    return 1\n    x = 2\n", "python")
    assert any(f["rule_id"] == "PY005" for f in findings)


def test_code_after_return_in_if_is_reachable():
    findings = analyse("def f():\n    if True:\n        return 1\n    x = 2\n", "python")
    # x = 2 is reachable when the if is False
    assert not any(f["rule_id"] == "PY005" for f in findings)


def test_list_mutated_during_iteration_is_flagged():
    findings = analyse("for x in items:\n    items.append(x)\n", "python")
    assert any(f["rule_id"] == "PY006" for f in findings)


def test_unused_import_is_flagged():
    findings = analyse("import os\nimport sys\nprint(1)\n", "python")
    rule_ids = {f["rule_id"] for f in findings}
    assert "PY007" in rule_ids
    titles = {f["title"] for f in findings if f["rule_id"] == "PY007"}
    assert any("os" in t for t in titles)
    assert any("sys" in t for t in titles)


def test_used_import_is_not_flagged():
    findings = analyse("import os\nprint(os.getcwd())\n", "python")
    assert not any(f["rule_id"] == "PY007" for f in findings)


def test_builtin_shadowing_is_flagged():
    findings = analyse("list = [1, 2]\nprint(list)\n", "python")
    assert any(f["rule_id"] == "PY008" and "list" in f["title"] for f in findings)


def test_builtin_shadowing_str_is_flagged():
    findings = analyse("str = \"hello\"\n", "python")
    assert any(f["rule_id"] == "PY008" for f in findings)


def test_normal_variable_is_not_shadowing():
    findings = analyse("my_list = [1, 2]\nprint(my_list)\n", "python")
    assert not any(f["rule_id"] == "PY008" for f in findings)


def test_dict_mutated_during_iteration_is_flagged():
    findings = analyse("for k in d:\n    d.pop(k)\n", "python")
    assert any(f["rule_id"] == "PY009" for f in findings)


def test_dict_clear_during_iteration_is_flagged():
    findings = analyse("for k in d:\n    d.clear()\n", "python")
    assert any(f["rule_id"] == "PY009" for f in findings)


def test_compare_none_with_eq_is_flagged():
    findings = analyse("if x == None:\n    pass\n", "python")
    assert any(f["rule_id"] == "PY010" for f in findings)


def test_compare_true_with_eq_is_flagged():
    findings = analyse("flag == True\n", "python")
    assert any(f["rule_id"] == "PY010" for f in findings)


def test_compare_none_with_is_is_not_flagged():
    findings = analyse("if x is None:\n    pass\n", "python")
    assert not any(f["rule_id"] == "PY010" for f in findings)


def test_type_eq_comparison_is_flagged():
    findings = analyse("if type(x) == int:\n    pass\n", "python")
    assert any(f["rule_id"] == "PY011" for f in findings)


def test_isinstance_is_not_flagged():
    findings = analyse("if isinstance(x, int):\n    pass\n", "python")
    assert not any(f["rule_id"] == "PY011" for f in findings)


def test_scope_aware_unused_variable_in_function():
    # x assigned inside f() and used inside f(); not flagged
    findings = analyse("def f():\n    x = 1\n    print(x)\n", "python")
    assert not any(f["rule_id"] == "PY004" and "x" in f["title"] for f in findings)


def test_scope_aware_unused_variable_only_in_function():
    # x assigned inside f() but never used there; flagged
    findings = analyse("def f():\n    x = 1\n    return 2\n", "python")
    assert any(f["rule_id"] == "PY004" and "x" in f["title"] for f in findings)


def test_module_level_unused_and_function_level_unused_both_flagged():
    findings = analyse("a = 1\ndef f():\n    b = 2\n    return 3\n", "python")
    py004 = [f for f in findings if f["rule_id"] == "PY004"]
    titles = {f["title"] for f in py004}
    assert any("a" in t for t in titles)
    assert any("b" in t for t in titles)
