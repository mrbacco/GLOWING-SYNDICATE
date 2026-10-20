# File:     backend/tests/test_results.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The results scraper, using pages shaped like lottery.ie's (no network in tests)."""

import asyncio
import json
from datetime import date, datetime, timedelta

import pytest

from app import config, models
from app.results import importer, lottery_ie, scheduler

PRIZES_17_OCT = [
    {"match": "6", "prizeType": "Cash", "numberOfWinners": 0, "prize": "€2,765,876"},
    {"match": "5+1", "prizeType": "Cash", "numberOfWinners": 0, "prize": "€69,370"},
    {"match": "3", "prizeType": "Cash", "numberOfWinners": 4100, "prize": "€4"},
    {"match": "2+1", "prizeType": "Cash", "numberOfWinners": 3200, "prize": "€4"},
]


def entry(when: str, numbers, bonus, prizes=(), title="Lotto"):
    return {
        "standard": {
            "gameTitle": title,
            "drawDates": [when],
            "grids": [{"standard": [list(numbers)], "additional": [[bonus]]}],
            "prizes": list(prizes),
        },
        "addonGames": [],
        "raffle": None,
    }


def page(*entries) -> str:
    data = {"props": {"pageProps": {"list": list(entries), "pageSize": 5}}}
    return f'<html><body><script id="__NEXT_DATA__" type="application/json">{json.dumps(data)}</script></body></html>'


SATURDAY_17 = entry("2026-10-17T18:45:00.000Z", [43, 13, 21, 27, 38, 41], 42, PRIZES_17_OCT)
WEDNESDAY_21 = entry("2026-10-21T18:45:00.000Z", [1, 2, 3, 4, 5, 6], 7)
LATEST = page(entry("2026-10-19T18:45:00.000Z", [19, 26, 30, 33, 34, 40], 14), SATURDAY_17, WEDNESDAY_21)


# ------------------------------------------------------------------ parsing


def test_parses_the_page():
    result = lottery_ie.parse(LATEST)
    assert result.skipped == []
    saturday = next(d for d in result.draws if d.draw_date == date(2026, 10, 17))
    assert saturday.numbers == (13, 21, 27, 38, 41, 43)  # sorted
    assert saturday.bonus == 42
    prizes = {p.tier_code: p for p in saturday.prizes}
    assert prizes["JACKPOT"].prize_cents == 276587600
    assert prizes["MATCH_3"].prize_cents == 400
    assert prizes["MATCH_2_BONUS"].winners == 3200


def test_draw_time_in_utc_gives_the_irish_date():
    # 23:30 UTC on Saturday 31 October is still Saturday in Ireland (winter time, UTC+0)...
    result = lottery_ie.parse(page(entry("2026-10-31T23:30:00.000Z", [1, 2, 3, 4, 5, 6], 7)))
    assert result.draws[0].draw_date == date(2026, 10, 31)
    # ...and 23:30 UTC on Friday 2 October is already Saturday 3 October in Irish summer time.
    result = lottery_ie.parse(page(entry("2026-10-02T23:30:00.000Z", [1, 2, 3, 4, 5, 6], 7)))
    assert result.draws[0].draw_date == date(2026, 10, 3)


def test_skips_entries_that_break_the_rules():
    result = lottery_ie.parse(
        page(
            entry("2026-10-19T18:45:00.000Z", [1, 2, 3, 4, 5, 46], 7),  # 46 after the change to 45 balls
            entry("2026-10-20T18:45:00.000Z", [1, 2, 3, 4, 5, 6], 7),  # a Tuesday
            entry("2026-10-17T18:45:00.000Z", [1, 2, 3, 4, 5, 6], 6),  # bonus is a main number
            entry("2026-10-17T18:45:00.000Z", [1, 2, 3, 4, 5, 6], 7, title="Lotto Plus 1"),
            {"standard": {"drawDates": []}},  # broken entry
            entry("2026-10-14T18:45:00.000Z", [1, 18, 25, 26, 39, 45], 8),
        )
    )
    assert [d.draw_date for d in result.draws] == [date(2026, 10, 14)]
    assert len(result.skipped) == 5


def test_old_47_ball_draws_are_still_valid():
    result = lottery_ie.parse(page(entry("2026-08-29T18:45:00.000Z", [1, 2, 3, 4, 5, 47], 46)))
    assert result.draws[0].numbers[-1] == 47


def test_page_without_data_is_an_error():
    with pytest.raises(lottery_ie.ScrapeError):
        lottery_ie.parse("<html>Loading...</html>")
    with pytest.raises(lottery_ie.ScrapeError):
        lottery_ie.parse('<script id="__NEXT_DATA__" type="application/json">{"props": {}}</script>')


def test_parse_euro():
    assert lottery_ie.parse_euro("€2,904,338") == 290433800
    assert lottery_ie.parse_euro("€4") == 400
    assert lottery_ie.parse_euro("€12.50") == 1250
    assert lottery_ie.parse_euro("Free ticket") is None


# ------------------------------------------------------------------- saving


def test_save_adds_corrects_and_skips_unchanged(client):
    make = client.app.state.sessionmaker
    first = importer.fetch_and_save(make, lambda: LATEST)
    assert sorted(first.added) == [date(2026, 10, 17), date(2026, 10, 19), date(2026, 10, 21)]

    again = importer.fetch_and_save(make, lambda: LATEST)
    assert (again.added, again.updated, again.unchanged) == ([], [], 3)

    corrected = page(entry("2026-10-17T18:45:00.000Z", [13, 21, 27, 38, 41, 44], 42, PRIZES_17_OCT[:2]))
    summary = importer.fetch_and_save(make, lambda: corrected)
    assert summary.updated == [date(2026, 10, 17)]
    with make() as session:
        draw = session.get(models.Draw, date(2026, 10, 17))
        assert draw.numbers[-1] == 44
        assert draw.source == "lottery.ie"
        assert {p.tier_code for p in draw.prizes} == {"JACKPOT", "MATCH_5_BONUS"}


def test_results_screen_shows_what_the_prize_paid(seeded):
    importer.fetch_and_save(seeded.app.state.sessionmaker, lambda: page(SATURDAY_17))
    screen = seeded.get("/screens/syndicates/s-office/results").json()
    assert screen["verdict"] == "Possible win: Match 3, €4! Check the ticket."
    assert screen["results"][0]["prize_amount"] == "€4"


# ------------------------------------------------------------- fetch endpoint


def test_fetch_endpoint(client):
    client.app.state.fetch_html = lambda: LATEST
    response = client.post("/draws/fetch")
    assert response.status_code == 200
    assert len(response.json()["added"]) == 3
    assert client.post("/draws/fetch").status_code == 429  # once a minute at most
    assert client.get("/draws?limit=1").json()[0]["source"] == "lottery.ie"


def test_fetch_endpoint_when_lottery_ie_fails(client):
    def broken():
        raise lottery_ie.ScrapeError("Could not download: timed out")

    client.app.state.fetch_html = broken
    response = client.post("/draws/fetch")
    assert response.status_code == 502
    assert "lottery.ie" in response.json()["detail"]


# ---------------------------------------------------------------- scheduler


def irish(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=config.TIMEZONE)


def test_which_draw_is_due():
    assert scheduler.latest_due_draw(irish(2026, 10, 19, 20, 0)) == date(2026, 10, 17)  # Monday, before 20:30
    assert scheduler.latest_due_draw(irish(2026, 10, 19, 20, 30)) == date(2026, 10, 19)
    assert scheduler.latest_due_draw(irish(2026, 10, 20, 9, 0)) == date(2026, 10, 19)  # Tuesday
    assert scheduler.latest_due_draw(irish(2026, 8, 31, 21, 0)) == date(2026, 8, 29)  # no Monday draws then
    assert scheduler.is_due(irish(2026, 10, 19, 21, 0), date(2026, 10, 17))
    assert not scheduler.is_due(irish(2026, 10, 19, 21, 0), date(2026, 10, 19))


class Stop(Exception):
    pass


def run_watch(client, now, fetch, max_sleeps):
    """Runs the watcher with a fake clock and fake lottery.ie; returns each wait in minutes."""
    waits = []

    async def sleep(seconds):
        waits.append(int(seconds // 60))
        if len(waits) >= max_sleeps:
            raise Stop

    with pytest.raises(Stop):
        asyncio.run(scheduler.watch(client.app.state.sessionmaker, fetch, lambda: now, sleep))
    return waits


def test_watcher_backs_off_until_the_result_appears(seeded):
    # Wednesday 21 October, 21:00: Wednesday's result is due, but lottery.ie has it only on the 3rd try.
    pages = [page(SATURDAY_17), page(SATURDAY_17), page(WEDNESDAY_21)]
    fetches = []

    def fetch():
        fetches.append(1)
        return pages[len(fetches) - 1]

    waits = run_watch(seeded, irish(2026, 10, 21, 21, 0), fetch, max_sleeps=5)
    assert waits == [30, 60, 15, 15, 15]  # waits longer while it's missing, then back to normal
    assert len(fetches) == 3  # and stops fetching once it has the result


def test_watcher_does_not_fetch_when_nothing_is_due(seeded):
    # Tuesday: Monday 19 October is already in the sample data.
    fetches = []
    waits = run_watch(seeded, irish(2026, 10, 20, 12, 0), lambda: fetches.append(1) or LATEST, max_sleeps=3)
    assert fetches == []
    assert waits == [15, 15, 15]


def test_watcher_survives_lottery_ie_being_down(client):
    def broken():
        raise lottery_ie.ScrapeError("down")

    waits = run_watch(client, irish(2026, 10, 21, 21, 0), broken, max_sleeps=7)
    assert waits == [30, 60, 120, 240, 360, 360, 360]  # never more than 6 hours apart
