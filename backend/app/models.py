# File:     backend/app/models.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Database tables. Money is kept in cents; lists of numbers and days as comma-separated text."""

import secrets
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.domain.lotto import DrawDay


def new_id() -> str:
    return str(uuid.uuid4())


def new_share_token() -> str:
    """The secret part of a member page link: 128 random bits, so links can't be guessed."""
    return secrets.token_urlsafe(16)


def utcnow() -> datetime:
    return datetime.now(UTC)


def _join(values) -> str:
    return ",".join(str(v) for v in values)


class Syndicate(Base):
    __tablename__ = "syndicates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100))
    weekly_cost_cents: Mapped[int]
    draw_days_text: Mapped[str] = mapped_column("draw_days", String(20))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    members: Mapped[list["Member"]] = relationship(
        back_populates="syndicate", cascade="all, delete-orphan", order_by="Member.created_at"
    )
    lines: Mapped[list["Line"]] = relationship(
        back_populates="syndicate", cascade="all, delete-orphan", order_by="Line.created_at"
    )

    @property
    def draw_days(self) -> list[DrawDay]:
        days = {DrawDay(d) for d in self.draw_days_text.split(",") if d}
        return [d for d in DrawDay if d in days]  # always Mon, Wed, Sat order

    @draw_days.setter
    def draw_days(self, days: list[DrawDay]) -> None:
        self.draw_days_text = _join(d.value for d in DrawDay if d in set(days))


class Member(Base):
    __tablename__ = "members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    syndicate_id: Mapped[str] = mapped_column(ForeignKey("syndicates.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    joined: Mapped[date]
    # Whoever has the link /m/<share_token> can see this member's page.
    share_token: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=new_share_token)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    syndicate: Mapped[Syndicate] = relationship(back_populates="members")
    payments: Mapped[list["Payment"]] = relationship(back_populates="member", cascade="all, delete-orphan")


class Payment(Base):
    """A member has paid for the week starting on [week_start] (always a Monday)."""

    __tablename__ = "payments"

    member_id: Mapped[str] = mapped_column(ForeignKey("members.id", ondelete="CASCADE"), primary_key=True)
    week_start: Mapped[date] = mapped_column(primary_key=True)
    recorded_at: Mapped[datetime] = mapped_column(default=utcnow)

    member: Mapped[Member] = relationship(back_populates="payments")


class Line(Base):
    """One line of numbers the syndicate plays every draw."""

    __tablename__ = "lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    syndicate_id: Mapped[str] = mapped_column(ForeignKey("syndicates.id", ondelete="CASCADE"), index=True)
    numbers_text: Mapped[str] = mapped_column("numbers", String(40))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    syndicate: Mapped[Syndicate] = relationship(back_populates="lines")

    @property
    def numbers(self) -> list[int]:
        return [int(n) for n in self.numbers_text.split(",")]

    @numbers.setter
    def numbers(self, numbers: list[int]) -> None:
        self.numbers_text = _join(sorted(numbers))


class Draw(Base):
    """An official Lotto result: the main numbers plus the bonus ball. Shared by all syndicates."""

    __tablename__ = "draws"

    draw_date: Mapped[date] = mapped_column(primary_key=True)
    numbers_text: Mapped[str] = mapped_column("numbers", String(40))
    bonus: Mapped[int]
    # "lottery.ie" when fetched by the results scraper, "manual" when entered through the API.
    source: Mapped[str] = mapped_column(String(20), default="manual")

    prizes: Mapped[list["DrawPrize"]] = relationship(back_populates="draw", cascade="all, delete-orphan")

    def prize_for(self, tier_code: str) -> "DrawPrize | None":
        return next((p for p in self.prizes if p.tier_code == tier_code), None)

    @property
    def numbers(self) -> list[int]:
        return [int(n) for n in self.numbers_text.split(",")]

    @numbers.setter
    def numbers(self, numbers: list[int]) -> None:
        self.numbers_text = _join(sorted(numbers))


class DrawPrize(Base):
    """What one prize tier paid in a draw, as published with the result."""

    __tablename__ = "draw_prizes"

    draw_date: Mapped[date] = mapped_column(ForeignKey("draws.draw_date", ondelete="CASCADE"), primary_key=True)
    tier_code: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g. "MATCH_3"
    winners: Mapped[int]
    # Cash prize per winning line, or None when it isn't cash (e.g. a free ticket).
    prize_cents: Mapped[int | None]
    prize_text: Mapped[str] = mapped_column(String(60))  # as published, e.g. "€4"

    draw: Mapped[Draw] = relationship(back_populates="prizes")
