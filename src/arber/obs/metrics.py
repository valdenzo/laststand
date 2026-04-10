from prometheus_client import Counter, Histogram

INGEST_RUNS = Counter(
    "arber_ingest_runs_total",
    "Total ingest runs by kind/source/job/status.",
    labelnames=("kind", "source", "job", "status"),
)

INGEST_ERRORS = Counter(
    "arber_ingest_errors_total",
    "Ingest errors by kind/source/job.",
    labelnames=("kind", "source", "job"),
)

INGEST_DURATION = Histogram(
    "arber_ingest_duration_seconds",
    "Ingest run wall-clock duration.",
    labelnames=("kind", "source", "job"),
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

ODDS_ROWS_UPSERTED = Counter(
    "arber_odds_rows_upserted_total",
    "Odds rows written to odds_current (diffed).",
    labelnames=("bookmaker",),
)
