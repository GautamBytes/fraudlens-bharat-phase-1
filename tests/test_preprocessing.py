from fraudlens.preprocessing import normalize_text, tokenize_for_display


def test_normalize_text_cleans_whitespace_and_lowercases():
    text = "  URGENT   KYC\nUpdate  http://example.com  "
    assert normalize_text(text) == "urgent kyc update http://example.com"


def test_normalize_text_preserves_evidence_tokens():
    text = "Pay to refund@upi or call 98765-01234"
    cleaned = normalize_text(text)
    assert "refund@upi" in cleaned
    assert "98765-01234" in cleaned


def test_tokenize_for_display():
    assert tokenize_for_display("A  B") == ["a", "b"]

