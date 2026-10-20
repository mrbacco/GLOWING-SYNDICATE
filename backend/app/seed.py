# File:     backend/app/seed.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Sample data, the same as the Android app's FakeSyndicateRepository.

Run `python -m app.seed` to wipe the database and load it.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import config, models
from app.db import Base, make_engine, make_sessionmaker
from app.domain.lotto import DrawDay
from app.domain.weeks import week_start, weeks_between

# Real Irish Lotto results from lottery.ie/results/lotto/history (fetched 2026-10-20).
SAMPLE_DRAWS = [
    (date(2026, 10, 19), [19, 26, 30, 33, 34, 40], 14),
    (date(2026, 10, 17), [13, 21, 27, 38, 41, 43], 42),
    (date(2026, 10, 14), [1, 18, 25, 26, 39, 45], 8),
    (date(2026, 10, 12), [20, 22, 23, 28, 39, 41], 2),
    (date(2026, 10, 10), [5, 8, 15, 22, 24, 41], 29),
]


def seed(session: Session, today: date) -> None:
    this_week = week_start(today)
    office = models.Syndicate(id="s-office", name="Office Syndicate", weekly_cost_cents=500)
    office.draw_days = [DrawDay.WEDNESDAY, DrawDay.SATURDAY]
    family = models.Syndicate(id="s-family", name="Family Lotto", weekly_cost_cents=300)
    family.draw_days = [DrawDay.SATURDAY]
    session.add_all([office, family])

    def member(id_: str, syndicate: models.Syndicate, name: str, weeks_ago: int) -> models.Member:
        return models.Member(id=id_, syndicate=syndicate, name=name, joined=this_week - timedelta(weeks=weeks_ago))

    members = [
        member("m1", office, "Aoife", 3),
        member("m2", office, "Ciarán", 3),
        member("m3", office, "Niamh", 2),
        member("m4", office, "Seán", 1),
        member("m5", family, "Mam", 1),
        member("m6", family, "Dad", 1),
    ]
    session.add_all(members)  # in this order, so the members list keeps it

    # Everyone paid every week, except: Ciarán missed this week, Seán has paid nothing.
    for m in members:
        if m.id == "m4":
            continue
        for week in weeks_between(m.joined, this_week):
            if not (m.id == "m2" and week == this_week):
                session.add(models.Payment(member=m, week_start=week))

    for id_, syndicate, numbers in [
        ("l1", office, [3, 12, 24, 27, 38, 41]),
        ("l2", office, [7, 11, 14, 21, 22, 33]),
        ("l3", family, [1, 9, 17, 25, 33, 45]),
    ]:
        line = models.Line(id=id_, syndicate=syndicate)
        line.numbers = numbers
        session.add(line)

    for draw_date, numbers, bonus in SAMPLE_DRAWS:
        draw = models.Draw(draw_date=draw_date, bonus=bonus, source="lottery.ie")
        draw.numbers = numbers
        session.add(draw)
    session.commit()


def reset_and_seed(database_url: str = config.DATABASE_URL, today: date | None = None) -> None:
    engine = make_engine(database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with make_sessionmaker(engine)() as session:
        seed(session, today or config.today())
    engine.dispose()


if __name__ == "__main__":
    reset_and_seed()
    print(f"Loaded sample data into {config.DATABASE_URL}")
