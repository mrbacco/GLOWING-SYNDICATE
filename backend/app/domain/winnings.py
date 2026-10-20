# File:     backend/app/domain/winnings.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Who shares a win, and how much each gets.

A member shares in a draw's winnings if they had joined by the draw and had paid for the week the
draw fell in. The cash prizes of all winning lines are added up and divided equally; cents that
can't be divided evenly are left over for the syndicate's kitty. Prizes that aren't cash (such as a
free ticket) are listed but not divided.
"""

from dataclasses import dataclass, field
from datetime import date

from app.domain.weeks import week_start


@dataclass(frozen=True)
class MemberIn:
    id: str
    name: str
    joined: date
    paid_weeks: frozenset[date]


@dataclass(frozen=True)
class LinePrize:
    """What one winning line won: cash in cents, or a non-cash prize's text. Both None = not published yet."""

    cents: int | None = None
    text: str | None = None

    @property
    def published(self) -> bool:
        return self.cents is not None or bool(self.text)


@dataclass(frozen=True)
class LeftOut:
    id: str
    name: str
    reason: str  # "hadn't paid for that week"


@dataclass
class Split:
    draw_date: date
    winning_lines: int
    total_cents: int = 0
    non_cash: list[str] = field(default_factory=list)
    all_published: bool = True
    sharers: list[MemberIn] = field(default_factory=list)
    left_out: list[LeftOut] = field(default_factory=list)
    each_cents: int = 0
    left_over_cents: int = 0

    @property
    def week(self) -> date:
        return week_start(self.draw_date)

    def share_of(self, member_id: str) -> int | None:
        """A member's share in cents, or None if they don't share in this draw."""
        return self.each_cents if any(m.id == member_id for m in self.sharers) else None


def why_left_out(member: MemberIn, draw_date: date) -> str | None:
    if member.joined > draw_date:
        return "joined after this draw"
    if week_start(draw_date) not in member.paid_weeks:
        return "hadn't paid for that week"
    return None


def split_winnings(draw_date: date, prizes: list[LinePrize], members: list[MemberIn]) -> Split:
    """[prizes] has one entry per winning line."""
    split = Split(draw_date=draw_date, winning_lines=len(prizes))
    for prize in prizes:
        if not prize.published:
            split.all_published = False
        elif prize.cents is not None:
            split.total_cents += prize.cents
        else:
            split.non_cash.append(prize.text)

    for member in members:
        reason = why_left_out(member, draw_date)
        if reason:
            split.left_out.append(LeftOut(member.id, member.name, reason))
        else:
            split.sharers.append(member)

    if split.sharers and split.all_published:
        split.each_cents, split.left_over_cents = divmod(split.total_cents, len(split.sharers))
    return split
