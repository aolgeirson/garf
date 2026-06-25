# Three source types write to three tables:
#
#   TimeSeriesSource  → metric_samples (ts, metric, value)
#     Set metric, client_method, value_key. No subclassing needed.
#     Example: HeartRate in heart_rate.py
#
#   DailySummarySource → daily_summary (one row per day, sparse columns)
#     Set client_method and update_columns; implement extract(raw) → {col: val}.
#     Also add the column to Models.daily_summary in models.py.
#     Example: Calories in calories.py
#
#   WorkoutSource → workouts (one row per activity)
#     Implement extract_activity(activity) → row dict.
#     Example: Workouts in workouts.py
#
# Register every new source in sources/__init__.py REGISTRY.

from abc import ABC, abstractmethod
from datetime import date, datetime, timezone
from typing import Any


class Source(ABC):
    """A single Garmin data stream: how to fetch it for a day and turn the raw
    response into table rows. The sync loop drives every source per-day."""

    table: str
    conflict_keys: list[str]
    # Columns to overwrite on conflict. None => every non-key column.
    update_columns: list[str] | None = None

    @abstractmethod
    def fetch(self, client: Any, day: date) -> Any: ...

    @abstractmethod
    def transform(self, raw: Any, day: date) -> list[dict]: ...


class DayBasedSource(ABC):
    day_key: str


class InstantBasedSource(ABC):
    time_key: str


class TimeSeriesSource(Source, InstantBasedSource):
    """Intraday samples → metric_samples. Garmin returns arrays of
    [epoch_millis, value]; we unnest them into (ts, metric, value) rows."""

    table = "metric_samples"
    conflict_keys = ["metric", "ts"]
    day_key = "ts"

    metric: str
    client_method: str
    value_key: str

    def fetch(self, client: Any, day: date) -> Any:
        return getattr(client, self.client_method)(day.isoformat())

    def transform(self, raw: Any, day: date) -> list[dict]:
        pairs = (raw or {}).get(self.value_key) or []
        rows = []
        for ts_ms, value in pairs:
            if value is None:
                continue
            rows.append(
                {
                    "ts": datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc),
                    "metric": self.metric,
                    "value": float(value),
                }
            )
        return rows


class DailySummarySource(Source, DayBasedSource):
    """Daily scalars → daily_summary. Each source owns a subset of columns and
    upserts only those for the day."""

    table = "daily_summary"
    conflict_keys = ["day"]

    day_key = "day"
    client_method: str

    def fetch(self, client: Any, day: date) -> Any:
        return getattr(client, self.client_method)(day.isoformat())

    @abstractmethod
    def extract(self, raw: dict) -> dict:
        """Map a raw response to {column: value} for the owned columns."""

    def transform(self, raw: Any, day: date) -> list[dict]:
        return [{"day": day, **self.extract(raw or {})}]


class WorkoutSource(Source, InstantBasedSource):
    """Activities → workouts. Fetched per-day via a single-date range so the
    sync loop stays uniform with the daily sources."""

    day_key = "start_time"
    table = "workouts"
    conflict_keys = ["activity_id"]

    def fetch(self, client: Any, day: date) -> Any:
        return client.get_activities_by_date(day.isoformat(), day.isoformat())

    @abstractmethod
    def extract_activity(self, activity: dict) -> dict:
        """Map one raw activity dict to a workouts row."""

    def transform(self, raw: Any, day: date) -> list[dict]:
        return [self.extract_activity(a) for a in (raw or [])]
