import json
from datetime import date, datetime, timezone
from pathlib import Path

from garf.sources.calories import Calories
from garf.sources.heart_rate import HeartRate
from garf.sources.sleep import Sleep
from garf.sources.workouts import Workouts

FIXTURES = Path(__file__).parent / "fixtures"
DAY = date(2026, 6, 1)


def load(name: str):
    return json.loads((FIXTURES / name).read_text())


def test_heart_rate_unnests_pairs_and_skips_nulls():
    rows = HeartRate().transform(load("heart_rates.json"), DAY)
    assert rows == [
        {"ts": datetime(2026, 6, 1, 1, 20, tzinfo=timezone.utc), "metric": "heart_rate", "value": 58.0},
        {"ts": datetime(2026, 6, 1, 1, 22, tzinfo=timezone.utc), "metric": "heart_rate", "value": 61.0},
        {"ts": datetime(2026, 6, 1, 1, 26, tzinfo=timezone.utc), "metric": "heart_rate", "value": 64.0},
    ]


def test_sleep_extracts_score_and_duration():
    rows = Sleep().transform(load("sleep.json"), DAY)
    assert rows == [{"day": DAY, "sleep_score": 82, "sleep_duration_s": 27000}]


def test_calories_extracts_three_columns():
    rows = Calories().transform(load("stats.json"), DAY)
    assert rows == [
        {
            "day": DAY,
            "total_kilocalories": 2450,
            "active_kilocalories": 620,
            "bmr_kilocalories": 1830,
        }
    ]


def test_workouts_maps_activity_to_row():
    rows = Workouts().transform(load("activities.json"), DAY)
    assert rows == [
        {
            "activity_id": 18446744073,
            "activity_type": "running",
            "start_time": datetime(2026, 6, 1, 6, 0, tzinfo=timezone.utc),
            "duration_s": 1830.5,
            "distance_m": 5012.3,
            "calories": 312,
            "avg_hr": 151,
            "max_hr": 176,
        }
    ]


def test_empty_responses_yield_no_rows_or_nulls():
    assert HeartRate().transform(None, DAY) == []
    assert Workouts().transform(None, DAY) == []
    assert Sleep().transform({}, DAY) == [
        {"day": DAY, "sleep_score": None, "sleep_duration_s": None}
    ]
