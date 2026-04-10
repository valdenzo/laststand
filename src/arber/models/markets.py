from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base

if TYPE_CHECKING:
    from arber.models.canonical import Sport, SportPeriod


class SportPeriod(Base):
    __tablename__ = "sport_periods"
    __table_args__ = (UniqueConstraint("sport_id", "slug"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    sport: Mapped[Sport] = relationship(back_populates="periods")
    betting_markets: Mapped[list[BettingMarket]] = relationship(back_populates="period")


class BettingMarket(Base):
    __tablename__ = "betting_markets"
    __table_args__ = (
        # name is just the suffix; naming convention yields ck_betting_markets_market_type
        CheckConstraint(
            "market_type IN ('moneyline', 'spreads', 'totals', 'btts', 'draw_no_bet')",
            name="market_type",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id"), nullable=False
    )
    period_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("sport_periods.id")
    )
    market_type: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    has_line: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sport: Mapped[Sport] = relationship(back_populates="betting_markets")
    period: Mapped[SportPeriod | None] = relationship(back_populates="betting_markets")
    outcomes: Mapped[list[MarketOutcome]] = relationship(back_populates="market")


class MarketOutcome(Base):
    __tablename__ = "market_outcomes"
    __table_args__ = (UniqueConstraint("market_id", "slug"),)

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    market_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("betting_markets.id"), nullable=False
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    market: Mapped[BettingMarket] = relationship(back_populates="outcomes")
