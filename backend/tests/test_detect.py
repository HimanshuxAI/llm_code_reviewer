from app.analysis.detect import detect_language


def test_detects_by_filename():
    assert detect_language("print('hi')", "main.py") == "python"
    assert detect_language("let x = 1;", "app.js") == "javascript"
    assert detect_language("#include <stdio.h>", "main.c") == "c"
    assert detect_language("public class A {}", "A.java") == "java"


def test_detects_by_content():
    assert detect_language("def hello():\n    pass", None) == "python"
    assert detect_language("function hello() {}", None) == "javascript"
    assert detect_language("#include <stdio.h>\nint main() {", None) == "c"


def test_unknown_language_is_text():
    assert detect_language("plain prose", None) == "text"
