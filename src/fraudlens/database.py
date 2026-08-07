"""SQLite persistence for consented case history and privacy-safe links."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fraudlens.config import DB_PATH
from fraudlens.privacy import mask_entity, stable_entity_id
from fraudlens.schemas import AnalysisResult


_DEFAULT_HMAC_SECRET = "local-demo-only-secret-not-for-production"
_DEFAULT_RETENTION_DAYS = 30


def _connect(path: Optional[Path] = None) -> sqlite3.Connection:
    database_path = Path(path) if path is not None else DB_PATH
    database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat()


def _parse_utc(value: object) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _model_dump(result: AnalysisResult) -> Dict[str, Any]:
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return json.loads(result.json())


def _add_column_if_missing(conn: sqlite3.Connection, name: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(cases)")}
    if name not in columns:
        conn.execute("ALTER TABLE cases ADD COLUMN {} {}".format(name, definition))


def _migrate_cases(conn: sqlite3.Connection) -> None:
    _add_column_if_missing(conn, "stored_raw_text", "INTEGER NOT NULL DEFAULT 1")
    _add_column_if_missing(conn, "expires_at", "TEXT")
    _add_column_if_missing(conn, "model_version", "TEXT")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS case_entities (
            case_id TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            masked_value TEXT NOT NULL,
            PRIMARY KEY (case_id, entity_type, entity_id),
            FOREIGN KEY (case_id) REFERENCES cases(case_id) ON DELETE CASCADE
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cases_expires_at ON cases(expires_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_case_entities_entity ON case_entities(entity_type, entity_id)")

def init_db(path: Optional[Path] = None, retention_days: int = _DEFAULT_RETENTION_DAYS) -> None:
    """Create and idempotently migrate the local case database."""

    if retention_days <= 0:
        raise ValueError("retention_days must be positive")
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
        _migrate_cases(conn)


def save_case(
    result: AnalysisResult,
    path: Optional[Path] = None,
    hmac_secret: str = _DEFAULT_HMAC_SECRET,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> None:
    """Persist a consented result and opaque entity links as one transaction."""

    init_db(path, retention_days=retention_days)
    payload = _model_dump(result)
    created_at = _utc_iso(result.created_at)
    expires_at = _utc_iso(_parse_utc(created_at) + timedelta(days=retention_days))
    model_version = result.metadata.get("prediction_model_version")
    values = (
        created_at,
        result.original_text,
        result.predicted_label,
        result.confidence,
        result.risk_level,
        result.risk_score,
        json.dumps(payload, ensure_ascii=True),
        1,
        expires_at,
        model_version,
        result.case_id,
    )
    with _connect(path) as conn:
        existing = conn.execute("SELECT 1 FROM cases WHERE case_id = ?", (result.case_id,)).fetchone()
        if existing is None:
            conn.execute(
                """
                INSERT INTO cases
                (case_id, created_at, original_text, predicted_label, confidence, risk_level, risk_score,
                 result_json, stored_raw_text, expires_at, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (result.case_id,) + values[:-1],
            )
        else:
            conn.execute(
                """
                UPDATE cases SET created_at = ?, original_text = ?, predicted_label = ?, confidence = ?,
                risk_level = ?, risk_score = ?, result_json = ?, stored_raw_text = ?, expires_at = ?,
                model_version = ? WHERE case_id = ?
                """,
                values,
            )
            conn.execute("DELETE FROM case_entities WHERE case_id = ?", (result.case_id,))

        for entity in result.entities:
            try:
                entity_id = stable_entity_id(entity.type, entity.value, hmac_secret)
                masked_value = mask_entity(entity.type, entity.value)
            except ValueError:
                continue
            conn.execute(
                """
                INSERT INTO case_entities (case_id, entity_type, entity_id, masked_value)
                VALUES (?, ?, ?, ?)
                """,
                (result.case_id, entity.type.casefold(), entity_id, masked_value),
            )


def _purge_expired(conn: sqlite3.Connection, now: datetime) -> int:
    expired_case_ids = []
    for row in conn.execute("SELECT case_id, expires_at FROM cases WHERE expires_at IS NOT NULL"):
        expires_at = _parse_utc(row["expires_at"])
        if expires_at is not None and expires_at <= now:
            expired_case_ids.append(row["case_id"])
    for case_id in expired_case_ids:
        conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
    return len(expired_case_ids)


def purge_expired(
    path: Optional[Path] = None,
    now: Optional[datetime] = None,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> int:
    init_db(path, retention_days=retention_days)
    reference_time = now or datetime.now(timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)
    else:
        reference_time = reference_time.astimezone(timezone.utc)
    with _connect(path) as conn:
        return _purge_expired(conn, reference_time)


def list_cases(
    limit: int = 20,
    path: Optional[Path] = None,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> List[Dict[str, Any]]:
    purge_expired(path=path, retention_days=retention_days)
    with _connect(path) as conn:
        rows = conn.execute(
            """
            SELECT case_id, created_at, predicted_label, confidence, risk_level, risk_score, expires_at, model_version
            FROM cases ORDER BY created_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_case(
    case_id: str,
    path: Optional[Path] = None,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> Optional[Dict[str, Any]]:
    purge_expired(path=path, retention_days=retention_days)
    with _connect(path) as conn:
        row = conn.execute("SELECT result_json FROM cases WHERE case_id = ?", (case_id,)).fetchone()
    return None if row is None else json.loads(row["result_json"])


def delete_case(
    case_id: str,
    path: Optional[Path] = None,
    retention_days: int = _DEFAULT_RETENTION_DAYS,
) -> bool:
    init_db(path, retention_days=retention_days)
    with _connect(path) as conn:
        cursor = conn.execute("DELETE FROM cases WHERE case_id = ?", (case_id,))
        return cursor.rowcount == 1


def clear_cases(path: Optional[Path] = None, retention_days: int = _DEFAULT_RETENTION_DAYS) -> int:
    init_db(path, retention_days=retention_days)
    with _connect(path) as conn:
        cursor = conn.execute("DELETE FROM cases")
        return cursor.rowcount
