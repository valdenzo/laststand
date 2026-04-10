from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from arber.models.base import Base

if TYPE_CHECKING:
    from arber.models.bookmakers import Bookmaker, BookmakerFixture
    from arber.models.canonical import Team


class TeamAlias(Base):
    __tablename__ = "team_aliases"
    __table_args__ = (
        UniqueConstraint("bookmaker_id", "alias_norm"),
        Index("ix_team_aliases_alias_norm", "alias_norm"),
        Index(
            "ix_team_aliases_alias_raw_trgm",
            "alias_raw",
            postgresql_using="gin",
            postgresql_ops={"alias_raw": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    bookmaker_id: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id")
    )
    alias_raw: Mapped[str] = mapped_column(Text, nullable=False)
    alias_norm: Mapped[str] = mapped_column(
        Text,
        Computed(
            "lower(regexp_replace(alias_raw, '[^[:alnum:]]', '', 'g'))",
            persisted=True,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    team: Mapped[Team] = relationship()
    bookmaker: Mapped[Bookmaker | None] = relationship()


class TeamAliasCandidate(Base):
    __tablename__ = "team_alias_candidates"
    __table_args__ = (
        UniqueConstraint("bookmaker_id", "raw_name", "matched_team_id"),
        Index(
            "ix_team_alias_candidates_score",
            "bookmaker_id",
            "score",
            postgresql_where="promoted_at IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bookmaker_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bookmakers.id"), nullable=False
    )
    bookmaker_fixture_id: Mapped[int] = mapped_column(
        ForeignKey("bookmaker_fixtures.id"), nullable=False
    )
    raw_name: Mapped[str] = mapped_column(Text, nullable=False)
    matched_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    promoted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    promoted_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))

    bookmaker: Mapped[Bookmaker] = relationship()
    bookmaker_fixture: Mapped[BookmakerFixture] = relationship(
        back_populates="alias_candidates"
    )
    matched_team: Mapped[Team] = relationship()
