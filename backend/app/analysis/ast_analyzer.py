"""Python semantic checks via the stdlib ast module."""
import ast

AUTH_WORDS = ("admin", "auth", "permission", "role", "is_", "user")

BROAD_EXCEPTIONS = frozenset({"Exception", "BaseException"})


def _call_name(node):
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _is_broad_handler(type_node):
    # Bare `except:` is left to QUAL001 (regex) so the two never double count;
    # this check reports broad named exceptions that swallow errors with pass.
    if type_node is None:
        return False
    if isinstance(type_node, ast.Name):
        return type_node.id in BROAD_EXCEPTIONS
    if isinstance(type_node, ast.Tuple):
        return any(
            isinstance(elt, ast.Name) and elt.id in BROAD_EXCEPTIONS
            for elt in type_node.elts
        )
    return False


def _mode_value(node):
    # open() accepts the mode positionally or as a keyword; binary modes do
    # not need an encoding.
    positional = node.args[1] if len(node.args) >= 2 else None
    keyword = next((k.value for k in node.keywords if k.arg == "mode"), None)
    value = keyword if keyword is not None else positional
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


def analyse_python(source_code: str) -> list[dict]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    findings = []

    def add(rule_id, title, severity, lineno, explanation, suggestion, evidence):
        findings.append({
            "rule_id": rule_id,
            "title": title,
            "severity": severity,
            "line": lineno,
            "explanation": explanation,
            "suggestion": suggestion,
            "source": "ast",
            "fixed_snippet": None,
            "evidence": evidence[:200],
            "confidence": "high",
            "related_lines": [],
        })

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults:
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    add("BUG001", "Mutable default argument", "high", node.lineno,
                        "The default list/dict/set is shared across all calls, so bugs leak state between invocations.",
                        "Use None as the default and initialise inside the function.",
                        f"def {node.name}(...): default={ast.unparse(default)}")

        elif isinstance(node, ast.Assert):
            test_str = ast.unparse(node.test) if hasattr(ast, "unparse") else ""
            if any(word in test_str.lower() for word in AUTH_WORDS):
                add("SEC014", "assert used for an authorization check", "medium",
                    node.lineno,
                    "assert is stripped when Python runs with -O, so authorization is silently skipped.",
                    "Raise PermissionError explicitly instead.",
                    f"assert {test_str}")

        elif isinstance(node, ast.ExceptHandler):
            body_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
            if body_pass and _is_broad_handler(node.type):
                add("QUAL002", "Broad except swallowing everything", "low",
                    node.lineno,
                    "Ignoring a broad exception with pass hides every error, including bugs you want to see.",
                    "Catch the specific exception types you expect, or remove the try.",
                    f"except {ast.unparse(node.type)}: pass")

        elif isinstance(node, ast.Call):
            name = _call_name(node)
            kw = {k.arg for k in node.keywords}
            if name in {"get", "post", "put", "delete", "patch", "request"} and \
               node.keywords is not None and "timeout" not in kw:
                add("SEC015", "HTTP call without a timeout", "medium",
                    node.lineno,
                    "requests/httpx calls wait forever when the server stops responding.",
                    "Pass timeout=10 or similar on every HTTP call.",
                    f"{name}(...) without timeout=")
            elif name == "open" and "encoding" not in kw:
                mode = _mode_value(node)
                # binary modes do not need an encoding
                if not (mode is not None and "b" in mode):
                    add("QUAL003", "open() without an explicit encoding", "low",
                        node.lineno,
                        "open() uses the platform default encoding, which differs across machines.",
                        "Pass encoding='utf-8' explicitly.",
                        "open(...) without encoding=")

    return findings
