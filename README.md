# arber

Sports betting arbitrage engine. Pulls reference data (sports, competitions, seasons, teams, fixtures) from ESPN / SofaScore / PandaScore, scrapes odds from Baltic-region bookmakers (cbet.lt, topsport.lt, optibet.lt, unibet.lt), resolves bookmaker fixtures to canonical ones via team aliases + fuzzy matching, normalizes odds into a canonical market schema, persists current + historical odds, and detects cross-book arbitrage opportunities in near-real-time.

## Stack

| Concern        | Choice                                                                     |
| -------------- | -------------------------------------------------------------------------- |
| Runtime        | Python 3.13, `uv`, `uvloop`                                                |
| Database       | PostgreSQL 16, `asyncpg`, SQLAlchemy 2 async ORM + raw SQL for upserts     |
| Migrations     | Alembic (async env)                                                        |
| Scheduler      | APScheduler 3.x `AsyncIOScheduler` with `MemoryJobStore`                   |
| HTTP           | `httpx[http2]` + `curl_cffi` (Cloudflare-protected books via `to_thread`)  |
| Retries        | `tenacity`                                                                 |
| Fuzzy matching | `rapidfuzz`                                                                |
| Config         | `pydantic-settings`                                                        |
| Logging        | `structlog`                                                                |
| CLI            | `typer`                                                                    |
| Observability  | `prometheus-client` over `aiohttp` (`/metrics`, `/healthz`)                |
| Tests          | `pytest`, `pytest-asyncio`, `testcontainers[postgresql]`                   |
| Tooling        | `ruff`, `mypy --strict`, `pre-commit`                                      |

## Architecture

```
src/arber/
  config/        settings + structlog
  db/            async engine, session cm, alembic migrations, hand-written upsert SQL
  models/        SQLAlchemy ORM (single source of truth for Alembic autogen)
  schemas/       pydantic DTOs (no DB coupling)
  http/          httpx + curl_cffi clients, per-host token bucket
  reference/     canonical reference providers (espn / sofascore / pandascore)
  bookmakers/    odds-feed providers (cbet / topsport / optibet / unibet)
  mapping/       alias store, fuzzy fixture resolver, market/outcome/odds normalizer
  odds/          diff-write ingest + PG LISTEN/NOTIFY publisher
  arbitrage/     NOTIFY listener, edge calculator, persistence
  scheduler/     AsyncIOScheduler factory + statically-defined jobs
  obs/           prometheus metrics + /metrics server
  cli/           typer commands (one-shot runs of the same service functions)
```

Boundary rules:

- `scheduler/jobs.py` imports only from `reference/`, `bookmakers/`, `odds/`, `arbitrage/`, `mapping/` — never from `cli/`.
- `cli/` imports the same service modules; no business logic lives inside CLI files.
- `models/` has zero IO. `schemas/` has zero DB coupling. `db/` owns the engine and raw SQL.
- APScheduler uses `MemoryJobStore` — persistent state lives in domain tables (`ingest_runs` + others), not in a pickled job store.

## Development

```bash
# install deps
uv sync

# start postgres (exposed on :5433 to avoid clashing with any local :5432)
docker compose up -d postgres

# lint / typecheck / test
uv run ruff check src tests
uv run ruff format src tests
uv run mypy src
uv run pytest

# migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "message"

# run the daemon (scheduler + /metrics)
uv run python -m arber.main

# cli one-shots
uv run arber reference sync espn basketball_nba
uv run arber bookmakers fetch cbet basketball_nba
```

Environment variables are prefixed `ARBER_` — see [.env.example](.env.example).

## Implementation roadmap

Tracked as phases. Each phase is verifiable end-to-end before the next starts.

- [x] **Phase 1 — Bootstrap**
  - [x] `pyproject.toml` deps + ruff/mypy/pytest config
  - [x] `config/settings.py`, `config/logging.py`
  - [x] `db/engine.py`, `db/session.py`
  - [x] `obs/metrics.py`, `obs/server.py` (`/metrics`, `/healthz`)
  - [x] `main.py` entrypoint (uvloop + signal handling)
  - [x] Alembic async env under `src/arber/db/migrations/`
  - [x] `docker-compose.yml` Postgres 16 on `:5433`
  - [x] `.env.example`

- [ ] **Phase 2 — Core schema**
  - [ ] ORM models for `sports`, `competitions`, `seasons`, `teams`, `fixtures` (+ `fixture_status` enum)
  - [ ] ORM models for `reference_sources`, `reference_competitions`, `reference_teams`, `reference_fixtures`
  - [ ] ORM models for `bookmakers`, `bookmaker_competitions`, `bookmaker_fixtures`, `bookmaker_markets`
  - [ ] ORM models for `team_aliases` (generated `alias_norm`), `team_alias_candidates`
  - [ ] ORM models for `sport_periods`, `betting_markets`, `market_outcomes`
  - [ ] ORM models for `odds_current`, `arbitrage_opportunities`, `arbitrage_legs`, `ingest_runs`
  - [ ] Raw-SQL migration for `odds_history` (range-partitioned on `observed_at`, single default partition to start)
  - [ ] Initial Alembic migration applies everything cleanly up + down against a testcontainer Postgres
  - [ ] Extensions: `pg_trgm`, `pgcrypto`, `btree_gin`

- [ ] **Phase 3 — ESPN reference sync**
  - [ ] `http/client.py` (httpx) + `http/rate_limit.py` (per-host token bucket)
  - [ ] `reference/base.py` Protocol
  - [ ] `reference/espn/{client,parser,sync}.py` — upserts into `sports/competitions/seasons/teams/fixtures` + `reference_*` provenance
  - [ ] CLI: `arber reference sync espn <competition_key>`
  - [ ] Scheduler job wired into `scheduler/jobs.py` (6h interval)
  - [ ] Rerun is idempotent (row counts stable, `last_synced_at` advances)

- [ ] **Phase 4 — Markets & periods seed**
  - [ ] Alembic data migration inserting `sport_periods` (basketball FT/Q1-Q4, icehockey FT/P1-P3, tennis S1-S5, soccer FT/H1/H2, ...)
  - [ ] Alembic data migration inserting canonical `betting_markets` + `market_outcomes` for initial sports (moneyline, spreads, totals, btts, draw_no_bet)

- [ ] **Phase 5 — Bookmaker scaffolding (cbet first)**
  - [ ] `http/cffi_client.py` (`curl_cffi` wrapper via `asyncio.to_thread`)
  - [ ] `bookmakers/base.py` Protocol + `bookmakers/registry.py`
  - [ ] `bookmakers/cbet/{client,parser,market_map}.py`
  - [ ] Seed `bookmaker_competitions` for cbet basketball NBA
  - [ ] `sync_fixtures` populates `bookmaker_fixtures` + `last_seen_at`

- [ ] **Phase 6 — Fixture resolution**
  - [ ] `mapping/aliases.py` — alias CRUD + candidate promotion policy (≥0.97 immediate, 0.92–0.97 after 3 observations, <0.92 manual)
  - [ ] `mapping/fixture_resolver.py` — alias-first lookup, rapidfuzz fallback scoped to sport + competition
  - [ ] Background job `mapping.resolve_unmatched` (5m interval)
  - [ ] Background job `mapping.promote_candidates` (10m interval)

- [ ] **Phase 7 — Odds ingest**
  - [ ] `bookmakers/cbet/parser.py` odds extraction
  - [ ] `mapping/market_mapper.py` (bookmaker market → canonical `betting_markets.id`)
  - [ ] `mapping/odds_normalizer.py` (bookmaker odds DTO → canonical rows)
  - [ ] `odds/ingest.py` — diff-write: fetch current, compare price/availability, upsert `odds_current` + append `odds_history` in one tx
  - [ ] `odds/events.py` — `NOTIFY odds_changed, '<fixture_id>'` post-commit (payload is id-only, re-SELECT on listener side)
  - [ ] Integration test: identical payload twice = exactly one history row per key; price change = second row

- [ ] **Phase 8 — Arbitrage detection**
  - [ ] `arbitrage/detector.py` — LISTEN on `odds_changed`, re-query `odds_current` grouped by `(fixture_id, market_id, line)`
  - [ ] `arbitrage/calculator.py` — implied prob, edge, equal-profit stake allocation
  - [ ] `arbitrage/persistence.py` — `arbitrage_opportunities` + `arbitrage_legs`, expire on worsened legs
  - [ ] Unit test: synthetic 2-book fixture where `1/p_home + 1/p_away < 1` produces an opportunity with correct `edge`

- [ ] **Phase 9 — Remaining bookmakers**
  - [ ] `topsport` client/parser/market_map
  - [ ] `optibet` client/parser/market_map
  - [ ] `unibet` client/parser/market_map
  - [ ] Each with `bookmaker_markets` seed migration

- [ ] **Phase 10 — Partitioning & retention**
  - [ ] Monthly-partition cron for `odds_history` (or `pg_partman`)
  - [ ] Retention policy for old partitions
  - [ ] Evaluate TimescaleDB hypertable + compression as a later optimization
