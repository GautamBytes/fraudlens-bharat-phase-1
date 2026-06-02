from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Suspicious message or complaint text")
    user_notes: Optional[str] = Field(default=None, description="Optional user context")


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

