from garf.sources.base import Source
from datetime import date

from garf.sync import daterange, run_sync, trailing_window


# This should block somthing from being written as it lies that t.e data already
def ALWAYS_SOME_READER(_: Source, _2: date) -> list[dict]:
    return [{"thing": "yep"}]


def test_daterange_is_inclusive():
    assert daterange(date(2026, 6, 1), date(2026, 6, 3)) == [
        date(2026, 6, 1),
        date(2026, 6, 2),
        date(2026, 6, 3),
    ]


def test_trailing_window_includes_today_and_n_minus_1_prior():
    assert trailing_window(date(2026, 6, 5), 3) == [
        date(2026, 6, 3),
        date(2026, 6, 4),
        date(2026, 6, 5),
    ]


class FakeSource:
    table = "metric_samples"
    conflict_keys = ["metric", "ts"]
    update_columns = None

    def __init__(self):
        self.fetched = []

    def fetch(self, client, day):
        self.fetched.append(day)
        return {"day": day}

    def transform(self, raw, day):
        return [{"metric": "x", "ts": day, "value": 1.0}]


def test_run_sync_fetches_each_source_per_day_and_writes():
    src = FakeSource()
    writes = []

    run_sync(
        client=object(),
        sources=[src],
        days=[date(2026, 6, 1), date(2026, 6, 2)],
        writer=lambda s, rows: writes.append((s.table, rows)),
        sleep_s=0.0,
        reader=lambda s, day: [],  # Assumes t.e no data
    )

    assert src.fetched == [date(2026, 6, 1), date(2026, 6, 2)]
    assert writes == [
        ("metric_samples", [{"metric": "x", "ts": date(2026, 6, 1), "value": 1.0}]),
        ("metric_samples", [{"metric": "x", "ts": date(2026, 6, 2), "value": 1.0}]),
    ]


def test_partial_fill():
    src = FakeSource()
    writes = []

    run_sync(
        client=object(),
        sources=[src],
        days=[date(2026, 6, 1), date(2026, 6, 2)],
        writer=lambda s, rows: writes.append((s.table, rows)),
        sleep_s=0.0,
        reader=ALWAYS_SOME_READER,
    )
    assert writes == []
