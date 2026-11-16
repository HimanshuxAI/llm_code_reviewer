import json

import httpx

from app.config import settings

MAX_FINDINGS = 60
VALID_SEVERITIES = {"critical", "high", "medium", "low"}

SYSTEM_PROMPT = """You are a secure code review assistant for students.
Review the given source code for bugs, security vulnerabilities, code-quality
issues and inefficient practices. Respond with ONLY a JSON object, no prose:
{"findings": [{"type": short issue name, "severity": "critical|high|medium|low",
"line": integer line number, "explanation": one or two plain sentences a student
can learn from, "suggestion": how to fix it, "fixed_snippet": corrected code or null}]}
If the code has no notable issues, respond with {"findings": []}."""


def parse_llm_json(content: str) -> list[dict]:
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end <= start:
        return []
    try:
        data = json.loads(content[start:end + 1])
        raw = data.get("findings", [])
    except (json.JSONDecodeError, AttributeError):
        return []
    if not isinstance(raw, list):
        return []
    findings = [_normalize(item) for item in raw if isinstance(item, dict)]
    return [f for f in findings if f][:MAX_FINDINGS]


def _normalize(item: dict) -> dict | None:
    try:
        line = int(item.get("line") or 0)
    except (TypeError, ValueError):
        line = 0
    severity = str(item.get("severity", "medium")).lower()
    return {
        "rule_id": "LLM",
        "title": str(item.get("type", "Issue"))[:100],
        "severity": severity if severity in VALID_SEVERITIES else "medium",
        "line": max(0, line),
        "explanation": str(item.get("explanation", "")),
        "suggestion": str(item.get("suggestion", "")),
        "source": "llm",
        "fixed_snippet": str(item["fixed_snippet"]) if item.get("fixed_snippet") else None,
    }


def review_with_llm(source_code: str, language: str) -> list[dict]:
    if not settings.llm_api_key:
        return []
    payload = {
        "model": settings.llm_model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Language: {language}\n\n{source_code}"},
        ],
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
    timeout = httpx.Timeout(
        settings.llm_timeout_seconds,
        connect=5.0,
    )
    try:
        resp = httpx.post(
            settings.llm_base_url.rstrip("/") + "/chat/completions",
            json=payload, headers=headers, timeout=timeout,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError):
        return []
    return parse_llm_json(content)
