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

