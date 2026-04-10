from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from arber.models.bookmakers import BookmakerFixture
    from arber.models.markets import BettingMarket, SportPeriod


class FixtureStatus(enum.Enum):
    scheduled = "scheduled"
    live = "live"
    finished = "finished"
    postponed = "postponed"
    cancelled = "cancelled"
    abandoned = "abandoned"


class Sport(Base, TimestampMixin):
    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    periods: Mapped[list[SportPeriod]] = relationship(back_populates="sport")
    competitions: Mapped[list[Competition]] = relationship(back_populates="sport")
    teams: Mapped[list[Team]] = relationship(back_populates="sport")
    betting_markets: Mapped[list[BettingMarket]] = relationship(back_populates="sport")


class Competition(Base, TimestampMixin):
    __tablename__ = "competitions"
    __table_args__ = (UniqueConstraint("sport_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    short_name: Mapped[str | None] = mapped_column(Text)
    abbreviation: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(Text)

    sport: Mapped[Sport] = relationship(back_populates="competitions")
    seasons: Mapped[list[Season]] = relationship(back_populates="competition")
    fixtures: Mapped[list[Fixture]] = relationship(
        back_populates="competition", foreign_keys="Fixture.competition_id"
    )


class Season(Base, TimestampMixin):
    __tablename__ = "seasons"
    __table_args__ = (UniqueConstraint("competition_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str | None] = mapped_column(Date)
    end_date: Mapped[str | None] = mapped_column(Date)

    competition: Mapped[Competition] = relationship(back_populates="seasons")
    fixtures: Mapped[list[Fixture]] = relationship(back_populates="season")


class Team(Base, TimestampMixin):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("sport_id", "slug"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    short_name: Mapped[str | None] = mapped_column(Text)
    abbreviation: Mapped[str | None] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    country: Mapped[str | None] = mapped_column(Text)

    sport: Mapped[Sport] = relationship(back_populates="teams")
    home_fixtures: Mapped[list[Fixture]] = relationship(
        back_populates="home_team", foreign_keys="Fixture.home_team_id"
    )
    away_fixtures: Mapped[list[Fixture]] = relationship(
        back_populates="away_team", foreign_keys="Fixture.away_team_id"
    )


class Fixture(Base, TimestampMixin):
    __tablename__ = "fixtures"
    __table_args__ = (
        Index("ix_fixtures_sport_id", "sport_id"),
        Index("ix_fixtures_competition_id_starts_at", "competition_id", "starts_at"),
        Index("ix_fixtures_season_id", "season_id"),
        Index("ix_fixtures_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sport_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sports.id"), nullable=False
    )
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[FixtureStatus] = mapped_column(
        Enum(FixtureStatus, name="fixture_status"),
        nullable=False,
        default=FixtureStatus.scheduled,
    )

    sport: Mapped[Sport] = relationship(foreign_keys=[sport_id])
    competition: Mapped[Competition] = relationship(
        back_populates="fixtures", foreign_keys=[competition_id]
    )
    season: Mapped[Season] = relationship(back_populates="fixtures")
    home_team: Mapped[Team] = relationship(
        back_populates="home_fixtures", foreign_keys=[home_team_id]
    )
    away_team: Mapped[Team] = relationship(
        back_populates="away_fixtures", foreign_keys=[away_team_id]
    )
    bookmaker_fixtures: Mapped[list[BookmakerFixture]] = relationship(
        back_populates="fixture"
    )
