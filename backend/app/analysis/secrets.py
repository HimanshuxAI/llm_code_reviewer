"""Credential detection: Shannon entropy plus known token prefixes.

Detection is deliberately line-oriented over raw source; credential-looking
text in trailing comments is flagged because commented-out secrets still leak.

Secrets are always redacted to their first four characters so findings
never echo the full credential.
"""
import math
import re
from collections import Counter

ENTROPY_THRESHOLD = 3.5
MAX_FINDINGS = 60

CRED_NAME = re.compile(
    r"(password|passwd|secret|api_?key|apikey|access_?token|auth_?token|"
    r"client_?secret|private_?key|signing_?key|aws_?key|session_?key)", re.I)

KNOWN_PREFIXES = (
    ("sk-live-", "Stripe live secret key"),
    ("sk_live_", "Stripe live secret key"),
    ("pk_live_", "Stripe publishable key (not a secret)"),
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

# Compiled prefix patterns, hoisted to module level so detection and redaction
# share one table. Aligned one-to-one with KNOWN_PREFIXES.
PREFIX_RES = tuple(
    (re.compile(re.escape(p) + r"[A-Za-z0-9_\-\.]{4,}"), title)
    for p, title in KNOWN_PREFIXES
)

STRING_RE = re.compile(r'"([^"\n\\]{8,})"|\'([^\'\n\\]{8,})\'')

# Placeholder literals that must not be flagged as credentials when they sit
# next to a credential-like name. Any other high-entropy value is caught by
# the entropy check alone; this list exists only for low-entropy placeholders.
DENYLIST = {
    "password",       # placeholder standing in for a real password
    "changeme",       # default-credential placeholder in configs and docs
    "your-key-here",  # documentation placeholder
    "xxxxxxxx",       # masking placeholder
}

# pk_live_ is publishable by design, so it is reported as a low-severity
# signal rather than as a credential leak.
PK_LIVE_EXPLANATION = (
    "A Stripe publishable key is committed; it is not a credential, but its "
    "presence suggests the sibling secret key may be nearby or committed."
)


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _redacted(secret: str) -> str:
    return f"{secret[:4]}...({len(secret)} chars)"


def _redact_line(line: str) -> str:
    """Redact every secret detected on a raw line, not just one.

    Finds all PREFIX_RES matches and every STRING_RE match (same regexes
    used for detection) and replaces each with its redacted form. Spans may
    contain other spans (a prefix match can sit fully inside a string-literal
    match); spans are applied left-to-right, longest first, with the cursor
    strictly advancing — a span that begins before the cursor is clipped to
    it rather than skipped, so the output can never contain a partial literal.
    Returns at most 200 chars.
    """
    spans = []  # (start, end, replacement)
    for regex, _title in PREFIX_RES:
        for mm in regex.finditer(line):
            spans.append((mm.start(), mm.end(), _redacted(mm.group(0))))
    # Every quoted literal on the line is redacted, not only the ones
    # detection flagged, so evidence can never echo a secret.
    for mm in STRING_RE.finditer(line):
        if mm.group(1) is not None:
            vstart, vend, value = mm.start(1), mm.end(1), mm.group(1)
        else:
            vstart, vend, value = mm.start(2), mm.end(2), mm.group(2)
        spans.append((vstart, vend, _redacted(value)))
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    out = []
    cursor = 0
    for start, end, repl in spans:
        if end <= cursor:
            continue  # fully contained in an already-redacted span
        if start < cursor:
            start = cursor  # clip; never emit a partial literal
        out.append(line[cursor:start])
        out.append(repl)
        cursor = end
    out.append(line[cursor:])
    return "".join(out).strip()[:200]


def detect_secrets(source: str, language: str) -> list[dict]:
    from app.analysis.tokenizer import strip_comments

    masked = strip_comments(source, language)
    masked_lines = masked.splitlines()
    findings = []

    for lineno, line in enumerate(source.splitlines(), start=1):
        # strip_comments preserves line counts, so this index is always valid.
        # Named-credential detection runs against the raw line by design:
        # the mask is used only to skip purely commented-out lines.
        m_line = masked_lines[lineno - 1]
        if m_line.strip() == "":
            continue  # purely a comment

        # 1) known prefixes anywhere on the line; every match gets a finding
        for (regex, title), (prefix, _) in zip(PREFIX_RES, KNOWN_PREFIXES):
            for mm in regex.finditer(line):
                secret = mm.group(0)
                severity = "low" if prefix == "pk_live_" else "high"
                explanation = PK_LIVE_EXPLANATION if prefix == "pk_live_" else None
                findings.append(_finding(
                    "SECRET002", f"{title} ({prefix.strip()})",
                    lineno, line, secret, severity, explanation))

        # 2) credential-style name assigned a high-entropy value
        m = CRED_NAME.search(line)
        if m:
            for sm in STRING_RE.finditer(line):
                value = sm.group(1) if sm.group(1) is not None else sm.group(2)
                # Shannon entropy of an n-character string is at most log2(n),
                # so exceeding ENTROPY_THRESHOLD (3.5) requires n >= 12. The
                # len(value) >= 8 check is unreachable in practice and kept
                # only as defense-in-depth; credentials of 8-11 characters
                # cannot be detected by this entropy test.
                if len(value) >= 8 and value.lower() not in DENYLIST \
                        and shannon_entropy(value) > ENTROPY_THRESHOLD:
                    findings.append(_finding(
                        "SECRET001", "Hardcoded credential",
                        lineno, line, value, "high"))

    return findings[:MAX_FINDINGS]


def _finding(rule_id, title, lineno, line, secret, severity, explanation=None):
    evidence = _redact_line(line)
    return {
        "rule_id": rule_id,
        "title": title,
        "severity": severity,
        "line": lineno,
        "explanation": explanation or (
            f"A credential literal ({_redacted(secret)}) is committed in source. "
            "It leaks through version history and shared repos."
        ),
        "suggestion": "Load the value from an environment variable or a .env file excluded from git.",
        "source": "secrets",
        "fixed_snippet": None,
        "evidence": evidence,
        "confidence": "high",
        "related_lines": [],
    }
