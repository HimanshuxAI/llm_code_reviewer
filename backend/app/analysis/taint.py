# backend/app/analysis/taint.py
"""Two-phase interprocedural taint analysis.

Phase 1 (bottom-up): for each function compute which parameters can reach a
    sink and which can reach the return value. No parameter is assumed tainted.
Phase 2 (top-down): propagate taint from real sources through call sites;
    report a sink only when tainted data reaches it.

Confidence is "high" when the tainted expression at the sink contains a name
that was directly assigned from a source in that same function, and "medium"
otherwise (the flow crossed a function boundary).
"""
import ast

from app.analysis.sinks import SOURCES, SINKS

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
    if isinstance(node, ast.JoinedStr):
        out = set()
        for v in node.values:
            if isinstance(v, ast.FormattedValue):
                out |= _tainted_params(v.value, tainted, functions, sources)
        return out
    if isinstance(node, ast.Call):
        out = set()
        for arg in node.args:
            out |= _tainted_params(arg, tainted, functions, sources)
        cn = _callee(node)
        if cn in sources:
            return out  # reads external data; args contribute nothing
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
                        if isinstance(target, ast.Name):
                            tainted[target.id] = t
                    if isinstance(n.value, ast.Call) and _callee(n.value) in sources:
                        for target in n.targets:
                            if isinstance(target, ast.Name):
                                f.source_locals.add(target.id)

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

    for _ in range(20):
        changed = False
        for name, f in functions.items():
            local_taint = {p: {i} for p, i in f.param_index.items()
                           if i in tainted_params[name]}

            def tainted(node):
                if node is None:
                    return False
                if isinstance(node, ast.Name):
                    return bool(local_taint.get(node.id)) or node.id in f.source_locals
                if isinstance(node, ast.Constant):
                    return False
                if isinstance(node, ast.BinOp):
                    return tainted(node.left) or tainted(node.right)
                if isinstance(node, ast.Attribute):
                    return tainted(node.value)
                if isinstance(node, ast.Subscript):
                    return tainted(node.value)
                if isinstance(node, ast.JoinedStr):
                    return any(isinstance(v, ast.FormattedValue) and tainted(v.value)
                               for v in node.values)
                if isinstance(node, ast.Call):
                    cn = _callee(node)
                    if cn in sources or cn in tainted_returns:
                        return True
                    return any(tainted(a) for a in node.args)
                return False

            for n in ast.walk(f.node):
                if isinstance(n, ast.Assign):
                    is_t = tainted(n.value)
                    for target in n.targets:
                        if isinstance(target, ast.Name):
                            local_taint[target.id] = {1} if is_t else set()
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
    return _phase2(functions, "python")


def analyse_taint(source_code: str, language: str) -> list[dict]:
    if language == "python":
        return _analyse_python(source_code)
    if language in ("javascript", "java", "c", "cpp"):
        return _token_analyse(source_code, language)
    return []
