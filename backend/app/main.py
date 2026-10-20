# File:     backend/app/main.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The FastAPI application. Run with: uvicorn app.main:app --reload"""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app import __version__, config
from app.api import draws, member_page, screens, syndicates
from app.api.deps import require_api_key
from app.db import Base, make_engine, make_sessionmaker
from app.results import lottery_ie, scheduler

logging.getLogger("syndicate").setLevel(logging.INFO)


def create_app(
    database_url: str = config.DATABASE_URL,
    public_url: str = config.PUBLIC_URL,
    fetch_results: bool = config.FETCH_RESULTS,
    api_key: str | None = config.API_KEY,
    production: bool = config.PRODUCTION,
) -> FastAPI:
    if production and not api_key:
        raise RuntimeError("SYNDICATE_API_KEY must be set when SYNDICATE_ENV=production.")
    engine = make_engine(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Creates missing tables. Proper migrations (Alembic) come with Postgres.
        Base.metadata.create_all(engine)
        watcher = asyncio.create_task(scheduler.watch(app.state.sessionmaker)) if fetch_results else None
        yield
        if watcher:
            watcher.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watcher
        engine.dispose()

    # No interactive docs in production: they would show the whole API to anyone.
    docs = {} if not production else {"docs_url": None, "redoc_url": None, "openapi_url": None}
    app = FastAPI(title="SYNDICATE API", version=__version__, lifespan=lifespan, **docs)
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.engine = engine
    app.state.public_url = public_url
    app.state.api_key = api_key
    app.state.fetch_html = lottery_ie.fetch_html  # replaced in tests
    app.state.last_manual_fetch = None

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok", "version": __version__}

    # Everything the app uses needs the organiser's key; member pages are opened by their own secret link.
    organiser_only = [Depends(require_api_key)]
    app.include_router(screens.router, dependencies=organiser_only)
    app.include_router(syndicates.router, dependencies=organiser_only)
    app.include_router(draws.router, dependencies=organiser_only)
    app.include_router(member_page.router)
    return app


app = create_app()
