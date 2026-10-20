# File:     backend/app/domain/ledger.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Who owes what. A member owes for every week from the week they joined up to this week."""

from dataclasses import dataclass
from datetime import date

from app.domain.weeks import week_start, weeks_between


@dataclass(frozen=True)
class MemberBalance:
    paid_this_week: bool
    weeks_owed: int
    amount_owed_cents: int


def balance(joined: date, paid_weeks: set[date], weekly_cost_cents: int, today: date) -> MemberBalance:
    owed = sum(1 for week in weeks_between(joined, today) if week not in paid_weeks)
    return MemberBalance(
        paid_this_week=week_start(today) in paid_weeks,
        weeks_owed=owed,
        amount_owed_cents=owed * weekly_cost_cents,
    )
