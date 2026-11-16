from app.analysis.tokenizer import tokenize_source, strip_comments_and_strings


def test_comment_is_not_code():
    toks = tokenize_source('# password = "x"\ny = 1\n', "python")
    kinds = [t.kind for t in toks]
    assert "comment" in kinds


def test_string_and_code_are_distinguished():
    toks = tokenize_source('x = "os.system(1)"\n', "python")
    strings = [t for t in toks if t.kind == "string"]
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert len(strings) == 1
    assert "os" not in idents  # inside the string


def test_strip_comments_and_strings_preserves_lines():
    code = '# password = "x"\nreal = 1\n'
    stripped = strip_comments_and_strings(code, "python")
    assert stripped.splitlines()[0].strip() == ""
    assert stripped.splitlines()[1].strip() == "real = 1"
    assert len(stripped.splitlines()) == 2


def test_block_comment_is_not_code():
    toks = tokenize_source('/* eval(userInput) */\nconst z = 1;\n', "javascript")
    comments = [t for t in toks if t.kind == "comment"]
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert len(comments) == 1
    assert "eval" not in idents


def test_template_string_is_one_string_token():
    toks = tokenize_source('const y = `hello ${name} there`;\n', "javascript")
    strings = [t for t in toks if t.kind == "string"]
    assert len(strings) == 1
    assert strings[0].text == "`hello ${name} there`"


def test_line_numbers_match():
    code = "a = 1\n\nb = 2\n"
    toks = tokenize_source(code, "python")
    b = [t for t in toks if t.text == "b"]
    assert b[0].line == 3


def test_unknown_language_returns_empty_list():
    assert tokenize_source("x", "ruby") == []


def test_strip_comments_masks_comment_but_keeps_string():
    from app.analysis.tokenizer import strip_comments
    src = 'const url = "https://example.com"; // TODO: rotate keys\n'
    out = strip_comments(src, "javascript")
    assert "// TODO: rotate keys" not in out
    assert '"https://example.com"' in out


def test_python_syntax_error_returns_empty_list():
    assert tokenize_source("def broken(:\n", "python") == []


def test_python_syntax_error_logs_a_warning(caplog):
    import logging

    with caplog.at_level(logging.WARNING, logger="app.analysis.tokenizer"):
        tokenize_source("def broken(:\n", "python")
    assert any("tokenizer" in r.name for r in caplog.records)


def test_unterminated_string_and_comment_do_not_crash():
    assert tokenize_source('const s = "unterminated\n', "javascript") is not None
    assert tokenize_source('/* unterminated block comment', "c") is not None
    assert tokenize_source('const t = `unterminated\n', "javascript") is not None


def test_python_fstring_literal_is_string():
    toks = tokenize_source('f"os.system({x})"\n', "python")
    strings = [t for t in toks if t.kind == "string"]
    assert any("os.system(" in t.text for t in strings)
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert "os" not in idents


def test_java_text_block_is_string():
    src = 'String q = """\nSELECT * FROM users;\n""";\n'
    toks = tokenize_source(src, "java")
    strings = [t for t in toks if t.kind == "string"]
    assert len(strings) == 1
    assert "SELECT" in strings[0].text
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert "SELECT" not in idents


def test_c_block_comment_is_comment():
    toks = tokenize_source('/* eval(userInput) */\nint x = 1;\n', "c")
    comments = [t for t in toks if t.kind == "comment"]
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert len(comments) == 1
    assert "eval" not in idents


def test_number_does_not_swallow_member_access():
    toks = tokenize_source("1.toString()\n", "javascript")
    numbers = [t for t in toks if t.kind == "number"]
    assert numbers[0].text == "1"
    assert tokenize_source("0x1f\n", "javascript")[0].text == "0x1f"
    assert tokenize_source("2.5\n", "javascript")[0].text == "2.5"


def test_dollar_is_identifier_in_javascript():
    toks = tokenize_source("$el = $\n", "javascript")
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert "$el" in idents
    assert "$" in idents
