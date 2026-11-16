from app.analysis.detect import detect_language
from app.analysis.rules import RULES

MAX_FINDINGS = 60


def scan(source_code: str, language: str | None = None) -> list[dict]:
    language = language or detect_language(source_code)
    findings: list[dict] = []
    for line_number, line in enumerate(source_code.splitlines(), start=1):
        for rule in RULES:
            if rule.languages and language not in rule.languages:
                continue
            if not rule.pattern.search(line):
                continue
            findings.append({
                "rule_id": rule.id,
                "title": rule.title,
                "severity": rule.severity,
                "line": line_number,
                "explanation": rule.explanation,
                "suggestion": rule.suggestion,
                "source": "static",
                "fixed_snippet": None,
            })
    return findings[:MAX_FINDINGS]
