import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fraudlens.config import DB_PATH
from fraudlens.schemas import AnalysisResult


def _connect(path: Optional[Path] = None) -> sqlite3.Connection:
    database_path = Path(path) if path is not None else DB_PATH
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path: Optional[Path] = None) -> None:
    with _connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cases (
                case_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                original_text TEXT NOT NULL,
                predicted_label TEXT NOT NULL,
                confidence REAL NOT NULL,
                risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _model_dump(result: AnalysisResult) -> Dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return json.loads(result.json())


def save_case(result: AnalysisResult, path: Optional[Path] = None) -> None:
    init_db(path)
    payload = _model_dump(result)
    with _connect(path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO cases
            (case_id, created_at, original_text, predicted_label, confidence, risk_level, risk_score, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.case_id,
                result.created_at.isoformat(),
                result.original_text,
                result.predicted_label,
                result.confidence,
                result.risk_level,
                result.risk_score,
                json.dumps(payload, ensure_ascii=True),
            ),
        )
        conn.commit()


def list_cases(limit: int = 20, path: Optional[Path] = None) -> List[Dict[str, Any]]:
    init_db(path)
    with _connect(path) as conn:
        rows = conn.execute(
            """
            SELECT case_id, created_at, predicted_label, confidence, risk_level, risk_score
            FROM cases
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_case(case_id: str, path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    init_db(path)
    with _connect(path) as conn:
        row = conn.execute("SELECT result_json FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row["result_json"])


def clear_cases(path: Optional[Path] = None) -> None:
    init_db(path)
    with _connect(path) as conn:
        conn.execute("DELETE FROM cases")
        conn.commit()
