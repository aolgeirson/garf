import os

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.dialects import postgresql

from garf.db import build_upsert_stmt, upsert
from garf.models import metric_samples


def compiled(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect())).upper()


def test_metric_samples_upsert_targets_pk_and_updates_value():
    stmt = build_upsert_stmt(
        "metric_samples",
        ["metric", "ts"],
        None,
        [{"ts": "2026-06-01T00:00:00Z", "metric": "heart_rate", "value": 58.0}],
    )
    sql = compiled(stmt)
    assert "ON CONFLICT (METRIC, TS) DO UPDATE" in sql
    assert "VALUE =" in sql


def test_daily_summary_upsert_only_updates_owned_columns():
    stmt = build_upsert_stmt(
        "daily_summary",
        ["day"],
        ["sleep_score", "sleep_duration_s"],
        [{"day": "2026-06-01", "sleep_score": 82, "sleep_duration_s": 27000}],
    )
    sql = compiled(stmt)
    assert "ON CONFLICT (DAY) DO UPDATE" in sql
    assert "SLEEP_SCORE =" in sql
    assert "TOTAL_KILOCALORIES" not in sql


# Round-trip against a real TimescaleDB. Skipped unless GARF_TEST_DATABASE_URL is set.
DB_URL = os.environ.get("GARF_TEST_DATABASE_URL")


@pytest.mark.skipif(not DB_URL, reason="no GARF_TEST_DATABASE_URL")
def test_upsert_is_idempotent_round_trip():
    engine = create_engine(DB_URL)
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
        metric_samples.drop(conn, checkfirst=True)
        metric_samples.create(conn)

    row = [{"ts": "2026-06-01T00:00:00+00:00", "metric": "heart_rate", "value": 58.0}]
    upsert(engine, "metric_samples", ["metric", "ts"], None, row)
    upsert(engine, "metric_samples", ["metric", "ts"], None, row)  # second run = no dupe

    with engine.connect() as conn:
        count = conn.execute(select(metric_samples)).fetchall()
    assert len(count) == 1
