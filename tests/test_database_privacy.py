import json
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from fraudlens.analysis_service import DatabaseCaseStore
from fraudlens.database import list_entity_links
from fraudlens.schemas import AnalysisResult, Entity


def _result(case_id="case-1", created_at=None):
    return AnalysisResult(
        case_id=case_id,
        created_at=created_at or datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc),
        original_text="Call +91 98765 43210 or pay alice@upi. Visit https://login.example.com/reset?token=raw-token",
        cleaned_text="call 9876543210 or pay alice@upi visit https://login.example.com/reset?token=raw-token",
        predicted_label="upi_scam",
        confidence=0.9,
        risk_level="high",
        risk_score=80.0,
        entities=[
            Entity(type="phone", value="9876543210"),
            Entity(type="upi_id", value="alice@upi"),
            Entity(type="email", value="alice@example.com"),
            Entity(type="url", value="https://login.example.com/reset?token=raw-token"),
        ],
        risk_signals=[],
        explanation=["test"],
        complaint_draft="raw complaint text",
        metadata={"prediction_model_version": "test-v2"},
    )


def _store(tmp_path, retention_days=30):
    return DatabaseCaseStore(
        tmp_path / "cases.sqlite3", hmac_secret="unit-test-secret", retention_days=retention_days
    )


def test_initialize_migrates_old_cases_without_losing_them_and_is_idempotent(tmp_path):
    database_path = tmp_path / "cases.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE cases (
                case_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, original_text TEXT NOT NULL,
                predicted_label TEXT NOT NULL, confidence REAL NOT NULL, risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL, result_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("legacy", "2099-01-01T00:00:00+00:00", "legacy raw", "kyc_scam", 0.8, "high", 70, "{}"),
        )

    store = _store(tmp_path)
    store.initialize()
    store.initialize()

    with sqlite3.connect(database_path) as conn:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(cases)")}
        entities_columns = {row[1] for row in conn.execute("PRAGMA table_info(case_entities)")}
        legacy = conn.execute("SELECT stored_raw_text, expires_at, model_version FROM cases WHERE case_id = ?", ("legacy",)).fetchone()
    assert {"stored_raw_text", "expires_at", "model_version"} <= columns
    assert {"case_id", "entity_type", "entity_id", "masked_value"} <= entities_columns
    assert legacy[0] == 1
    assert legacy[1] == "2099-01-31T00:00:00+00:00"
    assert store.get_case("legacy") == {}


def test_migration_removes_expired_or_malformed_legacy_raw_rows(tmp_path):
    database_path = tmp_path / "cases.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE cases (
                case_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, original_text TEXT NOT NULL,
                predicted_label TEXT NOT NULL, confidence REAL NOT NULL, risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL, result_json TEXT NOT NULL,
                stored_raw_text INTEGER NOT NULL DEFAULT 1, expires_at TEXT, model_version TEXT
            )
            """
        )
        rows = [
            ("future", "2099-01-01T00:00:00+00:00", None),
            ("expired", "2000-01-01T00:00:00+00:00", None),
            ("bad-created", "not-a-date", None),
            ("bad-expiry", "2099-01-01T00:00:00+00:00", "not-a-date"),
        ]
        for case_id, created_at, expires_at in rows:
            conn.execute(
                "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, created_at, "legacy raw", "kyc_scam", 0.8, "high", 70, "{}", 1, expires_at, None),
            )

    store = _store(tmp_path)
    store.initialize()
    store.initialize()

    with sqlite3.connect(database_path) as conn:
        remaining = conn.execute("SELECT case_id, expires_at FROM cases").fetchall()
    assert remaining == [("future", "2099-01-31T00:00:00+00:00")]


def test_reducing_retention_clamps_existing_case_expiry(tmp_path):
    database_path = tmp_path / "cases.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute(
            """
            CREATE TABLE cases (
                case_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, original_text TEXT NOT NULL,
                predicted_label TEXT NOT NULL, confidence REAL NOT NULL, risk_level TEXT NOT NULL,
                risk_score REAL NOT NULL, result_json TEXT NOT NULL,
                stored_raw_text INTEGER NOT NULL DEFAULT 1, expires_at TEXT, model_version TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "future",
                "2099-01-01T00:00:00+00:00",
                "legacy raw",
                "kyc_scam",
                0.8,
                "high",
                70,
                "{}",
                1,
                "2099-01-31T00:00:00+00:00",
                None,
            ),
        )

    _store(tmp_path, retention_days=7).initialize()

    with sqlite3.connect(database_path) as conn:
        expiry = conn.execute(
            "SELECT expires_at FROM cases WHERE case_id = ?", ("future",)
        ).fetchone()[0]
    assert expiry == "2099-01-08T00:00:00+00:00"


def test_saved_cases_persist_raw_result_only_in_case_record_and_masked_entities(tmp_path):
    store = _store(tmp_path)
    store.save(_result())

    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        case = conn.execute(
            "SELECT original_text, stored_raw_text, result_json, expires_at, model_version FROM cases WHERE case_id = ?",
            ("case-1",),
        ).fetchone()
        entities = conn.execute(
            "SELECT entity_type, entity_id, masked_value FROM case_entities WHERE case_id = ?", ("case-1",)
        ).fetchall()

    assert case[1] == 1
    assert case[0] == _result().original_text
    assert json.loads(case[2])["original_text"] == case[0]
    assert case[3] == "2026-09-06T12:00:00+00:00"
    assert case[4] == "test-v2"
    serialized_entities = repr(entities)
    for raw_value in ("9876543210", "alice@upi", "alice@example.com", "https://login.example.com/reset?token=raw-token"):
        assert raw_value not in serialized_entities
    assert {row[0] for row in entities} == {"phone", "upi_id", "email", "url"}


def test_save_rejects_an_already_expired_result_without_persisting_raw_data(tmp_path):
    store = _store(tmp_path, retention_days=1)
    store.save(_result("stale", datetime(2099, 1, 1, tzinfo=timezone.utc)))
    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        conn.execute("UPDATE cases SET expires_at = ? WHERE case_id = ?", ("2000-01-01T00:00:00+00:00", "stale"))

    with pytest.raises(ValueError, match="already expired"):
        store.save(_result("expired", datetime(2000, 1, 1, tzinfo=timezone.utc)))

    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM case_entities").fetchone()[0] == 0


@pytest.mark.parametrize(
    ("duplicate_entities", "expected_mask"),
    [
        (
            [
                Entity(type="email", value="Alice@Example.COM"),
                Entity(type="email", value="alice@example.com"),
            ],
            "a***@example.com",
        ),
        (
            [
                Entity(type="url", value="https://login.example.com/reset#first"),
                Entity(type="url", value="https://login.example.com/reset#second"),
            ],
            "login.example.com",
        ),
    ],
)
def test_save_deduplicates_entities_with_the_same_canonical_identity(
    tmp_path, duplicate_entities, expected_mask
):
    store = _store(tmp_path)
    result = _result()
    result.entities = duplicate_entities

    store.save(result)

    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        rows = conn.execute(
            "SELECT entity_type, entity_id, masked_value FROM case_entities WHERE case_id = ?",
            (result.case_id,),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][2] == expected_mask


def test_save_rolls_back_case_when_an_entity_insert_fails(tmp_path):
    store = _store(tmp_path)
    store.initialize()
    store.save(_result("expired", datetime(2099, 1, 1, tzinfo=timezone.utc)))
    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        conn.execute("UPDATE cases SET expires_at = ? WHERE case_id = ?", ("2000-01-01T00:00:00+00:00", "expired"))
        conn.execute(
            """CREATE TRIGGER reject_entities BEFORE INSERT ON case_entities
            WHEN NEW.entity_type = 'email' BEGIN SELECT RAISE(ABORT, 'reject'); END"""
        )

    with pytest.raises(sqlite3.IntegrityError):
        store.save(_result(created_at=datetime(2099, 1, 1, tzinfo=timezone.utc)))

    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        assert conn.execute("SELECT case_id FROM cases").fetchall() == [("expired",)]
        assert conn.execute("SELECT COUNT(*) FROM case_entities").fetchone()[0] == 4


def test_delete_clear_and_case_id_sql_injection_are_safe(tmp_path):
    store = _store(tmp_path)
    store.save(_result("case-1"))
    store.save(_result("case-2"))

    assert store.delete("case-1' OR 1=1 --") is False
    assert len(store.list_cases(10)) == 2
    assert store.delete("case-1") is True
    assert store.delete("case-1") is False
    assert store.clear() == 1
    assert store.list_cases(10) == []


def test_save_purges_expired_raw_cases_without_a_list_or_get_request(tmp_path):
    store = _store(tmp_path, retention_days=1)
    store.save(_result("expired", datetime(2099, 1, 1, tzinfo=timezone.utc)))
    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        conn.execute("UPDATE cases SET expires_at = ? WHERE case_id = ?", ("2000-01-01T00:00:00+00:00", "expired"))

    store.save(_result("active", datetime(2099, 1, 2, tzinfo=timezone.utc)))

    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        case_ids = [row[0] for row in conn.execute("SELECT case_id FROM cases ORDER BY case_id")]
    assert case_ids == ["active"]


def test_purge_expired_uses_an_inclusive_utc_boundary_and_deletes_malformed_expiry(tmp_path):
    store = _store(tmp_path, retention_days=1)
    created_at = datetime(2099, 1, 1, 12, 0, tzinfo=timezone.utc)
    store.save(_result("expires-now", created_at))
    store.save(_result("later", created_at + timedelta(seconds=1)))
    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        conn.execute("UPDATE cases SET expires_at = ? WHERE case_id = ?", ("not-a-date", "later"))

    assert store.purge_expired(datetime(2099, 1, 2, 12, 0, tzinfo=timezone.utc)) == 2
    assert store.list_cases(10) == []


def test_entity_graph_returns_only_retained_consented_rows_and_safe_link_fields(tmp_path):
    store = _store(tmp_path)
    first = _result("case-1", datetime(2099, 1, 1, tzinfo=timezone.utc))
    second = _result("case-2", datetime(2099, 1, 2, tzinfo=timezone.utc))
    expired = _result("expired", datetime(2099, 1, 3, tzinfo=timezone.utc))
    store.save(first)
    store.save(second)
    store.save(expired)
    database_path = tmp_path / "cases.sqlite3"
    with sqlite3.connect(database_path) as conn:
        conn.execute("UPDATE cases SET result_json = ? WHERE case_id = ?", ('{"raw":"leak-me"}', "case-1"))
        conn.execute("UPDATE cases SET expires_at = ? WHERE case_id = ?", ("not-a-date", "expired"))

    links, truncated = list_entity_links(path=database_path)

    assert truncated is False
    assert {link.case_id for link in links} == {"case-1", "case-2"}
    assert set(links[0].__dataclass_fields__) == {
        "case_id",
        "created_at",
        "predicted_label",
        "risk_level",
        "risk_score",
        "entity_type",
        "entity_id",
        "masked_value",
    }
    serialized_links = repr(links)
    assert "leak-me" not in serialized_links
    assert first.original_text not in serialized_links
    assert "unit-test-secret" not in serialized_links
    with sqlite3.connect(database_path) as conn:
        assert conn.execute("SELECT case_id FROM cases ORDER BY case_id").fetchall() == [
            ("case-1",),
            ("case-2",),
        ]


def test_entity_graph_deletion_and_clear_remove_retained_links(tmp_path):
    store = _store(tmp_path)
    first = _result("case-1", datetime(2099, 1, 1, tzinfo=timezone.utc))
    second = _result("case-2", datetime(2099, 1, 2, tzinfo=timezone.utc))
    first.predicted_label = second.predicted_label = "kyc_scam"
    store.save(first)
    store.save(second)

    assert store.entity_graph().summary.edge_count == 8
    assert store.delete("case-1") is True
    assert store.entity_graph().summary.edge_count == 0
    assert store.clear() == 1
    assert store.entity_graph().summary.edge_count == 0


def test_entity_graph_survives_repeat_database_initialization_and_migration(tmp_path):
    store = _store(tmp_path)
    first = _result("case-1", datetime(2099, 1, 1, tzinfo=timezone.utc))
    second = _result("case-2", datetime(2099, 1, 2, tzinfo=timezone.utc))
    first.predicted_label = second.predicted_label = "kyc_scam"
    store.save(first)
    store.save(second)

    store.initialize()
    store.initialize()

    assert store.entity_graph().summary.edge_count == 8


def test_entity_links_use_full_recent_case_set_for_repetition_before_edge_limit(tmp_path):
    store = _store(tmp_path)
    for index in range(101):
        store.save(_result("case-{:03d}".format(index), datetime(2099, 1, 1, tzinfo=timezone.utc)))

    links, truncated = list_entity_links(
        path=tmp_path / "cases.sqlite3",
        minimum_case_count=2,
        case_limit=100,
        edge_limit=2,
    )

    assert truncated is True
    assert [link.case_id for link in links] == ["case-000", "case-000"]
    assert {link.entity_type for link in links} == {"email", "phone"}


def test_entity_link_case_selection_is_bounded_and_deterministic_by_case_id(tmp_path):
    store = _store(tmp_path)
    for index in range(101):
        result = _result("case-{:03d}".format(index), datetime(2099, 1, 1, tzinfo=timezone.utc))
        result.entities = [Entity(type="phone", value="9876543210")]
        store.save(result)

    links, truncated = list_entity_links(
        path=tmp_path / "cases.sqlite3", case_limit=100, edge_limit=101
    )

    assert truncated is True
    assert [link.case_id for link in links] == ["case-{:03d}".format(index) for index in range(100)]


def test_entity_link_case_selection_orders_legacy_offsets_by_utc_instant(tmp_path):
    store = _store(tmp_path)
    for case_id in ("newest", "middle", "oldest"):
        result = _result(case_id, datetime(2099, 1, 1, tzinfo=timezone.utc))
        result.entities = [Entity(type="phone", value="9876543210")]
        store.save(result)
    with sqlite3.connect(tmp_path / "cases.sqlite3") as conn:
        conn.executemany(
            "UPDATE cases SET created_at = ? WHERE case_id = ?",
            [
                ("2099-01-01T00:30:00+00:00", "newest"),
                ("2099-01-01T00:15:00+00:00", "middle"),
                ("2099-01-01T01:00:00+01:00", "oldest"),
            ],
        )

    links, truncated = list_entity_links(
        path=tmp_path / "cases.sqlite3", case_limit=2, edge_limit=3
    )

    assert truncated is True
    assert [link.case_id for link in links] == ["newest", "middle"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"retention_days": 0},
        {"retention_days": "30"},
        {"retention_days": True},
        {"minimum_case_count": 1},
        {"minimum_case_count": "2"},
        {"minimum_case_count": True},
        {"case_limit": 101},
        {"case_limit": "100"},
        {"case_limit": True},
        {"edge_limit": 1002},
        {"edge_limit": "1001"},
        {"edge_limit": True},
    ],
)
def test_entity_link_invalid_bounds_fail_before_sql(tmp_path, monkeypatch, kwargs):
    import fraudlens.database as database

    monkeypatch.setattr(database, "_connect", lambda *args, **kw: pytest.fail("SQL was reached"))

    with pytest.raises(ValueError):
        list_entity_links(path=tmp_path / "cases.sqlite3", **kwargs)
