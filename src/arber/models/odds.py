from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from arber.models.bookmakers import Bookmaker, BookmakerFixture
    from arber.models.canonical import Fixture
    from arber.models.markets import BettingMarket, MarketOutcome


class OddsCurrent(Base, TimestampMixin):
    __tablename__ = "odds_current"
    __table_args__ = (
        # Unique key with nullable line — emitted as raw SQL in the migration
        # (NULLS NOT DISTINCT requires PG 15+; see migration for op.execute).
        # We define no UniqueConstraint here to avoid Alembic trying to manage it.
        Index("ix_odds_current_fixture_available", "fixture_id", postgresql_where="is_available = TRUE"),
        Index("ix_odds_current_bookmaker_fixture", "bookmaker_id", "fixture_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False)
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    bookmaker_fixture_id: Mapped[int] = mapped_column(
        ForeignKey("bookmaker_fixtures.id"), nullable=False
    )
    market_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("betting_markets.id"), nullable=False
    )
    outcome_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("market_outcomes.id"), nullable=False
    )
    line: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    line_pair: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), Computed("abs(line)", persisted=True)
    )
    decimal_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    fixture: Mapped[Fixture] = relationship()
    bookmaker: Mapped[Bookmaker] = relationship()
    bookmaker_fixture: Mapped[BookmakerFixture] = relationship()
    market: Mapped[BettingMarket] = relationship()
    outcome: Mapped[MarketOutcome] = relationship()


class ArbitrageOpportunity(Base, TimestampMixin):
    __tablename__ = "arbitrage_opportunities"
    # Partial unique index (WHERE is_active = TRUE, NULLS NOT DISTINCT) is emitted
    # as raw SQL in the migration — cannot be expressed as a standard UniqueConstraint.

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False)
    market_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("betting_markets.id"), nullable=False
    )
    line: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    edge: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    total_implied_prob: Mapped[Decimal] = mapped_column(Numeric(8, 6), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    fixture: Mapped[Fixture] = relationship()
    market: Mapped[BettingMarket] = relationship()
    legs: Mapped[list[ArbitrageLeg]] = relationship(back_populates="opportunity")


class ArbitrageLeg(Base):
    __tablename__ = "arbitrage_legs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("arbitrage_opportunities.id"), nullable=False
    )
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    outcome_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("market_outcomes.id"), nullable=False
    )
    decimal_odds: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)
    stake_fraction: Mapped[Decimal] = mapped_column(Numeric(10, 8), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    opportunity: Mapped[ArbitrageOpportunity] = relationship(back_populates="legs")
    bookmaker: Mapped[Bookmaker] = relationship()
    outcome: Mapped[MarketOutcome] = relationship()


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    __table_args__ = (
        Index("ix_ingest_runs_job_started", "job_name", "started_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    job_name: Mapped[str] = mapped_column(Text, nullable=False)
    bookmaker_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id")
    )
    competition_id: Mapped[int | None] = mapped_column(ForeignKey("competitions.id"))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, nullable=False, default="running")
    rows_fetched: Mapped[int | None] = mapped_column(Integer)
    rows_upserted: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    bookmaker: Mapped[Bookmaker | None] = relationship()
