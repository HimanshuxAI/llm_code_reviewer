from app.analysis.scorer import compute_score


def finding(severity):
    return {"severity": severity}


def test_clean_code_scores_100():
    assert compute_score([]) == 100


def test_severity_weights():
    assert compute_score([finding("critical")]) == 80
    assert compute_score([finding("high")]) == 90
    assert compute_score([finding("medium")]) == 95
    assert compute_score([finding("low")]) == 98


def test_score_never_below_zero():
    assert compute_score([finding("critical")] * 10) == 0
