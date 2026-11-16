from app.analysis.secrets import shannon_entropy, detect_secrets


def test_shannon_entropy_orders_strings():
    assert shannon_entropy("xxxxxxxxxxxx") < 0.1
    assert shannon_entropy("AKIAIOSFODNN7EXAMPLE") > 3.5
    assert shannon_entropy("sk-live-9f3a2b8c7d6e5f4a") > 3.5


def test_detects_aws_access_key_with_non_credential_name():
    # the existing scanner misses this; it must not
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = detect_secrets(code, "python")
    assert any("AKIA" in f["title"] for f in findings)


def test_detects_named_secret():
    code = 'api_key = "a8f3c2b1e9d4f6a7c5b8"\n'
    findings = detect_secrets(code, "python")
    assert any(f["rule_id"] == "SECRET001" for f in findings)


def test_ignores_low_entropy_string():
    code = 'greeting = "hello world"\n'
    assert detect_secrets(code, "python") == []


def test_ignores_comment():
    code = '# AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    assert detect_secrets(code, "python") == []


def test_two_credential_literals_on_one_line_are_all_detected_and_redacted():
    code = 'token = "AKIAIOSFODNN7EXAMPLE" ; secret = "b9e4d3c2a1f5e6b7c8d9a0b1"\n'
    findings = detect_secrets(code, "python")
    rule_ids = [f["rule_id"] for f in findings]
    # the AWS prefix literal yields SECRET002; the named high-entropy
    # literal yields SECRET001 — both must be found
    assert "SECRET002" in rule_ids
    assert "SECRET001" in rule_ids
    for f in findings:
        body = " ".join(
            f["title"] + f["explanation"] + f["suggestion"] + f["evidence"]
        )
        assert "AKIAIOSFODNN7EXAMPLE" not in body
        assert "b9e4d3c2a1f5e6b7c8d9a0b1" not in body


def test_comment_region_credential_is_flagged():
    # detection runs on raw source by design: commented-out secrets still leak
    code = 'x = 1  # api_key = "a8f3c2b1e9d4f6a7c5b8"\n'
    findings = detect_secrets(code, "python")
    assert any(f["rule_id"] == "SECRET001" for f in findings)


def test_evidence_is_truncated_to_200_chars():
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"' + "  # padding padding padding" * 20 + "\n"
    findings = detect_secrets(code, "python")
    assert findings
    for f in findings:
        assert len(f["evidence"]) <= 200


def test_findings_cap_at_60():
    code = "".join(f'AWS_KEY_{i} = "AKIAIOSFODNN7EXAMPLE"\n' for i in range(70))
    findings = detect_secrets(code, "python")
    assert len(findings) == 60


def test_secret_is_redacted_in_output():
    code = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
    findings = detect_secrets(code, "python")
    body = " ".join(f["explanation"] + f["evidence"] for f in findings)
    assert "AKIAIOSFODNN7EXAMPLE" not in body
    assert "AKIA" in body  # first 4 chars shown


def test_flags_standalone_jwt():
    code = 'token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.signature"\n'
    findings = detect_secrets(code, "python")
    assert findings


def test_evidence_redacts_all_secrets_on_the_line():
    code = 'a = "AKIAIOSFODNN7EXAMPLE"; b = "ghp_1234567890abcdefghij"\n'
    findings = detect_secrets(code, "python")
    secret_findings = [f for f in findings if f["rule_id"] == "SECRET002"]
    assert len(secret_findings) == 2
    for f in findings:
        body = " ".join(
            f["title"] + f["explanation"] + f["suggestion"] + f["evidence"]
        )
        assert "AKIAIOSFODNN7EXAMPLE" not in body
        assert "ghp_1234567890abcdefghij" not in body
    # evidence is built from the raw line, so both redactions are visible
    for f in secret_findings:
        assert "AKIA" in f["evidence"]
        assert "ghp_" in f["evidence"]


def test_evidence_redacts_secret_in_trailing_comment():
    code = "x = 1  # AKIAIOSFODNN7EXAMPLE\n"
    findings = detect_secrets(code, "python")
    assert findings
    for f in findings:
        body = " ".join(
            f["title"] + f["explanation"] + f["suggestion"] + f["evidence"]
        )
        assert "AKIAIOSFODNN7EXAMPLE" not in body
        assert "AKIA" in f["evidence"]
        assert "x = 1" in f["evidence"]


def test_form_feed_in_comment_does_not_crash():
    # A form feed (\x0c) is a line boundary for str.splitlines() but not for
    # the \n-only split used by the scanner; the two line models must agree.
    src = 'x = 1 # comment\x0c api_key = "a8f3c2b1e9d4f6a7c5b8"\n'
    findings = detect_secrets(src, "python")  # must not raise
    assert all(f["line"] == 1 for f in findings)

    # a purely commented-out line containing a form feed and a secret-looking
    # literal is masked away and must not flag
    pure = '# comment\x0c api_key = "a8f3c2b1e9d4f6a7c5b8"\n'
    assert detect_secrets(pure, "python") == []
