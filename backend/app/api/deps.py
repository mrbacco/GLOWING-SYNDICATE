# File:     backend/app/api/deps.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Shared pieces the endpoints ask for: the database session, today's date, lookups."""

import secrets
from collections.abc import Iterator
from datetime import date
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app import config, models


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.sessionmaker() as session:
        yield session


def get_today() -> date:
    """Overridden in tests to pin the date."""
    return config.today()


def require_api_key(request: Request) -> None:
    """Lets a request through only with the organiser's key, when the server has one set."""
    expected = request.app.state.api_key
    if expected is None:
        return
    scheme, _, given = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not secrets.compare_digest(given.strip().encode(), expected.encode()):
        raise HTTPException(
            status_code=401, detail="Missing or wrong access key.", headers={"WWW-Authenticate": "Bearer"}
        )


def get_public_url(request: Request) -> str:
    return request.app.state.public_url


SessionDep = Annotated[Session, Depends(get_session)]
TodayDep = Annotated[date, Depends(get_today)]
PublicUrlDep = Annotated[str, Depends(get_public_url)]


def find(session: Session, model: type, key, what: str):
    row = session.get(model, key)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{what} not found")
    return row


def get_syndicate(syndicate_id: str, session: SessionDep) -> models.Syndicate:
    return find(session, models.Syndicate, syndicate_id, "Syndicate")


def get_member(member_id: str, session: SessionDep) -> models.Member:
    return find(session, models.Member, member_id, "Member")


def get_line(line_id: str, session: SessionDep) -> models.Line:
    return find(session, models.Line, line_id, "Line")


SyndicateDep = Annotated[models.Syndicate, Depends(get_syndicate)]
MemberDep = Annotated[models.Member, Depends(get_member)]
LineDep = Annotated[models.Line, Depends(get_line)]
