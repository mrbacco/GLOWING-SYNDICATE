# File:     backend/tests/test_winnings.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Winnings split: who shares a win and how much each gets."""

from datetime import date
from html import unescape

from app.domain.winnings import LinePrize, MemberIn, split_winnings
from app.results import importer
from tests.test_results import SATURDAY_17, page

SAT = date(2026, 10, 17)
WEEK = date(2026, 10, 12)


def member(id_, joined=date(2026, 10, 1), paid=(WEEK,)):
    return MemberIn(id_, id_.title(), joined, frozenset(paid))


def test_split_with_left_over_cents():
    split = split_winnings(SAT, [LinePrize(400)], [member("a"), member("b"), member("c")])
    assert (split.total_cents, split.each_cents, split.left_over_cents) == (400, 133, 1)


def test_unpaid_and_late_joiners_are_left_out():
    split = split_winnings(SAT, [LinePrize(400)], [member("a"), member("b", paid=()), member("c", joined=date(2026, 10, 18))])
    assert [m.id for m in split.sharers] == ["a"]
    assert {m.id: m.reason for m in split.left_out} == {"b": "hadn't paid for that week", "c": "joined after this draw"}


def test_unpublished_amounts_are_not_split():
    split = split_winnings(SAT, [LinePrize()], [member("a")])
    assert not split.all_published and split.each_cents == 0


def test_results_screen_and_member_page(seeded):
    importer.fetch_and_save(seeded.app.state.sessionmaker, lambda: page(SATURDAY_17))
    card = seeded.get("/screens/syndicates/s-office/results").json()["winnings"]
    assert card["lines"][0] == "Total: €4 from 1 winning line"
    assert "€1.33 each" in card["lines"][1]
    assert "1 cent left over for the syndicate kitty" in card["lines"]
    assert card["lines"][-1] == "Not included: Seán (hadn't paid for that week)"
    members = seeded.get("/screens/syndicates/s-office/members").json()["members"]
    url = {m["name"]: m["page_url"] for m in members}
    aoife = unescape(seeded.get(url["Aoife"].removeprefix("http://127.0.0.1:8000")).text)
    assert "Your share of the latest win: €1.33" in aoife and "Seán" not in aoife
    sean = unescape(seeded.get(url["Seán"].removeprefix("http://127.0.0.1:8000")).text)
    assert "you hadn't paid for that week" in sean


def test_messages_mention_each_members_share(seeded):
    importer.fetch_and_save(seeded.app.state.sessionmaker, lambda: page(SATURDAY_17))
    members = {m["name"]: m for m in seeded.get("/screens/syndicates/s-office/members").json()["members"]}
    assert members["Aoife"]["message"].startswith(
        "Hi Aoife! Good news: we won €4 in the Sat 17 Oct 2026 draw, and your share is €1.33. Your page for Office Syndicate:"
    )
    assert "We won €4 in the Sat 17 Oct 2026 draw, but you hadn't paid for that week" in members["Seán"]["message"]
    assert "you owe €10.00" in members["Seán"]["message"]


def test_group_message_names_nobody(seeded):
    importer.fetch_and_save(seeded.app.state.sessionmaker, lambda: page(SATURDAY_17))
    message = seeded.get("/screens/syndicates/s-office/results").json()["group_message"]
    assert message.splitlines() == [
        "Office Syndicate: Sat 17 Oct 2026 results",
        "Numbers: 13 21 27 38 41 43 + bonus 42",
        "We won €4 (Match 3)!",
        "Shared by the 3 members who paid for the week of 12 Oct: €1.33 each.",
        "Reminder: it's €5.00 a week. If you haven't paid this week yet, please do, and check your own page for your payments.",
    ]
    for name in ("Aoife", "Ciarán", "Niamh", "Seán"):
        assert name not in message


def test_group_message_without_a_win(seeded):
    message = seeded.get("/screens/syndicates/s-family/results").json()["group_message"]
    assert "No win this time across our 1 line." in message
