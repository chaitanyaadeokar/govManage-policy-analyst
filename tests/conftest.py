"""
conftest.py
-----------
Shared pytest fixtures for govManage test suite.

Strategy:
- Patch database.MongoClient BEFORE importing app, so no real MongoDB
  connection is made during tests.
- Patch ChromaDB, ChatGroq, and crawler so tests are fully offline.
- Expose a Flask test client as `client`.
"""
from __future__ import annotations

import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — build minimal stubs so imports don't fail
# ---------------------------------------------------------------------------

def _make_mongo_stub():
    """Return a MagicMock that quacks like a MongoClient + collection."""
    col = MagicMock()
    col.count_documents.return_value = 1          # seed guards skip re-seeding
    col.find.return_value = iter([])
    col.find_one.return_value = None
    col.insert_one.return_value = MagicMock(inserted_id="fake_id")
    col.insert_many.return_value = MagicMock()
    col.update_one.return_value = MagicMock(upserted_id=None)
    col.delete_one.return_value = MagicMock()
    col.aggregate.return_value = iter([])

    db_obj = MagicMock()
    db_obj.__getitem__ = lambda self, key: col   # db["collection_name"] → col

    client = MagicMock()
    client.__getitem__ = lambda self, key: db_obj
    return client, db_obj, col


@pytest.fixture(scope="session")
def mongo_col():
    """Session-scoped raw mongo collection mock."""
    _, _, col = _make_mongo_stub()
    return col


@pytest.fixture(scope="session")
def app(mongo_col):
    """
    Create the Flask test app once per session.
    All external services are mocked.
    """
    client_mock, db_mock, col_mock = _make_mongo_stub()

    with (
        patch("pymongo.MongoClient", return_value=client_mock),
        patch("database.MongoClient", return_value=client_mock),
        # ChromaDB — stub so vector_store imports cleanly
        patch.dict("sys.modules", {
            "chromadb": MagicMock(),
            "chromadb.utils": MagicMock(),
            "chromadb.utils.embedding_functions": MagicMock(),
        }),
        # Crawler — stub
        patch.dict("sys.modules", {
            "firecrawl": MagicMock(),
            "tavily": MagicMock(),
        }),
        # APScheduler — don't actually start scheduler
        patch("scheduler.start_scheduler", return_value=False),
    ):
        # Now safe to import app
        import importlib
        if "app" in sys.modules:
            importlib.reload(sys.modules["app"])

        from app import app as flask_app
        flask_app.config["TESTING"] = True
        flask_app.config["WTF_CSRF_ENABLED"] = False
        # Disable rate limiting in tests
        from app import limiter
        limiter.enabled = False
        yield flask_app


@pytest.fixture()
def client(app):
    """Flask test client (function-scoped — fresh per test)."""
    with app.test_client() as c:
        yield c


@pytest.fixture()
def mock_db(app, monkeypatch):
    """
    Replace the global `db` instance in `app` with a MagicMock.
    Returns the mock so tests can configure return values.
    """
    import app as app_module
    mock = MagicMock()
    monkeypatch.setattr(app_module, "db", mock)
    return mock
