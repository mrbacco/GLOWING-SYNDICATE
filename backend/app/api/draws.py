# File:     backend/app/api/draws.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Official draw results and game rules.

Results come from lottery.ie by themselves after each draw (app/results). They can also be fetched
on request, or entered and corrected by hand.
"""

import time
from datetime import date

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from sqlalchemy import select

from app import models, schemas
from app.api.deps import SessionDep, TodayDep, find
from app.domain import lotto
from app.results import importer, lottery_ie

# A person can ask for results at most this often; the server also fetches them by itself.
MANUAL_FETCH_GAP_SECONDS = 60

router = APIRouter(tags=["draws"])


def rules_out(rules: lotto.GameRules) -> schemas.GameRulesOut:
    return schemas.GameRulesOut(
        name=rules.name,
        source=rules.source,
        first_draw=rules.first_draw,
        last_draw=rules.last_draw,
        numbers_per_line=rules.numbers_per_line,
        max_number=rules.max_number,
        draw_days=list(rules.draw_days),
        draw_day_labels=[d.label for d in rules.draw_days],
        tiers=[schemas.PrizeTierOut(**vars(t)) for t in rules.tiers],
    )


@router.get("/rules", response_model=schemas.GameRulesOut)
def get_rules(today: TodayDep, on: date | None = Query(default=None, description="Defaults to today")):
    """The Lotto rules on a date. The app uses this instead of having the rules built in."""
    return rules_out(lotto.rules_for(on or today))


@router.get("/draws", response_model=list[schemas.DrawOut])
def list_draws(session: SessionDep, limit: int = Query(default=20, ge=1, le=200)):
    return session.scalars(select(models.Draw).order_by(models.Draw.draw_date.desc()).limit(limit)).all()


@router.post("/draws/fetch", response_model=schemas.FetchSummary)
def fetch_draws(request: Request):
    """Fetches the latest results from lottery.ie now, instead of waiting for the schedule."""
    state = request.app.state
    last = state.last_manual_fetch
    if last is not None and time.monotonic() - last < MANUAL_FETCH_GAP_SECONDS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Results were just fetched. Try again in a minute.")
    state.last_manual_fetch = time.monotonic()
    try:
        summary = importer.fetch_and_save(state.sessionmaker, state.fetch_html)
    except lottery_ie.ScrapeError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Couldn't get the results from lottery.ie: {e}") from e
    return schemas.FetchSummary(
        added=summary.added, updated=summary.updated, unchanged=summary.unchanged, skipped=summary.skipped
    )


@router.put("/draws/{draw_date}", response_model=schemas.DrawOut)
def save_draw(draw_date: date, body: schemas.DrawIn, session: SessionDep):
    """Adds or corrects the result of one draw."""
    rules = lotto.rules_for(draw_date)
    if not rules.is_draw_day(draw_date):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"There is no {rules.name} draw on that day.")
    problem = lotto.validate_numbers(body.numbers, rules)
    if problem:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, problem)
    if body.bonus in body.numbers or not 1 <= body.bonus <= rules.max_number:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"The bonus must be from 1 to {rules.max_number} and not one of the main numbers.",
        )
    draw = session.get(models.Draw, draw_date) or models.Draw(draw_date=draw_date)
    draw.numbers = body.numbers
    draw.bonus = body.bonus
    draw.source = "manual"
    session.add(draw)
    session.commit()
    return draw


@router.delete("/draws/{draw_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_draw(draw_date: date, session: SessionDep):
    session.delete(find(session, models.Draw, draw_date, "Draw"))
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
