"""Two-phase interprocedural taint analysis.

Phase 1 (bottom-up): for each function compute which parameters can reach a
    sink and which can reach the return value. No parameter is assumed tainted.
Phase 2 (top-down): propagate taint from real sources through call sites;
    report a sink only when tainted data reaches it.

Confidence is "high" when the tainted expression at the sink contains a name
that was directly assigned from a source in that same function, and "medium"
otherwise (the flow crossed a function boundary).

Precedence: a user-defined function shadows a same-named source. `get(...)`
in a file that defines `def get(key)` is a call into that function, never a
read of external data.

Source anchoring (token path): a source word counts when it is call-shaped
(`prompt(`), or when it is a property of a member chain rooted at a
parameter of the current function or at another source name (`req.query`,
`params.mode`). A bare mention (`cfg.query` on a plain local, an
object-literal key) does not count.

Token-path layout (JavaScript, Java, C, C++): every brace-matched function
body is analysed, plus one `__module__` pseudo-function holding the depth-0
statements, so top-level code in a file that also defines functions is still
scanned — including calls into real functions with tainted arguments. Braces
are excluded from that segment, so the body of a top-level
`if (...) { ... }` is not scanned: a deliberate narrowing. Phase 2 runs at
most 50 propagation passes; definition-order-dependent chains deeper than
that are truncated, deterministically for a given input.
"""
import ast

from app.analysis.sinks import MAX_FINDINGS, SOURCES, SINKS
from app.analysis.tokens import Func

BARE_SOURCES = {"argv", "environ", "envp"}
OUTPUT_SOURCES = {"gets", "fgets", "scanf", "fscanf", "recv", "readLine",
                  "nextLine", "getline"}


class FunctionInfo:
    def __init__(self, node):
        self.node = node
        self.name = node.name
        self.params = [a.arg for a in node.args.args]
        self.param_index = {p: i for i, p in enumerate(self.params)}
        self.flows_to_sink = set()
        self.flows_to_return = set()
        self.source_locals = set()
        self.return_reads_source = False


def _callee(call):
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _store_names(node):
    """Yield the Name ids bound by an assignment target.

    Tuple and starred targets yield every nested name (tuple unpacking);
    attribute and subscript targets yield nothing, because the taint engine
    tracks plain locals only.
    """
    if isinstance(node, ast.Name):
        yield node.id
    elif isinstance(node, (ast.Tuple, ast.List, ast.Starred)):
        for elt in node.elts:
            yield from _store_names(elt)


def _tainted_params(node, tainted, functions, sources):
    """Set of param indices whose value flows into this expression."""
    if node is None:
        return set()
    if isinstance(node, ast.Name):
        return set(tainted.get(node.id, set()))
    if isinstance(node, ast.Constant):
        return set()
    if isinstance(node, ast.BinOp):
        return (_tainted_params(node.left, tainted, functions, sources)
                | _tainted_params(node.right, tainted, functions, sources))
    if isinstance(node, ast.Attribute):
        return _tainted_params(node.value, tainted, functions, sources)
    if isinstance(node, ast.Subscript):
        return _tainted_params(node.value, tainted, functions, sources)
    if isinstance(node, (ast.Tuple, ast.List)):
        out = set()
        for elt in node.elts:
            out |= _tainted_params(elt, tainted, functions, sources)
        return out
    if isinstance(node, ast.JoinedStr):
        out = set()
        for v in node.values:
            if isinstance(v, ast.FormattedValue):
                out |= _tainted_params(v.value, tainted, functions, sources)
        return out
    if isinstance(node, ast.NamedExpr):
        out = _tainted_params(node.value, tainted, functions, sources)
        if isinstance(node.target, ast.Name):
            out |= set(tainted.get(node.target.id, set()))
        return out
    if isinstance(node, ast.Call):
        out = set()
        for arg in node.args:
            out |= _tainted_params(arg, tainted, functions, sources)
        cn = _callee(node)
        # A user-defined function shadows a same-named source: its own
        # parameter flows decide, the source list never fires for it.
        if cn in functions:
            g = functions[cn]
            for i, arg in enumerate(node.args):
                if i in g.flows_to_return or i in g.flows_to_sink:
                    out |= _tainted_params(arg, tainted, functions, sources)
        return out
    return set()


def _phase1(functions, language):
    sources = SOURCES.get(language, set())
    sinks = SINKS.get(language, set())
    for _ in range(10):
        changed = False
        for f in functions.values():
            tainted = {p: {i} for p, i in f.param_index.items()}

            def taint_of(node):
                return _tainted_params(node, tainted, functions, sources)

            new_sink = set(f.flows_to_sink)
            new_ret = set(f.flows_to_return)

            for n in ast.walk(f.node):
                if isinstance(n, ast.Assign):
                    t = taint_of(n.value)
                    for target in n.targets:
                        for tid in _store_names(target):
                            tainted[tid] = t
                    if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                        for target in n.targets:
                            for tid in _store_names(target):
                                f.source_locals.add(tid)

                elif isinstance(n, ast.AugAssign):
                    if isinstance(n.target, ast.Name):
                        t = taint_of(n.value) | tainted.get(n.target.id, set())
                        tainted[n.target.id] = t
                        if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                            f.source_locals.add(n.target.id)

                elif isinstance(n, ast.AnnAssign) and n.value is not None:
                    t = taint_of(n.value)
                    for tid in _store_names(n.target):
                        tainted[tid] = t
                    if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                        for tid in _store_names(n.target):
                            f.source_locals.add(tid)

                elif isinstance(n, ast.NamedExpr):
                    t = taint_of(n.value)
                    if isinstance(n.target, ast.Name):
                        tainted[n.target.id] = t
                        if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                            f.source_locals.add(n.target.id)

                if isinstance(n, ast.Call) and _callee(n) in sinks:
                    for arg in n.args:
                        new_sink |= taint_of(arg)
                if isinstance(n, ast.Return) and n.value is not None:
                    new_ret |= taint_of(n.value)
                    if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                        f.return_reads_source = True

            if new_sink != f.flows_to_sink or new_ret != f.flows_to_return:
                f.flows_to_sink, f.flows_to_return = new_sink, new_ret
                changed = True
        if not changed:
            break


def _phase2(functions, language):
    sources = SOURCES.get(language, set())
    sinks = SINKS.get(language, set())
    tainted_params = {name: set() for name in functions}
    tainted_returns = set()
    findings = []
    reported = set()

    for _ in range(50):
        changed = False
        for name, f in functions.items():
            local_taint = {p: {i} for p, i in f.param_index.items()
                           if i in tainted_params[name]}

            def tainted(node):
                if node is None:
                    return False
                if isinstance(node, ast.Name):
                    return (bool(local_taint.get(node.id))
                            or node.id in f.source_locals
                            or node.id in BARE_SOURCES)
                if isinstance(node, ast.Constant):
                    return False
                if isinstance(node, ast.BinOp):
                    return tainted(node.left) or tainted(node.right)
                if isinstance(node, ast.Attribute):
                    return (tainted(node.value)
                            or node.attr in sources
                            or node.attr in BARE_SOURCES)
                if isinstance(node, ast.Subscript):
                    return tainted(node.value)
                if isinstance(node, (ast.Tuple, ast.List)):
                    return any(tainted(elt) for elt in node.elts)
                if isinstance(node, ast.NamedExpr):
                    return (tainted(node.value)
                            or bool(local_taint.get(node.target.id))
                            or node.target.id in f.source_locals)
                if isinstance(node, ast.JoinedStr):
                    return any(isinstance(v, ast.FormattedValue) and tainted(v.value)
                               for v in node.values)
                if isinstance(node, ast.Call):
                    cn = _callee(node)
                    if cn in functions and cn not in tainted_returns:
                        # a user-defined function shadows a same-named source
                        return any(tainted(a) for a in node.args)
                    if cn in sources or cn in tainted_returns:
                        return True
                    return any(tainted(a) for a in node.args)
                return False

            for n in ast.walk(f.node):
                if isinstance(n, ast.Assign):
                    is_t = tainted(n.value)
                    for target in n.targets:
                        for tid in _store_names(target):
                            local_taint[tid] = {1} if is_t else set()
                elif isinstance(n, ast.AugAssign):
                    if isinstance(n.target, ast.Name):
                        is_t = (tainted(n.value)
                                or bool(local_taint.get(n.target.id))
                                or n.target.id in f.source_locals)
                        local_taint[n.target.id] = {1} if is_t else set()
                elif isinstance(n, ast.AnnAssign) and n.value is not None:
                    is_t = tainted(n.value)
                    for tid in _store_names(n.target):
                        local_taint[tid] = {1} if is_t else set()
                elif isinstance(n, ast.NamedExpr):
                    if isinstance(n.target, ast.Name):
                        local_taint[n.target.id] = {1} if tainted(n.value) else set()
                if isinstance(n, ast.Return) and n.value is not None:
                    if (tainted(n.value) or f.return_reads_source):
                        if name not in tainted_returns:
                            tainted_returns.add(name)
                            changed = True
                if isinstance(n, ast.Call):
                    cn = _callee(n)
                    if cn in sinks and any(tainted(a) for a in n.args):
                        key = (name, n.lineno)
                        if key not in reported:
                            reported.add(key)
                            confidence = "high" if _contains_source_local(n, f) else "medium"
                            findings.append(_finding(n, confidence))
                    elif cn in functions:
                        g = functions[cn]
                        for i, a in enumerate(n.args):
                            if tainted(a) and i not in tainted_params[cn]:
                                tainted_params[cn].add(i)
                                changed = True
        if not changed:
            break
    return findings


def _contains_source_local(sink_call, func):
    for n in ast.walk(sink_call):
        if isinstance(n, ast.Name) and n.id in func.source_locals:
            return True
    return False


def _finding(sink_call, confidence):
    return {
        "rule_id": "TAINT001",
        "title": "Untrusted data reaches a dangerous call",
        "severity": "high",
        "line": sink_call.lineno,
        "explanation": ("Data from an untrusted source flows into a call that "
                        "interprets it as code or as a shell command."),
        "suggestion": "Validate or escape the input, or pass arguments as a list without a shell.",
        "source": "taint",
        "fixed_snippet": None,
        "evidence": ast.unparse(sink_call)[:200],
        "confidence": confidence,
        "related_lines": [],
    }


def _analyse_python(source_code: str) -> list[dict]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[node.name] = FunctionInfo(node)
    _phase1(functions, "python")
    return _phase2(functions, "python")[:MAX_FINDINGS]


def analyse_taint(source_code: str, language: str) -> list[dict]:
    if language == "python":
        return _analyse_python(source_code)
    if language in ("javascript", "java", "c", "cpp"):
        return _token_analyse(source_code, language)
    return []


def _find_stmt_end(tokens, i):
    depth = 0
    for k in range(i, len(tokens)):
        t = tokens[k].text
        if t in "([{":
            depth += 1
        elif t in ")]}":
            if depth == 0:
                return k
            depth -= 1
        elif t == ";" and depth == 0:
            return k
    return len(tokens)


def _find_call(tokens, i):
    if tokens[i].kind != "identifier":
        return None
    if i + 1 >= len(tokens) or tokens[i + 1].text != "(":
        return None
    depth = 1
    j = i + 2
    while j < len(tokens) and depth:
        t = tokens[j].text
        if t == "(":
            depth += 1
        elif t == ")":
            depth -= 1
        j += 1
    return (tokens[i].text, i + 2, j - 1)


def _split_args(tokens, a, b):
    parts, start, depth = [], a, 0
    for k in range(a, b):
        t = tokens[k].text
        if t in "([{":
            depth += 1
        elif t in ")]}":
            depth -= 1
        elif t == "," and depth == 0:
            parts.append((start, k))
            start = k + 1
    parts.append((start, b))
    return parts


def _is_assign(tokens, i):
    """True when the identifier at i is followed by a plain `=` assignment.

    The scanner emits punctuation character-wise, so `==` and `===` arrive
    as separate `=` tokens. An assignment requires the next token to be `=`
    and the one after it NOT to be `=` (index guarded).
    """
    if i + 1 >= len(tokens) or tokens[i + 1].text != "=":
        return False
    if i + 2 < len(tokens) and tokens[i + 2].text == "=":
        return False
    return True


def _source_at(tokens, idx, sources, params):
    """True when the identifier at idx reads external data.

    A source name in call position (`prompt(`) always counts. Otherwise a
    source word counts only as a property of a member chain rooted at a
    parameter of the current function or at another source name —
    `req.query.name` and `params.mode` read request data. A bare mention
    does not count, which keeps broad source words like `query` and `body`
    from firing on their own, and neither does an object-literal key.
    """
    if tokens[idx].text not in sources:
        return False
    nxt = tokens[idx + 1].text if idx + 1 < len(tokens) else ""
    if nxt == "(":
        return True
    if nxt == ":":
        return False
    if idx > 0 and tokens[idx - 1].text == ".":
        j = idx
        while j >= 2 and tokens[j - 1].text == ".":
            j -= 2
        root = tokens[j].text
        return root in params or root in sources
    if nxt == ".":
        return True
    return False


def _expr_has_tainted(tokens, a, b, tainted_map, sources, params):
    """True when tokens[a:b] holds tainted data or reads a source."""
    for idx in range(a, min(b, len(tokens))):
        t = tokens[idx]
        if t.kind != "identifier":
            continue
        if t.text in BARE_SOURCES:
            return True
        if tainted_map.get(t.text):
            return True
        if _source_at(tokens, idx, sources, params):
            return True
    return False


def _returns_taint(tokens, a, b, tainted_map, sources, params, functions,
                   tainted_returns):
    """True when a call in the range returns data made tainted by its args."""
    for j in range(a, min(b, len(tokens))):
        t = tokens[j]
        if t.kind != "identifier":
            continue
        call = _find_call(tokens, j)
        if not call:
            continue
        callee, ca, cb = call
        if callee in functions and callee in tainted_returns:
            for ta, tb in _split_args(tokens, ca, cb):
                if _expr_has_tainted(tokens, ta, tb, tainted_map, sources,
                                     params):
                    return True
    return False


def _phase1_tokens(func, sources):
    """Anchor which locals hold external data.

    A local is marked when a plain assignment's right-hand side reads a
    source (call-shaped, or a member chain rooted at a parameter or source
    name), or when an output-parameter call (`gets(buf)`) writes through
    its argument. Phase 2 re-derives parameter and return flow itself, so
    this pass tracks nothing else.
    """
    tokens = func.body
    for i, tok in enumerate(tokens):
        if tok.kind != "identifier" or not _is_assign(tokens, i):
            continue
        start = i + 2
        end = _find_stmt_end(tokens, start)
        if _expr_has_tainted(tokens, start, end, {}, sources, func.params):
            func.source_locals.add(tok.text)
    i = 0
    while i < len(tokens):
        call = _find_call(tokens, i)
        if call:
            callee, a, b = call
            if callee in OUTPUT_SOURCES:
                for ta, tb in _split_args(tokens, a, b):
                    if tb - ta == 1 and tokens[ta].kind == "identifier":
                        func.source_locals.add(tokens[ta].text)
            i = b
        else:
            i += 1


def _phase2_tokens(functions, sources, sinks, language):
    tainted_params = {name: set() for name in functions}
    tainted_returns = set()
    findings = []
    reported = set()

    for _ in range(50):
        changed = False
        for name, func in functions.items():
            tokens = func.body
            tainted_map = {p: (i in tainted_params[name])
                           for i, p in enumerate(func.params)}
            for src in func.source_locals:
                tainted_map[src] = True

            def taint_expr(a, b):
                return (_expr_has_tainted(tokens, a, b, tainted_map,
                                          sources, func.params)
                        or _returns_taint(tokens, a, b, tainted_map, sources,
                                          func.params, functions,
                                          tainted_returns))

            def scan_calls(a, b):
                """Report sink hits and propagate into callees for every
                call in tokens[a:b]."""
                nonlocal changed
                k = a
                while k < b:
                    call = _find_call(tokens, k)
                    if not call:
                        k += 1
                        continue
                    callee, ca, cb = call
                    if callee in OUTPUT_SOURCES:
                        for ta, tb in _split_args(tokens, ca, cb):
                            if tb - ta == 1 and tokens[ta].kind == "identifier":
                                tainted_map[tokens[ta].text] = True
                    elif callee in sinks:
                        for ta, tb in _split_args(tokens, ca, cb):
                            if _expr_has_tainted(tokens, ta, tb, tainted_map,
                                                 sources, func.params):
                                key = (name, tokens[k].line)
                                if key not in reported:
                                    reported.add(key)
                                    findings.append(_finding_token(tokens[k]))
                                break
                    elif callee in functions:
                        g = functions[callee]
                        for idx, (ta, tb) in enumerate(_split_args(tokens, ca, cb)):
                            if (idx < len(g.params)
                                    and _expr_has_tainted(tokens, ta, tb,
                                                          tainted_map, sources,
                                                          func.params)):
                                if idx not in tainted_params[callee]:
                                    tainted_params[callee].add(idx)
                                    changed = True
                    k = cb

            for j, tok in enumerate(tokens):
                if tok.text == "return":
                    end = _find_stmt_end(tokens, j + 1)
                    if taint_expr(j + 1, end) and name not in tainted_returns:
                        tainted_returns.add(name)
                        changed = True
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if tok.kind == "identifier" and _is_assign(tokens, i):
                    start_expr = i + 2
                    end = _find_stmt_end(tokens, start_expr)
                    if taint_expr(start_expr, end):
                        tainted_map[tok.text] = True
                    # a sink or a cross-function call can sit inside the
                    # right-hand side: `const x = eval(n2)`
                    scan_calls(start_expr, end)
                    i = end
                    continue
                call = _find_call(tokens, i)
                if call:
                    scan_calls(i, call[2])
                    i = call[2]
                else:
                    i += 1
        if not changed:
            break
    return findings[:MAX_FINDINGS]


def _finding_token(tok):
    return {
        "rule_id": "TAINT001",
        "title": "Untrusted data reaches a dangerous call",
        "severity": "high",
        "line": tok.line,
        "explanation": "Data from an untrusted source flows into a call that interprets it as code or a shell command.",
        "suggestion": "Validate or escape the input, or use arguments as a list without a shell.",
        "source": "taint",
        "fixed_snippet": None,
        "evidence": f"token {tok.text!r}",
        "confidence": "medium",
        "related_lines": [],
    }


def _braces_balanced(tokens):
    depth = 0
    for t in tokens:
        if t.kind != "code":
            continue
        if t.text == "{":
            depth += 1
        elif t.text == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _module_function(tokens):
    """Build the `__module__` pseudo-function from the depth-0 tokens.

    A file that defines even one function would otherwise leave its
    top-level statements scanned by nothing. Braces themselves are
    excluded from the segment, so the body of a top-level
    `if (...) { ... }` (inside its braces) is not scanned — a deliberate
    narrowing. Returns None when there are no depth-0 tokens.
    """
    depth = 0
    top = []
    for t in tokens:
        if t.kind == "code":
            if t.text == "{":
                depth += 1
                continue
            if t.text == "}":
                depth -= 1
                continue
        if depth == 0:
            top.append(t)
    if not top:
        return None
    return Func("__module__", [], top)


def _token_analyse(source_code: str, language: str) -> list[dict]:
    from app.analysis.tokens import function_inventory
    from app.analysis.tokenizer import tokenize_source
    functions = function_inventory(source_code, language)
    tokens = tokenize_source(source_code, language)
    if not functions and not _braces_balanced(tokens):
        # the inventory gave up on unbalanced braces: proximity fallback
        return _intraprocedural(source_code, language)
    module = _module_function(tokens)
    if module is not None:
        functions["__module__"] = module
    if not functions:
        return []
    sources = SOURCES.get(language, set())
    sinks = SINKS.get(language, set())
    for func in functions.values():
        _phase1_tokens(func, sources)
    return _phase2_tokens(functions, sources, sinks, language)


def _intraprocedural(source_code: str, language: str) -> list[dict]:
    """Fallback when braces do not balance: source and sink in one function."""
    from app.analysis.tokenizer import tokenize_source
    tokens = tokenize_source(source_code, language)
    sources = SOURCES.get(language, set())
    sinks = SINKS.get(language, set())
    source_lines = {t.line for t in tokens if t.kind == "identifier" and t.text in sources}
    sink_lines = {t.line for t in tokens if t.kind == "identifier" and t.text in sinks}
    findings = []
    for line in sorted(sink_lines):
        if any(abs(line - s) <= 40 for s in source_lines):
            findings.append({
                "rule_id": "TAINT001",
                "title": "Untrusted data may reach a dangerous call",
                "severity": "high",
                "line": line,
                "explanation": "Untrusted input and a dangerous call occur close together; the file could not be parsed into functions, so the analysis fell back to a proximity heuristic.",
                "suggestion": "Check the dataflow manually; the tool flagged the suspicious pairing.",
                "source": "taint",
                "fixed_snippet": None,
                "evidence": "",
                "confidence": "medium",
                "related_lines": sorted(source_lines),
            })
    return findings[:MAX_FINDINGS]
