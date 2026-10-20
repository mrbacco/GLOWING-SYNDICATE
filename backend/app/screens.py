# File:     backend/app/screens.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Builds the screen responses: everything a screen shows, worked out and worded on the server."""

from datetime import date

from app import models, schemas
from app.domain import lotto, phones, text
from app.domain.ledger import balance
from app.domain.weeks import week_start

PREVIOUS_DRAWS_SHOWN = 4


def syndicate_out(syndicate: models.Syndicate) -> schemas.SyndicateOut:
    return schemas.SyndicateOut.model_validate(syndicate)


def _days(syndicate: models.Syndicate) -> str:
    return ", ".join(d.label for d in syndicate.draw_days)


def syndicate_list(syndicates: list[models.Syndicate]) -> schemas.SyndicateListScreen:
    return schemas.SyndicateListScreen(
        syndicates=[
            schemas.SyndicateRow(
                id=s.id,
                name=s.name,
                subtitle=f"{text.euro(s.weekly_cost_cents)} per week · {_days(s)}",
            )
            for s in syndicates
        ]
    )


def page_url(public_url: str, member: models.Member) -> str:
    return f"{public_url}/m/{member.share_token}"


def members(syndicate: models.Syndicate, today: date, public_url: str) -> schemas.MembersScreen:
    rows = []
    for member in syndicate.members:
        url = page_url(public_url, member)
        paid_weeks = {p.week_start for p in member.payments}
        b = balance(member.joined, paid_weeks, syndicate.weekly_cost_cents, today)
        status = (
            "All paid up"
            if b.weeks_owed == 0
            else f"Owes {text.euro(b.amount_owed_cents)} ({text.weeks(b.weeks_owed)})"
        )
        rows.append(
            schemas.MemberRow(
                id=member.id,
                name=member.name,
                phone=member.phone,
                whatsapp_number=phones.international(member.phone) if member.phone else None,
                paid_this_week=b.paid_this_week,
                weeks_owed=b.weeks_owed,
                amount_owed_cents=b.amount_owed_cents,
                status=status,
                message=text.member_message(member.name, syndicate.name, b.amount_owed_cents, url),
                page_url=url,
            )
        )
    this_week = week_start(today)
    paid = sum(r.paid_this_week for r in rows)
    return schemas.MembersScreen(
        syndicate=syndicate_out(syndicate),
        week_start=this_week,
        summary=schemas.SummaryCard(
            title=f"Week of {text.short_date(this_week)}",
            lines=[
                f"{paid} of {len(rows)} members paid this week",
                f"Total owed: {text.euro(sum(r.amount_owed_cents for r in rows))}",
            ],
        ),
        members=rows,
        empty_text=None if rows else "No members yet. Tap + to add the first one.",
    )


def lines(syndicate: models.Syndicate) -> schemas.LinesScreen:
    count = len(syndicate.lines)
    return schemas.LinesScreen(
        syndicate=syndicate_out(syndicate),
        summary=schemas.SummaryCard(
            title="Lines played",
            lines=[f"{count} {'line' if count == 1 else 'lines'} every draw ({_days(syndicate)})"],
        ),
        lines=[schemas.LineRow(id=line.id, numbers=line.numbers) for line in syndicate.lines],
        empty_text=None if count else "No lines yet. Tap + to add the numbers you play.",
    )


def _draw_card(draw: models.Draw) -> schemas.DrawCard:
    return schemas.DrawCard(
        draw_date=draw.draw_date, title=text.draw_date(draw.draw_date), numbers=draw.numbers, bonus=draw.bonus
    )


def _prize_amount(draw: models.Draw, tier_code: str) -> str | None:
    """What a tier paid per winning line in [draw], as published; None until it is known."""
    prize = draw.prize_for(tier_code)
    if prize is None:
        return None
    return text.amount(prize.prize_cents) if prize.prize_cents is not None else prize.prize_text or None


def results(syndicate: models.Syndicate, draws: list[models.Draw]) -> schemas.ResultsScreen:
    """[draws] newest first. Only draws on the syndicate's draw days are shown."""
    days = set(syndicate.draw_days)
    played = [d for d in draws if lotto.DrawDay.of(d.draw_date) in days]
    if not played:
        return schemas.ResultsScreen(
            syndicate=syndicate_out(syndicate),
            latest_draw=None,
            verdict=None,
            results=[],
            previous_draws=[],
            empty_text="No draw results yet.",
        )

    latest = played[0]
    rules = lotto.rules_for(latest.draw_date)
    checked = [(line, lotto.check_line(line.numbers, latest.numbers, latest.bonus, rules)) for line in syndicate.lines]
    checked.sort(key=lambda pair: (lotto.tier_rank(pair[1], rules), -pair[1].match_count))
    rows = [
        schemas.LineResultRow(
            line_id=line.id,
            numbers=line.numbers,
            matched=sorted(result.matched),
            bonus_matched=result.bonus_matched,
            text=f"Matched {result.label}",
            prize_tier=result.tier.label if result.tier else None,
            prize_amount=_prize_amount(latest, result.tier.code) if result.tier else None,
            won=result.tier is not None,
        )
        for line, result in checked
    ]
    if not rows:
        verdict = "Add your lines to check them automatically."
    elif rows[0].prize_tier:
        amount = f", {rows[0].prize_amount}" if rows[0].prize_amount else ""
        verdict = f"Possible win: {rows[0].prize_tier}{amount}! Check the ticket."
    else:
        verdict = "No win this time."

    return schemas.ResultsScreen(
        syndicate=syndicate_out(syndicate),
        latest_draw=_draw_card(latest),
        verdict=verdict,
        results=rows,
        previous_draws=[_draw_card(d) for d in played[1 : 1 + PREVIOUS_DRAWS_SHOWN]],
        empty_text=None,
    )
