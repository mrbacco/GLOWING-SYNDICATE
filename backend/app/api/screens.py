# File:     backend/app/api/screens.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""One endpoint per app screen, returning exactly what that screen shows."""

from fastapi import APIRouter
from sqlalchemy import select

from app import models, schemas, screens
from app.api.deps import PublicUrlDep, SessionDep, SyndicateDep, TodayDep

router = APIRouter(prefix="/screens", tags=["screens"])

# Enough draws to find the latest few on any syndicate's days.
DRAWS_LOOKED_AT = 30


@router.get("/syndicates", response_model=schemas.SyndicateListScreen)
def syndicate_list(session: SessionDep):
    rows = session.scalars(select(models.Syndicate).order_by(models.Syndicate.created_at)).all()
    return screens.syndicate_list(list(rows))


@router.get("/syndicates/{syndicate_id}/members", response_model=schemas.MembersScreen)
def members(syndicate: SyndicateDep, today: TodayDep, public_url: PublicUrlDep, session: SessionDep):
    return screens.members(syndicate, today, public_url, recent_draws(session))


@router.get("/syndicates/{syndicate_id}/lines", response_model=schemas.LinesScreen)
def lines(syndicate: SyndicateDep):
    return screens.lines(syndicate)


@router.get("/syndicates/{syndicate_id}/results", response_model=schemas.ResultsScreen)
def results(syndicate: SyndicateDep, session: SessionDep):
    return screens.results(syndicate, recent_draws(session))


def recent_draws(session) -> list[models.Draw]:
    return list(session.scalars(select(models.Draw).order_by(models.Draw.draw_date.desc()).limit(DRAWS_LOOKED_AT)))
