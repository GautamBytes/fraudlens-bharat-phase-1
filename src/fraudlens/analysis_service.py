"""Application service for one fraud-message analysis."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, Mapping, Optional, Protocol
from uuid import uuid4

from fraudlens.entity_extraction import extract_entities
from fraudlens.model_inference import predictor as default_predictor
from fraudlens.prediction import Predictor
from fraudlens.preprocessing import normalize_text
from fraudlens.risk_scoring import score_risk
from fraudlens.schemas import AnalysisResult, Entity
from fraudlens.url_risk import analyze_urls


@dataclass(frozen=True)
class AnalysisInput:
    text: str
    user_notes: Optional[str] = None
    store_case: bool = False
    metadata: Optional[Mapping[str, Any]] = None


class CaseStore(Protocol):
    def save(self, result: AnalysisResult) -> None:
        """Persist an analysis result."""


class DatabaseCaseStore:
    """Small adapter around the existing database functions."""

    def initialize(self) -> None:
        from fraudlens.database import init_db

        init_db()

    def save(self, result: AnalysisResult) -> None:
        from fraudlens.database import save_case

        save_case(result)

    def list_cases(self, limit: int) -> list[dict]:
        from fraudlens.database import list_cases

        return list_cases(limit=limit)

    def get_case(self, case_id: str) -> Optional[dict]:
        from fraudlens.database import get_case

        return get_case(case_id)


def build_complaint_draft(
    predicted_label: str,
    risk_level: str,
    entities: list[Entity],
    original_text: str,
) -> str:
    entity_summary: Dict[str, list[str]] = {}
    for entity in entities:
        entity_summary.setdefault(entity.type, []).append(entity.value)

    lines = [
        "Suspected fraud type: {}".format(predicted_label),
        "Risk level: {}".format(risk_level),
        "Incident summary: The user received a suspicious message that appears to request sensitive action, payment, verification, or credentials.",
    ]
    for entity_type, values in sorted(entity_summary.items()):
        lines.append("Detected {}: {}".format(entity_type, ", ".join(values[:5])))
    lines.append("Original message: {}".format(original_text))
    lines.append(
        "Recommended manual action: preserve screenshots, do not share OTP/PIN/password, contact 1930 if money was lost, and file a report on NCRP if applicable."
    )
    return "\n".join(lines)


class AnalysisService:
    """Coordinates pure analysis components and optional case persistence."""

    def __init__(
        self,
        predictor: Predictor,
        store: Optional[CaseStore] = None,
        clock: Callable[[], datetime] = datetime.utcnow,
        id_generator: Callable[[], object] = uuid4,
    ) -> None:
        self._predictor = predictor
        self._store = store
        self._clock = clock
        self._id_generator = id_generator

    def analyze(self, analysis_input: AnalysisInput) -> AnalysisResult:
        cleaned_text = normalize_text(analysis_input.text)
        entities = extract_entities(cleaned_text)
        urls = [entity.value for entity in entities if entity.type == "url"]
        url_signals = analyze_urls(urls)
        prediction = self._predictor.predict(cleaned_text)
        risk_level, risk_score, risk_signals, explanation = score_risk(
            prediction.label,
            prediction.confidence,
            entities,
            url_signals,
        )
        metadata = dict(analysis_input.metadata or {})
        metadata.update(
            {
                "prediction_source": prediction.source,
                "prediction_model_version": prediction.model_version,
                "prediction_abstained": prediction.abstained,
                "user_notes": analysis_input.user_notes,
                "stored": False,
            }
        )
        result = AnalysisResult(
            case_id=str(self._id_generator()),
            created_at=self._clock(),
            original_text=analysis_input.text,
            cleaned_text=cleaned_text,
            predicted_label=prediction.label,
            confidence=prediction.confidence,
            risk_level=risk_level,
            risk_score=risk_score,
            entities=entities,
            risk_signals=risk_signals,
            explanation=explanation,
            complaint_draft=build_complaint_draft(prediction.label, risk_level, entities, analysis_input.text),
            metadata=metadata,
        )
        if analysis_input.store_case and self._store is not None:
            result.metadata["stored"] = True
            try:
                self._store.save(result)
            except Exception:
                result.metadata["stored"] = False
                result.metadata["storage_warning"] = "Case storage was unavailable."
        return result


def create_analysis_service(
    predictor: Optional[Predictor] = None,
    store: Optional[CaseStore] = None,
) -> AnalysisService:
    return AnalysisService(
        predictor=predictor or default_predictor,
        store=store if store is not None else DatabaseCaseStore(),
    )
