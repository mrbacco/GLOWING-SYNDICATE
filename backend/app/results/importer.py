# File:     backend/app/results/importer.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Saves fetched results. The official results win: they add missing draws and correct wrong ones."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.results import lottery_ie

log = logging.getLogger("syndicate.results")
SOURCE = "lottery.ie"


@dataclass
class ImportSummary:
    added: list[date] = field(default_factory=list)
    updated: list[date] = field(default_factory=list)
    unchanged: int = 0
    skipped: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [f"{len(self.added)} added", f"{len(self.updated)} updated", f"{self.unchanged} unchanged"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts)


def latest_draw_date(session: Session) -> date | None:
    return session.scalar(select(func.max(models.Draw.draw_date)))


def _prize_rows(draw: lottery_ie.ScrapedDraw) -> set[tuple]:
    return {(p.tier_code, p.winners, p.prize_cents, p.prize_text) for p in draw.prizes}


def save_draws(session: Session, result: lottery_ie.ScrapeResult) -> ImportSummary:
    summary = ImportSummary(skipped=list(result.skipped))
    for scraped in result.draws:
        draw = session.get(models.Draw, scraped.draw_date)
        if draw is None:
            draw = models.Draw(draw_date=scraped.draw_date)
            session.add(draw)
            summary.added.append(scraped.draw_date)
        else:
            stored = {(p.tier_code, p.winners, p.prize_cents, p.prize_text) for p in draw.prizes}
            if (
                tuple(draw.numbers) == scraped.numbers
                and draw.bonus == scraped.bonus
                and stored == _prize_rows(scraped)
            ):
                summary.unchanged += 1
                continue
            summary.updated.append(scraped.draw_date)
        draw.numbers = list(scraped.numbers)
        draw.bonus = scraped.bonus
        draw.source = SOURCE
        # Remove the old prize rows before adding new ones: they share the same keys.
        draw.prizes.clear()
        session.flush()
        draw.prizes = [
            models.DrawPrize(tier_code=p.tier_code, winners=p.winners, prize_cents=p.prize_cents, prize_text=p.prize_text)
            for p in scraped.prizes
        ]
        session.flush()
    session.commit()
    return summary


def fetch_and_save(
    make_session: sessionmaker[Session], fetch: Callable[[], str] = lottery_ie.fetch_html
) -> ImportSummary:
    """Downloads the results page and saves what it finds. Raises ScrapeError if it can't."""
    result = lottery_ie.parse(fetch())
    for reason in result.skipped:
        log.warning("Skipped a result: %s", reason)
    with make_session() as session:
        summary = save_draws(session, result)
    log.info("Fetched results from lottery.ie: %s", summary)
    return summary
