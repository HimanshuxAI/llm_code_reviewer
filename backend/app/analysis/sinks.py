"""Per-language sources, sinks, and the dangerous-pattern catalogue.

Sources mark where attacker-controlled data enters. Sinks mark calls where
untrusted data must never appear. The catalogue holds patterns that are
unsafe on their own, independent of dataflow.

SOURCES and SINKS contain broad bare names (e.g. python "get", javascript
"write") accepted as plan-mandated data; the taint engine must anchor on
call-position context before treating them as meaningful.
"""
import re
from dataclasses import dataclass

from app.analysis.tokenizer import strip_comments

MAX_FINDINGS = 60

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
                 re.compile(r"getInstance\(\s*[\"'](DES|RC4|DESede)[\/\w-]*[\"']", re.I),
                 "DES and RC4 are broken ciphers; data encrypted with them is recoverable.",
                 "Use AES-256-GCM.", frozenset({"java"})),
    SemanticRule("SEC014", "Weak digest algorithm", "medium",
                 re.compile(r"getInstance\(\s*[\"'](MD5|SHA-?1)[\/\w-]*[\"']", re.I),
                 "MD5 and SHA-1 are broken for integrity checks.",
                 "Use SHA-256 or better.", frozenset({"java"})),
    SemanticRule("SEC015", "XMLDecoder on untrusted data", "high",
                 re.compile(r"\bnew\s+XMLDecoder\b"),
                 "XMLDecoder deserialises arbitrary objects and allows remote code execution.",
                 "Use a strict XML parser or JSON with schema validation.", frozenset({"java"})),
    SemanticRule("SEC016", "TrustManager that accepts everything", "high",
                 re.compile(r"check(?:Client|Server)Trusted\s*\("),
                 "A custom TrustManager method was defined; this is the canonical trust-all pattern in Android/TLS code.",
                 "Delete the custom trust manager and validate against a real CA bundle.", frozenset({"java"})),
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
                 re.compile(r"\bscanf\s*\(\s*\"[^\"]*%s"),
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
    masked = strip_comments(source, language)
    has_child_process = "child_process" in masked
    findings = []
    # Line-oriented on purpose: rules cannot span lines, so multi-line
    # constructs must fit on one line or be refactored.
    for lineno, line in enumerate(masked.splitlines(), start=1):
        for rule in SEMANTIC_RULES:
            if language not in rule.languages:
                continue
            if rule.id == "JS004" and not has_child_process:
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
    return findings[:MAX_FINDINGS]
