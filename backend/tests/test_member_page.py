# File:     backend/tests/test_member_page.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The member page at /m/<token>, with the sample data and today pinned to Tuesday 20 October 2026."""

from html import unescape


def page_path(client, name: str, syndicate: str = "s-office") -> str:
    members = client.get(f"/screens/syndicates/{syndicate}/members").json()["members"]
    url = next(m["page_url"] for m in members if m["name"] == name)
    return url.removeprefix("http://127.0.0.1:8000")


def page_text(client, name: str) -> str:
    """The page as a browser shows it (the template encodes characters like ' as &#39;)."""
    response = client.get(page_path(client, name))
    assert response.status_code == 200
    return unescape(response.text)


def test_member_who_owes(seeded):
    html = page_text(seeded, "Seán")
    assert "<h1>Hi Seán</h1>" in html
    assert "You owe €10.00" in html
    assert "That's 2 weeks at €5.00 a week." in html
    assert "2 of 4 members paid this week" in html
    # Office plays Wed and Sat: the latest is Saturday's draw, where line 1 got Match 3.
    assert "Sat 17 Oct 2026" in html
    assert "Possible win: Match 3! Check the ticket." in html
    assert "Prize tier: Match 3" in html
    assert "2 lines every draw (Wed, Sat)" in html
    assert "Wed 14 Oct 2026" in html  # previous draws
    assert "Mon 19 Oct 2026" not in html  # not a draw this syndicate plays


def test_member_who_is_paid_up(seeded):
    html = page_text(seeded, "Aoife")
    assert "You're all paid up" in html
    assert "You owe" not in html


def test_page_shows_no_other_members_amounts(seeded):
    html = page_text(seeded, "Aoife")
    assert "Seán" not in html and "€10.00" not in html


def test_unknown_link(seeded):
    response = seeded.get("/m/not-a-real-link")
    assert response.status_code == 404
    assert "This link doesn't work" in unescape(response.text)


def test_page_is_private(seeded):
    response = seeded.get(page_path(seeded, "Aoife"))
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "noindex" in response.headers["x-robots-tag"]
    assert "default-src 'none'" in response.headers["content-security-policy"]


def test_links_are_unique_and_long(seeded):
    members = seeded.get("/screens/syndicates/s-office/members").json()["members"]
    tokens = [m["page_url"].rsplit("/", 1)[1] for m in members]
    assert len(set(tokens)) == len(tokens)
    assert all(len(t) >= 20 for t in tokens)


def test_names_are_escaped(seeded):
    seeded.post("/syndicates/s-office/members", json={"name": "<script>alert(1)</script>"})
    html = seeded.get(page_path(seeded, "<script>alert(1)</script>")).text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_removed_member_link_stops_working(seeded):
    path = page_path(seeded, "Seán")
    seeded.delete("/members/m4")
    assert seeded.get(path).status_code == 404
