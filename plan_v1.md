# garf — Plan v1 (revised)

> Revision of `plan_v0.md`. Original intent preserved; my additions are marked
> **[suggestion]**, **[note]**, or **[question]**. Open questions are collected
> at the bottom so you can answer them in one pass.

# Abstract
Bridge from Garmin Connect to Grafana to visualize and analyze health/fitness
data beyond what the Garmin Connect app offers. Start small, build to extend.

# Architecture
```
garf (python) ──pull──> Garmin Connect API
   │
   └──write──> PostgreSQL / TimescaleDB ──read──> Grafana
```

- `garf` pulls via the `garminconnect` library, transforms, and upserts into Postgres.
- Grafana reads Postgres directly (no API layer in between).
- Postgres/TimescaleDB and Grafana run in **separate** Docker stacks (Grafana is
  shared across projects, single instance).

**[note] On the data source library (`garminconnect` 0.3.5):**
- It's an *unofficial* scraper of Garmin's private web API. There is no official
  API. Expect occasional breakage when Garmin changes endpoints, and expect
  **rate limiting / throttling** on bulk requests.
- Auth uses `garth` (OAuth token store) under the hood. Pattern:
  `Garmin(email, pw, prompt_mfa=...)` then `client.login(tokenstore="~/.garminconnect")`.
  First run logs in (+MFA); later runs reuse/refresh saved tokens. So password is
  only needed for the initial token mint — fits your "I'll handle auth" note.
- It is **synchronous** (curl-cffi/requests). Fine for a daily cron; matters if you
  ever backfill years of data (do it serially with sleeps, not concurrently).
- Almost every daily endpoint is **per-single-date**: `get_heart_rates(date)`,
  `get_hrv_data(date)`, `get_stress_data(date)`, `get_sleep_data(date)`,
  `get_steps_data(date)`, `get_respiration_data(date)`, `get_body_battery(start,end)`,
  `get_stats(date)`. Activities are range-based: `get_activities_by_date(start, end, type)`.

**[note] Shape of the data — this drives the schema.** Intraday metrics come back
as arrays of `[epoch_millis, value]` pairs nested inside the daily response (e.g.
`get_heart_rates(d)["heartRateValues"]`). HRV/sleep are per-night summaries plus
nested arrays. So "time series" really splits into two shapes:
1. **Intraday samples** — many rows/day (HR every ~2 min, stress, body battery, respiration).
2. **Daily scalars** — one row/day (resting HR, sleep score, HRV status, steps total, VO2max).

# Schema

**[suggestion] Three logical groups instead of two:**

1. `metric_samples` — intraday time series (the "one table" you described).
   Long/narrow design so new metric types need **no migration**:
   ```
   metric_samples(
     ts          timestamptz not null,   -- stored UTC
     metric      text       not null,    -- 'heart_rate' | 'stress' | 'body_battery' | ...
     value       double precision not null,
     primary key (metric, ts)
   )
   ```
   - **[suggestion]** If TimescaleDB: make this a hypertable partitioned on `ts`.
   - **[question]** Long/narrow (above) vs wide (`ts, hr, stress, spo2, ...`)? Narrow is
     more extensible and Grafana-friendly (`WHERE metric=$x`); wide is easier to
     read raw and avoids type coercion. I lean narrow given your "build to extend" goal.

2. `daily_summary` — one row per (date, …): resting HR, HRV status, sleep score,
   steps, floors, intensity minutes, VO2max, training readiness, etc. These are
   genuinely columnar (fixed set), so a wide table is fine here.

3. `workouts` — one row per activity (id, type, start, duration, distance, calories,
   avg/max HR, …). **[suggestion]** Optionally `workout_samples` later for per-activity
   intraday traces (splits, HR-in-zones) — defer until needed.

**[suggestion] Idempotency is essential.** Daily re-syncs and backfills will
re-fetch overlapping dates. Use `INSERT ... ON CONFLICT (...) DO UPDATE` (upsert)
keyed on natural keys (`(metric, ts)`, `(date)`, `activity_id`). This makes re-runs safe.

**[suggestion] Timezones/units.** Garmin returns epoch-millis (UTC) with separate
local-offset fields. Store everything as `timestamptz` in UTC; let Grafana handle
display tz. Pick a unit convention (metric vs imperial) and normalize on write —
`get_unit_system()` tells you the account default.

# File structure & OOP

**[suggestion] A small "metric definition" abstraction makes the whole thing
extensible and maps cleanly onto your requested base classes.** Each data type
owns: which endpoint to call, how to transform the raw response into rows, and
which table it targets. A registry drives a generic sync loop, so adding a metric
= add one subclass.

```
garf/
  __init__.py
  config.py            # env: DATABASE_URL, GC creds, tokenstore path
  client.py            # thin wrapper around garminconnect (auth placeholder)
  db.py                # connection + upsert helpers
  sync.py              # orchestration: dates -> sources -> rows -> db
  sources/
    base.py            # TimeSeriesSource (ABC), WorkoutSource (ABC)
    heart_rate.py      # class HeartRate(TimeSeriesSource)
    stress.py
    sleep.py
    workouts.py
    __init__.py        # REGISTRY = [...]
  tests/
    fixtures/          # captured JSON responses (mock the API)
```

### Required base classes (as you asked)
- `TimeSeriesSource` (ABC): `endpoint(date) -> raw`, `transform(raw) -> list[Row]`,
  `metric`/`table` attrs.
- `WorkoutSource` (ABC): same idea, range-based fetch + activity-row transform.
- Concrete variants subclass these. The sync loop just iterates the registry.

**[question]** Are you set on a hand-rolled DB layer, or open to `SQLAlchemy`
(ORM or Core)? ORM gives you model classes "for free" and pairs with Alembic
migrations; raw `psycopg` (v3) is lighter and keeps SQL explicit. My lean for a
small, extensible project: **psycopg3 + SQLAlchemy Core** (typed tables, no ORM
session overhead) — but ORM is reasonable if you want model objects.

# Sync / orchestration

**[suggestion]** Two modes:
- `backfill <start> <end>` — serial, throttled (sleep between dates) to respect Garmin limits.
- `daily` (default) — sync yesterday/today; idempotent so safe to cron.

**[suggestion]** Track `last_synced_date` (small state table or file) so daily runs
know where to resume. **[question]** Do you want a state table, or just always
re-sync a trailing window (e.g. last 3 days) to catch late-arriving data?

# Dependencies to add
Current `pyproject.toml` only has `garminconnect` + `readchar`. You'll need:
- **DB driver**: `psycopg[binary]` (v3) — and `sqlalchemy` if you go that route.
- **Migrations**: `alembic` (if SQLAlchemy) or a `migrations/*.sql` folder + a tiny runner.
- **Config**: `python-dotenv` (or read env directly).
- **[question]** Confirm Python 3.13 target (pyproject says `>=3.13`).

# Docker / Grafana
- Postgres/TimescaleDB stack: its own `docker-compose.yml` with a named volume.
- **[note] Networking is the real question for a shared Grafana.** If Grafana is a
  separate stack, it must reach Postgres. Options: (a) publish Postgres on a host
  port and point Grafana at `host.docker.internal`/host IP; (b) put both on a shared
  external Docker network. **[question]** Which model do you want — host-port, or a
  shared external network?
- **[suggestion]** Provision the Grafana Postgres datasource + dashboards as code
  (provisioning files) so they're reproducible, rather than clicking in the UI.
  Defer dashboards until at least one metric is flowing.

# Testing
**[suggestion]** Capture real API responses as JSON fixtures (you already have the
pattern in `../garmin-research/your_data/response.json`). Test `transform()` against
fixtures so you never need the live API or credentials in CI.

# Authentication
Placeholder, you'll handle it. **[note]** The natural seam is `client.py`:
`build_client() -> Garmin` returning an authenticated client; everything downstream
just consumes it.

---

# Open questions (please answer)
1. **TimescaleDB vs plain Postgres?** (I lean Timescale for intraday samples.)
TimescaleDB, if you reccomend it
2. **Schema: narrow `metric_samples` vs wide per-metric columns?** (I lean narrow.)
Narrow for the sake of extensibility
3. **DB layer: psycopg3 + SQLAlchemy Core, full ORM, or hand-rolled SQL?**
psycopg3 and SQLAlchemy core for the sake of using industry standard tech
4. **Migrations: Alembic vs plain SQL files?**
I'm impartial on this one. You can chose.
5. **Grafana↔Postgres networking: host-port vs shared external Docker network?**
This will only ever live on a single laptop. Assume you can go over the host, as that should keep networking simple.
6. **Sync resume: state table vs trailing re-sync window?**
TODO: explain this one a bit more so I know the tradeoffs
7. **Which metrics for the first slice?** (e.g. heart rate + sleep + workouts) — keeps v1 small.
Let's keep it at heart rate, sleep, and calories for now.
8. **Units: metric or imperial as the stored canonical?**
Metric
```
