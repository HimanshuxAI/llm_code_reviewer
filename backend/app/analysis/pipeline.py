from app.analysis.detect import detect_language
from app.analysis.engine import analyse
from app.analysis.scorer import compute_score


def run_review(source_code: str, filename: str | None) -> dict:
    language = detect_language(source_code, filename)
    findings = analyse(source_code, language)
    return {"language": language, "findings": findings, "score": compute_score(findings)}
