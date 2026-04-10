from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from arber.models.canonical import Competition, Fixture, Season, Team


class ReferenceSource(Base):
    __tablename__ = "reference_sources"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reference_competitions: Mapped[list[ReferenceCompetition]] = relationship(
        back_populates="source"
    )
    reference_teams: Mapped[list[ReferenceTeam]] = relationship(back_populates="source")
    reference_seasons: Mapped[list[ReferenceSeason]] = relationship(
        back_populates="source"
    )
    reference_fixtures: Mapped[list[ReferenceFixture]] = relationship(
        back_populates="source"
    )


class ReferenceCompetition(Base, TimestampMixin):
    __tablename__ = "reference_competitions"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("reference_sources.id"), nullable=False
    )
    competition_id: Mapped[int] = mapped_column(
        ForeignKey("competitions.id"), nullable=False
    )
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str | None] = mapped_column(Text)
    external_short_name: Mapped[str | None] = mapped_column(Text)
    external_abbr: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[ReferenceSource] = relationship(
        back_populates="reference_competitions"
    )
    competition: Mapped[Competition] = relationship()


class ReferenceTeam(Base, TimestampMixin):
    __tablename__ = "reference_teams"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("reference_sources.id"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str | None] = mapped_column(Text)
    external_short_name: Mapped[str | None] = mapped_column(Text)
    external_abbr: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[ReferenceSource] = relationship(back_populates="reference_teams")
    team: Mapped[Team] = relationship()


class ReferenceSeason(Base, TimestampMixin):
    __tablename__ = "reference_seasons"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("reference_sources.id"), nullable=False
    )
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[ReferenceSource] = relationship(back_populates="reference_seasons")
    season: Mapped[Season] = relationship()


class ReferenceFixture(Base, TimestampMixin):
    __tablename__ = "reference_fixtures"
    __table_args__ = (UniqueConstraint("source_id", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("reference_sources.id"), nullable=False
    )
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), nullable=False)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    external_status: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped[ReferenceSource] = relationship(back_populates="reference_fixtures")
    fixture: Mapped[Fixture] = relationship()
