"""Severity-weighted 0-100 score with damping for repeated findings."""
WEIGHTS = {"critical": 20, "high": 10, "medium": 5, "low": 2}
MULTIPLIERS = (1.0, 0.7, 0.5, 0.35, 0.3)


def compute_score(findings: list[dict]) -> int:
    """Repeated findings of the same severity cost less than the first.

    The engine finds far more than the old regex rules did; without damping
    any file with ten medium findings would score 0 and the number would
    stop meaning anything.
    """
    counts: dict[str, int] = {}
    for f in findings:
        sev = f.get("severity", "medium")
        counts[sev] = counts.get(sev, 0) + 1

    penalty = 0.0
    for sev, count in counts.items():
        weight = WEIGHTS.get(sev, 5)
        for occurrence in range(count):
            penalty += weight * MULTIPLIERS[min(occurrence, len(MULTIPLIERS) - 1)]
    return max(0, int(100 - penalty))
