"""SQLAlchemy database models for Fantasy League History Tracker.

This schema supports:
- Multiple platforms (Yahoo Fantasy, Sleeper)
- Owners that persist across seasons and platforms
- Comprehensive matchup and trade tracking
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    Table,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Platform(enum.Enum):
    """Supported fantasy platforms."""
    YAHOO = "yahoo"
    SLEEPER = "sleeper"


# Association table for trades (many-to-many between Trade and Team)
trade_teams = Table(
    "trade_teams",
    Base.metadata,
    Column("trade_id", Integer, ForeignKey("trades.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
)


class Owner(Base):
    """
    An owner represents a real person who participates in fantasy leagues.

    Owners persist across seasons and platforms - they can be linked to
    multiple platform-specific identities (Yahoo user, Sleeper user).
    """
    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Platform-specific identifiers (for owner mapping)
    yahoo_user_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    sleeper_user_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    teams: Mapped[List["Team"]] = relationship("Team", back_populates="owner")

    def __repr__(self) -> str:
        return f"<Owner(id={self.id}, name='{self.name}')>"


class League(Base):
    """
    A league represents a fantasy football league on a specific platform.

    A league can span multiple seasons (years) and is linked to a specific
    platform (Yahoo or Sleeper).
    """
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    platform_league_id: Mapped[str] = mapped_column(String(100), nullable=False)

    # League settings
    team_count: Mapped[Optional[int]] = mapped_column(Integer)
    scoring_type: Mapped[Optional[str]] = mapped_column(String(50))  # e.g., "PPR", "Standard"

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    seasons: Mapped[List["Season"]] = relationship("Season", back_populates="league")

    def __repr__(self) -> str:
        return f"<League(id={self.id}, name='{self.name}', platform={self.platform.value})>"


class Season(Base):
    """
    A season represents one year of a league's competition.

    Contains standings, playoff results, and links to all teams that participated.
    """
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    league_id: Mapped[int] = mapped_column(Integer, ForeignKey("leagues.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Season results
    champion_team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    runner_up_team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    regular_season_winner_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))

    # Season configuration
    regular_season_weeks: Mapped[Optional[int]] = mapped_column(Integer)
    playoff_weeks: Mapped[Optional[int]] = mapped_column(Integer)
    playoff_team_count: Mapped[Optional[int]] = mapped_column(Integer)

    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    league: Mapped["League"] = relationship("League", back_populates="seasons")
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        back_populates="season",
        foreign_keys="Team.season_id"
    )
    matchups: Mapped[List["Matchup"]] = relationship("Matchup", back_populates="season")
    trades: Mapped[List["Trade"]] = relationship("Trade", back_populates="season")

    def __repr__(self) -> str:
        return f"<Season(id={self.id}, year={self.year})>"


class Team(Base):
    """
    A team represents an owner's participation in a specific season.

    Tracks season-specific stats like wins, losses, points, and final standing.
    """
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id"), nullable=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("owners.id"), nullable=False)

    # Team identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform_team_id: Mapped[Optional[str]] = mapped_column(String(100))

    # Regular season stats
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    ties: Mapped[int] = mapped_column(Integer, default=0)
    points_for: Mapped[float] = mapped_column(Float, default=0.0)
    points_against: Mapped[float] = mapped_column(Float, default=0.0)

    # Final standings
    regular_season_rank: Mapped[Optional[int]] = mapped_column(Integer)
    final_rank: Mapped[Optional[int]] = mapped_column(Integer)
    made_playoffs: Mapped[bool] = mapped_column(Boolean, default=False)

    # Win streaks (computed/cached)
    longest_win_streak: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    season: Mapped["Season"] = relationship(
        "Season",
        back_populates="teams",
        foreign_keys=[season_id]
    )
    owner: Mapped["Owner"] = relationship("Owner", back_populates="teams")

    # Matchups where this team was home or away
    home_matchups: Mapped[List["Matchup"]] = relationship(
        "Matchup",
        back_populates="home_team",
        foreign_keys="Matchup.home_team_id"
    )
    away_matchups: Mapped[List["Matchup"]] = relationship(
        "Matchup",
        back_populates="away_team",
        foreign_keys="Matchup.away_team_id"
    )

    def __repr__(self) -> str:
        return f"<Team(id={self.id}, name='{self.name}', record={self.wins}-{self.losses})>"


class Matchup(Base):
    """
    A matchup represents a head-to-head game between two teams in a week.

    Tracks scores, winner, and whether it was a playoff game.
    """
    __tablename__ = "matchups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id"), nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)

    # Participating teams
    home_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)

    # Scores
    home_score: Mapped[float] = mapped_column(Float, default=0.0)
    away_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Game type
    is_playoff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_championship: Mapped[bool] = mapped_column(Boolean, default=False)
    is_consolation: Mapped[bool] = mapped_column(Boolean, default=False)

    # Result
    winner_team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    is_tie: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="matchups")
    home_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="home_matchups",
        foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        "Team",
        back_populates="away_matchups",
        foreign_keys=[away_team_id]
    )

    def __repr__(self) -> str:
        return f"<Matchup(week={self.week}, home={self.home_score}, away={self.away_score})>"


class Trade(Base):
    """
    A trade represents a transaction between two or more teams.

    Stores the raw trade data and links to participating teams.
    """
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    season_id: Mapped[int] = mapped_column(Integer, ForeignKey("seasons.id"), nullable=False)

    # Trade metadata
    platform_trade_id: Mapped[Optional[str]] = mapped_column(String(100))
    trade_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    week: Mapped[Optional[int]] = mapped_column(Integer)  # Week when trade occurred

    # Trade details (JSON-like storage for flexibility)
    # Format: {"team_id": ["player1", "player2", ...], ...}
    assets_exchanged: Mapped[Optional[str]] = mapped_column(Text)

    # Trade status
    status: Mapped[str] = mapped_column(String(50), default="completed")  # completed, vetoed, cancelled

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    season: Mapped["Season"] = relationship("Season", back_populates="trades")
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        secondary=trade_teams,
        backref="trades"
    )

    def __repr__(self) -> str:
        return f"<Trade(id={self.id}, date={self.trade_date}, status={self.status})>"
