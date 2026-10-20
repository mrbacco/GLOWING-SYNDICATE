# File:     backend/app/config.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Settings, read from environment variables so production can change them without code."""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

# SQLite file next to where the server is started. Postgres later: postgresql+psycopg://...
DATABASE_URL = os.environ.get("SYNDICATE_DATABASE_URL", "sqlite:///./syndicate.db")

# The address people use to reach this server, for the member page links in messages.
# On the developer's PC that is only reachable from the PC itself (or a phone with adb reverse).
PUBLIC_URL = os.environ.get("SYNDICATE_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/")

# Fetch Lotto results from lottery.ie by itself after each draw. Set to 0 to switch it off.
FETCH_RESULTS = os.environ.get("SYNDICATE_FETCH_RESULTS", "1") != "0"

# "production" when hosted: then an API key is required and the interactive docs are switched off.
PRODUCTION = os.environ.get("SYNDICATE_ENV", "development") == "production"

# The organiser's access key. Every API call must send it as "Authorization: Bearer <key>";
# member pages (/m/<code>) and /health stay open. Unset means no key is checked (development only).
API_KEY = os.environ.get("SYNDICATE_API_KEY") or None

# Syndicates are Irish, so "this week" and "today" follow Irish time, not the server's.
TIMEZONE = ZoneInfo(os.environ.get("SYNDICATE_TIMEZONE", "Europe/Dublin"))


def today() -> date:
    return datetime.now(TIMEZONE).date()
