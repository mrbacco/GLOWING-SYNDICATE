<!--
File:     backend/README.md
Author:   mrbacco04@gmail.com
GitHub:   https://github.com/mrbacco
Created:  2026-10-20
Updated:  2026-10-20
Project:  SYNDICATE
License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial
-->
# SYNDICATE backend

Python service (FastAPI + SQLite) that stores syndicates, members, payments, played lines
and draw results, and owns every business rule: who owes what, the Lotto rules, line checking
and all the text the app shows. The Android app only displays what it gets back.

## Set up and run

From this `backend` folder (Python 3.12):

```
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m app.seed                 # wipes the database, loads sample data
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/docs to see and try every endpoint.

Tests: `.venv\Scripts\python -m pytest`

Settings (environment variables):

| Variable | Default | Meaning |
|---|---|---|
| `SYNDICATE_DATABASE_URL` | `sqlite:///./syndicate.db` | Database. Postgres later. |
| `SYNDICATE_TIMEZONE` | `Europe/Dublin` | Decides "today" and "this week". |
| `SYNDICATE_PUBLIC_URL` | `http://127.0.0.1:8000` | Address used in member page links. |
| `SYNDICATE_FETCH_RESULTS` | `1` | `0` stops the server fetching results by itself. |

## Results

Lotto results come from the official results history page,
https://www.lottery.ie/results/lotto/history, which embeds the last ~33 draws (about 11 weeks) as
JSON: numbers, bonus, and what each prize tier paid. Every draw is checked against the game rules
for its date (47 balls on Wed/Sat until 2 Sep 2026, then 45 on Mon/Wed/Sat) before it is saved;
anything odd is skipped and logged. The official results win: they add missing draws and correct
wrong ones.

- **By itself:** while the server runs, it checks every 15 minutes whether a result is due (from
  20:30 Irish time on a draw day) and missing, and only then downloads the page. If the result
  isn't up yet, or lottery.ie is down, it waits twice as long each time, up to 6 hours.
- **Once, now:** `.venv\Scripts\python -m app.results`, or `POST /draws/fetch` (at most once a minute).
- **By hand:** `PUT /draws/{date}` still works, e.g. if lottery.ie changes its page.

## Winnings split

When the syndicate's lines win in the latest draw, the Results screen gets a winnings card: the
total from lottery.ie's published prize amounts, divided equally between the members who had
joined by the draw and paid for that draw's week. Cents that don't divide go to the syndicate
kitty; members left out are named with the reason. Non-cash prizes are listed, not divided.
Each member's page shows only their own share (`app/domain/winnings.py`).

## Member page

Every member has a private web page at `/m/<code>`, for members who don't have the app
(for example on an iPhone): their payments ("You owe €10.00" or "You're all paid up"), how many
paid this week, the syndicate's lines, the latest result with prize tiers, and previous draws.
It never shows other members' names or amounts.

- The link is in every reminder and WhatsApp/SMS message the app sends (the `page_url` and
  `message` fields of the Members screen), so the organiser shares it with no extra step.
- The code is 128 random bits, so links can't be guessed. Removing a member stops their link.
- The page is plain HTML (no scripts, nothing loaded from elsewhere), is never cached or
  indexed, and sends no referrer.
- Until the server is hosted, links only open on the PC itself, or on a phone or emulator with
  `adb reverse tcp:8000 tcp:8000`.

## API

**Screens**: one call per app screen, returning everything it shows, already worded:

| Endpoint | Screen |
|---|---|
| `GET /screens/syndicates` | My syndicates |
| `GET /screens/syndicates/{id}/members` | Members tab: week summary, who owes what, ready-to-send messages |
| `GET /screens/syndicates/{id}/lines` | Lines tab |
| `GET /screens/syndicates/{id}/results` | Results tab: latest draw on the syndicate's days, checked lines, prize tiers |

**Changes**:

| Endpoint | Does |
|---|---|
| `POST /syndicates`, `PATCH`/`DELETE /syndicates/{id}` | Add, edit, delete a syndicate (and everything in it) |
| `POST /syndicates/{id}/members`, `PATCH`/`DELETE /members/{id}` | Add, edit, delete a member |
| `PUT`/`DELETE /members/{id}/payments/{date}` | Mark the week containing `{date}` paid or unpaid |
| `POST /syndicates/{id}/lines`, `PUT`/`DELETE /lines/{id}` | Add, change, delete a line |
| `POST /draws/fetch` | Fetch the latest results from lottery.ie now |
| `PUT`/`DELETE /draws/{date}`, `GET /draws` | Enter or correct a result by hand; list results |
| `GET /rules?on={date}` | Lotto rules on a date: number range, draw days, prize tiers |

## Code layout

```
app/
├── main.py        creates the app; run with uvicorn app.main:app
├── config.py      settings and "today" in Irish time
├── db.py          database connection
├── models.py      tables: syndicates, members, payments, lines, draws
├── schemas.py     request and response bodies
├── screens.py     builds the screen responses
├── seed.py        sample data (python -m app.seed)
├── templates/     member page HTML (base layout, member page, link not found)
├── results/       results from lottery.ie: lottery_ie.py (download, read), importer.py (save),
│                  scheduler.py (fetch after each draw), __main__.py (python -m app.results)
├── api/           endpoints: screens, syndicates (members, payments, lines), draws and rules,
│                  member_page (/m/<code>)
└── domain/        rules with no database or web code
    ├── lotto.py   game rules by date (6/47 until 2 Sep 2026, then 6/45), line checking
    ├── ledger.py  who owes what
    ├── winnings.py  who shares a win and how much each gets
    ├── weeks.py   Monday-to-Sunday payment weeks
    ├── text.py    euro amounts, dates, reminder messages
    └── phones.py  phone numbers for WhatsApp links
```

## Not yet

- Accounts and login: today anyone who can reach the server can read and change everything,
  so only run it on your own PC or network.
- Migrations (Alembic), added together with Postgres. Until then, a change to the tables means
  running `python -m app.seed` again, which wipes the data.
- A way to give a member a new link if theirs was shared by mistake.
- Notifications: next step.
- The PREDICTOR project's scraper was not found on this PC, so this one was written fresh; the
  two can be compared once PREDICTOR is available.
