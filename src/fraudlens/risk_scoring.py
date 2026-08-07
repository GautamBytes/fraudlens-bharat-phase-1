from typing import List, Tuple

from fraudlens.schemas import Entity, RiskSignal


def score_risk(
    predicted_label: str,
    confidence: float,
    entities: List[Entity],
    url_signals: List[RiskSignal],
) -> Tuple[str, float, List[RiskSignal], List[str]]:
    signals: List[RiskSignal] = list(url_signals)
    explanation: List[str] = []

    score = 0.0
    if predicted_label.casefold() not in {"unknown", "legitimate", "benign"}:
        model_score = min(max(confidence, 0.0), 1.0) * 35
        score += model_score
        signals.append(
            RiskSignal(
                name="classifier_confidence",
                score=round(model_score, 2),
                reason=f"Classifier predicts {predicted_label} with confidence {confidence:.2f}",
            )
        )

    entity_types = {entity.type for entity in entities}
    entity_counts = {entity_type: sum(1 for item in entities if item.type == entity_type) for entity_type in entity_types}

    if "url" in entity_types:
        score += 10
        signals.append(RiskSignal(name="url_present", score=10, reason="Message contains at least one URL"))
    if "upi_id" in entity_types:
        score += 12
        signals.append(RiskSignal(name="upi_present", score=12, reason="Message contains a UPI ID"))
    if "phone" in entity_types:
        score += 8
        signals.append(RiskSignal(name="phone_present", score=8, reason="Message contains a phone number"))
    if "money" in entity_types:
        score += 10
        signals.append(RiskSignal(name="money_present", score=10, reason="Message asks for or references money"))
    if "otp_like_code" in entity_types:
        score += 18
        signals.append(RiskSignal(name="otp_signal", score=18, reason="Message references OTP/PIN/code details"))
    if "urgency_phrase" in entity_types:
        urgency_score = min(entity_counts.get("urgency_phrase", 0) * 5, 15)
        score += urgency_score
        signals.append(RiskSignal(name="urgency_language", score=urgency_score, reason="Urgency language detected"))
    if "threat_phrase" in entity_types:
        threat_score = min(entity_counts.get("threat_phrase", 0) * 6, 18)
        score += threat_score
        signals.append(RiskSignal(name="threat_language", score=threat_score, reason="Threat or coercion language detected"))

    score += sum(signal.score for signal in url_signals)
    score = round(min(score, 100), 2)

    if score >= 70:
        risk_level = "high"
    elif score >= 35:
        risk_level = "medium"
    else:
        risk_level = "low"

    top_signals = sorted(signals, key=lambda item: item.score, reverse=True)[:6]
    for signal in top_signals:
        explanation.append(signal.reason)

    if not explanation:
        explanation.append("No strong fraud signals were detected in the message.")

    return risk_level, score, signals, explanation
