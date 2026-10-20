# File:     backend/app/domain/text.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Text shown to people: money, dates and messages. Kept here so the app only displays it."""

from datetime import date

_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def euro(cents: int) -> str:
    """500 -> "€5.00"."""
    return f"€{cents // 100}.{cents % 100:02d}"


def amount(cents: int) -> str:
    """A prize: whole euros with thousands separators when it has no cents. 290433800 -> "€2,904,338"."""
    if cents % 100 == 0:
        return f"€{cents // 100:,}"
    return f"€{cents // 100:,}.{cents % 100:02d}"


def draw_date(day: date) -> str:
    """"Mon 19 Oct 2026"."""
    return f"{_DAYS[day.weekday()]} {day.day} {_MONTHS[day.month - 1]} {day.year}"


def short_date(day: date) -> str:
    """"19 Oct"."""
    return f"{day.day} {_MONTHS[day.month - 1]}"


def weeks(count: int) -> str:
    return "1 week" if count == 1 else f"{count} weeks"


def member_message(name: str, syndicate: str, owed_cents: int, page_url: str) -> str:
    """A payment reminder if the member owes money, otherwise their page link. Both carry the link."""
    if owed_cents == 0:
        return f"Hi {name}, here's your page for {syndicate}, with your payments and our results: {page_url}"
    return (
        f"Hi {name}, a quick reminder for {syndicate}: you owe {euro(owed_cents)}. Thanks! "
        f"Your page: {page_url}"
    )
