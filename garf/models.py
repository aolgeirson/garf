from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
)


class Models:
    """Namespace for the database schema. Used like a C++ namespace —
    access via `Models.metadata`, `Models.metric_samples`, etc.
    Not intended to be instantiated."""

    def __init__():
        raise NotImplementedError

    metadata = MetaData()

    # Intraday time series. Narrow/long so new metrics need no migration.
    # Becomes a TimescaleDB hypertable on `ts` (see first Alembic migration).
    metric_samples = Table(
        "metric_samples",
        metadata,
        Column("ts", DateTime(timezone=True), primary_key=True, nullable=False),
        Column("metric", String, primary_key=True, nullable=False),
        Column("value", Float, nullable=False),
    )

    # One row per day; each source upserts only the columns it owns.
    daily_summary = Table(
        "daily_summary",
        metadata,
        Column("day", Date, primary_key=True, nullable=False),
        Column("resting_hr", Integer),
        Column("sleep_score", Integer),
        Column("sleep_duration_s", Integer),
        Column("total_kilocalories", Integer),
        Column("active_kilocalories", Integer),
        Column("bmr_kilocalories", Integer),
    )

    # One row per Garmin activity.
    workouts = Table(
        "workouts",
        metadata,
        Column(
            "activity_id",
            BigInteger,
            primary_key=True,
            autoincrement=False,
            nullable=False,
        ),
        Column("activity_type", String),
        Column("start_time", DateTime(timezone=True), nullable=False),
        Column("duration_s", Numeric),
        Column("distance_m", Numeric),
        Column("calories", Integer),
        Column("avg_hr", Integer),
        Column("max_hr", Integer),
    )
