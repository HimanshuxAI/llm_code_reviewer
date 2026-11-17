"""Maintainability checks. Python via AST; other languages via tokens."""
import ast

from app.analysis.tokens import function_inventory

MAX_FINDINGS = 60
MAX_LINES = 60
MAX_COMPLEXITY = 12
MAX_NESTING = 4
MAX_PARAMS = 5

_TODO = ("TODO", "FIXME", "HACK", "XXX")
_DECISION_KW = {"if", "else", "elif", "for", "while", "case", "catch", "except"}


def _python_metrics(node):
    complexity = 1
    nesting = 0

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.depth = 0

        def _block(self, body):
            nonlocal nesting
            self.depth += 1
            nesting = max(nesting, self.depth)
            for child in body:
                self.visit(child)
            self.depth -= 1

        def visit_If(self, n):
            nonlocal complexity
            complexity += 1
            self._block(n.body)
            self._block(n.orelse)

        def visit_For(self, n):
            nonlocal complexity
            complexity += 1
            self._block(n.body)
            self._block(n.orelse)

        def visit_While(self, n):
            nonlocal complexity
            complexity += 1
            self._block(n.body)
            self._block(n.orelse)

        def visit_BoolOp(self, n):
            nonlocal complexity
            complexity += len(n.values) - 1
            self.generic_visit(n)

        def visit_ExceptHandler(self, n):
            nonlocal complexity
            complexity += 1
            self._block(n.body)

    Visitor().visit(node)
    return complexity, nesting


def _finding(rule_id, title, lineno, explanation, suggestion):
    return {
        "rule_id": rule_id, "title": title, "severity": "low",
        "line": lineno, "explanation": explanation, "suggestion": suggestion,
        "source": "quality", "fixed_snippet": None,
        "evidence": "", "confidence": "high", "related_lines": [],
    }


def _analyse_python(source_code: str) -> list[dict]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        lines = (node.end_lineno or node.lineno) - node.lineno + 1
        complexity, nesting = _python_metrics(node)
        params = (len(node.args.args) + len(node.args.kwonlyargs)
                  + len(node.args.posonlyargs))
        if lines > MAX_LINES:
            findings.append(_finding("QUAL007", "Function is too long", node.lineno,
                f"This function has {lines} lines; long functions are hard to review and test.",
                "Split it into smaller functions with single responsibilities."))
        if complexity > MAX_COMPLEXITY:
            findings.append(_finding("QUAL008", "Cyclomatic complexity is too high", node.lineno,
                f"Complexity is {complexity}; this function has too many branches.",
                "Extract branches into named helpers."))
        if nesting > MAX_NESTING:
            findings.append(_finding("QUAL009", "Nesting is too deep", node.lineno,
                f"Nesting goes {nesting} levels deep.",
                "Return early, or extract the inner logic into a helper."))
        if params > MAX_PARAMS:
            findings.append(_finding("QUAL010", "Too many parameters", node.lineno,
                f"{params} parameters; callers struggle to use this correctly.",
                "Group related arguments into an object or config."))
    # Line-based scan of raw source (deliberately not comment/string masked,
    # matching the plan): a "# TODO" inside a string or "print(" in a comment
    # can false-positive. Line numbers stay accurate.
    for lineno, line in enumerate(source_code.splitlines(), start=1):
        s = line.strip()
        if s.startswith("print("):
            findings.append(_finding("QUAL011", "Leftover print() call", lineno,
                "print() calls left in code are debug leftovers.",
                "Remove it or route it through proper logging."))
        if any(t in s.upper() for t in _TODO):
            findings.append(_finding("QUAL012", "TODO/FIXME comment", lineno,
                "An unfinished TODO is committed.",
                "Resolve it or file it as an issue and link the number."))
    return findings[:MAX_FINDINGS]


def _generic_metrics(func):
    """Line count, complexity, nesting depth and parameter count.

    Complexity counts decision keywords in the body; nesting counts the
    deepest brace level reached inside it. A nested function's keywords are
    counted in the outer function as well — an approximation, and the same
    one the token-based taint pass makes.
    """
    complexity = 1
    depth = 0
    max_depth = 0
    for tok in func.body:
        if tok.text in _DECISION_KW:
            complexity += 1
        elif tok.text == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif tok.text == "}":
            depth -= 1
    lines = 0
    if func.start_line and func.end_line:
        lines = func.end_line - func.start_line + 1
    return lines, complexity, max_depth, len(func.params)


def _analyse_generic(source_code: str, language: str) -> list[dict]:
    findings = []
    for func in function_inventory(source_code, language).values():
        lines, complexity, nesting, params = _generic_metrics(func)
        where = func.start_line or 1
        if lines > MAX_LINES:
            findings.append(_finding("QUAL007", "Function is too long", where,
                f"This function has {lines} lines; long functions are hard to review and test.",
                "Split it into smaller functions with single responsibilities."))
        if complexity > MAX_COMPLEXITY:
            findings.append(_finding("QUAL008", "Cyclomatic complexity is too high", where,
                f"Complexity is {complexity}; this function has too many branches.",
                "Extract branches into named helpers."))
        if nesting > MAX_NESTING:
            findings.append(_finding("QUAL009", "Nesting is too deep", where,
                f"Nesting goes {nesting} levels deep.",
                "Return early or extract inner logic."))
        if params > MAX_PARAMS:
            findings.append(_finding("QUAL010", "Too many parameters", where,
                f"{params} parameters; callers struggle to use this correctly.",
                "Group related arguments into an object or config."))
    # Line-based scan of raw source; see the note in _analyse_python.
    for lineno, line in enumerate(source_code.splitlines(), start=1):
        s = line.strip()
        if "console.log(" in s or s.startswith("print("):
            findings.append(_finding("QUAL011", "Leftover console.log() call", lineno,
                "A console.log() call is left in the code.",
                "Remove it or route it through proper logging."))
        if any(t in s.upper() for t in _TODO):
            findings.append(_finding("QUAL012", "TODO/FIXME comment", lineno,
                "An unfinished TODO is committed.",
                "Resolve it or file it as an issue."))
    return findings[:MAX_FINDINGS]


def detect_quality_issues(source_code: str, language: str) -> list[dict]:
    if language == "python":
        return _analyse_python(source_code)
    if language in ("javascript", "java", "c", "cpp"):
        return _analyse_generic(source_code, language)
    return []
