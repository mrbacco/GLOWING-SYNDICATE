# File:     backend/app/results/scheduler.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Fetches results by itself, only when one is due.

Lotto is drawn at 19:45 Irish time; from 20:30 on a draw day the result is "due". Every 15 minutes
the server checks (in its own database) whether the latest due draw is missing, and only then
downloads the results page. If the result still isn't there, or the download fails, it waits twice
as long each time, up to 6 hours, so lottery.ie is never hammered. Nothing is fetched on other days.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session, sessionmaker

from app import config
from app.domain import lotto
from app.results import importer, lottery_ie

log = logging.getLogger("syndicate.results")

RESULT_DUE = time(20, 30)
CHECK_EVERY = timedelta(minutes=15)
LONGEST_WAIT = timedelta(hours=6)


def latest_due_draw(now: datetime) -> date | None:
    """The most recent draw whose result should be published by [now] (Irish time)."""
    today = now.date()
    for days_back in range(8):
        day = today - timedelta(days=days_back)
        if lotto.rules_for(day).is_draw_day(day) and (day < today or now.time() >= RESULT_DUE):
            return day
    return None


def is_due(now: datetime, latest_stored: date | None) -> bool:
    expected = latest_due_draw(now)
    return expected is not None and (latest_stored is None or latest_stored < expected)


def _latest_stored(make_session: sessionmaker[Session]) -> date | None:
    with make_session() as session:
        return importer.latest_draw_date(session)


async def watch(
    make_session: sessionmaker[Session],
    fetch: Callable[[], str] = lottery_ie.fetch_html,
    now: Callable[[], datetime] = lambda: datetime.now(config.TIMEZONE),
    sleep: Callable[[float], object] = asyncio.sleep,
) -> None:
    """Runs until cancelled, as a background task of the server."""
    wait = CHECK_EVERY
    while True:
        try:
            if is_due(now(), await asyncio.to_thread(_latest_stored, make_session)):
                await asyncio.to_thread(importer.fetch_and_save, make_session, fetch)
                still_missing = is_due(now(), await asyncio.to_thread(_latest_stored, make_session))
                wait = min(wait * 2, LONGEST_WAIT) if still_missing else CHECK_EVERY
                if still_missing:
                    log.info("Result not published yet; next try in %s", wait)
            else:
                wait = CHECK_EVERY
        except lottery_ie.ScrapeError as e:
            wait = min(wait * 2, LONGEST_WAIT)
            log.warning("Could not fetch results (%s); next try in %s", e, wait)
        except Exception:  # never let one bad run stop the watcher
            wait = min(wait * 2, LONGEST_WAIT)
            log.exception("Results watcher failed; next try in %s", wait)
        await sleep(wait.total_seconds())
