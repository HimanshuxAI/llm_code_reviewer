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
