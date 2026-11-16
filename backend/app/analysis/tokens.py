"""Function inventory from the token stream for JavaScript/Java/C/C++."""
from app.analysis.tokenizer import tokenize_source


class Func:
    def __init__(self, name, params, start_line, end_line, body):
        self.name = name
        self.params = params
        self.param_index = {p: i for i, p in enumerate(params)}
        self.start_line = start_line
        self.end_line = end_line
        self.body = body
        self.flows_to_sink = set()
        self.flows_to_return = set()
        self.source_locals = set()
        self.return_reads_source = False


def function_inventory(source, language):
    tokens = tokenize_source(source, language)
    n = len(tokens)
    functions = {}
    i = 0
    while i < n:
        tok = tokens[i]
        if tok.kind != "identifier":
            i += 1
            continue
        if i + 1 >= n or tokens[i + 1].text != "(":
            i += 1
            continue
        depth = 1
        j = i + 2
        while j < n and depth:
            if tokens[j].text == "(":
                depth += 1
            elif tokens[j].text == ")":
                depth -= 1
            j += 1
        if j >= n or tokens[j].text != "{":
            i += 1
            continue
        params = _parse_params(tokens[i + 2:j - 1])
        depth = 1
        k = j + 1
        while k < n and depth:
            if tokens[k].text == "{":
                depth += 1
            elif tokens[k].text == "}":
                depth -= 1
            k += 1
        if depth:
            # unbalanced braces: give up, the caller falls back
            return {}
        body = tokens[j + 1:k - 1]
        functions[tok.text] = Func(tok.text, params, tok.line, tokens[k - 1].line, body)
        i = k
    return functions


def _parse_params(tokens):
    params, current = [], []
    for t in tokens:
        if t.text == ",":
            name = _last_name(current)
            if name:
                params.append(name)
            current = []
        else:
            current.append(t)
    name = _last_name(current)
    if name:
        params.append(name)
    return params


def _last_name(tokens):
    names = [t.text for t in tokens if t.kind == "identifier"]
    return names[-1] if names else None
