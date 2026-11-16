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


def _binding_keys(target):
    # every name a binding target defines: Names, dotted attribute targets,
    # starred expressions and tuple/list unpacking
    if target is None:
        return
    if isinstance(target, (ast.Name, ast.Attribute)):
        key = _dotted(target)
        if key:
            yield key
    elif isinstance(target, ast.Starred):
        yield from _binding_keys(target.value)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            yield from _binding_keys(elt)


def _param_names(node):
    args = node.args
    for a in (list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
              + [args.vararg, args.kwarg]):
        if a is not None:
            yield a.arg


def _imported_names(tree):
    # provenance map: local binding name -> the requests/httpx module it came
    # from, or None for imports from anywhere else (negative provenance).
    # requests.api.get(...) is tracked once 'api' is imported from requests.
    # The last import of the same name wins (walk order is source order), so
    # `from requests import Session` followed by `from sqlalchemy.orm import
    # Session` leaves Session as None and it is never treated as a client.
    # Order-insensitivity: the map is built before analysis, so a module-level
    # alias (`import requests as rq` anywhere in the file) applies file-wide,
    # including on lines before its import. Documented, not fixed.
    m = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            http = module in HTTP_MODULES
            for a in node.names:
                if a.name == "*":
                    m["*"] = module if http else None
                    continue
                m[a.asname or a.name] = module if http else None
        elif isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                m[a.asname or root] = root if root in HTTP_MODULES else None
    return m


def _provenance(imported, name):
    # an explicit record (even a None negative one) wins over a *-import
    if name in imported:
        return imported[name]
    return imported.get("*")


def _is_client_constructor(call, imported):
    if not isinstance(call, ast.Call):
        return False
    f = call.func
    if isinstance(f, ast.Attribute) and f.attr in {"Session", "Client", "AsyncClient"}:
        base = _dotted(f.value)
        root = base.split(".")[0] if base else ""
        if root in HTTP_MODULES:
            return True
        return _provenance(imported, root) in HTTP_MODULES
    # from requests import Session / from httpx import Client (only when the
    # binding really came from requests/httpx; a *-import confers provenance)
    if isinstance(f, ast.Name) and f.id in {"Session", "Client", "AsyncClient"}:
        return _provenance(imported, f.id) in HTTP_MODULES
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
    # kind: "module" for the persistent file frame, "class" for the persistent
    # class-body frame shared by all methods, "function" for transient
    # function/method frames, "with" for transient with-block frames
    def __init__(self, kind):
        self.kind = kind
        self.reg = set()
        self.tomb = set()


class _Checker(ast.NodeVisitor):
    def __init__(self, imported):
        self.scopes = [_Frame("module")]  # persistent module frame
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

    def _tombstoned(self, key):
        # mirror of _lookup: True only when the nearest frame carrying any
        # state for key has it tombstoned (absent everywhere is not tombstoned)
        for frame in reversed(self.scopes):
            if key in frame.tomb:
                return True
            if key in frame.reg:
                return False
        return False

    def _open_scope(self, kind): self.scopes.append(_Frame(kind))

    def _close_scope(self, merge_dotted=False):
        frame = self.scopes.pop()
        if not merge_dotted:
            return
        # dotted keys from a function frame merge into their parent only when
        # the parent is a class frame: methods of a class share the class
        # namespace, but nothing defined in a module-level function may leak
        # file-wide. Class frames in turn never merge into the module frame.
        parent = self.scopes[-1]
        if parent.kind != "class":
            return
        # function frames merge their dotted keys (registrations and tombstones)
        # into the parent frame; bare names stay local to the function
        for key in frame.reg:
            if "." in key:
                parent.reg.add(key)
                parent.tomb.discard(key)
        for key in frame.tomb:
            if "." in key:
                parent.tomb.add(key)
                parent.reg.discard(key)

    def visit_FunctionDef(self, node):
        self._open_scope("function")
        # parameters bind names: they tombstone within the function so a
        # module-level client never leaks in through a same-named parameter
        for name in _param_names(node):
            self._unregister(name)
        self._check_function_defaults(node)
        self.generic_visit(node)
        # dotted keys merge into the parent frame, but only when that frame is
        # a class body (see _close_scope)
        self._close_scope(merge_dotted=True)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        # one frame per class body, persisted while the class is visited, so
        # all methods of the class see the same registrations
        self._open_scope("class")
        self.generic_visit(node)
        self._close_scope()

    # ---- statements
    def visit_Assign(self, node):
        keys = [k for t in node.targets for k in _binding_keys(t)]
        for key in keys:
            self._unregister(key)
        if _is_client_constructor(node.value, self.imported):
            for key in keys:
                self._register(key)
        self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            keys = list(_binding_keys(node.target))
            for key in keys:
                self._unregister(key)
            if _is_client_constructor(node.value, self.imported):
                for key in keys:
                    self._register(key)
        self.generic_visit(node)

    def visit_For(self, node):
        # loop targets bind names: tombstone so a same-named client binding
        # does not leak into the loop body
        for key in _binding_keys(node.target):
            self._unregister(key)
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.visit_For(node)

    def _visit_comprehension(self, node):
        # comprehension targets bind within the comprehension; the analyzer
        # tombstones them in the enclosing scope, because the element and
        # conditions are visited before the generators that bind them
        for gen in node.generators:
            for key in _binding_keys(gen.target):
                self._unregister(key)
        self.generic_visit(node)

    def visit_ListComp(self, node): self._visit_comprehension(node)
    def visit_SetComp(self, node): self._visit_comprehension(node)
    def visit_GeneratorExp(self, node): self._visit_comprehension(node)
    def visit_DictComp(self, node): self._visit_comprehension(node)

    def visit_With(self, node):
        # transient frame: `with requests.Session() as s` closes s at the end
        # of the block, so the registration must not outlive it
        self._open_scope("with")
        for item in node.items:
            keys = list(_binding_keys(item.optional_vars)) if item.optional_vars is not None else []
            # any `with ... as name` binds name: tombstone first so a client
            # binding from outside never leaks into a non-client block
            for key in keys:
                self._unregister(key)
            if _is_client_constructor(item.context_expr, self.imported):
                for key in keys:
                    self._register(key)
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
    # merge from function frames into a parent class frame on exit); also
    # direct module calls and aliases (`import requests as rq`). A name imported
    # from requests/httpx (`from requests import api`) makes api.get(...) flag.
    # A bare `from requests import get` followed by get(...) is not tracked by design.
    # A tombstoned root (e.g. `rq = {}`) silences the import-provenance clauses.
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
        root_blocked = bool(root) and self._tombstoned(root)
        root_module = _provenance(self.imported, root) if root else None
        is_http = (
            (bool(root) and not root_blocked and root in HTTP_MODULES)
            or (bool(root) and not root_blocked and root_module in HTTP_MODULES)
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
