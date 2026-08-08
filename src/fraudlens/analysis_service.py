"""Application service for one fraud-message analysis."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Protocol
from uuid import uuid4

from fraudlens.entity_extraction import extract_entities
from fraudlens.graph_analysis import EntityGraphResult, build_entity_graph
from fraudlens.model_inference import predictor_registry as default_predictor_registry
from fraudlens.prediction import Predictor, PredictorRegistry
from fraudlens.preprocessing import normalize_text
from fraudlens.risk_scoring import score_risk
from fraudlens.schemas import AnalysisResult, AnalyzeRequest, Entity
from fraudlens.settings import Settings
from fraudlens.url_risk import analyze_urls


@dataclass(frozen=True)
class AnalysisInput:
    text: str
    user_notes: Optional[str] = None
    store_case: bool = False
    metadata: Optional[Mapping[str, Any]] = None


class CaseStore(Protocol):
    def initialize(self) -> None:
        """Prepare storage and run safe migrations."""

    def save(self, result: AnalysisResult) -> None:
        """Persist an analysis result."""

    def list_cases(self, limit: int) -> list[dict]:
        """Return bounded case summaries."""

    def get_case(self, case_id: str) -> Optional[dict]:
        """Return one public case result when present."""

    def delete(self, case_id: str) -> bool:
        """Delete one case and report whether it existed."""

    def clear(self) -> int:
        """Delete all stored cases and return the affected count."""

    def entity_graph(
        self, minimum_case_count: int = 2, case_limit: int = 100, max_edges: int = 1_000
    ) -> EntityGraphResult:
        """Return the retained privacy-safe entity relationship graph."""


class DatabaseCaseStore:
    """Configured case persistence adapter with privacy-safe entity links."""

    def __init__(
        self,
        database_path: Path,
        hmac_secret: str = "local-demo-only-secret-not-for-production",
        retention_days: int = 30,
    ) -> None:
        self._database_path = Path(database_path)
        self._hmac_secret = hmac_secret
        self._retention_days = retention_days

    def initialize(self) -> None:
        from fraudlens.database import init_db

        from fraudlens.database import purge_expired

        init_db(path=self._database_path, retention_days=self._retention_days)
        purge_expired(path=self._database_path, retention_days=self._retention_days)

    def save(self, result: AnalysisResult) -> None:
        from fraudlens.database import save_case

        save_case(
            result,
            path=self._database_path,
            hmac_secret=self._hmac_secret,
            retention_days=self._retention_days,
        )

    def list_cases(self, limit: int) -> list[dict]:
        from fraudlens.database import list_cases

        return list_cases(limit=limit, path=self._database_path, retention_days=self._retention_days)

    def get_case(self, case_id: str) -> Optional[dict]:
        from fraudlens.database import get_case

        return get_case(case_id, path=self._database_path, retention_days=self._retention_days)

    def delete(self, case_id: str) -> bool:
        from fraudlens.database import delete_case

        return delete_case(case_id, path=self._database_path, retention_days=self._retention_days)

    def clear(self) -> int:
        from fraudlens.database import clear_cases

        return clear_cases(path=self._database_path, retention_days=self._retention_days)

    def entity_graph(
        self, minimum_case_count: int = 2, case_limit: int = 100, max_edges: int = 1_000
    ) -> EntityGraphResult:
        # Validate graph-domain limits before opening storage, then let the
        # graph module perform the actual construction from storage-safe links.
        build_entity_graph(
            (), minimum_case_count=minimum_case_count, max_edges=max_edges
        )
        from fraudlens.database import list_entity_links

        links, source_truncated = list_entity_links(
            path=self._database_path,
            retention_days=self._retention_days,
            minimum_case_count=minimum_case_count,
            case_limit=case_limit,
            edge_limit=max_edges + 1,
        )
        return build_entity_graph(
            links,
            minimum_case_count=minimum_case_count,
            max_edges=max_edges,
            source_truncated=source_truncated,
        )

    def purge_expired(self, now: Optional[datetime] = None) -> int:
        from fraudlens.database import purge_expired

        return purge_expired(path=self._database_path, now=now, retention_days=self._retention_days)


def build_complaint_draft(
    predicted_label: str,
    risk_level: str,
    entities: list[Entity],
    original_text: str,
) -> str:
    if predicted_label.casefold() in {"legitimate", "benign"}:
        return "\n".join(
            [
                "Classification: legitimate",
                "Risk level: {}".format(risk_level),
                "Classifier assessment: no scam indicators from the classifier.",
                "Recommended action: verify through the organisation's official channel if uncertain.",
                "Original message: {}".format(original_text),
            ]
        )

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
        # Dashboard and compatibility callers do not pass through FastAPI, so
        # the service owns this validation boundary as well.
        validated_input = AnalyzeRequest.model_validate(
            {"text": analysis_input.text, "user_notes": analysis_input.user_notes}
        )
        text = validated_input.text
        user_notes = validated_input.user_notes
        cleaned_text = normalize_text(text)
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
                "user_notes": user_notes,
                "stored": False,
            }
        )
        result = AnalysisResult(
            case_id=str(self._id_generator()),
            created_at=self._clock(),
            original_text=text,
            cleaned_text=cleaned_text,
            predicted_label=prediction.label,
            confidence=prediction.confidence,
            risk_level=risk_level,
            risk_score=risk_score,
            entities=entities,
            risk_signals=risk_signals,
            explanation=explanation,
            complaint_draft=build_complaint_draft(prediction.label, risk_level, entities, text),
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


def resolve_predictor(
    settings: Settings,
    predictor: Optional[Predictor] = None,
    predictor_registry: Optional[PredictorRegistry] = None,
) -> Predictor:
    if predictor is not None:
        return predictor
    registry = predictor_registry or default_predictor_registry
    try:
        return registry.get(settings.model_backend)
    except ValueError:
        raise ValueError("Predictor configuration is unavailable") from None


def create_analysis_service(
    settings: Optional[Settings] = None,
    predictor: Optional[Predictor] = None,
    store: Optional[CaseStore] = None,
    predictor_registry: Optional[PredictorRegistry] = None,
) -> AnalysisService:
    resolved_settings = settings or Settings.from_env()
    return AnalysisService(
        predictor=resolve_predictor(resolved_settings, predictor, predictor_registry),
        store=(
            store
            if store is not None
            else DatabaseCaseStore(
                resolved_settings.database_path,
                hmac_secret=resolved_settings.hmac_secret,
                retention_days=resolved_settings.retention_days,
            )
        ),
    )
