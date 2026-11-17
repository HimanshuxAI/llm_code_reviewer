"""Python correctness bugs detectable by static analysis.

Logic mistakes the scanner can flag without running the code, Python-only
(uses the stdlib ``ast`` module for scope-aware analysis):

- PY004: unused variable (assigned but never read, scope-aware)
- PY005: unreachable code after a terminator
- PY006: list mutated while iterating over it
- PY007: unused import (name imported but never referenced)
- PY008: builtin shadowing (assigning to ``list``, ``str``, ``id``, etc.)
- PY009: dict mutated while iterating over it
- PY010: comparing to ``None``/``True``/``False`` with ``==`` instead of ``is``
- PY011: ``type(x) == Y`` instead of ``isinstance(x, Y)``
"""
import ast

MAX_FINDINGS = 60

# Names Python reserves as builtins. Assigning to one silently breaks the
# builtin everywhere it's used after the assignment.
BUILTINS = frozenset({
    "abs", "all", "any", "ascii", "bin", "bool", "breakpoint", "bytearray",
    "bytes", "callable", "chr", "classmethod", "compile", "complex",
    "delattr", "dict", "dir", "divmod", "enumerate", "eval", "exec",
    "filter", "float", "format", "frozenset", "getattr", "globals",
    "hasattr", "hash", "hex", "id", "input", "int", "isinstance",
    "issubclass", "iter", "len", "list", "locals", "map", "max",
    "memoryview", "min", "next", "object", "oct", "open", "ord", "pow",
    "print", "range", "repr", "reversed", "round", "set", "setattr",
    "slice", "sorted", "staticmethod", "str", "sum", "super", "tuple",
    "type", "vars", "zip", "__import__",
})

# Dict methods that mutate the container in place.
DICT_MUTATORS = frozenset({
    "clear", "pop", "popitem", "setdefault", "update",
})


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


def _is_none_true_false(node):
    """True when the node is the literal None / True / False."""
    return (
        isinstance(node, ast.Constant) and node.value in {None, True, False}
    )


def _is_type_call(node):
    """True when the node is a bare ``type(...)`` call (not ``type.attr``)."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "type"
    )


def _add(findings, rule_id, title, severity, lineno, explanation, suggestion, evidence, confidence="medium"):
    findings.append({
        "rule_id": rule_id, "title": title, "severity": severity,
        "line": lineno, "explanation": explanation, "suggestion": suggestion,
        "source": "bugs", "fixed_snippet": None,
        "evidence": evidence[:200], "confidence": confidence,
        "related_lines": [],
    })


def detect_bugs(source_code: str, language: str | None = None) -> list[dict]:
    if language != "python":
        return []
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return []

    findings = []

    class _Checker(ast.NodeVisitor):
        """Scope-aware tracker: assigned/used names per frame, imports per scope."""

        def __init__(self):
            # Stack of frames; each frame holds names assigned and names loaded.
            self.frames = [{"assigned": set(), "used": set(), "imports": {}}]
            # Names that are function/class definitions — never flag as unused.
            self.defined_funcs = set()
            self.findings = findings

        # ---- scope helpers
        def _current(self):
            return self.frames[-1]

        def _assign(self, name):
            if name:
                self._current()["assigned"].add(name)

        def _use(self, name):
            if name:
                self._current()["used"].add(name)

        def _open(self):
            self.frames.append({"assigned": set(), "used": set(), "imports": {}})

        def _close(self):
            if len(self.frames) > 1:
                self.frames.pop()

        # ---- statement visitors
        def visit_Assign(self, node):
            for target in node.targets:
                for name in _binding_names(target):
                    self._assign(name)
                    # builtin shadowing check
                    if name in BUILTINS:
                        _add(
                            self.findings, "PY008",
                            f"Builtin shadowed: '{name}'", "high", node.lineno,
                            f"Assigning to '{name}' hides the Python builtin, "
                            f"breaking it for everything that runs after this line.",
                            f"Rename the variable to something other than '{name}'.",
                            name, confidence="high",
                        )
            self.generic_visit(node)

        def visit_AnnAssign(self, node):
            if node.target is not None and isinstance(node.target, ast.Name):
                self._assign(node.target.id)
                if node.target.id in BUILTINS:
                    _add(
                        self.findings, "PY008",
                        f"Builtin shadowed: '{node.target.id}'", "high", node.lineno,
                        f"Annotating '{node.target.id}' hides the Python builtin.",
                        f"Rename the variable to something other than '{node.target.id}'.",
                        node.target.id, confidence="high",
                    )
            self.generic_visit(node)

        def visit_NamedExpr(self, node):
            if isinstance(node.target, ast.Name):
                self._assign(node.target.id)
                if node.target.id in BUILTINS:
                    _add(
                        self.findings, "PY008",
                        f"Builtin shadowed: '{node.target.id}'", "high", node.lineno,
                        f"Walrus assignment to '{node.target.id}' hides the Python builtin.",
                        f"Rename the variable to something other than '{node.target.id}'.",
                        node.target.id, confidence="high",
                    )
            self.generic_visit(node)

        def visit_For(self, node):
            # loop target binds a name
            for name in _binding_names(node.target):
                self._assign(name)
            # detect mutating the iterated container inside the loop body
            if isinstance(node.iter, ast.Name):
                container = node.iter.id
                is_dict = False
                # check if the container was annotated or used as a dict elsewhere;
                # fall back to list rule when we can't tell
                self._check_mutation(
                    node.body, container,
                    "PY009", "Dict mutated during iteration",
                    "PY006", "List mutated during iteration",
                )
            self.generic_visit(node)
            # loop target is only used inside the loop; remove from assigned so
            # it doesn't get falsely flagged as unused after the loop
            for name in _binding_names(node.target):
                self._current()["assigned"].discard(name)

        def visit_AsyncFor(self, node):
            self.visit_For(node)

        def visit_While(self, node):
            self.generic_visit(node)

        def visit_With(self, node):
            # `with ... as name` binds a name inside the block
            for item in node.items:
                if item.optional_vars is not None:
                    for name in _binding_names(item.optional_vars):
                        self._assign(name)
            self.generic_visit(node)
            for item in node.items:
                if item.optional_vars is not None:
                    for name in _binding_names(item.optional_vars):
                        self._current()["assigned"].discard(name)

        def visit_AsyncWith(self, node):
            self.visit_With(node)

        def visit_FunctionDef(self, node):
            # function name binds in the enclosing scope
            self._assign(node.name)
            self.defined_funcs.add(node.name)
            self._open()
            # parameters bind inside the function
            args = node.args
            for a in (list(args.posonlyargs) + list(args.args)
                      + list(args.kwonlyargs) + [args.vararg, args.kwarg]):
                if a is not None:
                    self._assign(a.arg)
            # unreachable statements inside the body
            for i in _find_unreachable(node.body):
                stmt = node.body[i]
                _add(
                    self.findings, "PY005", "Unreachable code", "medium",
                    stmt.lineno,
                    "Code after a return/break/continue/raise can never execute.",
                    "Remove the dead block or move the terminator.",
                    ast.unparse(stmt)[:120] if hasattr(ast, "unparse") else "",
                    confidence="high",
                )
            self.generic_visit(node)
            self._close_and_report_unused()

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_ClassDef(self, node):
            self._assign(node.name)
            self.defined_funcs.add(node.name)
            self._open()
            self.generic_visit(node)
            self._close_and_report_unused()

        def _close_and_report_unused(self):
            """Pop the current frame and report its unused assigned names and imports."""
            if len(self.frames) <= 1:
                return
            frame = self.frames.pop()
            unused = frame["assigned"] - frame["used"]
            for name in sorted(unused):
                if name in self.defined_funcs:
                    continue
                if name.startswith("__") and name.endswith("__"):
                    continue
                if name in frame["imports"]:
                    continue
                _add(
                    self.findings, "PY004",
                    f"Unused variable '{name}'", "low", 1,
                    f"'{name}' is assigned but never read, so the assignment has no effect.",
                    f"Remove the assignment to '{name}' or use the value.",
                    name, confidence="medium",
                )
            # unused imports inside this frame
            for name, full in frame["imports"].items():
                if name not in frame["used"]:
                    _add(
                        self.findings, "PY007",
                        f"Unused import '{name}'", "low", 1,
                        f"'{name}' is imported from {full} but never referenced.",
                        f"Remove the import or use the imported name.",
                        full, confidence="medium",
                    )

        def visit_Import(self, node):
            for alias in node.names:
                root = alias.name.split(".")[0]
                name = alias.asname or root
                self._current()["imports"][name] = alias.name
                self._assign(name)
            self.generic_visit(node)

        def visit_ImportFrom(self, node):
            module = node.module or ""
            for alias in node.names:
                if alias.name == "*":
                    # can't statically know what a *-import brings in
                    continue
                name = alias.asname or alias.name
                self._current()["imports"][name] = f"{module}.{alias.name}"
                self._assign(name)
            self.generic_visit(node)

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Load):
                self._use(node.id)
            self.generic_visit(node)

        # ---- expression visitors
        def visit_Compare(self, node):
            # flag ``x == None`` / ``x == True`` / ``x == False`` -> use ``is``
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, ast.Eq) and _is_none_true_false(comparator):
                    target = ast.unparse(node.left)[:60] if hasattr(ast, "unparse") else "value"
                    _add(
                        self.findings, "PY010",
                        f"Compare {target} to literal with == instead of is",
                        "high", node.lineno,
                        f"Comparing {target} to {ast.unparse(comparator)[:40]} "
                        f"with == works but is the wrong tool; use ``is`` for "
                        f"singletons like None, True, False.",
                        f"Use ``{target} is {ast.unparse(comparator)[:40]}`` instead of ==.",
                        f"{target} == {ast.unparse(comparator)[:40]}",
                        confidence="high",
                    )
                # flag ``type(x) == Y`` -> use isinstance
                if isinstance(op, ast.Eq) and _is_type_call(node.left):
                    target = ast.unparse(node.left.args[0])[:60] if node.left.args and hasattr(ast, "unparse") else "value"
                    _add(
                        self.findings, "PY011",
                        "Use isinstance() instead of type() == comparison",
                        "medium", node.lineno,
                        "``type(x) == Y`` fails for subclasses; ``isinstance`` "
                        "respects inheritance.",
                        f"Use ``isinstance({target}, ...)`` instead of ``type({target}) == ...``.",
                        ast.unparse(node)[:120] if hasattr(ast, "unparse") else "",
                        confidence="high",
                    )
            self.generic_visit(node)

        def _check_mutation(self, body, container, dict_rule_id, dict_title, list_rule_id, list_title):
            """Look for mutating calls on ``container`` inside ``body``."""
            for stmt in body:
                for inner in ast.walk(stmt):
                    if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute):
                        attr = inner.func.attr
                        is_mutator = (
                            attr in DICT_MUTATORS
                            or attr in {"append", "extend", "insert", "pop",
                                        "remove", "clear", "sort", "reverse"}
                        )
                        if not is_mutator:
                            continue
                        # the container must be the receiver (dict.method()) or
                        # passed as an argument (list.method(container, ...))
                        receiver_match = (
                            isinstance(inner.func.value, ast.Name)
                            and inner.func.value.id == container
                        )
                        arg_match = any(
                            isinstance(a, ast.Name) and a.id == container
                            for a in inner.args
                        )
                        if receiver_match or arg_match:
                            rule_id = dict_rule_id if attr in DICT_MUTATORS else list_rule_id
                            title = dict_title if attr in DICT_MUTATORS else list_title
                            _add(
                                self.findings, rule_id, title, "high",
                                inner.lineno,
                                f"Mutating '{container}' while iterating over it "
                                f"skips elements or raises RuntimeError.",
                                f"Iterate over a copy: for x in list({container}): ...",
                                f"{attr}(...)",
                                confidence="medium",
                            )

    checker = _Checker()
    checker.visit(tree)

    # ---- post-visit: unused variables and imports still on the module frame
    module_frame = checker.frames[0]
    unused = module_frame["assigned"] - module_frame["used"]
    for name in sorted(unused):
        if name in checker.defined_funcs:
            continue
        if name.startswith("__") and name.endswith("__"):
            continue
        if name in module_frame["imports"]:
            continue
        _add(
            checker.findings, "PY004",
            f"Unused variable '{name}'", "low", 1,
            f"'{name}' is assigned but never read, so the assignment has no effect.",
            f"Remove the assignment to '{name}' or use the value.",
            name, confidence="medium",
        )

    # ---- post-visit: unused imports still on the module frame
    for name, full in module_frame["imports"].items():
        if name not in module_frame["used"]:
            _add(
                checker.findings, "PY007",
                f"Unused import '{name}'", "low", 1,
                f"'{name}' is imported from {full} but never referenced.",
                f"Remove the import or use the imported name.",
                full, confidence="medium",
            )

    return checker.findings[:MAX_FINDINGS]
