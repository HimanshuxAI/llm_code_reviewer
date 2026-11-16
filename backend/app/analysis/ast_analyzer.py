"""Python semantic checks via the stdlib ast module."""
import ast
import re

MAX_FINDINGS = 60
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "request", "head", "options"}
HTTP_MODULES = {"requests", "httpx"}
AUTH_PARTS = ("admin", "auth", "permission", "role", "staff", "superuser")

BROAD_EXCEPTIONS = frozenset({"Exception", "BaseException"})


def _dotted(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return None


def _ident_parts(name):
    return [p.lower() for p in re.split(r"[^A-Za-z0-9]+|(?<=[a-z0-9])(?=[A-Z])", name) if p]


def _imported_names(tree):
    # provenance map: local binding name -> the requests/httpx module it came from
    m = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "") in HTTP_MODULES:
            for a in node.names:
                m[a.asname or a.name] = node.module
        elif isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root in HTTP_MODULES:
                    m[a.asname or root] = root
    return m


def _is_client_constructor(call, imported):
    if not isinstance(call, ast.Call):
        return False
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr in {"Session", "Client", "AsyncClient"}:
        base = _dotted(f.value)
        root = base.split(".")[0] if base else ""
        return root in HTTP_MODULES or imported.get(root) in HTTP_MODULES
    # from requests import Session / from httpx import Client (only when the
    # binding really came from requests/httpx)
    if isinstance(f, ast.Name) and f.id in {"Session", "Client", "AsyncClient"}:
        return imported.get(f.id) in HTTP_MODULES
    return False


def _is_broad_handler(type_node):
    # Bare `except:` is left to QUAL001 (regex) so the two never double count;
    # this check reports broad named exceptions that swallow errors with pass.
    if type_node is None:
        return False
    if isinstance(type_node, ast.Name):
        return type_node.id in BROAD_EXCEPTIONS
    if isinstance(type_node, ast.Tuple):
        return any(
            isinstance(e, ast.Name) and e.id in BROAD_EXCEPTIONS
            for e in type_node.elts
        )
    return False


class _Frame:
    def __init__(self):
        self.reg = set()
        self.tomb = set()


class _Checker(ast.NodeVisitor):
    def __init__(self, imported):
        self.scopes = [_Frame()]  # persistent module frame
        self.findings = []
        self.imported = imported

    # ---- scope helpers
    def _register(self, key):
        self.scopes[-1].reg.add(key)
        self.scopes[-1].tomb.discard(key)

    def _unregister(self, key):
        # writes a tombstone, never removes an outer registration
        self.scopes[-1].tomb.add(key)

    def _lookup(self, key):
        # walks from innermost scope outwards; nearest frame with any state wins
        for frame in reversed(self.scopes):
            if key in frame.tomb:
                return False
            if key in frame.reg:
                return True
        return False

    def _open_scope(self): self.scopes.append(_Frame())

    def _close_scope(self, merge_dotted=False):
        frame = self.scopes.pop()
        if not merge_dotted:
            return
        # function frames merge their dotted keys (registrations and tombstones)
        # into the parent frame; bare names stay local to the function
        parent = self.scopes[-1]
        for key in frame.reg:
            if "." in key:
                parent.reg.add(key)
                parent.tomb.discard(key)
        for key in frame.tomb:
            if "." in key:
                parent.tomb.add(key)
                parent.reg.discard(key)

    def visit_FunctionDef(self, node):
        self._open_scope()
        self._check_function_defaults(node)
        self.generic_visit(node)
        # dotted keys merge into the parent frame (module or class body)
        self._close_scope(merge_dotted=True)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        # one frame per class body, persisted while the class is visited, so
        # all methods of the class see the same registrations
        self._open_scope()
        self.generic_visit(node)
        self._close_scope()

    # ---- statements
    def visit_Assign(self, node):
        for t in node.targets:
            key = _dotted(t)
            if key: self._unregister(key)
        if _is_client_constructor(node.value, self.imported):
            for t in node.targets:
                key = _dotted(t)
                if key: self._register(key)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            key = _dotted(node.target)
            if key: self._unregister(key)
            if _is_client_constructor(node.value, self.imported):
                if key: self._register(key)
        self.generic_visit(node)

    def visit_With(self, node):
        # transient frame: `with requests.Session() as s` closes s at the end
        # of the block, so the registration must not outlive it
        self._open_scope()
        for item in node.items:
            if _is_client_constructor(item.context_expr, self.imported) and item.optional_vars is not None:
                key = _dotted(item.optional_vars)
                if key: self._register(key)
        self.generic_visit(node)
        self._close_scope()

    def visit_AsyncWith(self, node):
        self.visit_With(node)

    def visit_Call(self, node):
        self._check_http_call(node)
        self._check_open_call(node)
        self.generic_visit(node)

    def visit_Assert(self, node):
        if self._assert_is_auth(node):
            # confidence is medium: token matching is a heuristic
            self._add("PY001", "assert used for an authorization check", "medium",
                      node.lineno,
                      "assert is stripped when Python runs with -O, so authorization is silently skipped.",
                      "Raise PermissionError explicitly instead.",
                      f"assert {ast.unparse(node)[:180]}")
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        body_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
        if body_pass and _is_broad_handler(node.type):
            self._add("QUAL002", "Broad except swallowing everything", "low",
                      node.lineno,
                      "Ignoring a broad exception with pass hides every error, including bugs you want to see.",
                      "Catch the specific exception types you expect, or remove the try.",
                      f"except {ast.unparse(node.type)}: pass")
        self.generic_visit(node)

    # http: registered clients (scope-aware via the frame stack; dotted keys
    # merge from function frames into their parent on exit); also direct
    # module calls and aliases (`import requests as rq`). Dotted module calls
    # (`from requests import api; api.get(...)`) are not tracked.
    def _check_http_call(self, node):
        func = node.func
        if not isinstance(func, ast.Attribute):
            return
        if func.attr not in HTTP_METHODS:
            return
        # **kwargs means we cannot see the timeout flag; a *args positional
        # may carry it too
        if any(k.arg is None for k in node.keywords):
            return
        if any(isinstance(a, ast.Starred) for a in node.args):
            return
        key = _dotted(func.value)
        root = key.split(".")[0] if key else ""
        is_http = (
            root in HTTP_MODULES
            or self.imported.get(root) in HTTP_MODULES
            or (key is not None and self._lookup(key))
        )
        if not is_http:
            return
        if "timeout" in {k.arg for k in node.keywords}:
            return
        self._add("PY002", "HTTP call without a timeout", "medium",
                  node.lineno,
                  "requests/httpx calls wait forever when the server stops responding.",
                  "Pass timeout=10 or similar on every HTTP call.",
                  f"{func.attr}(...) without timeout=")

    # QUAL003: only the builtin open (Name), NOT os.open/tarfile.open/etc.
    def _check_open_call(self, node):
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "open"):
            return
        kw = {k.arg for k in node.keywords}
        # encoding may be 4th positional arg: file, mode, buffering, encoding
        if "encoding" in kw:
            return
        if len(node.args) >= 4:
            a3 = node.args[3]
            if isinstance(a3, ast.Constant) and isinstance(a3.value, str):
                return
        mode_pos = node.args[1] if len(node.args) >= 2 else None
        if isinstance(mode_pos, ast.Constant) and isinstance(mode_pos.value, str) and "b" in mode_pos.value:
            return
        for k in node.keywords:
            if k.arg == "mode" and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str) and "b" in k.value.value:
                return
        self._add("QUAL003", "open() without an explicit encoding", "low",
                  node.lineno,
                  "open() uses the platform default encoding, which differs across machines.",
                  "Pass encoding='utf-8' explicitly.",
                  "open(...) without encoding=")

    def _check_function_defaults(self, node):
        all_defaults = [d for d in (list(node.args.defaults) + list(node.args.kw_defaults)) if d is not None]
        for default in all_defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self._add("BUG001", "Mutable default argument", "high",
                          default.lineno,
                          "The default list/dict/set is shared across all calls, so bugs leak state between invocations.",
                          "Use None as the default and initialise inside the function.",
                          f"def {node.name}(...): default={ast.unparse(default)[:180]}")

    def _assert_is_auth(self, node):
        ids = []
        for n in ast.walk(node):
            if isinstance(n, (ast.Name, ast.Attribute)):
                ids.append(ast.unparse(n) if isinstance(n, ast.Attribute) else n.id)
        parts = []
        for i in ids:
            parts.extend(_ident_parts(i))
        return any(p in AUTH_PARTS for p in parts)

    def _add(self, rule_id, title, severity, lineno, explanation, suggestion, evidence):
        self.findings.append({
            "rule_id": rule_id, "title": title, "severity": severity,
            "line": lineno, "explanation": explanation, "suggestion": suggestion,
            "source": "ast", "fixed_snippet": None,
            "evidence": evidence[:200],
            "confidence": "high" if rule_id != "PY001" else "medium",
            "related_lines": [],
        })


def analyse_python(source_code: str) -> list[dict]:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []
    checker = _Checker(_imported_names(tree))
    checker.visit(tree)
    # Lambdas with mutable defaults are not flagged: lambda arguments are not
    # visited by visit_FunctionDef (documented narrowness).
    return checker.findings[:MAX_FINDINGS]
