"""Common correctness bugs detectable by static analysis.

These are logic mistakes the scanner can flag without running the code:
unused assignments, unreachable code after a terminator, and mutating a
sequence while iterating over it.
"""
import ast

MAX_FINDINGS = 40


def _binding_names(target):
    """Yield every name bound by an assignment target."""
    if target is None:
        return
    if isinstance(target, ast.Name):
        yield target.id
    elif isinstance(target, ast.Tuple):
        for elt in target.elts:
            yield from _binding_names(elt)
    elif isinstance(target, ast.List):
        for elt in target.elts:
            yield from _binding_names(elt)
    elif isinstance(target, ast.Starred):
        if isinstance(target.value, ast.Name):
            yield target.value.id


def _is_terminator(stmt):
    return isinstance(stmt, (ast.Return, ast.Break, ast.Continue, ast.Raise))


def _find_unreachable(body):
    """Return indices of statements that follow a terminator in a block."""
    unreachable = []
    terminated = False
    for i, stmt in enumerate(body):
        if terminated:
            unreachable.append(i)
        elif _is_terminator(stmt):
            terminated = True
    return unreachable


def detect_bugs(source_code: str, language: str | None = None) -> list[dict]:
    if language != "python":
        return []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    findings = []

    class _Checker(ast.NodeVisitor):
        def __init__(self):
            self.assigned = set()   # names assigned somewhere in scope
            self.used = set()       # names read somewhere in scope

        def visit_Assign(self, node):
            for target in node.targets:
                for name in _binding_names(target):
                    self.assigned.add(name)
            self.generic_visit(node)

        def visit_AnnAssign(self, node):
            if node.target is not None and isinstance(node.target, ast.Name):
                self.assigned.add(node.target.id)
            self.generic_visit(node)

        def visit_NamedExpr(self, node):
            if isinstance(node.target, ast.Name):
                self.assigned.add(node.target.id)
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                self.used.add(node.id)
            self.generic_visit(node)

        def visit_For(self, node):
            # detect mutating the iterated container inside the loop body
            if isinstance(node.iter, ast.Name):
                container = node.iter.id
                for stmt in node.body:
                    for inner in ast.walk(stmt):
                        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                            if inner.func.attr in {"append", "extend", "insert", "pop", "remove", "clear", "sort", "reverse"}:
                                if any(
                                    isinstance(a, ast.Name) and a.id == container
                                    for a in inner.args
                                ) or (
                                    isinstance(inner.func.value, ast.Name)
                                    and inner.func.value.id == container
                                ):
                                    findings.append({
                                        "rule_id": "PY006",
                                        "title": "List mutated during iteration",
                                        "severity": "high",
                                        "line": inner.lineno,
                                        "explanation": f"Mutating '{container}' while iterating over it skips elements or raises RuntimeError.",
                                        "suggestion": "Iterate over a copy: for x in list(container): ...",
                                        "source": "bugs",
                                        "fixed_snippet": None,
                                        "evidence": f"{inner.func.attr}(...)",
                                        "confidence": "medium",
                                        "related_lines": [],
                                    })
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            # check for unreachable statements inside the function body
            body = node.body
            for i in _find_unreachable(body):
                stmt = body[i]
                findings.append({
                    "rule_id": "PY005",
                    "title": "Unreachable code",
                    "severity": "medium",
                    "line": stmt.lineno,
                    "explanation": "Code after a return/break/continue/raise can never execute and is dead code.",
                    "suggestion": "Remove the unreachable block or move the terminator.",
                    "source": "bugs",
                    "fixed_snippet": None,
                    "evidence": ast.unparse(stmt)[:120] if hasattr(ast, "unparse") else "",
                    "confidence": "high",
                    "related_lines": [],
                })
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

    checker = _Checker()
    checker.visit(tree)

    # unused assigned names (after full visit so reads are collected)
    unused = checker.assigned - checker.used
    # never flag dunder names or loop variables that are only written
    for name in sorted(unused):
        if name.startswith("__") and name.endswith("__"):
            continue
        findings.append({
            "rule_id": "PY004",
            "title": f"Unused variable '{name}'",
            "severity": "low",
            "line": 1,
            "explanation": f"'{name}' is assigned but never read, so the assignment has no effect.",
            "suggestion": f"Remove the assignment to '{name}' or use the value.",
            "source": "bugs",
            "fixed_snippet": None,
            "evidence": name,
            "confidence": "medium",
            "related_lines": [],
        })

    return findings[:MAX_FINDINGS]

