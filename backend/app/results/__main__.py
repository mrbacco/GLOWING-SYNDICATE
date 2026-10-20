# File:     backend/app/results/__main__.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""`python -m app.results`: fetches the latest results from lottery.ie once and saves them."""

import logging
import sys

from app import config
from app.db import Base, make_engine, make_sessionmaker
from app.results import importer, lottery_ie


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = make_engine(config.DATABASE_URL)
    Base.metadata.create_all(engine)
    try:
        summary = importer.fetch_and_save(make_sessionmaker(engine))
    except lottery_ie.ScrapeError as e:
        print(f"Could not fetch results: {e}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()
    print(f"Results: {summary}")
    for day in summary.added:
        print(f"  added   {day}")
    for day in summary.updated:
        print(f"  updated {day}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
