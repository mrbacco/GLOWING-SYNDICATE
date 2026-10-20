# File:     backend/app/schemas.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Request and response bodies of the API.

Two kinds of responses: plain records (what was saved), and "screen" responses that carry
everything one app screen shows, already worked out and worded, so the app only displays them.
"""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain import phones
from app.domain.lotto import DrawDay

Name = Field(min_length=1, max_length=100)
# Up to €1,000 a week per member; anything more is a typo.
WeeklyCost = Field(gt=0, le=100_000, description="Cost per member per week, in cents")


def _clean_name(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise ValueError("Please enter a name.")
    return value


def _clean_phone(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    if phones.international(value) is None:
        raise ValueError("That doesn't look like a phone number.")
    return value.strip()


# ------------------------------------------------------------------ requests


class SyndicateCreate(BaseModel):
    name: str = Name
    weekly_cost_cents: int = WeeklyCost
    draw_days: list[DrawDay] | None = Field(default=None, description="Defaults to every draw day of the current game")

    _name = field_validator("name")(_clean_name)


class SyndicateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    weekly_cost_cents: int | None = Field(default=None, gt=0, le=100_000)
    draw_days: list[DrawDay] | None = None

    _name = field_validator("name")(_clean_name)


class MemberCreate(BaseModel):
    name: str = Name
    phone: str | None = Field(default=None, max_length=30)
    joined: date | None = Field(default=None, description="Defaults to today")

    _name = field_validator("name")(_clean_name)
    _phone = field_validator("phone")(_clean_phone)


class MemberUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30, description="Empty text removes the number")
    joined: date | None = None

    _name = field_validator("name")(_clean_name)

    @field_validator("phone")
    @classmethod
    def _phone(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            return ""  # keep "remove the number" apart from "not sent"
        return _clean_phone(value)


class LineIn(BaseModel):
    numbers: list[int]


class DrawIn(BaseModel):
    numbers: list[int]
    bonus: int


# ----------------------------------------------------------------- records


class Record(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SyndicateOut(Record):
    id: str
    name: str
    weekly_cost_cents: int
    draw_days: list[DrawDay]


class MemberOut(Record):
    id: str
    syndicate_id: str
    name: str
    phone: str | None
    joined: date


class LineOut(Record):
    id: str
    syndicate_id: str
    numbers: list[int]


class DrawOut(Record):
    draw_date: date
    numbers: list[int]
    bonus: int
    source: str  # "lottery.ie" or "manual"


class FetchSummary(BaseModel):
    added: list[date]
    updated: list[date]
    unchanged: int
    skipped: list[str]


class PrizeTierOut(BaseModel):
    code: str
    label: str
    matches: int
    bonus: bool
    fixed_prize_cents: int | None


class GameRulesOut(BaseModel):
    name: str
    source: str
    first_draw: date | None
    last_draw: date | None
    numbers_per_line: int
    max_number: int
    draw_days: list[DrawDay]
    draw_day_labels: list[str]
    tiers: list[PrizeTierOut]


# ------------------------------------------------------------------ screens


class SyndicateRow(BaseModel):
    id: str
    name: str
    subtitle: str  # "€5.00 per week · Wed, Sat"


class SyndicateListScreen(BaseModel):
    syndicates: list[SyndicateRow]


class SummaryCard(BaseModel):
    title: str
    lines: list[str]


class MemberRow(BaseModel):
    id: str
    name: str
    phone: str | None
    whatsapp_number: str | None  # international digits for wa.me links
    paid_this_week: bool
    weeks_owed: int
    amount_owed_cents: int
    status: str  # "All paid up" or "Owes €5.00 (1 week)"
    message: str  # ready to send by SMS or WhatsApp; includes page_url
    page_url: str  # the member's own web page


class MembersScreen(BaseModel):
    syndicate: SyndicateOut
    week_start: date
    summary: SummaryCard
    members: list[MemberRow]
    empty_text: str | None


class LineRow(BaseModel):
    id: str
    numbers: list[int]


class LinesScreen(BaseModel):
    syndicate: SyndicateOut
    summary: SummaryCard
    lines: list[LineRow]
    empty_text: str | None


class DrawCard(BaseModel):
    draw_date: date
    title: str  # "Mon 19 Oct 2026"
    numbers: list[int]
    bonus: int


class LineResultRow(BaseModel):
    line_id: str
    numbers: list[int]
    matched: list[int]
    bonus_matched: bool
    text: str  # "Matched 3 numbers + bonus"
    prize_tier: str | None  # "Match 3 + Bonus"
    prize_amount: str | None  # what that tier paid per line, e.g. "€25", once published
    won: bool


class ResultsScreen(BaseModel):
    syndicate: SyndicateOut
    latest_draw: DrawCard | None
    verdict: str | None  # "Possible win: Match 3! Check the ticket."
    results: list[LineResultRow]
    previous_draws: list[DrawCard]
    empty_text: str | None
