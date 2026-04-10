from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from arber.models.aliases import TeamAlias, TeamAliasCandidate
    from arber.models.canonical import Competition, Fixture
    from arber.models.markets import BettingMarket


class Bookmaker(Base, TimestampMixin):
    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    competitions: Mapped[list[BookmakerCompetition]] = relationship(
        back_populates="bookmaker"
    )
    fixtures: Mapped[list[BookmakerFixture]] = relationship(back_populates="bookmaker")
    markets: Mapped[list[BookmakerMarket]] = relationship(back_populates="bookmaker")


class BookmakerCompetition(Base, TimestampMixin):
    __tablename__ = "bookmaker_competitions"
    __table_args__ = (UniqueConstraint("bookmaker_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    bookmaker: Mapped[Bookmaker] = relationship(back_populates="competitions")
    competition: Mapped[Competition] = relationship()
    fixtures: Mapped[list[BookmakerFixture]] = relationship(
        back_populates="bookmaker_competition"
    )


class BookmakerFixture(Base, TimestampMixin):
    __tablename__ = "bookmaker_fixtures"
    __table_args__ = (
        UniqueConstraint("bookmaker_id", "external_id"),
        Index("ix_bookmaker_fixtures_last_seen_at", "last_seen_at"),
        Index(
            "ix_bookmaker_fixtures_unresolved",
            "bookmaker_id",
            "bookmaker_competition_id",
            postgresql_where="fixture_id IS NULL",
        ),
        Index(
            "ix_bookmaker_fixtures_resolved",
            "fixture_id",
            postgresql_where="fixture_id IS NOT NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    bookmaker_competition_id: Mapped[int] = mapped_column(
        ForeignKey("bookmaker_competitions.id"), nullable=False
    )
    fixture_id: Mapped[int | None] = mapped_column(ForeignKey("fixtures.id"))
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    bookmaker: Mapped[Bookmaker] = relationship(back_populates="fixtures")
    bookmaker_competition: Mapped[BookmakerCompetition] = relationship(
        back_populates="fixtures"
    )
    fixture: Mapped[Fixture | None] = relationship(back_populates="bookmaker_fixtures")
    alias_candidates: Mapped[list[TeamAliasCandidate]] = relationship(
        back_populates="bookmaker_fixture"
    )


class BookmakerMarket(Base):
    __tablename__ = "bookmaker_markets"
    __table_args__ = (UniqueConstraint("bookmaker_id", "external_name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    market_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("betting_markets.id"), nullable=False
    )
    external_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    bookmaker: Mapped[Bookmaker] = relationship(back_populates="markets")
    market: Mapped[BettingMarket] = relationship()
