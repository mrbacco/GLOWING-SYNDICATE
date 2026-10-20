# File:     backend/app/api/syndicates.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Syndicates, their members, payments and lines."""

from datetime import date

from fastapi import APIRouter, HTTPException, Response, status

from app import models, schemas
from app.api.deps import LineDep, MemberDep, SessionDep, SyndicateDep, TodayDep
from app.domain import lotto
from app.domain.weeks import week_start

router = APIRouter(tags=["syndicates"])


def _check_draw_days(days: list[lotto.DrawDay], today: date) -> list[lotto.DrawDay]:
    rules = lotto.rules_for(today)
    if not days:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Choose at least one draw day.")
    if any(d not in rules.draw_days for d in days):
        allowed = ", ".join(d.label for d in rules.draw_days)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{rules.name} is drawn on {allowed} only.")
    return days


def _check_numbers(numbers: list[int], today: date) -> list[int]:
    problem = lotto.validate_numbers(numbers, lotto.rules_for(today))
    if problem:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, problem)
    return numbers


# ---------------------------------------------------------------- syndicates


@router.post("/syndicates", status_code=status.HTTP_201_CREATED, response_model=schemas.SyndicateOut)
def create_syndicate(body: schemas.SyndicateCreate, session: SessionDep, today: TodayDep):
    days = body.draw_days if body.draw_days is not None else list(lotto.rules_for(today).draw_days)
    syndicate = models.Syndicate(name=body.name, weekly_cost_cents=body.weekly_cost_cents)
    syndicate.draw_days = _check_draw_days(days, today)
    session.add(syndicate)
    session.commit()
    return syndicate


@router.get("/syndicates/{syndicate_id}", response_model=schemas.SyndicateOut)
def get_syndicate(syndicate: SyndicateDep):
    return syndicate


@router.patch("/syndicates/{syndicate_id}", response_model=schemas.SyndicateOut)
def update_syndicate(body: schemas.SyndicateUpdate, syndicate: SyndicateDep, session: SessionDep, today: TodayDep):
    if body.name is not None:
        syndicate.name = body.name
    if body.weekly_cost_cents is not None:
        syndicate.weekly_cost_cents = body.weekly_cost_cents
    if body.draw_days is not None:
        syndicate.draw_days = _check_draw_days(body.draw_days, today)
    session.commit()
    return syndicate


@router.delete("/syndicates/{syndicate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_syndicate(syndicate: SyndicateDep, session: SessionDep):
    session.delete(syndicate)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------- members


@router.post(
    "/syndicates/{syndicate_id}/members", status_code=status.HTTP_201_CREATED, response_model=schemas.MemberOut
)
def add_member(body: schemas.MemberCreate, syndicate: SyndicateDep, session: SessionDep, today: TodayDep):
    member = models.Member(syndicate=syndicate, name=body.name, phone=body.phone, joined=body.joined or today)
    session.add(member)
    session.commit()
    return member


@router.patch("/members/{member_id}", response_model=schemas.MemberOut)
def update_member(body: schemas.MemberUpdate, member: MemberDep, session: SessionDep):
    if body.name is not None:
        member.name = body.name
    if body.phone is not None:
        member.phone = body.phone or None
    if body.joined is not None:
        member.joined = body.joined
    session.commit()
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member: MemberDep, session: SessionDep):
    session.delete(member)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------ payments


@router.put("/members/{member_id}/payments/{week}", status_code=status.HTTP_204_NO_CONTENT)
def mark_paid(week: date, member: MemberDep, session: SessionDep):
    """Marks the week containing [week] as paid. Doing it twice is fine."""
    start = week_start(week)
    if session.get(models.Payment, (member.id, start)) is None:
        session.add(models.Payment(member=member, week_start=start))
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/members/{member_id}/payments/{week}", status_code=status.HTTP_204_NO_CONTENT)
def mark_unpaid(week: date, member: MemberDep, session: SessionDep):
    payment = session.get(models.Payment, (member.id, week_start(week)))
    if payment is not None:
        session.delete(payment)
        session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --------------------------------------------------------------------- lines


@router.post("/syndicates/{syndicate_id}/lines", status_code=status.HTTP_201_CREATED, response_model=schemas.LineOut)
def add_line(body: schemas.LineIn, syndicate: SyndicateDep, session: SessionDep, today: TodayDep):
    line = models.Line(syndicate=syndicate)
    line.numbers = _check_numbers(body.numbers, today)
    session.add(line)
    session.commit()
    return line


@router.put("/lines/{line_id}", response_model=schemas.LineOut)
def update_line(body: schemas.LineIn, line: LineDep, session: SessionDep, today: TodayDep):
    line.numbers = _check_numbers(body.numbers, today)
    session.commit()
    return line


@router.delete("/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line(line: LineDep, session: SessionDep):
    session.delete(line)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
