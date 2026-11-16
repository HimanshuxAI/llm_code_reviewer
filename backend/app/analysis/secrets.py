"""Credential detection: Shannon entropy plus known token prefixes.

Secrets are always redacted to their first four characters so findings
never echo the full credential.
"""
import math
import re
from collections import Counter

ENTROPY_THRESHOLD = 3.5

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
    from app.analysis.tokenizer import strip_comments

    masked = strip_comments(source, language)
    masked_lines = masked.splitlines()
    findings = []
    seen = set()

    for lineno, line in enumerate(source.splitlines(), start=1):
        m_line = masked_lines[lineno - 1] if lineno <= len(masked_lines) else ""
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
                findings.append(_finding(
                    "SECRET002", f"{title} ({prefix.strip()})",
                    lineno, m_line, secret, "high"))

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
                            "SECRET001", "Hardcoded credential",
                            lineno, m_line, value, "high"))

    return findings[:60]


def _finding(rule_id, title, lineno, m_line, secret, severity):
    evidence = m_line.replace(secret, _redacted(secret)).strip()[:200]
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
        "evidence": evidence,
        "confidence": "high",
        "related_lines": [],
    }
