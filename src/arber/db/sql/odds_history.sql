-- odds_history: range-partitioned on observed_at.
-- No foreign keys — PostgreSQL does not support FKs from/to partitioned tables
-- when the partition key is not part of the referenced column set.
-- This file is executed verbatim from the Alembic migration via op.execute().

CREATE TABLE odds_history (
    id                      BIGINT          NOT NULL GENERATED ALWAYS AS IDENTITY,
    fixture_id              INT             NOT NULL,
    bookmaker_id            SMALLINT        NOT NULL,
    bookmaker_fixture_id    INT             NOT NULL,
    market_id               SMALLINT        NOT NULL,
    outcome_id              SMALLINT        NOT NULL,
    line                    NUMERIC(8, 2),
    line_pair               NUMERIC(8, 2)   GENERATED ALWAYS AS (abs(line)) STORED,
    decimal_odds            NUMERIC(10, 4)  NOT NULL,
    is_available            BOOLEAN         NOT NULL DEFAULT TRUE,
    observed_at             TIMESTAMPTZ     NOT NULL,
    PRIMARY KEY (id, observed_at)
) PARTITION BY RANGE (observed_at);

-- Default partition catches all rows until monthly partitions are added (Phase 10).
CREATE TABLE odds_history_default PARTITION OF odds_history DEFAULT;

-- Time-range queries per fixture across all partitions.
CREATE INDEX ix_odds_history_fixture_observed
    ON odds_history (fixture_id, observed_at DESC);
