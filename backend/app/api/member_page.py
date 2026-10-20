# File:     backend/app/api/member_page.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The member page: a web page each member opens from their own link, with nothing to install.

It shows that member's payments and the syndicate's lines and results. The link is the only key
(there are no logins yet), so the page is never cached or indexed and never leaks its address.
"""

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app import models, screens
from app.api.deps import PublicUrlDep, SessionDep, TodayDep
from app.api.screens import recent_draws
from app.domain import text

router = APIRouter(tags=["member page"])
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

PRIVATE_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Robots-Tag": "noindex, nofollow",
    "X-Content-Type-Options": "nosniff",
    # Plain HTML and inline styles only: no scripts, no outside requests.
    "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'",
}


@router.get("/m/{token}", response_class=HTMLResponse, include_in_schema=False)
def member_page(token: str, request: Request, session: SessionDep, today: TodayDep, public_url: PublicUrlDep):
    member = session.scalars(select(models.Member).where(models.Member.share_token == token)).first()
    if member is None:
        return templates.TemplateResponse(request, "not_found.html", status_code=404, headers=PRIVATE_HEADERS)

    syndicate = member.syndicate
    draws = recent_draws(session)
    latest = screens.latest_played_draw(syndicate, draws)
    my_share = screens.my_share(screens.draw_split(syndicate, latest) if latest else None, member.id)
    members = screens.members(syndicate, today, public_url)
    me = next(row for row in members.members if row.id == member.id)
    paid_count = sum(row.paid_this_week for row in members.members)
    if me.weeks_owed:
        status = {
            "owes": True,
            "headline": f"You owe {text.euro(me.amount_owed_cents)}",
            "detail": f"That's {text.weeks(me.weeks_owed)} at {text.euro(syndicate.weekly_cost_cents)} a week. "
            "Please pay your organiser.",
        }
    else:
        status = {
            "owes": False,
            "headline": "You're all paid up",
            "detail": "Thanks! You're in for every draw this week.",
        }

    context = {
        "syndicate": syndicate.name,
        "member": member.name,
        "status": status,
        "week_title": members.summary.title,
        "week_line": f"{paid_count} of {len(members.members)} members paid this week",
        "draw_days": ", ".join(d.label for d in syndicate.draw_days),
        "lines": screens.lines(syndicate),
        "results": screens.results(syndicate, draws),
        "my_share": my_share,
    }
    return templates.TemplateResponse(request, "member.html", context, headers=PRIVATE_HEADERS)
