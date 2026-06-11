from fraudlens.entity_extraction import extract_entities


def _values_by_type(text, entity_type):
    return [entity.value for entity in extract_entities(text) if entity.type == entity_type]


def test_extracts_phone_upi_url_email_money_and_otp():
    text = (
        "Call +91 98765-01234, pay Rs 1499 to refund@upi, "
        "open http://kyc-login.example and email support@fakebank.example. "
        "Your OTP code is 482913."
    )
    assert "9876501234" in _values_by_type(text, "phone")
    assert "refund@upi" in _values_by_type(text, "upi_id")
    assert "http://kyc-login.example" in _values_by_type(text, "url")
    assert "support@fakebank.example" in _values_by_type(text, "email")
    assert any("1499" in value for value in _values_by_type(text, "money"))
    assert "482913" in _values_by_type(text, "otp_like_code")


def test_extracts_urgency_and_threat_phrases():
    text = "Urgent update now or account block and legal action."
    entities = extract_entities(text.lower())
    entity_types = {entity.type for entity in entities}
    assert "urgency_phrase" in entity_types
    assert "threat_phrase" in entity_types


def test_email_is_not_partially_extracted_as_upi_id():
    text = "Send resume to hr@jobpay.example and pay Rs 999 as joining fee."
    assert "hr@jobpay.example" in _values_by_type(text, "email")
    assert "hr@jobpay" not in _values_by_type(text, "upi_id")


def test_extracts_contextual_bare_money_amounts():
    text = "Join VIP group. Invest 5000 now and receive 2500 cashback."
    money_values = _values_by_type(text, "money")
    assert "5000" in money_values
    assert "2500" in money_values
