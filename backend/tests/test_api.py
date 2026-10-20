# File:     backend/tests/test_api.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The HTTP API, using the sample data with today pinned to Tuesday 20 October 2026."""


def by_name(rows):
    return {r["name"]: r for r in rows}


# ------------------------------------------------------------------ screens


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_syndicate_list_screen(seeded):
    rows = seeded.get("/screens/syndicates").json()["syndicates"]
    assert [(r["name"], r["subtitle"]) for r in rows] == [
        ("Office Syndicate", "€5.00 per week · Wed, Sat"),
        ("Family Lotto", "€3.00 per week · Sat"),
    ]


def test_members_screen_matches_the_app(seeded):
    screen = seeded.get("/screens/syndicates/s-office/members").json()
    assert screen["summary"] == {
        "title": "Week of 19 Oct",
        "lines": ["2 of 4 members paid this week", "Total owed: €15.00"],
    }
    assert [m["name"] for m in screen["members"]] == ["Aoife", "Ciarán", "Niamh", "Seán"]
    members = by_name(screen["members"])
    assert members["Aoife"]["status"] == "All paid up"
    assert members["Ciarán"]["status"] == "Owes €5.00 (1 week)"
    assert members["Seán"]["status"] == "Owes €10.00 (2 weeks)"
    # The sample Sat 17 Oct draw won Match 3 (amounts not loaded in the sample), and Seán hadn't paid that week.
    assert members["Seán"]["message"].startswith(
        "Hi Seán! We won in the Sat 17 Oct 2026 draw, but you hadn't paid for that week, so there's no share "
        "for you this time. A quick reminder for Office Syndicate: you owe €10.00."
    )
    assert members["Seán"]["message"].endswith(members["Seán"]["page_url"])
    assert members["Seán"]["page_url"].startswith("http://127.0.0.1:8000/m/")
    assert screen["week_start"] == "2026-10-19"


def test_lines_screen(seeded):
    screen = seeded.get("/screens/syndicates/s-office/lines").json()
    assert screen["summary"]["lines"] == ["2 lines every draw (Wed, Sat)"]
    assert [line["numbers"] for line in screen["lines"]] == [[3, 12, 24, 27, 38, 41], [7, 11, 14, 21, 22, 33]]


def test_results_screen_only_uses_the_syndicates_draw_days(seeded):
    screen = seeded.get("/screens/syndicates/s-office/results").json()
    # Office plays Wed and Sat, so Monday 19 October is skipped.
    assert screen["latest_draw"]["title"] == "Sat 17 Oct 2026"
    assert screen["verdict"] == "Possible win: Match 3! Check the ticket."
    best = screen["results"][0]
    assert best["numbers"] == [3, 12, 24, 27, 38, 41]
    assert best["matched"] == [27, 38, 41]
    assert (best["text"], best["prize_tier"], best["won"]) == ("Matched 3 numbers", "Match 3", True)
    assert screen["results"][1]["text"] == "Matched 1 number"
    assert [d["title"] for d in screen["previous_draws"]] == ["Wed 14 Oct 2026", "Sat 10 Oct 2026"]


def test_results_screen_without_lines_or_draws(client):
    syndicate = client.post("/syndicates", json={"name": "New", "weekly_cost_cents": 200}).json()
    screen = client.get(f"/screens/syndicates/{syndicate['id']}/results").json()
    assert screen["latest_draw"] is None
    assert screen["empty_text"] == "No draw results yet."


def test_unknown_syndicate_is_404(client):
    assert client.get("/screens/syndicates/nope/members").status_code == 404


# ---------------------------------------------------------------- syndicates


def test_create_update_delete_syndicate(seeded):
    created = seeded.post("/syndicates", json={"name": "  GAA Club ", "weekly_cost_cents": 400})
    assert created.status_code == 201
    syndicate = created.json()
    assert syndicate["name"] == "GAA Club"
    assert syndicate["draw_days"] == ["MON", "WED", "SAT"]  # every draw of the current game

    updated = seeded.patch(f"/syndicates/{syndicate['id']}", json={"draw_days": ["SAT", "MON"]}).json()
    assert updated["draw_days"] == ["MON", "SAT"]

    assert seeded.delete("/syndicates/s-office").status_code == 204
    assert seeded.get("/syndicates/s-office").status_code == 404
    assert seeded.patch("/members/m1", json={"name": "x"}).status_code == 404  # members went too


def test_rejects_bad_syndicates(client):
    assert client.post("/syndicates", json={"name": " ", "weekly_cost_cents": 400}).status_code == 422
    assert client.post("/syndicates", json={"name": "A", "weekly_cost_cents": 0}).status_code == 422
    assert client.post("/syndicates", json={"name": "A", "weekly_cost_cents": 400, "draw_days": []}).status_code == 422
    assert client.post("/syndicates", json={"name": "A", "weekly_cost_cents": 400, "draw_days": ["FRI"]}).status_code == 422


# ------------------------------------------------------- members, payments


def test_add_member_with_phone(seeded):
    member = seeded.post("/syndicates/s-office/members", json={"name": "Pat", "phone": "087 123 4567"}).json()
    assert member["joined"] == "2026-10-20"
    row = by_name(seeded.get("/screens/syndicates/s-office/members").json()["members"])["Pat"]
    assert row["whatsapp_number"] == "353871234567"
    assert row["status"] == "Owes €5.00 (1 week)"


def test_rejects_bad_phone(seeded):
    response = seeded.post("/syndicates/s-office/members", json={"name": "Pat", "phone": "call me"})
    assert response.status_code == 422


def test_update_and_remove_phone(seeded):
    assert seeded.patch("/members/m1", json={"phone": "0861112222"}).json()["phone"] == "0861112222"
    assert seeded.patch("/members/m1", json={"phone": ""}).json()["phone"] is None
    assert seeded.patch("/members/m1", json={"name": "Aoife B"}).json()["name"] == "Aoife B"


def test_payments_by_any_day_of_the_week(seeded):
    # Wednesday 21 October counts as the week of Monday 19 October; doing it twice is fine.
    assert seeded.put("/members/m2/payments/2026-10-21").status_code == 204
    assert seeded.put("/members/m2/payments/2026-10-19").status_code == 204
    members = by_name(seeded.get("/screens/syndicates/s-office/members").json()["members"])
    assert members["Ciarán"]["status"] == "All paid up"

    assert seeded.delete("/members/m2/payments/2026-10-19").status_code == 204
    members = by_name(seeded.get("/screens/syndicates/s-office/members").json()["members"])
    assert members["Ciarán"]["paid_this_week"] is False


def test_delete_member(seeded):
    assert seeded.delete("/members/m4").status_code == 204
    screen = seeded.get("/screens/syndicates/s-office/members").json()
    assert screen["summary"]["lines"] == ["2 of 3 members paid this week", "Total owed: €5.00"]


# --------------------------------------------------------------------- lines


def test_lines_crud(seeded):
    line = seeded.post("/syndicates/s-office/lines", json={"numbers": [41, 3, 12, 24, 27, 38]}).json()
    assert line["numbers"] == [3, 12, 24, 27, 38, 41]
    assert seeded.put(f"/lines/{line['id']}", json={"numbers": [1, 2, 3, 4, 5, 6]}).json()["numbers"] == [1, 2, 3, 4, 5, 6]
    assert seeded.delete(f"/lines/{line['id']}").status_code == 204
    assert seeded.delete(f"/lines/{line['id']}").status_code == 404


def test_rejects_bad_lines(seeded):
    response = seeded.post("/syndicates/s-office/lines", json={"numbers": [1, 2, 3, 4, 5, 46]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Numbers must be from 1 to 45."


# --------------------------------------------------------------- draws, rules


def test_save_draw(seeded):
    body = {"numbers": [1, 2, 3, 4, 5, 6], "bonus": 7}
    assert seeded.put("/draws/2026-10-21", json=body).status_code == 200  # Wednesday
    assert seeded.get("/draws?limit=1").json()[0]["draw_date"] == "2026-10-21"
    assert seeded.put("/draws/2026-10-20", json=body).status_code == 422  # no Tuesday draw
    assert seeded.put("/draws/2026-10-21", json={"numbers": [1, 2, 3, 4, 5, 6], "bonus": 6}).status_code == 422
    assert seeded.put("/draws/2026-10-21", json={"numbers": [1, 2, 3, 4, 5, 46], "bonus": 7}).status_code == 422
    # The old game had 47 balls.
    assert seeded.put("/draws/2026-08-29", json={"numbers": [1, 2, 3, 4, 5, 46], "bonus": 47}).status_code == 200


def test_rules(client):
    current = client.get("/rules").json()
    assert (current["name"], current["max_number"], current["draw_day_labels"]) == ("Lotto 6/45", 45, ["Mon", "Wed", "Sat"])
    assert current["tiers"][-1] == {
        "code": "MATCH_2_BONUS", "label": "Match 2 + Bonus", "matches": 2, "bonus": True, "fixed_prize_cents": 400,
    }
    assert client.get("/rules?on=2026-08-01").json()["name"] == "Lotto 6/47"
