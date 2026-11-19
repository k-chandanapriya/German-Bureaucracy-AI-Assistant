"""Persistence: cases and letters (SQLite locally, Postgres via DATABASE_URL)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import JSON, Column
from sqlmodel import Field, Session, SQLModel, create_engine

from app.config import settings

CASE_STATUSES = ["new", "understood", "action_needed", "replied", "waiting", "closed"]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Case(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    sender_name: str
    sender_category: str
    reference: str | None = Field(default=None, index=True)
    status: str = "new"
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Letter(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    letter_type: str
    title: str
    letter_date: str | None = None
    bundesland: str
    model: str
    extraction: dict = Field(sa_column=Column(JSON))
    card: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)


class CaseEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    kind: str  # letter_received | status_changed | reply_drafted | note
    text: str
    created_at: datetime = Field(default_factory=_now)


if settings.database_url.startswith("sqlite:///"):
    Path(settings.database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
