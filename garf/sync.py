from ast import Call
import argparse
import time
from datetime import date, timedelta, datetime
from typing import Any, Callable, Iterable


from yaspin import yaspin, Spinner
from garf.client import build_client
from garf.config import Config
from garf.db import make_engine, upsert, read, ValidWhereKey
from garf.sources import REGISTRY
from garf.sources.base import Source

Writer = Callable[[Source, list[dict]], None]
Reader = Callable[[Source, date | datetime], list[dict]]


def daterange(start: date, end: date) -> list[date]:
    days = (end - start).days
    return [start + timedelta(days=i) for i in range(days + 1)]


def trailing_window(today: date, n: int) -> list[date]:
    return daterange(today - timedelta(days=n - 1), today)


def run_sync(
    client: Any,
    sources: Iterable[Source],
    days: list[date],
    writer: Writer,
    reader: Reader | None = None,
    sleep_s: float = 1.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    sparse: bool = False,
) -> None:

    # check or create database table
    run_spinner = Spinner(
        ["🏃‍♀️‍➡️", ".🏃‍♀️‍➡️", "..🏃‍♀️‍➡️", "...🏃‍♀️‍➡️", "...🏃‍♀️", "..🏃‍♀️", ".🏃‍♀️", "🏃‍♀️"], 200
    )
    with yaspin(run_spinner, "getting data"):
        for day in days:
            for src in sources:
                if (
                    sparse
                    and reader is not None
                    and reader(src, day)
                    and all(
                        v is not None for row in reader(src, day) for v in row.values()
                    )
                ):
                    continue
                else:
                    raw = src.fetch(client, day)
                    writer(src, src.transform(raw, day))
                    sleep_fn(sleep_s)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="garf-sync")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("sync", help="re-pull the trailing window (default)")
    bf = sub.add_parser("backfill", help="pull an explicit inclusive date range")
    bf.add_argument("start", type=date.fromisoformat)
    bf.add_argument("end", type=date.fromisoformat)
    bf.add_argument("-s", "--sparse", help="Don't pull data already in the database")

    args = parser.parse_args(argv)

    config = Config.from_env()
    engine = make_engine(config.database_url)
    client = build_client(config)

    def writer(src: Source, rows: list[dict]) -> None:
        upsert(engine, src.table, src.conflict_keys, src.update_columns, rows)

    def reader(src: Source, day_or_time: date | datetime) -> list[dict]:
        if src.update_columns is not None:
            result = read(engine, src.table, src.update_columns, src, day_or_time)
            # print(result)
            return result
        return []

    if args.command == "backfill":
        days = daterange(args.start, args.end)
    else:
        days = trailing_window(date.today(), config.trailing_days)

    run_sync(client, REGISTRY, days, writer, reader, sparse=args.sparse)


if __name__ == "__main__":
    main()
