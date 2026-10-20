# File:     backend/app/results/lottery_ie.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Reads Lotto results from the official results history page on lottery.ie.

The page is a Next.js site that embeds its data as JSON in <script id="__NEXT_DATA__">: for each
of the last few weeks of draws, the draw time, the six numbers, the bonus and what each prize tier
paid. Reading that JSON is much sturdier than reading the visible text. Every draw is checked
against the game rules for its date before it is used; anything odd is skipped and reported.
"""

import json
import re
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app import config
from app.domain import lotto

HISTORY_URL = "https://www.lottery.ie/results/lotto/history"
USER_AGENT = "SYNDICATE-results/0.1 (lotto syndicate organiser app; fetches after each draw)"

# How lottery.ie names the tiers -> our tier codes (app/domain/lotto.py).
MATCH_TO_TIER = {
    "6": "JACKPOT",
    "5+1": "MATCH_5_BONUS",
    "5": "MATCH_5",
    "4+1": "MATCH_4_BONUS",
    "4": "MATCH_4",
    "3+1": "MATCH_3_BONUS",
    "3": "MATCH_3",
    "2+1": "MATCH_2_BONUS",
}

_NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S)


class ScrapeError(Exception):
    """The page could not be read: lottery.ie may be down or may have changed its page."""


@dataclass(frozen=True)
class ScrapedPrize:
    tier_code: str
    winners: int
    prize_cents: int | None  # None when the prize isn't cash
    prize_text: str


@dataclass(frozen=True)
class ScrapedDraw:
    draw_date: date
    numbers: tuple[int, ...]
    bonus: int
    prizes: tuple[ScrapedPrize, ...]


@dataclass
class ScrapeResult:
    draws: list[ScrapedDraw] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)  # why entries were not used


def fetch_html(url: str = HISTORY_URL, timeout: float = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except OSError as e:  # includes URLError, HTTPError and timeouts
        raise ScrapeError(f"Could not download {url}: {e}") from e


def parse_euro(text: str) -> int | None:
    """"€2,904,338" -> 290433800 cents. None if it isn't an amount."""
    cleaned = text.replace("€", "").replace(",", "").strip()
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        return None
    return int(value * 100) if value >= 0 else None


def parse(html: str) -> ScrapeResult:
    match = _NEXT_DATA.search(html)
    if match is None:
        raise ScrapeError("No results data on the page: lottery.ie may have changed it.")
    try:
        items = json.loads(match.group(1))["props"]["pageProps"]["list"]
    except (ValueError, KeyError, TypeError) as e:
        raise ScrapeError(f"The results data is not in the expected shape: {e}") from e

    result = ScrapeResult()
    for index, item in enumerate(items):
        try:
            result.draws.append(_draw(item["standard"]))
        except (KeyError, IndexError, TypeError, ValueError) as e:
            result.skipped.append(f"entry {index}: {e}")
    return result


def _draw(game: dict) -> ScrapedDraw:
    if game.get("gameTitle", "Lotto") != "Lotto":
        raise ValueError(f"not the main Lotto game ({game.get('gameTitle')})")
    # "2026-10-19T18:45:00.000Z": the date in Ireland, where the draw is held.
    when = datetime.fromisoformat(game["drawDates"][0].replace("Z", "+00:00"))
    draw_date = when.astimezone(config.TIMEZONE).date()
    grid = game["grids"][0]
    numbers = [int(n) for n in grid["standard"][0]]
    bonus = int(grid["additional"][0][0])

    rules = lotto.rules_for(draw_date)
    if not rules.is_draw_day(draw_date):
        raise ValueError(f"{draw_date} is not a {rules.name} draw day")
    problem = lotto.validate_numbers(numbers, rules)
    if problem:
        raise ValueError(f"{draw_date}: {problem}")
    if bonus in numbers or not 1 <= bonus <= rules.max_number:
        raise ValueError(f"{draw_date}: bad bonus {bonus}")

    prizes = []
    for prize in game.get("prizes") or []:
        tier = MATCH_TO_TIER.get(str(prize.get("match")))
        if tier is None:
            continue  # a tier we don't know about; ignore rather than guess
        text = str(prize.get("prize", "")).strip()
        cents = parse_euro(text) if prize.get("prizeType", "Cash") == "Cash" else None
        prizes.append(ScrapedPrize(tier, int(prize.get("numberOfWinners") or 0), cents, text))
    return ScrapedDraw(draw_date, tuple(sorted(numbers)), bonus, tuple(prizes))
