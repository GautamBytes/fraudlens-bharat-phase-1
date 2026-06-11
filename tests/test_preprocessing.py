from fraudlens.preprocessing import normalize_text, prepare_model_text, tokenize_for_display


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


def test_prepare_model_text_does_not_treat_hinglish_fir_as_police_fir():
    model_text = prepare_model_text("Loan approved, CIBIL low hai fir bhi approval.")
    assert "__signal_loan_scam" in model_text
    assert "__signal_digital_arrest" not in model_text
