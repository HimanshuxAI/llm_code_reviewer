from app.analysis.taint import analyse_taint


def test_direct_source_into_sink():
    code = 'import os\ndef h(request):\n    name = request.args.get("name")\n    os.system(name)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 4 for f in findings)


def test_user_input_through_helper():
    code = (
        "import os\n"
        "def get_command(name):\n    return \"ls \" + name\n"
        "def handler(name):\n    cmd = get_command(name)\n    os.system(cmd)\n"
        "def route(request):\n    user_input = request.args.get(\"name\")\n    handler(user_input)\n"
    )
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 6 for f in findings)


def test_helper_called_with_constant_is_clean():
    code = "import os\ndef helper(name):\n    os.system(name)\ndef caller():\n    helper(\"ls\")\n"
    assert analyse_taint(code, "python") == []


def test_sink_with_literal_is_not_flagged():
    code = "import os\ndef h():\n    os.system(\"ls -la\")\n"
    assert analyse_taint(code, "python") == []


def test_taint_through_return_value():
    code = (
        "import os\n"
        "def read_name(request):\n    return request.args.get(\"name\")\n"
        "def h(request):\n    os.system(read_name(request))\n"
    )
    assert analyse_taint(code, "python") != []


def test_confidence_is_high_for_direct_and_medium_for_cross_function():
    direct = analyse_taint(
        "import os\ndef h(request):\n    name = request.args.get(\"name\")\n    os.system(name)\n",
        "python")
    cross = analyse_taint(
        "import os\n"
        "def get_command(name):\n    return \"ls \" + name\n"
        "def handler(name):\n    cmd = get_command(name)\n    os.system(cmd)\n"
        "def route(request):\n    user_input = request.args.get(\"name\")\n    handler(user_input)\n",
        "python")
    assert all(f["confidence"] == "high" for f in direct)
    assert any(f["confidence"] == "medium" for f in cross)


def test_parser_error_returns_empty_list():
    assert analyse_taint("def f(: pass\n", "python") == []


def test_javascript_vulnerable():
    code = 'function route(req) {\n  const name = req.query.name;\n  const cmd = name;\n  eval(cmd);\n}\n'
    findings = analyse_taint(code, "javascript")
    assert any(f["line"] == 4 for f in findings)


def test_javascript_clean():
    code = 'function add(a, b) {\n  return a + b;\n}\n'
    assert analyse_taint(code, "javascript") == []


def test_java_vulnerable():
    code = 'void route(HttpServletRequest req) {\n  String name = req.getParameter("name");\n  Runtime.exec(name);\n}\n'
    findings = analyse_taint(code, "java")
    assert findings


def test_c_vulnerable_argv():
    code = 'int main(int argc, char **argv) {\n  system(argv[1]);\n  return 0;\n}\n'
    findings = analyse_taint(code, "c")
    assert findings


def test_c_output_parameter_source():
    code = 'void h() {\n  char buf[64];\n  gets(buf);\n  system(buf);\n}\n'
    findings = analyse_taint(code, "c")
    assert findings


def test_c_clean():
    code = 'int add(int a, int b) {\n  return a + b;\n}\n'
    assert analyse_taint(code, "c") == []
