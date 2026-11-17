from app.analysis.scorer import compute_score


def finding(severity):
    return {"severity": severity, "line": 1, "title": "t"}


def test_clean_code_scores_100():
    assert compute_score([]) == 100


def test_single_high_finding_costs_10():
    assert compute_score([finding("high")]) == 90


def test_single_critical_costs_20():
    assert compute_score([finding("critical")]) == 80


def test_single_medium_costs_5():
    assert compute_score([finding("medium")]) == 95


def test_single_low_costs_2():
    assert compute_score([finding("low")]) == 98


def test_four_high_findings_are_damped():
    # 10 * (1.0 + 0.7 + 0.5 + 0.35) = 25.5
    # int(100 - 25.5) = int(74.5) = 74
    assert compute_score([finding("high")] * 4) == 74


def test_repeated_findings_are_damped():
    six = compute_score([finding("medium")] * 6)
    five = compute_score([finding("medium")] * 5)
    assert six < five  # more findings still cost more
    # The 6th medium costs the floor multiplier (5*0.3=1.5), not the full 5:
    # 5*(1.0 + 0.7 + 0.5 + 0.35 + 0.3) + 5*0.3 = 15.75 -> int(100 - 15.75) = 84
    assert six == 84


def test_score_floors_at_zero():
    # 20 * (1.0 + 0.7 + 0.5 + 0.35 + 0.3*10) = 20 * 5.85 = 117 -> 0
    assert compute_score([finding("critical")] * 15) == 0


def test_mixed_severities():
    # 20*1.0 + 10*(1.0 + 0.7) + 5*(1.0 + 0.7) = 20 + 17 + 8.5 = 45.5
    # int(100 - 45.5) = int(54.5) = 54
    assert compute_score([
        finding("critical"), finding("high"), finding("high"),
        finding("medium"), finding("medium"),
    ]) == 54
