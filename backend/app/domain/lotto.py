# File:     backend/app/domain/lotto.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Irish Lotto game rules and line checking.

The rules change over time (47 balls on Wed/Sat until 2 September 2026, then 45 balls on
Mon/Wed/Sat), so every draw is checked against the rules that applied on its date. The app
reads the current rules from the API instead of having them built in.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class DrawDay(str, Enum):
    MONDAY = "MON"
    WEDNESDAY = "WED"
    SATURDAY = "SAT"

    @property
    def label(self) -> str:
        return {"MON": "Mon", "WED": "Wed", "SAT": "Sat"}[self.value]

    @property
    def weekday(self) -> int:
        """Python weekday number: Monday is 0."""
        return {"MON": 0, "WED": 2, "SAT": 5}[self.value]

    @classmethod
    def of(cls, day: date) -> "DrawDay | None":
        return next((d for d in cls if d.weekday == day.weekday()), None)


@dataclass(frozen=True)
class PrizeTier:
    code: str
    label: str
    matches: int
    bonus: bool
    # Fixed prizes are the same for every winner; the others share a prize pool.
    fixed_prize_cents: int | None = None


@dataclass(frozen=True)
class GameRules:
    name: str
    source: str
    first_draw: date | None
    last_draw: date | None
    max_number: int
    draw_days: tuple[DrawDay, ...]
    tiers: tuple[PrizeTier, ...]  # best first
    numbers_per_line: int = 6

    def covers(self, day: date) -> bool:
        return (self.first_draw is None or day >= self.first_draw) and (
            self.last_draw is None or day <= self.last_draw
        )

    def is_draw_day(self, day: date) -> bool:
        return DrawDay.of(day) in self.draw_days


def _tiers(match_3_cents: int | None, match_2_bonus_cents: int) -> tuple[PrizeTier, ...]:
    return (
        PrizeTier("JACKPOT", "Jackpot", 6, False),
        PrizeTier("MATCH_5_BONUS", "Match 5 + Bonus", 5, True),
        PrizeTier("MATCH_5", "Match 5", 5, False),
        PrizeTier("MATCH_4_BONUS", "Match 4 + Bonus", 4, True),
        PrizeTier("MATCH_4", "Match 4", 4, False),
        PrizeTier("MATCH_3_BONUS", "Match 3 + Bonus", 3, True),
        PrizeTier("MATCH_3", "Match 3", 3, False, match_3_cents),
        PrizeTier("MATCH_2_BONUS", "Match 2 + Bonus", 2, True, match_2_bonus_cents),
    )


LOTTO_6_47 = GameRules(
    name="Lotto 6/47",
    source="Lotto 6/47 Rules, Issue 9 (29 October 2024)",
    first_draw=None,
    last_draw=date(2026, 9, 2),
    max_number=47,
    draw_days=(DrawDay.WEDNESDAY, DrawDay.SATURDAY),
    # Match 2 + Bonus paid a €3 Daily Million Quick Pick, or €3 cash in shops.
    tiers=_tiers(match_3_cents=None, match_2_bonus_cents=300),
)

LOTTO_6_45 = GameRules(
    name="Lotto 6/45",
    source="Lotto 6/45 Rules, Issue 10 (3 September 2026)",
    first_draw=date(2026, 9, 5),
    last_draw=None,
    max_number=45,
    draw_days=(DrawDay.MONDAY, DrawDay.WEDNESDAY, DrawDay.SATURDAY),
    tiers=_tiers(match_3_cents=400, match_2_bonus_cents=400),
)

ALL_RULES = (LOTTO_6_47, LOTTO_6_45)


def rules_for(day: date) -> GameRules:
    """The rules for a draw on [day]. Days between two games use the newer game."""
    return next((r for r in ALL_RULES if r.covers(day)), ALL_RULES[-1])


def validate_numbers(numbers: list[int], rules: GameRules) -> str | None:
    """An error message, or None if [numbers] is a valid line under [rules]."""
    n = rules.numbers_per_line
    if len(numbers) != n or len(set(numbers)) != n:
        return f"Enter {n} different numbers."
    if any(not 1 <= x <= rules.max_number for x in numbers):
        return f"Numbers must be from 1 to {rules.max_number}."
    return None


@dataclass(frozen=True)
class LineResult:
    matched: frozenset[int]
    bonus_matched: bool
    tier: PrizeTier | None

    @property
    def match_count(self) -> int:
        return len(self.matched)

    @property
    def label(self) -> str:
        """Short description such as "3 numbers + bonus"."""
        if self.match_count == 0 and self.bonus_matched:
            return "the bonus ball only"
        numbers = {0: "no numbers", 1: "1 number"}.get(self.match_count, f"{self.match_count} numbers")
        return f"{numbers} + bonus" if self.bonus_matched else numbers


def check_line(numbers: list[int], draw_numbers: list[int], bonus: int, rules: GameRules) -> LineResult:
    matched = frozenset(numbers) & frozenset(draw_numbers)
    bonus_matched = bonus in numbers
    # A bonus match only counts where a tier has one.
    tier = next(
        (t for t in rules.tiers if t.matches == len(matched) and (bonus_matched or not t.bonus)),
        None,
    )
    return LineResult(matched, bonus_matched, tier)


def tier_rank(result: LineResult, rules: GameRules) -> int:
    """Sort key: best prize first, lines with no prize last."""
    return rules.tiers.index(result.tier) if result.tier else len(rules.tiers)
