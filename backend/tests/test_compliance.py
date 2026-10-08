from app.security.compliance import redact_text, redact_payload

def test_redaction():
    text = "contact alice@example.com or +1 555-123-4567 with api_key=SECRET123"
    out = redact_text(text)
    assert "alice@example.com" not in out
    assert "555-123-4567" not in out
    assert "SECRET123" not in out

def test_nested_payload_redaction():
    out = redact_payload({"contact": "bob@example.com", "items": ["x@example.org"]})
    assert "@" not in out["contact"]
    assert "@" not in out["items"][0]
