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


# --- inline sink(source(...)) in the token languages (call-shaped sources) ---

def test_javascript_inline_source_into_sink():
    code = 'function f() {\n  eval(prompt("x"));\n}\n'
    findings = analyse_taint(code, "javascript")
    assert any(f["line"] == 2 for f in findings)


def test_c_inline_source_into_sink():
    code = 'int main() {\n  system(getenv("CMD"));\n}\n'
    findings = analyse_taint(code, "c")
    assert any(f["line"] == 2 for f in findings)


def test_java_inline_source_into_sink():
    code = ('public static void main(String[] args) throws IOException {\n'
            '  Runtime.getRuntime().exec(request.getParameter("c"));\n'
            '}\n')
    findings = analyse_taint(code, "java")
    assert any(f["line"] == 2 for f in findings)


def test_interprocedural_inline_source_call():
    code = 'function run() { f(prompt("n")); }\nfunction f(y) { eval(y); }\n'
    findings = analyse_taint(code, "javascript")
    assert any(f["line"] == 2 for f in findings)


# --- top-level code is scanned even when functions exist ---

def test_toplevel_call_into_helper_with_tainted_arg():
    code = 'function f(y) { eval(y); }\nf(prompt("n"));\n'
    findings = analyse_taint(code, "javascript")
    assert findings


def test_toplevel_source_to_sink_without_functions():
    code = 'eval(prompt("x"));\n'
    findings = analyse_taint(code, "javascript")
    assert findings


# --- Python source idioms from the spec ---

def test_python_sys_argv_source():
    code = 'import os, sys\ndef h():\n    os.system(sys.argv[1])\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 3 for f in findings)


def test_python_request_args_subscript_source():
    code = 'import os\ndef h(request):\n    os.system(request.args["cmd"])\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 3 for f in findings)


def test_python_augassign_propagates_taint():
    code = 'import os\ndef h():\n    cmd = "ls "\n    cmd += input()\n    os.system(cmd)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 5 for f in findings)


def test_python_annassign_propagates_taint():
    code = 'import os\ndef h() -> None:\n    cmd: str = input()\n    os.system(cmd)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 4 for f in findings)


def test_python_walrus_propagates_taint():
    code = 'import os\ndef h():\n    if (u := input()):\n        os.system(u)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 4 for f in findings)


def test_python_tuple_unpack_propagates_taint():
    code = 'import os\ndef h():\n    a, b = input(), "x"\n    os.system(a)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 4 for f in findings)


def test_python_subprocess_run_with_tainted_arg_fires():
    code = 'import subprocess\ndef h():\n    subprocess.run(input(), shell=True)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 3 for f in findings)


# --- Java throws clauses do not hide function bodies ---

def test_java_throws_clause_methods_are_discovered():
    code = ('class Main {\n'
            '  public static void main(String[] args) throws IOException {\n'
            '    Runtime.getRuntime().exec("ls");\n'
            '  }\n'
            '  static void run(HttpServletRequest req) throws ServletException, IOException {\n'
            '    Runtime.getRuntime().exec(req.getParameter("cmd"));\n'
            '  }\n'
            '}\n')
    findings = analyse_taint(code, "java")
    assert any(f["line"] == 6 for f in findings)


# --- false-positive regressions ---

def test_javascript_static_document_write_stays_clean():
    code = 'function show() {\n  document.write("static");\n}\n'
    assert analyse_taint(code, "javascript") == []


def test_javascript_object_literal_key_stays_clean():
    code = 'const cfg = { query: "users" };\n$("#out").html(cfg.query);\n'
    assert analyse_taint(code, "javascript") == []


def test_javascript_equality_comparison_stays_clean():
    code = ('function check() {\n'
            '  const u = "a";\n'
            '  if (u == params.expected) { eval(u); }\n'
            '}\n')
    assert analyse_taint(code, "javascript") == []


def test_javascript_toplevel_control_flow_stays_clean():
    code = ('function setMode(u) { const t = params.mode; if (t) { } }\n'
            'if (body) { document.write(body); }\n')
    assert analyse_taint(code, "javascript") == []


def test_java_execute_with_constant_stays_clean():
    code = 'void h() {\n  stmt.execute("SELECT 1");\n}\n'
    assert analyse_taint(code, "java") == []


def test_python_no_source_stays_clean():
    code = 'import os\ndef h():\n    os.system("ls -la")\n'
    assert analyse_taint(code, "python") == []


def test_c_strcpy_with_literal_stays_clean():
    code = 'void f() {\n  char d[16];\n  strcpy(d, "ok");\n}\n'
    assert analyse_taint(code, "c") == []


def test_python_user_function_shadows_same_named_source():
    code = ('import os\n'
            'CONFIG = {"c": "ls"}\n'
            'def get(key):\n'
            '    return CONFIG[key]\n'
            'def h():\n'
            '    os.system(get("cmd"))\n')
    assert analyse_taint(code, "python") == []


def test_python_subprocess_run_with_list_stays_clean():
    code = 'import subprocess\ndef h():\n    subprocess.run(["ls"], shell=False)\n'
    assert analyse_taint(code, "python") == []
