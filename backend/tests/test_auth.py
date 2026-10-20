# File:     backend/tests/test_auth.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""The organiser's access key, and production settings."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.seed import seed
from tests.conftest import TODAY

KEY = "test-key-0123456789"


@pytest.fixture
def locked(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}", fetch_results=False, api_key=KEY)
    with TestClient(app) as client:
        with app.state.sessionmaker() as session:
            seed(session, TODAY)
        yield client


def test_api_needs_the_key(locked):
    assert locked.get("/screens/syndicates").status_code == 401
    assert locked.get("/screens/syndicates", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert locked.post("/syndicates", json={"name": "X", "weekly_cost_cents": 100}).status_code == 401
    assert locked.post("/draws/fetch").status_code == 401
    ok = locked.get("/screens/syndicates", headers={"Authorization": f"Bearer {KEY}"})
    assert ok.status_code == 200 and len(ok.json()["syndicates"]) == 2


def test_member_pages_and_health_stay_open(locked):
    assert locked.get("/health").status_code == 200
    members = locked.get("/screens/syndicates/s-office/members", headers={"Authorization": f"Bearer {KEY}"}).json()
    path = members["members"][0]["page_url"].removeprefix("http://127.0.0.1:8000")
    assert locked.get(path).status_code == 200


def test_production_needs_a_key(tmp_path):
    with pytest.raises(RuntimeError):
        create_app(f"sqlite:///{tmp_path / 'p.db'}", fetch_results=False, production=True, api_key=None)


def test_production_hides_the_docs(tmp_path):
    app = create_app(f"sqlite:///{tmp_path / 'p.db'}", fetch_results=False, production=True, api_key=KEY)
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
