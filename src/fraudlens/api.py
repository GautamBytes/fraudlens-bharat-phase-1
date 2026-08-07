from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from fraudlens.database import get_case, init_db, list_cases, save_case
from fraudlens.entity_extraction import extract_entities
from fraudlens.model_inference import predictor
from fraudlens.preprocessing import normalize_text
from fraudlens.risk_scoring import score_risk
from fraudlens.schemas import AnalysisResult, AnalyzeRequest, Entity
from fraudlens.url_risk import analyze_urls


app = FastAPI(
    title="FraudLens Bharat Phase 1 API",
    description="Baseline cyber-fraud triage API for Hinglish/Hindi/English scam messages.",
    version="0.1.0",
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def build_complaint_draft(
    predicted_label: str,
    risk_level: str,
    entities: List[Entity],
    original_text: str,
) -> str:
    entity_summary = {}
    for entity in entities:
        entity_summary.setdefault(entity.type, []).append(entity.value)

    lines = [
        f"Suspected fraud type: {predicted_label}",
        f"Risk level: {risk_level}",
        "Incident summary: The user received a suspicious message that appears to request sensitive action, payment, verification, or credentials.",
    ]
    for entity_type, values in sorted(entity_summary.items()):
        compact_values = ", ".join(values[:5])
        lines.append(f"Detected {entity_type}: {compact_values}")
    lines.append(f"Original message: {original_text}")
    lines.append("Recommended manual action: preserve screenshots, do not share OTP/PIN/password, contact 1930 if money was lost, and file a report on NCRP if applicable.")
    return "\n".join(lines)


def analyze_message(text: str, user_notes: Optional[str] = None) -> AnalysisResult:
    cleaned_text = normalize_text(text)
    entities = extract_entities(cleaned_text)
    urls = [entity.value for entity in entities if entity.type == "url"]
    url_signals = analyze_urls(urls)
    prediction = predictor.predict(cleaned_text)
    risk_level, risk_score, risk_signals, explanation = score_risk(
        prediction.label,
        prediction.confidence,
        entities,
        url_signals,
    )
    complaint_draft = build_complaint_draft(prediction.label, risk_level, entities, text)
    result = AnalysisResult(
        case_id=str(uuid4()),
        created_at=datetime.utcnow(),
        original_text=text,
        cleaned_text=cleaned_text,
        predicted_label=prediction.label,
        confidence=prediction.confidence,
        risk_level=risk_level,
        risk_score=risk_score,
        entities=entities,
        risk_signals=risk_signals,
        explanation=explanation,
        complaint_draft=complaint_draft,
        metadata={
            "prediction_source": prediction.source,
            "prediction_model_version": prediction.model_version,
            "prediction_abstained": prediction.abstained,
            "user_notes": user_notes,
        },
    )
    save_case(result)
    return result


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "fraudlens-bharat-phase-1"}


@app.post("/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    return analyze_message(request.text, request.user_notes)


@app.get("/cases")
def cases(limit: int = 20) -> list[dict]:
    return list_cases(limit=limit)


@app.get("/cases/{case_id}")
def case_detail(case_id: str) -> dict:
    result = get_case(case_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return result
