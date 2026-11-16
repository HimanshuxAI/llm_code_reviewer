WEIGHTS = {"critical": 20, "high": 10, "medium": 5, "low": 2}


def compute_score(findings: list[dict]) -> int:
    penalty = sum(WEIGHTS.get(f.get("severity", "medium"), 5) for f in findings)
    return max(0, 100 - penalty)
