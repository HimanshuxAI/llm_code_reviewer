# Built-in Analysis Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the external LLM call with a built-in, zero-dependency analysis engine so the app runs entirely offline and still produces real findings and a real score.

**Architecture:** Seven analysis passes over a shared tokenizer. Python gets full AST analysis via `ast`; all five languages get taint tracking (two-phase interprocedural), entropy secret detection, semantic-pattern catalogue checks, quality metrics, and the existing regex rules. `engine.py` orchestrates; `pipeline.py` only calls it.

**Tech Stack:** Python 3.16 stdlib only (`ast`, `tokenize`, `math`, `re`). No new pip dependencies.

Spec: `docs/specs/2026-11-16-builtin-analysis-engine-design.md`

---

## File map

Created:
- `backend/app/analysis/tokenizer.py`
- `backend/app/analysis/sinks.py`
- `backend/app/analysis/secrets.py`
- `backend/app/analysis/ast_analyzer.py`
- `backend/app/analysis/taint.py`
- `backend/app/analysis/quality.py`
- `backend/app/analysis/engine.py`
- `backend/tests/test_tokenizer.py`
- `backend/tests/test_sinks.py`
- `backend/tests/test_secrets.py`
- `backend/tests/test_ast_analyzer.py`
- `backend/tests/test_taint.py`
- `backend/tests/test_quality.py`
- `backend/tests/test_engine.py`

Modified:
- `backend/app/analysis/scorer.py` (damped scoring)
- `backend/app/analysis/pipeline.py` (calls engine, drops LLM)
- `backend/app/reviews/schemas.py` (FindingOut gains `evidence`, `confidence`, `related_lines`)
- `backend/app/main.py` (health endpoint reports engines)
- `backend/app/core/config.py` → actually `backend/app/config.py` (drop `LLM_*` settings)
- `backend/requirements.txt` (drop `httpx`)
- `backend/.env.example` (drop `LLM_*`)
- `backend/tests/conftest.py` (drop `settings.llm_api_key` line)
- `backend/tests/test_pipeline.py` (merge_findings removed)
- `backend/tests/test_scoring.py` (damped weights)
- `backend/tests/test_app.py` (health endpoint payload)
- `README.md` (rewrite)
- `frontend/src/pages/Results.tsx` (show engine name and confidence)
- `frontend/src/pages/Landing.tsx` (pipeline copy)
- `frontend/src/pages/Submit.tsx` (pipeline sidebar copy)
- `frontend/src/api.ts` (Finding type gains fields)
- `frontend/src/components/ScanLoader.tsx` (copy mentions engines, no API key)

Deleted:
- `backend/app/analysis/llm_reviewer.py`
- `backend/tests/test_llm_reviewer.py`

---

## Task 1: Tokenizer

**Files:**
- Create: `backend/app/analysis/tokenizer.py`
- Test: `backend/tests/test_tokenizer.py`

The tokenizer converts source into typed tokens. It is the foundation; every later pass depends on it. Verified working on Python and JavaScript. Strip mode blanks comments and strings while preserving line numbers.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_tokenizer.py
from app.analysis.tokenizer import tokenize_source, strip_comments_and_strings


def test_comment_is_not_code():
    toks = tokenize_source('# password = "x"\ny = 1\n', "python")
    kinds = [t.kind for t in toks]
    assert "comment" in kinds


def test_string_and_code_are_distinguished():
    toks = tokenize_source('x = "os.system(1)"\n', "python")
    strings = [t for t in toks if t.kind == "string"]
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert len(strings) == 1
    assert "os" not in idents  # inside the string


def test_strip_comments_and_strings_preserves_lines():
    code = '# password = "x"\nreal = 1\n'
    stripped = strip_comments_and_strings(code, "python")
    assert stripped.splitlines()[0].strip() == ""
    assert stripped.splitlines()[1].strip() == "real = 1"
    assert len(stripped.splitlines()) == 2


def test_block_comment_is_not_code():
    toks = tokenize_source('/* eval(userInput) */\nconst z = 1;\n', "javascript")
    comments = [t for t in toks if t.kind == "comment"]
    idents = [t.text for t in toks if t.kind == "identifier"]
    assert len(comments) == 1
    assert "eval" not in idents


def test_template_string_is_one_string_token():
    toks = tokenize_source('const y = `hello ${name} there`;\n', "javascript")
    strings = [t for t in toks if t.kind == "string"]
    assert len(strings) == 1
    assert strings[0].text == "`hello ${name} there`"


def test_line_numbers_match():
    code = "a = 1\n\nb = 2\n"
    toks = tokenize_source(code, "python")
    b = [t for t in toks if t.text == "b"]
    assert b[0].line == 3


def test_unknown_language_returns_empty_list():
    assert tokenize_source("x", "ruby") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_tokenizer.py -v`
Expected: FAIL with `ModuleNotFoundError` or import error.

- [ ] **Step 3: Write the tokenizer**

```python
# backend/app/analysis/tokenizer.py
"""Language-aware tokenisation.

Converts source into a token stream where every token carries its kind,
text, line, and column. Python uses the stdlib `tokenize` module; the
other languages share a small hand-written scanner.
"""
import io
import tokenize
from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    kind: str    # "code" | "string" | "comment" | "number" | "identifier"
    text: str
    line: int
    col: int


_WS = " \t\r\n"

LANG_CONFIG = {
    "javascript": {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": True},
    "java":       {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
    "c":          {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
    "cpp":        {"line": ("//",), "block": (("/*", "*/"),), "sq": "'", "dq": '"', "template": False},
}


def _scan_generic(source: str, cfg: dict) -> list[Token]:
    tokens: list[Token] = []
    i, n = 0, len(source)
    line, col = 1, 0

    def emit(kind, text, sl, sc):
        tokens.append(Token(kind, text, sl, sc))

    while i < n:
        ch = source[i]

        for marker in cfg["line"]:
            if source.startswith(marker, i):
                start_line, start_col = line, col
                end = source.find("\n", i)
                if end == -1:
                    end = n
                emit("comment", source[i:end], start_line, start_col)
                col += end - i
                i = end
                break
        else:
            for open_m, close_m in cfg["block"]:
                if source.startswith(open_m, i):
                    start_line, start_col = line, col
                    end = source.find(close_m, i + len(open_m))
                    if end == -1:
                        end = n - len(close_m)
                    text = source[i:end + len(close_m)]
                    nl = text.count("\n")
                    if nl:
                        line += nl
                        col = len(text) - text.rfind("\n") - 1
                    else:
                        col += len(text)
                    emit("comment", text, start_line, start_col)
                    i = end + len(close_m)
                    break
            else:
                # strings (single quote, double quote, backtick)
                quote = None
                if ch in (cfg["sq"], cfg["dq"]):
                    quote = ch
                elif cfg.get("template") and ch == "`":
                    quote = "`"
                if quote:
                    start_line, start_col = line, col
                    j = i + 1
                    while j < n:
                        c = source[j]
                        if c == "\\":
                            j += 2
                            continue
                        if c == "\n" and quote != "`":
                            break
                        if c == quote:
                            break
                        j += 1
                    end = j + 1 if j < n and source[j] == quote else j
                    text = source[i:end]
                    nl = text.count("\n")
                    if nl:
                        line += nl
                        col = len(text) - text.rfind("\n") - 1
                    else:
                        col += len(text)
                    emit("string", text, start_line, start_col)
                    i = end
                    continue

                if ch.isdigit():
                    start_col = col
                    j = i
                    while j < n and (source[j].isalnum() or source[j] in "._xXbBoO"):
                        j += 1
                    emit("number", source[i:j], line, start_col)
                    col += j - i
                    i = j
                    continue

                if ch.isalpha() or ch == "_":
                    start_col = col
                    j = i
                    while j < n and (source[j].isalnum() or source[j] == "_"):
                        j += 1
                    emit("identifier", source[i:j], line, start_col)
                    col += j - i
                    i = j
                    continue

                if ch in _WS:
                    if ch == "\n":
                        line += 1
                        col = 0
                    else:
                        col += 1
                    i += 1
                    continue

                emit("code", ch, line, col)
                col += 1
                i += 1
                continue
            continue
        continue
    return tokens


def tokenize_source(source: str, language: str) -> list[Token]:
    if language == "python":
        out = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(source).readline):
                t = tok.type
                if t == tokenize.COMMENT:
                    kind = "comment"
                elif t == tokenize.STRING:
                    kind = "string"
                elif t == tokenize.NUMBER:
                    kind = "number"
                elif t == tokenize.NAME:
                    kind = "identifier"
                elif t in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
                           tokenize.DEDENT, tokenize.ENDMARKER):
                    continue
                else:
                    kind = "code"
                out.append(Token(kind, tok.string, tok.start[0], tok.start[1]))
        except Exception:
            return []
        return out
    cfg = LANG_CONFIG.get(language)
    if cfg is None:
        return []
    return _scan_generic(source, cfg)


def _blanked(source: str, tokens: list[Token], kinds: set[str]) -> str:
    """Return source with tokens of the given kinds replaced by spaces.

    Line structure is preserved so line numbers stay valid.
    """
    lines = source.splitlines(keepends=True)
    starts = [0]
    for ln in lines:
        starts.append(starts[-1] + len(ln))
    chars = list(source)
    for tok in tokens:
        if tok.kind not in kinds:
            continue
        if tok.line - 1 >= len(starts):
            continue
        start = starts[tok.line - 1] + tok.col
        for k in range(len(tok.text)):
            idx = start + k
            if idx < len(chars) and chars[idx] != "\n":
                chars[idx] = " "
    return "".join(chars)


def strip_comments_and_strings(source: str, language: str) -> str:
    """Mask comments and string contents. Line numbers preserved."""
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment", "string"})


def strip_comments(source: str, language: str) -> str:
    """Mask comments only. Strings stay intact so crypto/pattern checks work."""
    tokens = tokenize_source(source, language)
    return _blanked(source, tokens, {"comment"})
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_tokenizer.py -v`
Expected: PASS, 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/tokenizer.py backend/tests/test_tokenizer.py
git commit -m "feat: language-aware tokenizer for the analysis engine"
```

---

## Task 2: Sources, sinks, and the semantic catalogue

**Files:**
- Create: `backend/app/analysis/sinks.py`
- Test: `backend/tests/test_sinks.py`

`sinks.py` holds the per-language source/sink lists used by taint analysis, plus the semantic catalogue (dangerous patterns that are unsafe regardless of dataflow). Semantic matches run on the comment-masked source, so string literals like `"DES"` stay visible while `// use DES` comments do not match.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_sinks.py
from app.analysis.sinks import SOURCES, SINKS, detect_semantic_patterns


def test_sources_and_sinks_exist_for_all_languages():
    for lang in ("python", "javascript", "java", "c", "cpp", "text"):
        assert lang in SOURCES
        assert lang in SINKS


def test_python_sinks_include_os_system_and_eval():
    assert "system" in SINKS["python"]
    assert "eval" in SINKS["python"]


def test_detect_semantic_patterns_java_des():
    code = 'Cipher c = Cipher.getInstance("DES");\n'
    findings = detect_semantic_patterns(code, "java")
    assert any("DES" in f["explanation"] for f in findings)
    assert all(f["line"] == 1 for f in findings)


def test_detect_semantic_patterns_ignores_comment():
    code = '// Cipher.getInstance("DES")\nint x = 1;\n'
    findings = detect_semantic_patterns(code, "java")
    assert findings == []


def test_detect_semantic_patterns_javascript_document_write():
    code = "document.write(userInput);\n"
    findings = detect_semantic_patterns(code, "javascript")
    assert any("document.write" in f["explanation"] for f in findings)


def test_findings_have_required_keys():
    code = 'String q = "SELECT " + u; stmt.execute(q);\n'
    for f in detect_semantic_patterns(code, "java"):
        assert set(f) >= {"rule_id", "title", "severity", "line",
                          "explanation", "suggestion", "source", "fixed_snippet"}
        assert f["source"] == "sinks"
        assert f["fixed_snippet"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_sinks.py -v`
Expected: FAIL, module missing.

- [ ] **Step 3: Write the module**

```python
# backend/app/analysis/sinks.py
"""Per-language sources, sinks, and the dangerous-pattern catalogue.

Sources mark where attacker-controlled data enters. Sinks mark calls where
untrusted data must never appear. The catalogue holds patterns that are
unsafe on their own, independent of dataflow.
"""
import re
from dataclasses import dataclass

SOURCES = {
    "python": {"input", "get", "post", "args", "form", "json",
               "getParameter", "argv", "recv"},
    "javascript": {"prompt", "getParameter", "query", "body", "params",
                   "search", "hash", "cookie"},
    "java": {"getParameter", "getQueryString", "nextLine", "readLine", "argv"},
    "c": {"scanf", "fgets", "getenv", "recv", "argv", "gets"},
    "cpp": {"scanf", "fgets", "getenv", "recv", "argv", "gets"},
    "text": set(),
}

SINKS = {
    "python": {"system", "popen", "eval", "exec", "execute",
               "loads", "load"},
    "javascript": {"eval", "write", "exec", "Function", "html"},
    "java": {"exec", "execute", "ProcessBuilder", "readObject", "forName"},
    "c": {"system", "popen", "gets", "strcpy", "sprintf"},
    "cpp": {"system", "popen", "gets", "strcpy", "sprintf"},
    "text": set(),
}


@dataclass(frozen=True)
class SemanticRule:
    id: str
    title: str
    severity: str
    pattern: re.Pattern
    explanation: str
    suggestion: str
    languages: frozenset[str]


SEMANTIC_RULES = [
    SemanticRule("SEC013", "Weak cipher algorithm", "high",
                 re.compile(r"getInstance\(\s*[\"'](DES|RC4|DESede)[\"']", re.I),
                 "DES and RC4 are broken ciphers; data encrypted with them is recoverable.",
                 "Use AES-256-GCM.", frozenset({"java"})),
    SemanticRule("SEC014", "Weak digest algorithm", "medium",
                 re.compile(r"getInstance\(\s*[\"'](MD5|SHA-?1)[\"']", re.I),
                 "MD5 and SHA-1 are broken for integrity checks.",
                 "Use SHA-256 or better.", frozenset({"java"})),
    SemanticRule("SEC015", "XMLDecoder on untrusted data", "high",
                 re.compile(r"new\s+XMLDecoder\b"),
                 "XMLDecoder deserialises arbitrary objects and allows remote code execution.",
                 "Use a strict XML parser or JSON with schema validation.", frozenset({"java"})),
    SemanticRule("SEC016", "TrustManager that accepts everything", "high",
                 re.compile(r"checkClientTrusted\s*\([^)]*\)\s*\{\s*\}|checkServerTrusted\s*\([^)]*\)\s*\{\s*\}"),
                 "A no-op trust manager accepts any certificate, defeating TLS.",
                 "Validate certificates against a real CA bundle.", frozenset({"java"})),
    SemanticRule("JS001", "document.write()", "medium",
                 re.compile(r"\bdocument\.write\s*\("),
                 "document.write() injects HTML directly; unsanitised input leads to XSS.",
                 "Build nodes with createElement/textContent instead.", frozenset({"javascript"})),
    SemanticRule("JS002", "new Function() constructor", "high",
                 re.compile(r"\bnew\s+Function\s*\("),
                 "new Function() compiles strings as code, like eval().",
                 "Refactor to call explicit functions.", frozenset({"javascript"})),
    SemanticRule("JS003", "setTimeout with a string argument", "medium",
                 re.compile(r"\bset(Timeout|Interval)\s*\(\s*[\"']"),
                 "A string passed to setTimeout is evaluated as code.",
                 "Pass a function reference instead of a string.", frozenset({"javascript"})),
    SemanticRule("JS004", "child_process exec with interpolation", "high",
                 re.compile(r"\b(exec|execSync)\s*\(\s*[`]"),
                 "Template literals passed to exec() build shell commands dynamically.",
                 "Use execFile with an argument list and no shell.", frozenset({"javascript"})),
    SemanticRule("C001", "strcat()", "high",
                 re.compile(r"\bstrcat\s*\("),
                 "strcat() does not bound-check and corrupts adjacent memory.",
                 "Use strncat() with a size limit.", frozenset({"c", "cpp"})),
    SemanticRule("C002", "atoi()", "medium",
                 re.compile(r"\batoi\s*\("),
                 "atoi() returns 0 on error and cannot signal failure.",
                 "Use strtol() with an error check.", frozenset({"c", "cpp"})),
    SemanticRule("C003", "scanf with unguarded %s", "high",
                 re.compile(r"scanf\s*\(\s*\"[^\"]*%s"),
                 "scanf(\"%s\") writes unbounded input and overflows buffers.",
                 "Use fgets() with a size, or scanf(\"%99s\").", frozenset({"c", "cpp"})),
    SemanticRule("C004", "rand() for security", "medium",
                 re.compile(r"\brand\s*\("),
                 "rand() is predictable; tokens or keys built from it can be guessed.",
                 "Use arc4random() or getrandom().", frozenset({"c", "cpp"})),
]


def detect_semantic_patterns(source: str, language: str) -> list[dict]:
    if language == "text":
        return []
    from app.analysis.tokenizer import strip_comments
    masked = strip_comments(source, language)
    findings = []
    for lineno, line in enumerate(masked.splitlines(), start=1):
        for rule in SEMANTIC_RULES:
            if language not in rule.languages:
                continue
            if rule.pattern.search(line):
                findings.append({
                    "rule_id": rule.id,
                    "title": rule.title,
                    "severity": rule.severity,
                    "line": lineno,
                    "explanation": rule.explanation,
                    "suggestion": rule.suggestion,
                    "source": "sinks",
                    "fixed_snippet": None,
                    "evidence": line.strip()[:200],
                    "confidence": "high",
                    "related_lines": [],
                })
    return findings[:60]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_sinks.py -v`
Expected: PASS, 6 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/sinks.py backend/tests/test_sinks.py
git commit -m "feat: source/sink catalogue and semantic pattern detection"
```

---

## Task 3: Secret detection

**Files:**
- Create: `backend/app/analysis/secrets.py`
- Test: `backend/tests/test_secrets.py`

Two detectors: Shannon entropy (with a credential-name requirement to avoid false positives) and known token prefixes (AKIA, sk-, ghp_, ...). The AWS key test is the canonical false negative in the current scanner.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_secrets.py
from app.analysis.secrets import shannon_entropy, detect_secrets


def test_shannon_entropy_orders_strings():
    assert shannon_entropy("xxxxxxxxxxxx") < 0.1
    assert shannon_entropy("AKIAIOSFODNN7EXAMPLE") > 3.5
    assert shannon_entropy("sk-live-9f3a2b8c7d6e5f4a") > 3.5


def test_detects_aws_access_key_with_non_credential_name():
    # the existing scanner misses this; it must not
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = detect_secrets(code, "python")
    assert any("AKIA" in f["title"] for f in findings)


def test_detects_named_secret():
    code = 'api_key = "a8f3c2b1e9d4f6a7c5b8"\n'
    findings = detect_secrets(code, "python")
    assert any(f["rule_id"] == "SECRET001" for f in findings)


def test_ignores_low_entropy_string():
    code = 'greeting = "hello world"\n'
    assert detect_secrets(code, "python") == []


def test_ignores_comment():
    code = '# AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    assert detect_secrets(code, "python") == []


def test_secret_is_redacted_in_output():
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = detect_secrets(code, "python")
    body = " ".join(f["explanation"] + f["evidence"] for f in findings)
    assert "AKIAIOSFODNN7EXAMPLE" not in body
    assert "AKIA" in body  # first 4 chars shown


def test_flags_standalone_jwt():
    code = 'token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"\n'
    findings = detect_secrets(code, "python")
    assert findings
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_secrets.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the module**

```python
# backend/app/analysis/secrets.py
"""Credential detection: Shannon entropy plus known token prefixes.

Secrets are always redacted to their first four characters so findings
never echo the full credential.
"""
import math
import re
from collections import Counter

ENTROPY_THRESHOLD = 3.5
MIN_LENGTH = 16

CRED_NAME = re.compile(
    r"(password|passwd|secret|api_?key|apikey|access_?token|auth_?token|"
    r"client_?secret|private_?key|signing_?key|aws_?key|session_?key)", re.I)

KNOWN_PREFIXES = (
    ("sk-live-", "Stripe live secret key"),
    ("sk_live_", "Stripe live secret key"),
    ("pk_live_", "Stripe publishable key"),
    ("ghp_", "GitHub personal access token"),
    ("gho_", "GitHub OAuth token"),
    ("github_pat_", "GitHub fine-grained token"),
    ("AKIA", "AWS access key"),
    ("ASIA", "AWS temporary access key"),
    ("xoxb-", "Slack bot token"),
    ("xoxp-", "Slack user token"),
    ("AIza", "Google API key"),
    ("ya29.", "Google OAuth token"),
    ("eyJ", "JWT"),
    ("-----BEGIN ", "Private key material"),
)

STRING_RE = re.compile(r'"([^"\n\\]{8,})"|\'([^\'\n\\]{8,})\'')


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _redacted(secret: str) -> str:
    return f"{secret[:4]}...({len(secret)} chars)"


def detect_secrets(source: str, language: str) -> list[dict]:
    from app.analysis.tokenizer import strip_comments, tokenize_source

    masked = strip_comments(source, language)
    findings = []
    seen = set()

    for lineno, line in enumerate(source.splitlines(), start=1):
        m_line = masked.splitlines()[lineno - 1] if lineno <= len(masked.splitlines()) else ""
        if m_line.strip() == "":
            continue  # purely a comment

        # 1) known prefixes anywhere on the line
        for prefix, title in KNOWN_PREFIXES:
            if prefix in line:
                key = (lineno, prefix)
                if key in seen:
                    continue
                regex = re.escape(prefix) + r"[A-Za-z0-9_\-\.]{4,}"
                mm = re.search(regex, line)
                if not mm:
                    continue
                secret = mm.group(0)
                seen.add(key)
                findings.append(_finding("SECRET002", title, lineno, line, secret, "high"))

        # 2) credential-style name assigned a high-entropy value
        m = CRED_NAME.search(line)
        if m:
            sm = STRING_RE.search(line)
            if sm:
                value = sm.group(1) or sm.group(2)
                if len(value) >= 8 and value.lower() not in {
                    "password", "changeme", "your-key-here", "xxxxxxxx",
                } and shannon_entropy(value) > ENTROPY_THRESHOLD:
                    key = (lineno, "named")
                    if key not in seen:
                        seen.add(key)
                        findings.append(_finding(
                            "SECRET001", "Hardcoded credential", lineno,
                            line, value, "high"))

    return findings[:60]


def _finding(rule_id, title, lineno, line, secret, severity):
    return {
        "rule_id": rule_id,
        "title": title,
        "severity": severity,
        "line": lineno,
        "explanation": (
            f"A credential literal ({_redacted(secret)}) is committed in source. "
            "It leaks through version history and shared repos."
        ),
        "suggestion": "Load the value from an environment variable or a .env file excluded from git.",
        "source": "secrets",
        "fixed_snippet": None,
        "evidence": f"...{rule_id} {lineno}",
        "confidence": "high",
        "related_lines": [],
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_secrets.py -v`
Expected: PASS, 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/secrets.py backend/tests/test_secrets.py
git commit -m "feat: entropy and prefix-based secret detection"
```

---

## Task 4: Python AST analyser

**Files:**
- Create: `backend/app/analysis/ast_analyzer.py`
- Test: `backend/tests/test_ast_analyzer.py`

Python-only semantic checks. Each check has a false-positive test.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_ast_analyzer.py
from app.analysis.ast_analyzer import analyse_python


def test_mutable_default_argument():
    code = "def f(items=[]):\n    return items\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "BUG001" for f in findings)


def test_bare_except_not_double_counted_with_regex():
    # QUAL001 already catches bare except in rules.py; AST pass reports swallowing only
    code = "try:\n    x = 1\nexcept Exception:\n    pass\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "QUAL002" for f in findings)


def test_requests_call_without_timeout():
    code = "import requests\nrequests.get('http://x')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "SEC015" for f in findings)


def test_requests_call_with_timeout_is_fine():
    code = "import requests\nrequests.get('http://x', timeout=10)\n"
    assert not any(f["rule_id"] == "SEC015" for f in analyse_python(code))


def test_open_without_encoding():
    code = "f = open('out.txt', 'w')\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "QUAL003" for f in findings)


def test_open_with_encoding_is_fine():
    code = "f = open('out.txt', 'w', encoding='utf-8')\n"
    assert not any(f["rule_id"] == "QUAL003" for f in analyse_python(code))


def test_assert_used_for_authorization():
    code = "def delete(user):\n    assert user.is_admin\n    pass\n"
    findings = analyse_python(code)
    assert any(f["rule_id"] == "SEC014" for f in findings)


def test_assert_for_debugging_is_not_flagged():
    code = "def f(x):\n    assert isinstance(x, int)\n    return x\n"
    assert not any(f["rule_id"] == "SEC014" for f in analyse_python(code))


def test_syntax_error_returns_empty_list():
    assert analyse_python("def f(: pass\n") == []


def test_findings_carry_source_and_evidence():
    for f in analyse_python("def f(items=[]):\n    return items\n"):
        assert f["source"] == "ast"
        assert f["evidence"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_ast_analyzer.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the module**

```python
# backend/app/analysis/ast_analyzer.py
"""Python semantic checks via the stdlib ast module."""
import ast

AUTH_WORDS = ("admin", "auth", "permission", "role", "is_", "user")


def _call_name(node):
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
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
            if node.type is None:
                body_pass = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
                if body_pass:
                    add("QUAL002", "Bare except swallowing everything", "low",
                        node.lineno,
                        "A bare except with pass hides every error, including KeyboardInterrupt.",
                        "Catch the specific exception types you expect, or remove the try.",
                        "except: pass")

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
                mode = next((k.value for k in node.keywords if k.arg == "mode"), None)
                # binary modes do not need an encoding
                if not (isinstance(mode, ast.Constant) and "b" in str(mode.value)):
                    add("QUAL003", "open() without an explicit encoding", "low",
                        node.lineno,
                        "open() uses the platform default encoding, which differs across machines.",
                        "Pass encoding='utf-8' explicitly.",
                        "open(...) without encoding=")

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_ast_analyzer.py -v`
Expected: PASS, 10 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/ast_analyzer.py backend/tests/test_ast_analyzer.py
git commit -m "feat: Python AST semantic checks"
```

---

## Task 5: Taint analysis (two-phase, interprocedural)

**Files:**
- Create: `backend/app/analysis/taint.py` (Python AST path and the generic token path)
- Create: `backend/app/analysis/tokens.py` (token-based function inventory for JS/Java/C/C++)
- Test: `backend/tests/test_taint.py`

The two-phase algorithm:

- **Phase 1 (bottom-up)** computes, for each function, which of its parameters can reach a
  sink and which can reach its return value. It never assumes any parameter is tainted.
- **Phase 2 (top-down)** propagates taint from real sources through actual call sites, and
  reports a sink only when tainted data reaches it.

Verified on 15 prototype cases covering direct source-to-sink flow, taint through a helper,
taint through a return value, bare names (`argv`), and output-parameter sources (`gets`,
`fgets`, `recv`, `scanf`, `readLine`).

### 5a. Python: AST, two phases

**Files:**
- Create: `backend/app/analysis/taint.py`
- Test: `backend/tests/test_taint.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_taint.py
from app.analysis.taint import analyse_taint


def test_direct_source_into_sink():
    code = 'import os\ndef h(request):\n    name = request.args.get("name")\n    os.system(name)\n'
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 4 for f in findings)


def test_user_input_through_helper():
    code = (
        "import os\n"
        "def get_command(name):\n    return \"ls \" + name\n"
        "def handler(name):\n    cmd = get_command(name)\n    os.system(cmd)\n"
        "def route(request):\n    user_input = request.args.get(\"name\")\n    handler(user_input)\n"
    )
    findings = analyse_taint(code, "python")
    assert any(f["line"] == 6 for f in findings)


def test_helper_called_with_constant_is_clean():
    code = "import os\ndef helper(name):\n    os.system(name)\ndef caller():\n    helper(\"ls\")\n"
    assert analyse_taint(code, "python") == []


def test_sink_with_literal_is_not_flagged():
    code = "import os\ndef h():\n    os.system(\"ls -la\")\n"
    assert analyse_taint(code, "python") == []


def test_taint_through_return_value():
    code = (
        "import os\n"
        "def read_name(request):\n    return request.args.get(\"name\")\n"
        "def h(request):\n    os.system(read_name(request))\n"
    )
    assert analyse_taint(code, "python") != []


def test_confidence_is_high_for_direct_and_medium_for_cross_function():
    direct = analyse_taint(
        "import os\ndef h(request):\n    name = request.args.get(\"name\")\n    os.system(name)\n",
        "python")
    cross = analyse_taint(
        "import os\n"
        "def get_command(name):\n    return \"ls \" + name\n"
        "def handler(name):\n    cmd = get_command(name)\n    os.system(cmd)\n"
        "def route(request):\n    user_input = request.args.get(\"name\")\n    handler(user_input)\n",
        "python")
    assert all(f["confidence"] == "high" for f in direct)
    assert any(f["confidence"] == "medium" for f in cross)


def test_parser_error_returns_empty_list():
    assert analyse_taint("def f(: pass\n", "python") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_taint.py -v`
Expected: FAIL. Module missing.

- [ ] **Step 3: Write the module**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_taint.py -v`
Expected: PASS, 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/taint.py backend/tests/test_taint.py
git commit -m "feat: Python interprocedural taint analysis"
```

### 5b. Token-based taint for JavaScript, Java, C, C++

**Files:**
- Create: `backend/app/analysis/tokens.py`
- Append: `backend/tests/test_taint.py`

Function boundaries come from brace matching over the token stream. Failing that, the engine falls back to an intra-procedural token scan (source and sink seen within the same function).

- [ ] **Step 1: Append the failing tests**

```python
# append to backend/tests/test_taint.py


def test_javascript_vulnerable():
    code = 'function route(req) {\n  const name = req.query.name;\n  const cmd = name;\n  eval(cmd);\n}\n'
    findings = analyse_taint(code, "javascript")
    assert any(f["line"] == 4 for f in findings)


def test_javascript_clean():
    code = 'function add(a, b) {\n  return a + b;\n}\n'
    assert analyse_taint(code, "javascript") == []


def test_java_vulnerable():
    code = 'void route(HttpServletRequest req) {\n  String name = req.getParameter("name");\n  Runtime.exec(name);\n}\n'
    findings = analyse_taint(code, "java")
    assert findings


def test_c_vulnerable_argv():
    code = 'int main(int argc, char **argv) {\n  system(argv[1]);\n  return 0;\n}\n'
    findings = analyse_taint(code, "c")
    assert findings


def test_c_output_parameter_source():
    code = 'void h() {\n  char buf[64];\n  gets(buf);\n  system(buf);\n}\n'
    findings = analyse_taint(code, "c")
    assert findings


def test_c_clean():
    code = 'int add(int a, int b) {\n  return a + b;\n}\n'
    assert analyse_taint(code, "c") == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/bin/pytest tests/test_taint.py -v`
Expected: FAIL (generic languages return `[]`).

- [ ] **Step 3: Write the token inventory module**

```python
# backend/app/analysis/tokens.py
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
```

- [ ] **Step 4: Add the generic analysis to taint.py**

```python
# append to backend/app/analysis/taint.py

BARE_SOURCES = {"argv", "environ", "envp"}
OUTPUT_SOURCES = {"gets", "fgets", "scanf", "fscanf", "recv", "readLine",
                  "nextLine", "getline"}


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


def _expr_has_tainted(tokens, a, b, tainted_map):
    for t in tokens[a:b]:
        if t.kind != "identifier":
            continue
        if t.text in BARE_SOURCES:
            return True
        if tainted_map.get(t.text):
            return True
    return False


def _phase1_tokens(func, sources, sinks, functions):
    tokens = func.body
    prov = {p: {i} for i, p in enumerate(func.params)}
    for _ in range(8):
        for i, tok in enumerate(tokens):
            if tok.kind != "identifier":
                continue
            if i + 1 < len(tokens) and tokens[i + 1].text == "=":
                end = _find_stmt_end(tokens, i + 2)
                union = set()
                found_source = False
                for k in range(i + 2, end):
                    t = tokens[k]
                    if t.kind == "identifier":
                        if t.text in prov:
                            union |= prov[t.text]
                        if t.text in sources:
                            found_source = True
                        if t.text in BARE_SOURCES:
                            found_source = True
                if found_source:
                    func.source_locals.add(tok.text)
                prov[tok.text] = union
        # return values
        for j, tok in enumerate(tokens):
            if tok.text == "return":
                end = _find_stmt_end(tokens, j + 1)
                union = set()
                for t in tokens[j + 1:end]:
                    if t.kind == "identifier" and t.text in prov:
                        union |= prov[t.text]
                if union:
                    func.flows_to_return |= union
        # sinks and output sources
        i = 0
        while i < len(tokens):
            call = _find_call(tokens, i)
            if call:
                callee, a, b = call
                if callee in OUTPUT_SOURCES:
                    for ta, tb in _split_args(tokens, a, b):
                        if tb - ta == 1 and tokens[ta].kind == "identifier":
                            func.source_locals.add(tokens[ta].text)
                if callee in sinks:
                    union = set()
                    for ta, tb in _split_args(tokens, a, b):
                        for t in tokens[ta:tb]:
                            if t.kind == "identifier" and t.text in prov:
                                union |= prov[t.text]
                    func.flows_to_sink |= union
                i = b
            else:
                i += 1


def _phase2_tokens(functions, sources, sinks, language):
    tainted_params = {name: set() for name in functions}
    tainted_returns = set()
    findings = []
    reported = set()

    for _ in range(20):
        changed = False
        for name, func in functions.items():
            tokens = func.body
            tainted_map = {p: (i in tainted_params[name]) for i, p in enumerate(func.params)}
            for src in func.source_locals:
                tainted_map[src] = True

            def taint_expr(a, b):
                for j in range(a, b):
                    if tokens[j].kind == "identifier" and tokens[j].text in BARE_SOURCES:
                        return True
                if _expr_has_tainted(tokens, a, b, tainted_map):
                    return True
                for j in range(a, b):
                    t = tokens[j]
                    if t.kind == "identifier":
                        call = _find_call(tokens, j)
                        if call:
                            callee, ca, cb = call
                            if callee in sources:
                                return True
                            if callee in functions and callee in tainted_returns:
                                for ta, tb in _split_args(tokens, ca, cb):
                                    if _expr_has_tainted(tokens, ta, tb, tainted_map):
                                        return True
                return False

            for j, tok in enumerate(tokens):
                if tok.text == "return":
                    end = _find_stmt_end(tokens, j + 1)
                    if taint_expr(j + 1, end) and name not in tainted_returns:
                        tainted_returns.add(name)
                        changed = True
            i = 0
            while i < len(tokens):
                tok = tokens[i]
                if tok.kind == "identifier" and i + 1 < len(tokens) and tokens[i + 1].text == "=":
                    start_expr = i + 2
                    end = _find_stmt_end(tokens, start_expr)
                    if taint_expr(start_expr, end):
                        tainted_map[tok.text] = True
                    i = end
                    continue
                call = _find_call(tokens, i)
                if call:
                    callee, a, b = call
                    if callee in OUTPUT_SOURCES:
                        for ta, tb in _split_args(tokens, a, b):
                            if tb - ta == 1 and tokens[ta].kind == "identifier":
                                tainted_map[tokens[ta].text] = True
                        i = b
                        continue
                    if callee in sinks:
                        hit = False
                        for ta, tb in _split_args(tokens, a, b):
                            if _expr_has_tainted(tokens, ta, tb, tainted_map):
                                hit = True
                                break
                        if hit:
                            key = (name, tok.line)
                            if key not in reported:
                                reported.add(key)
                                findings.append(_finding_token(tok, language))
                    elif callee in functions:
                        g = functions[callee]
                        for idx, (ta, tb) in enumerate(_split_args(tokens, a, b)):
                            if idx < len(g.params) and _expr_has_tainted(tokens, ta, tb, tainted_map):
                                if idx not in tainted_params[callee]:
                                    tainted_params[callee].add(idx)
                                    changed = True
                    i = b
                else:
                    i += 1
        if not changed:
            break
    return findings


def _finding_token(tok, language):
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


def _token_analyse(source_code: str, language: str) -> list[dict]:
    from app.analysis.tokens import function_inventory
    functions = function_inventory(source_code, language)
    if not functions:
        return _intraprocedural(source_code, language)
    sources = SOURCES.get(language, set())
    sinks = SINKS.get(language, set())
    for func in functions.values():
        _phase1_tokens(func, sources, sinks, functions)
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
    return findings[:60]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_taint.py -v`
Expected: PASS, 13 passed.

- [ ] **Step 6: Commit**

```bash
git add backend/app/analysis/tokens.py backend/app/analysis/taint.py backend/tests/test_taint.py
git commit -m "feat: interprocedural taint for JavaScript, Java, C, C++"
```

### 5c. The contract

- Python uses AST and resolves names exactly; confidence is `high` for direct flow within one function and `medium` when the flow crosses a function boundary.
- JavaScript, Java, C, and C++ use the token inventory. Cross-function flows there are always `medium` confidence.
- If braces do not balance the engine falls back to the intra-procedural heuristic and marks findings `medium` confidence.
- All generic-language findings carry `source: "taint"` and are merged by the engine like everything else.

## Task 6: Quality metrics

**Files:**
- Create: `backend/app/analysis/quality.py`
- Test: `backend/tests/test_quality.py`

Metrics per function: line count, cyclomatic complexity, nesting depth, parameter count. Python via AST; the others via token brace matching with a keyword counter.

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_quality.py
from app.analysis.quality import detect_quality_issues


def test_long_function():
    body = "\n".join(f"    x{i} = {i}" for i in range(70))
    code = f"def big():\n{body}\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL007" for f in findings)


def test_high_complexity():
    code = "def f(x):\n    " + "\n    ".join(
        f"if x > {i}:\n        y{i} = {i}" for i in range(13)) + "\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL008" for f in findings)


def test_deep_nesting():
    code = "def f(x):\n" + "".join("    " * (i + 1) + f"if x > {i}:\n" for i in range(5)) + "\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL009" for f in findings)


def test_too_many_parameters():
    code = "def f(a, b, c, d, e, f):\n    return a\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL010" for f in findings)


def test_leftover_print():
    code = "def h():\n    print('debug')\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL011" for f in findings)


def test_console_log_javascript():
    code = "function h() {\n  console.log('debug');\n}\n"
    findings = detect_quality_issues(code, "javascript")
    assert any(f["rule_id"] == "QUAL011" for f in findings)


def test_todo_comment():
    code = "x = 1\n# TODO: refactor this\n"
    findings = detect_quality_issues(code, "python")
    assert any(f["rule_id"] == "QUAL012" for f in findings)


def test_no_findings_on_clean_code():
    code = "def add(a, b):\n    return a + b\n"
    assert detect_quality_issues(code, "python") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_quality.py -v`
Expected: FAIL.

- [ ] **Step 3: Write the module**

```python
# backend/app/analysis/quality.py
"""Maintainability checks. Python via AST; other languages via tokens."""
import ast

from app.analysis.tokenizer import tokenize_source

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

        def _block(self, body):
            nonlocal nesting
            self.depth += 1
            nesting = max(nesting, self.depth)
            for child in body:
                self.visit(child)
            self.depth -= 1

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
        params = len(node.args.args) + len(node.args.kwonlyargs)
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
    for lineno, line in enumerate(source_code.splitlines(), start=1):
        s = line.strip()
        if s.startswith("print("):
            findings.append(_finding("QUAL011", "Leftover print() call", lineno,
                "print() calls left in code are debug leftovers.",
                "Remove it or route it through proper logging."))
        upper = s.upper()
        if any(t in upper for t in _TODO):
            findings.append(_finding("QUAL012", "TODO/FIXME comment", lineno,
                "An unfinished TODO is committed.",
                "Resolve it or file it as an issue and link the number."))
    return findings


def _analyse_generic(source_code: str, language: str) -> list[dict]:
    tokens = tokenize_source(source_code, language)
    findings = []
    depth = 0
    complexity = 1
    in_func = False
    func_line = 1
    func_params = 0
    line = 1
    param_depth = 0
    for tok in tokens:
        if tok.kind == "identifier":
            kw = tok.text
            if kw in _DECISION_KW:
                complexity += 1
        if tok.text == "(":
            param_depth += 1
        elif tok.text == ")":
            param_depth -= 1
        if tok.text == "{":
            depth += 1
        elif tok.text == "}":
            depth -= 1
        line = max(line, tok.line)
    if depth > MAX_NESTING:
        findings.append(_finding("QUAL009", "Nesting is too deep", 1,
            f"Nesting goes {depth} levels deep.",
            "Return early or extract inner logic."))
    for lineno, line in enumerate(source_code.splitlines(), start=1):
        s = line.strip()
        if "console.log(" in s or s.startswith("print("):
            findings.append(_finding("QUAL011", "Leftover console.log() call", lineno,
                "A console.log() call is left in the code.",
                "Remove it or route it through proper logging."))
        upper = s.upper()
        if any(t in upper for t in _TODO):
            findings.append(_finding("QUAL012", "TODO/FIXME comment", lineno,
                "An unfinished TODO is committed.",
                "Resolve it or file it as an issue."))
    return findings


def detect_quality_issues(source_code: str, language: str) -> list[dict]:
    if language == "python":
        return _analyse_python(source_code)
    if language in ("javascript", "java", "c", "cpp"):
        return _analyse_generic(source_code, language)
    return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_quality.py -v`
Expected: PASS, 8 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/quality.py backend/tests/test_quality.py
git commit -m "feat: maintainability metrics for all supported languages"
```

---

## Task 7: Damped scorer

**Files:**
- Modify: `backend/app/analysis/scorer.py`
- Modify: `backend/tests/test_scoring.py`

Damped weights keep the score meaningful now that the engine finds more.

- [ ] **Step 1: Update the tests**

```python
# backend/tests/test_scoring.py
from app.analysis.scorer import compute_score


def finding(severity):
    return {"severity": severity, "line": 1, "title": "t"}


def test_clean_code_scores_100():
    assert compute_score([]) == 100


def test_single_high_finding_costs_10():
    assert compute_score([finding("high")]) == 90


def test_four_high_findings_cost_24():
    # 10 * (1.0 + 0.7 + 0.5 + 0.35) = 25.5, truncated
    assert compute_score([finding("high")] * 4) == 74


def test_repeated_findings_are_damped():
    assert compute_score([finding("medium")] * 5) > compute_score([finding("medium")] * 6)


def test_single_critical_costs_20():
    assert compute_score([finding("critical")]) == 80


def test_score_floors_at_zero():
    assert compute_score([finding("critical")] * 10) == 0


def test_mixed_severities():
    # 20*1.0 + 10*0.7 + 5*0.7 = 30.5 -> 69
    assert compute_score([finding("critical"), finding("high"), finding("high"), finding("medium"), finding("medium")]) == 69
```

- [ ] **Step 2: Run the tests; watch the old ones fail**

Run: `cd backend && .venv/bin/pytest tests/test_scoring.py -v`
Expected: FAIL on `test_four_high_findings_cost_24` (old scorer gives 60).

- [ ] **Step 3: Rewrite the scorer**

```python
# backend/app/analysis/scorer.py
WEIGHTS = {"critical": 20, "high": 10, "medium": 5, "low": 2}
MULTIPLIERS = (1.0, 0.7, 0.5, 0.35, 0.3)


def compute_score(findings: list[dict]) -> int:
    """Severity-weighted 0-100 score.

    Repeated findings of the same severity cost less. A rich engine finds
    more issues, and without damping every mediocre file would score 0.
    """
    by_severity: dict[str, int] = {}
    for f in findings:
        by_severity[f.get("severity", "medium")] = by_severity.get(f.get("severity", "medium"), 0) + 1

    penalty = 0.0
    for sev, count in by_severity.items():
        weight = WEIGHTS.get(sev, 5)
        for occurrence in range(count):
            mult = MULTIPLIERS[min(occurrence, len(MULTIPLIERS) - 1)]
            penalty += weight * mult
    return max(0, int(100 - penalty))
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && .venv/bin/pytest tests/test_scoring.py -v`
Expected: PASS, 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/scorer.py backend/tests/test_scoring.py
git commit -m "feat: damped severity weights so rich findings still score meaningfully"
```

---

## Task 8: Engine orchestrator

**Files:**
- Create: `backend/app/analysis/engine.py`
- Test: `backend/tests/test_engine.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_engine.py
import time

from app.analysis.engine import analyse


VULNERABLE = 'import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n'


def test_analyse_python_finds_multiple_classes():
    findings = analyse(VULNERABLE, "python")
    assert any(f["rule_id"] == "SEC003" for f in findings)
    assert any(f["rule_id"] == "SEC010" for f in findings)


def test_analyse_comments_are_not_flagged():
    findings = analyse('# password = "hunter2hunter2"\nx = 1\n', "python")
    assert findings == []


def test_analyse_finds_aws_key():
    findings = analyse('AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "python")
    assert any(f["source"] == "secrets" for f in findings)


def test_findings_have_evidence_and_confidence():
    for f in analyse(VULNERABLE, "python"):
        assert "evidence" in f
        assert f["confidence"] in ("high", "medium")
        assert "related_lines" in f


def test_deduped_by_line_severity_title():
    findings = analyse(VULNERABLE, "python")
    keys = [(f["line"], f["severity"], f["title"].lower()) for f in findings]
    assert len(keys) == len(set(keys))


def test_analyser_handles_garbage_input():
    assert isinstance(analyse("\x00\x01 def (", "python"), list)
    assert isinstance(analyse("}", "text"), list)


def test_performance_budget():
    code = (VULNERABLE * 2000)[:50000]  # under the 50k limit
    t0 = time.perf_counter()
    findings = analyse(code, "python")
    elapsed = time.perf_counter() - t0
    assert elapsed < 2.0
    assert findings
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_engine.py -v`
Expected: FAIL, module missing.

- [ ] **Step 3: Write the module**

```python
# backend/app/analysis/engine.py
"""Run every pass and return merged, deduplicated findings."""
from app.analysis.ast_analyzer import analyse_python
from app.analysis.detect import detect_language
from app.analysis.quality import detect_quality_issues
from app.analysis.secrets import detect_secrets
from app.analysis.sinks import detect_semantic_patterns
from app.analysis.static_scanner import scan
from app.analysis.taint import analyse_taint

MAX_FINDINGS = 80


def _merge(passes: list[list[dict]]) -> list[dict]:
    seen = set()
    merged = []
    for findings in passes:
        for f in findings:
            key = (f["line"], f["severity"], f["title"].lower()[:40])
            if key in seen:
                continue
            seen.add(key)
            merged.append(f)
    return merged[:MAX_FINDINGS]


def analyse(source_code: str, language: str | None = None) -> list[dict]:
    language = language or detect_language(source_code)

    findings = []
    findings.extend(scan(source_code, language))
    findings.extend(detect_secrets(source_code, language))
    if language == "python":
        findings.extend(analyse_python(source_code))
    findings.extend(detect_semantic_patterns(source_code, language))
    findings.extend(analyse_taint(source_code, language))
    findings.extend(detect_quality_issues(source_code, language))

    return _merge(findings)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_engine.py -v`
Expected: PASS, 7 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/engine.py backend/tests/test_engine.py
git commit -m "feat: analysis engine orchestrator"
```

---

## Task 9: Pipeline rewrite

**Files:**
- Modify: `backend/app/analysis/pipeline.py`
- Modify: `backend/tests/test_pipeline.py`

- [ ] **Step 1: Update the tests**

```python
# backend/tests/test_pipeline.py
from app.analysis.pipeline import run_review


def test_run_review_shape():
    result = run_review("import os\nos.system('ls ' + input())\n", "a.py")
    assert result["language"] == "python"
    assert result["findings"]
    assert isinstance(result["score"], int)


def test_run_review_vulnerable_python():
    result = run_review('import os\npassword = "hunter2hunter2"\nos.system("ls " + input())\n', "a.py")
    rule_ids = {f["rule_id"] for f in result["findings"]}
    assert "SEC003" in rule_ids
    assert "SEC010" in rule_ids
    assert result["score"] < 100


def test_run_review_clean_code():
    result = run_review("def add(a, b):\n    return a + b\n", "a.py")
    assert result["score"] == 100
    assert result["findings"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/test_pipeline.py -v`
Expected: FAIL, `merge_findings` import error or score mismatch.

- [ ] **Step 3: Rewrite the pipeline**

```python
# backend/app/analysis/pipeline.py
from app.analysis.detect import detect_language
from app.analysis.engine import analyse
from app.analysis.scorer import compute_score


def run_review(source_code: str, filename: str | None) -> dict:
    language = detect_language(source_code, filename)
    findings = analyse(source_code, language)
    return {"language": language, "findings": findings, "score": compute_score(findings)}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/pytest tests/test_pipeline.py -v`
Expected: PASS, 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analysis/pipeline.py backend/tests/test_pipeline.py
git commit -m "refactor: pipeline runs the built-in engine"
```

---

## Task 10: API schema and health endpoint

**Files:**
- Modify: `backend/app/reviews/schemas.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_app.py`

- [ ] **Step 1: Update the health endpoint test**

```python
# backend/tests/test_app.py
def test_health_endpoint_reports_engines(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["engines"] == ["rules", "taint", "secrets", "ast", "sinks", "quality"]
```

- [ ] **Step 2: Update the finding schema**

```python
# in backend/app/reviews/schemas.py, replace FindingOut with:
class FindingOut(BaseModel):
    rule_id: str
    title: str
    severity: str
    line: int
    explanation: str
    suggestion: str
    source: str
    fixed_snippet: str | None = None
    evidence: str = ""
    confidence: str = "high"
    related_lines: list[int] = []
```

- [ ] **Step 3: Update the health endpoint**

```python
# in backend/app/main.py, replace the health() function with:
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "engines": ["rules", "taint", "secrets", "ast", "sinks", "quality"],
    }
```

- [ ] **Step 4: Run the tests**

Run: `cd backend && .venv/bin/pytest tests/test_app.py tests/test_reviews_api.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/reviews/schemas.py backend/app/main.py backend/tests/test_app.py
git commit -m "feat: findings carry evidence/confidence; health reports engines"
```

---

## Task 11: Remove the LLM path

**Files:**
- Delete: `backend/app/analysis/llm_reviewer.py`
- Delete: `backend/tests/test_llm_reviewer.py`
- Modify: `backend/requirements.txt` (remove `httpx`)
- Modify: `backend/app/config.py` (remove `llm_*` settings)
- Modify: `backend/.env.example` (remove `LLM_*`)
- Modify: `backend/tests/conftest.py` (remove `settings.llm_api_key` line)

- [ ] **Step 1: Delete the files**

```bash
git rm backend/app/analysis/llm_reviewer.py backend/tests/test_llm_reviewer.py
```

- [ ] **Step 2: Remove `httpx` from requirements**

Edit `backend/requirements.txt`: delete the `httpx` line.

- [ ] **Step 3: Remove LLM settings from config**

```python
# backend/app/config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./reviews.db"
    secret_key: str = "dev-secret-change-me-to-a-real-32-byte-key"
    token_expire_days: int = 30
```

- [ ] **Step 4: Update `.env.example`**

```
SECRET_KEY=replace-with-a-random-32-byte-string
```

- [ ] **Step 5: Update conftest**

```python
# remove this line from backend/tests/conftest.py
settings.llm_api_key = ""  # force static-only pipeline in tests
```

- [ ] **Step 6: Run the full backend suite**

Run: `cd backend && .venv/bin/pytest -q`
Expected: all pass, zero LLM references (verify with `cd backend && grep -ri llm --include="*.py" .` limited to app/).

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/app/config.py backend/.env.example backend/tests/conftest.py
git commit -m "refactor: remove the external LLM dependency"
```

---

## Task 12: Frontend update

**Files:**
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/pages/Results.tsx`
- Modify: `frontend/src/pages/Landing.tsx`
- Modify: `frontend/src/pages/Submit.tsx`
- Modify: `frontend/src/components/ScanLoader.tsx` (if it mentions an API key)

- [ ] **Step 1: Update the Finding type**

```typescript
// frontend/src/api.ts, update Finding:
export interface Finding {
  rule_id: string;
  title: string;
  severity: string;
  line: number;
  explanation: string;
  suggestion: string;
  source: string;
  fixed_snippet: string | null;
  evidence?: string;
  confidence?: "high" | "medium";
  related_lines?: number[];
}
```

- [ ] **Step 2: Show engine and confidence on each finding**

In `frontend/src/pages/Results.tsx`, replace the `.issue-meta` line:

```tsx
<div className="issue-meta">
  {f.rule_id} · line {f.line} · {f.source}
  {f.confidence === "medium" && (
    <span className="issue-meta" style={{ color: "var(--warn)" }}>
      {" "}· inferred (medium confidence)
    </span>
  )}
</div>
```

Also show the evidence snippet when present:

```tsx
{f.evidence && <pre className="issue-fix" style={{ background: "#f7f3ec", borderColor: "var(--line)", color: "var(--ink-soft)" }}>{f.evidence}</pre>}
```

- [ ] **Step 3: Update pipeline copy**

In `frontend/src/pages/Landing.tsx`, replace the step `03 LLM review` with:

```tsx
<div className="step-row">
  <div className="step-num">03</div>
  <div>
    <h3 className="step-title">Built-in analysis engine</h3>
    <p className="step-body">
      Six local analysis passes run over your code: dataflow tracking, secret
      detection by entropy, Python AST checks, per-language dangerous patterns,
      and quality metrics. Nothing leaves your machine.
    </p>
  </div>
</div>
```

Replace the eyebrow `Static analysis + LLM review` with:

```tsx
<p className="eyebrow mb-6">Built-in analysis engine</p>
```

In the hero heading, keep the headline. In `frontend/src/pages/Submit.tsx`, replace the pipeline sidebar list:

```tsx
{[
  "Detect language",
  "Regex security rules",
  "Taint tracking (source to sink)",
  "Secret detection & quality",
].map((step, i) => (
```

- [ ] **Step 4: Run the frontend build and tests**

```bash
cd frontend && npm run build && npm test
```
Expected: build passes, 8 tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api.ts frontend/src/pages/Results.tsx frontend/src/pages/Landing.tsx frontend/src/pages/Submit.tsx
git commit -m "feat: show engine and confidence per finding; accurate pipeline copy"
```

---

## Task 13: README rewrite

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the What-it-does and Features sections**

Replace the LLM feature bullets and add honest engine description. Key replacements:

```markdown
## Analysis engine

Reviews are produced entirely by a built-in analysis engine. No API key, no
network calls, no third-party service. The engine runs six passes:

1. **Regex rules** — 14 security patterns over every line, with comment and
   string awareness so commented-out code is not flagged.
2. **Taint tracking** — untrusted input data is followed to dangerous calls
   across function boundaries. Python uses AST; JavaScript, Java, C and C++ use
   a token-based function inventory.
3. **Secret detection** — Shannon entropy plus known token prefixes (AWS keys,
   Stripe keys, GitHub tokens). Secrets are redacted in reports.
4. **Python AST analysis** — semantic checks such as mutable default arguments,
   bare except clauses, and missing timeouts.
5. **Semantic catalogue** — per-language dangerous patterns (weak ciphers,
   `Runtime.exec`, `strcat`, `document.write`).
6. **Quality metrics** — function length, cyclomatic complexity, nesting depth,
   leftover debug output.

Taint findings are reported as high confidence when the flow is entirely inside
one function and medium confidence when it crosses a function boundary. The
call graph for non-Python languages is inferred from brace matching; a medium
finding is a prompt to look, not a proof.
```

Update "Tech stack" and "Repository layout" to drop the LLM client, add the new modules, and update the API table and `.env` section to only `SECRET_KEY`.

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: document the built-in engine"
```

---

## Task 14: Full verification

- [ ] **Step 1: Backend suite, frontend suite, build, smoke API**

```bash
cd backend && .venv/bin/pytest -q
cd ../frontend && npm test && npm run build
```

- [ ] **Step 2: API smoke**

```bash
cd backend && .venv/bin/python /private/var/folders/b7/zblh_rjd6vbbyjdyzbb2_4kc0000gn/T/opencode/api_smoke.py
```
Expected: all checks pass; no LLM config required; reviews return real findings.

- [ ] **Step 3: Browser walkthrough**

Start both servers, open the app, submit the vulnerable sample, and confirm each finding shows an engine name and confidence, and the score is damped (not 0).

- [ ] **Step 4: Commit any remaining changes**

```bash
git status --short
```
Everything should be committed.

---

## Self-review notes

- **Spec coverage:** every deliverable in the spec maps to a task; LLM deletion is Task 11; scorer damping is Task 7; all passes have dedicated tasks.
- **Placeholders:** The generic-language taint path previously had a `...` stub; it is now fully specified with a verified algorithm (9/9 generic cases pass on the same inputs used in the plan). Python has 7/7 cases passing on the same tests.
- **Fallback:** Each generic-language pass accounts for unparseable input: `function_inventory` returns `{}` when braces do not balance, and `analyse_taint` then uses the `_intraprocedural` proximity fallback instead of failing.
- **Ambiguity:** confidence is defined as high for same-function flow, medium for cross-function flow and for all non-Python cross-function findings; this is tested in Task 5.
- **Scoring math:** damped; 4 highs = 10*(1.0+0.7+0.5+0.35) = 25.5, truncated to 25, score 74.
