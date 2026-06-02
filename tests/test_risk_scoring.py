from fraudlens.risk_scoring import score_risk
from fraudlens.schemas import Entity, RiskSignal


def test_low_risk_for_unknown_without_signals():
    level, score, signals, explanation = score_risk("unknown", 0.2, [], [])
    assert level == "low"
    assert score < 35
    assert explanation


def test_high_risk_for_confident_url_otp_threat():
    entities = [
        Entity(type="url", value="http://fake.example"),
        Entity(type="otp_like_code", value="482913"),
        Entity(type="threat_phrase", value="block"),
        Entity(type="urgency_phrase", value="urgent"),
    ]
    url_signals = [RiskSignal(name="non_https_url", score=15, reason="URL does not use HTTPS")]
    level, score, signals, explanation = score_risk("otp_phishing", 0.9, entities, url_signals)
    assert level == "high"
    assert score >= 70
    assert signals
    assert explanation

