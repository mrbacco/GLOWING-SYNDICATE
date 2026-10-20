# File:     backend/tests/conftest.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_today
from app.main import create_app
from app.seed import seed

# A Tuesday: this week started on Monday 19 October 2026.
TODAY = date(2026, 10, 20)


@pytest.fixture
def client(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}", fetch_results=False)
    app.dependency_overrides[get_today] = lambda: TODAY
    with TestClient(app) as test_client:  # runs startup, which creates the tables
        yield test_client


@pytest.fixture
def seeded(client):
    with client.app.state.sessionmaker() as session:
        seed(session, TODAY)
    return client
