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
from app.domain import lotto, phones, text, winnings
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


def members(
    syndicate: models.Syndicate, today: date, public_url: str, draws: list[models.Draw] = ()
) -> schemas.MembersScreen:
    """[draws] newest first; if the latest one the syndicate plays won, messages mention each share."""
    latest = latest_played_draw(syndicate, list(draws))
    split = draw_split(syndicate, latest) if latest else None
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
                message=text.member_message(
                    member.name, syndicate.name, b.amount_owed_cents, url, win_note(split, member.id)
                ),
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
    split = draw_split(syndicate, latest)
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
        winnings=winnings_card(split) if split else None,
        group_message=group_message(syndicate, latest, rows, split),
        empty_text=None,
    )


def win_note(split: winnings.Split | None, member_id: str) -> str | None:
    """One sentence for a member's message about the latest win, or None if there's nothing to say."""
    if split is None:
        return None
    when = f"the {text.draw_date(split.draw_date)} draw"
    reason = next((m.reason for m in split.left_out if m.id == member_id), None)
    if reason == "joined after this draw":
        return None  # the win is nothing to do with them
    if reason:  # hadn't paid for that week
        won = f"{text.amount(split.total_cents)} " if split.all_published and split.total_cents else ""
        return f"We won {won}in {when}, but you {reason}, so there's no share for you this time."
    if not split.all_published:
        return f"Good news: we won in {when}! Your share will be on your page once the prize amounts are out."
    if not split.total_cents:
        return f"Good news: we won {text.names(split.non_cash)} in {when}." if split.non_cash else None
    return (
        f"Good news: we won {text.amount(split.total_cents)} in {when}, "
        f"and your share is {text.euro(split.share_of(member_id))}."
    )


def group_message(
    syndicate: models.Syndicate,
    draw: models.Draw,
    rows: list[schemas.LineResultRow],
    split: winnings.Split | None,
) -> str:
    """The latest result for the syndicate's group chat. It never names who paid or who owes."""
    numbers = " ".join(str(n) for n in draw.numbers)
    out = [
        f"{syndicate.name}: {text.draw_date(draw.draw_date)} results",
        f"Numbers: {numbers} + bonus {draw.bonus}",
    ]
    tiers = [r.prize_tier for r in rows if r.prize_tier]
    if not syndicate.lines:
        out.append("We don't have any lines entered yet.")
    elif not tiers:
        out.append(f"No win this time across our {len(syndicate.lines)} {'line' if len(syndicate.lines) == 1 else 'lines'}.")
    elif split is None or not split.all_published:
        out.append(f"We won ({text.names(tiers)})! The prize amount isn't published yet.")
    else:
        won = text.amount(split.total_cents) if split.total_cents else text.names(split.non_cash)
        out.append(f"We won {won} ({text.names(tiers)})!")
        if split.total_cents and split.sharers:
            count = len(split.sharers)
            who = "the 1 member" if count == 1 else f"the {count} members"
            out.append(
                f"Shared by {who} who paid for the week of {text.short_date(split.week)}: {text.euro(split.each_cents)} each."
            )
    out.append(
        f"Reminder: it's {text.euro(syndicate.weekly_cost_cents)} a week. If you haven't paid this week yet, "
        "please do, and check your own page for your payments."
    )
    return "\n".join(out)


def latest_played_draw(syndicate: models.Syndicate, draws: list[models.Draw]) -> models.Draw | None:
    days = set(syndicate.draw_days)
    return next((d for d in draws if lotto.DrawDay.of(d.draw_date) in days), None)


def draw_split(syndicate: models.Syndicate, draw: models.Draw) -> winnings.Split | None:
    """How the syndicate's winnings in [draw] are shared, or None if no line won anything."""
    rules = lotto.rules_for(draw.draw_date)
    prizes = []
    for line in syndicate.lines:
        tier = lotto.check_line(line.numbers, draw.numbers, draw.bonus, rules).tier
        if tier:
            prize = draw.prize_for(tier.code)
            prizes.append(winnings.LinePrize(prize.prize_cents, prize.prize_text) if prize else winnings.LinePrize())
    if not prizes:
        return None
    members = [
        winnings.MemberIn(m.id, m.name, m.joined, frozenset(p.week_start for p in m.payments))
        for m in syndicate.members
    ]
    return winnings.split_winnings(draw.draw_date, prizes, members)


def winnings_card(split: winnings.Split) -> schemas.SummaryCard:
    lines_won = f"{split.winning_lines} winning {'line' if split.winning_lines == 1 else 'lines'}"
    out = []
    if not split.all_published:
        out.append(f"{lines_won.capitalize()}. The prize amounts aren't published yet, so the split will show once they are.")
    else:
        out.append(f"Total: {text.amount(split.total_cents)} from {lines_won}")
        out.extend(f"Also won: {prize} (not shared as cash)" for prize in split.non_cash)
        week = text.short_date(split.week)
        if not split.sharers:
            out.append(f"No one had paid for the week of {week}, so there's no one to share it with yet.")
        elif split.total_cents:
            count = len(split.sharers)
            out.append(
                f"Shared by {'the 1 member' if count == 1 else f'{count} members'} who paid for the week of {week}: "
                f"{text.euro(split.each_cents)} each"
            )
            out.append(text.names([m.name for m in split.sharers]))
            if split.left_over_cents:
                out.append(f"{text.cents(split.left_over_cents)} left over for the syndicate kitty")
    if split.left_out:
        out.append("Not included: " + "; ".join(f"{m.name} ({m.reason})" for m in split.left_out))
    return schemas.SummaryCard(title=f"Winnings · {text.draw_date(split.draw_date)}", lines=out)


def my_share(split: winnings.Split | None, member_id: str) -> str | None:
    """One line for a member's page about their share of the latest win, or None if nothing was won."""
    if split is None:
        return None
    if not split.all_published:
        return "We won! Your share will show once the prize amounts are published."
    share = split.share_of(member_id)
    if share is not None:
        return f"Your share of the latest win: {text.euro(share)}" if split.total_cents else None
    reason = next((m.reason for m in split.left_out if m.id == member_id), None)
    return f"No share of the latest win for you: you {reason}." if reason else None
