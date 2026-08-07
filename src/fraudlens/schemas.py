from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=20_000, description="Suspicious message or complaint text")
    user_notes: Optional[str] = Field(default=None, max_length=2_000, description="Optional user context")

    @field_validator("text", mode="before")
    @classmethod
    def trim_and_validate_text(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("text must not be blank")
        return trimmed

    @field_validator("user_notes", mode="before")
    @classmethod
    def trim_user_notes(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        trimmed = value.strip()
        return trimmed or None


class Entity(BaseModel):
    type: str
    value: str
    confidence: float = 1.0
    source: str = "regex"


class RiskSignal(BaseModel):
    name: str
    score: float
    reason: str
    evidence: Optional[str] = None


class AnalysisResult(BaseModel):
    case_id: str
    created_at: datetime
    original_text: str
    cleaned_text: str
    predicted_label: str
    confidence: float
    risk_level: str
    risk_score: float
    entities: List[Entity]
    risk_signals: List[RiskSignal]
    explanation: List[str]
    complaint_draft: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
