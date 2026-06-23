import os
from garminconnect import Garmin
from datetime import date

import pytest

from garf.client import build_client
from garf.config import Config
from garf.sources import REGISTRY
from garf.sources.base import Source
from garf.sync import daterange, run_sync

from tests.test_sync import ALWAYS_SOME_READER

ENABLE_LIVE_TEST = False


@pytest.mark.skipif(not ENABLE_LIVE_TEST, reason="live API test disabled")
def test_all_real_sources():
    """Smoke test: fetch 3 days of all sources and print rows to stdout."""
    config = Config.from_env()
    # os.environ[]
    client = build_client(config)
    # client: Garmin = Garmin()

    days = daterange(date(2026, 6, 17), date(2026, 6, 19))

    def stdout_writer(source: Source, rows: list[dict]) -> None:
        print(f"[{source.table}] {len(rows)} rows")
        for row in rows:
            print(" ", row)
            assert row is not None

    run_sync(
        client, REGISTRY, days, stdout_writer, lambda s, d: []
    )  # assumes !t.e data


@pytest.mark.skipif(not ENABLE_LIVE_TEST, reason="live API test disabled")
def test_partial_fill_live(): ...
