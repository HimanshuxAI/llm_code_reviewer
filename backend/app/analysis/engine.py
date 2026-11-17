"""Run every pass and return merged, deduplicated findings."""
from app.analysis.ast_analyzer import analyse_python
from app.analysis.detect import detect_language
from app.analysis.quality import detect_quality_issues
from app.analysis.secrets import detect_secrets
from app.analysis.sinks import detect_semantic_patterns
from app.analysis.static_scanner import scan
from app.analysis.taint import analyse_taint
from app.analysis.tokenizer import strip_comments

MAX_FINDINGS = 80


def _merge(findings: list[dict]) -> list[dict]:
    """Drop duplicate findings, keeping the first pass that reports them.

    Passes run cheapest first, so a regex hit wins over a semantic or taint
    hit describing the same problem on the same line.
    """
    seen = set()
    merged = []
    for f in findings:
        key = (f["line"], f["severity"], f["title"].lower()[:40])
        if key in seen:
            continue
        seen.add(key)
        merged.append(f)
    return merged[:MAX_FINDINGS]


def _normalise(findings: list[dict]) -> list[dict]:
    """Guarantee the finding contract for every pass.

    Older passes (the regex rules) predate ``evidence``/``confidence``/
    ``related_lines``. The API schema defaults them too, but the engine is
    the single place where all passes converge, so fill them here once.
    """
    for f in findings:
        f.setdefault("evidence", "")
        f.setdefault("confidence", "high")
        f.setdefault("related_lines", [])
    return findings


def analyse(source_code: str, language: str | None = None) -> list[dict]:
    language = language or detect_language(source_code)

    findings = []
    # Regex rules match raw lines, so a commented-out secret would otherwise
    # be reported. Mask comments first; strings stay intact because several
    # rules match literal values inside them.
    findings.extend(scan(strip_comments(source_code, language), language))
    findings.extend(detect_secrets(source_code, language))
    if language == "python":
        findings.extend(analyse_python(source_code))
    findings.extend(detect_semantic_patterns(source_code, language))
    findings.extend(analyse_taint(source_code, language))
    findings.extend(detect_quality_issues(source_code, language))

    return _merge(_normalise(findings))
