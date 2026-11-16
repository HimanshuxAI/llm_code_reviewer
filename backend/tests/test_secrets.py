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
