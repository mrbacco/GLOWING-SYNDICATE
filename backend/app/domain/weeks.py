# File:     backend/app/domain/weeks.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Payments are tracked per week; a week always starts on Monday."""

from datetime import date, timedelta


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def weeks_between(start: date, end: date) -> list[date]:
    """Every week start from the week containing [start] up to and including the week containing [end]."""
    first, last = week_start(start), week_start(end)
    count = (last - first).days // 7 + 1
    return [first + timedelta(weeks=i) for i in range(max(count, 0))]
