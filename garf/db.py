from garf.sources.base import (
    Source,
    DailySummarySource,
    InstantBasedSource,
    DayBasedSource,
)
from enum import auto, StrEnum
from datetime import date, tzinfo, datetime, timezone, time, timedelta
from typing import Sequence, Any

from sqlalchemy import Engine, create_engine, select
from sqlalchemy.dialects.postgresql import insert


from garf.models import Models


def make_engine(url: str) -> Engine:
    return create_engine(url)


def build_upsert_stmt(
    table_name: str,
    conflict_keys: list[str],
    update_columns: list[str] | None,
    rows: Sequence[dict],
):
    """INSERT ... ON CONFLICT DO UPDATE for `rows`. When update_columns is None,
    every non-key column is refreshed; otherwise only the named columns (lets
    several sources own disjoint columns of the same daily row)."""
    table = Models.metadata.tables[table_name]
    stmt = insert(table).values(list(rows))
    cols = update_columns or [
        c.name for c in table.columns if c.name not in conflict_keys
    ]
    return stmt.on_conflict_do_update(
        index_elements=conflict_keys,
        set_={c: stmt.excluded[c] for c in cols},
    )


# Note that this method checks for tables existing
# Non-op if table exists
def build_hypertable(engine: Engine):
    with engine.begin() as conn:
        Models.metric_samples.create(conn, checkfirst=True)
        Models.daily_summary.create(conn, checkfirst=True)
        Models.workouts.create(conn, checkfirst=True)


class ValidWhereKey(StrEnum):
    DAY = "day"
    TIMESTAMP = "ts"
    ACTIVITY_ID = "activity_id"


def read(
    engine: Engine,
    table_name: str,
    update_columns: list[str],
    src: Source,
    inst: date | datetime,
) -> list[dict]:
    # SELECT the list of rows WHERE where_key_type IS where_key
    table = Models.metadata.tables[table_name]
    if isinstance(src, InstantBasedSource):
        stmt = select(*[table.c[col] for col in update_columns]).where(
            table.c[src.time_key] == inst
        )

    elif isinstance(src, DayBasedSource):
        start = datetime.combine(inst, time.min, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        stmt = select(*[table.c[col] for col in update_columns]).where(
            table.c[src.day_key] < end, table.c[src.day_key] >= start
        )
    else:
        raise NotImplementedError

    with engine.begin() as conn:
        return [dict(row) for row in conn.execute(stmt).mappings().all()]


# Update or insert. Creates the target table from the SQLAlchemy schema if it
# doesn't already exist. Caveat: this only creates the plain table — for
# metric_samples the Timescale create_hypertable(...) call still lives in the
# Alembic migration, so running upsert against a fresh DB skips that conversion.
def upsert(
    engine: Engine,
    table_name: str,
    conflict_keys: list[str],
    update_columns: list[str] | None,
    rows: Sequence[dict],
) -> int:
    if not rows:
        return 0

    table = Models.metadata.tables[table_name]
    stmt = build_upsert_stmt(table_name, conflict_keys, update_columns, rows)
    with engine.begin() as conn:
        table.create(conn, checkfirst=True)
        conn.execute(stmt)
    return len(rows)
