from typing import Sequence

from sqlalchemy import Engine, create_engine
from sqlalchemy.dialects.postgresql import insert

from garf.models import metadata


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
    table = metadata.tables[table_name]
    stmt = insert(table).values(list(rows))
    cols = update_columns or [
        c.name for c in table.columns if c.name not in conflict_keys
    ]
    return stmt.on_conflict_do_update(
        index_elements=conflict_keys,
        set_={c: stmt.excluded[c] for c in cols},
    )


def upsert(
    engine: Engine,
    table_name: str,
    conflict_keys: list[str],
    update_columns: list[str] | None,
    rows: Sequence[dict],
) -> int:
    if not rows:
        return 0
    stmt = build_upsert_stmt(table_name, conflict_keys, update_columns, rows)
    with engine.begin() as conn:
        conn.execute(stmt)
    return len(rows)
