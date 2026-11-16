from app.analysis.detect import detect_language
from app.analysis.llm_reviewer import review_with_llm
from app.analysis.scorer import compute_score
from app.analysis.static_scanner import scan

MAX_FINDINGS = 80


def merge_findings(static: list[dict], llm: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    merged: list[dict] = []
    for finding in static + llm:
        key = (finding["line"], finding["severity"], finding["title"].lower()[:40])
        if key in seen:
            continue
        seen.add(key)
        merged.append(finding)
    return merged[:MAX_FINDINGS]


def run_review(source_code: str, filename: str | None) -> dict:
    language = detect_language(source_code, filename)
    static = scan(source_code, language)
    llm = review_with_llm(source_code, language)
    findings = merge_findings(static, llm)
    return {"language": language, "findings": findings, "score": compute_score(findings)}
