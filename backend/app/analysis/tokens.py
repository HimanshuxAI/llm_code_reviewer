"""Function inventory from the token stream for JavaScript/Java/C/C++."""
from app.analysis.tokenizer import tokenize_source

# Keywords that open a parenthesised header without being function
# definitions. Without this skip, `if (`, `while (`, `for (`, `switch (`
# and `catch (` at top level register phantom "functions", and every
# `if (cond)` inside a real function then looks like a call into them,
# propagating taint across the wrong boundary.
_CONTROL_FLOW = {"if", "else", "while", "for", "switch", "catch", "do",
                 "try", "return", "with", "function", "class"}


class Func:
    """One function body with its parameter names, in source order.

    `param_index` maps each parameter name to its call-site position; the
    token phases bind call arguments to parameters by that position.
    """

    def __init__(self, name, params, body, start_line=None, end_line=None):
        self.name = name
        self.params = params
        self.param_index = {p: i for i, p in enumerate(params)}
        self.body = body
        self.start_line = start_line
        self.end_line = end_line
        self.flows_to_sink = set()
        self.flows_to_return = set()
        self.source_locals = set()
        self.return_reads_source = False


def function_inventory(source, language):
    """Find function bodies by brace matching.

    A definition is `name ( params ) { body`. Tokens between `)` and `{`
    (a Java `throws IOException` clause, a comma-separated exception list,
    dotted names) are skipped; a `;` there marks a prototype, which is not
    a definition. On a duplicate function name the first registration wins
    and later ones are skipped, so phase 2 never binds a call-site argument
    to the wrong body. Unbalanced braces return an empty inventory; the
    caller falls back to intra-procedural analysis.
    """
    tokens = tokenize_source(source, language)
    n = len(tokens)
    functions = {}
    i = 0
    while i < n:
        tok = tokens[i]
        if tok.kind != "identifier":
            i += 1
            continue
        if tok.text in _CONTROL_FLOW:
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
        if j >= n:
            i += 1
            continue
        close = j - 1  # index of the `)` closing the parameter list
        # Clause tokens between the parameter list and the body:
        # `throws IOException`, `throws A, B`, dotted names.
        while j < n and (tokens[j].kind == "identifier"
                         or tokens[j].text in (",", ".")):
            j += 1
        if j >= n or tokens[j].text != "{":
            i += 1
            continue
        params = _parse_params(tokens[i + 2:close])
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
        if tok.text not in functions:
            functions[tok.text] = Func(tok.text, params, body,
                                       start_line=tok.line,
                                       end_line=tokens[k - 1].line)
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
