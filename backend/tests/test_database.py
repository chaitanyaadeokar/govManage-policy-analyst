"""
test_database.py
----------------
Unit tests for the MongoGovDB data-access layer.
All tests use an in-memory MagicMock — no real MongoDB connection is made.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch, call


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mongo_col_fresh():
    """A fresh MagicMock that acts like a pymongo Collection."""
    col = MagicMock()
    col.count_documents.return_value = 1   # seed guards — "already seeded"
    col.find.return_value = iter([])
    col.find_one.return_value = None
    col.insert_one.return_value = MagicMock(inserted_id="fake_id")
    col.insert_many.return_value = MagicMock()
    col.update_one.return_value = MagicMock(upserted_id=None)
    col.delete_one.return_value = MagicMock()
    col.aggregate.return_value = iter([])
    return col


@pytest.fixture()
def db_instance(mongo_col_fresh):
    """
    Return a real MongoGovDB instance whose MongoClient is fully mocked.
    """
    db_obj = MagicMock()
    db_obj.__getitem__ = lambda self, key: mongo_col_fresh

    client_mock = MagicMock()
    client_mock.__getitem__ = lambda self, key: db_obj

    with patch("pymongo.MongoClient", return_value=client_mock), \
         patch("database.MongoClient", return_value=client_mock):
        from database import MongoGovDB
        instance = MongoGovDB()
        # Swap all internal collections to the fresh mock col
        for attr in vars(instance):
            if attr.endswith("_col"):
                setattr(instance, attr, mongo_col_fresh)
        # Also expose the underlying db mock
        instance.db = db_obj
        yield instance


# ===========================================================================
# _strip_id
# ===========================================================================

class TestStripId:
    def test_none_returns_none(self, db_instance):
        assert db_instance._strip_id(None) is None

    def test_removes_id_field(self, db_instance):
        doc = {"_id": "mongo_id", "name": "Alice", "role": "manager"}
        result = db_instance._strip_id(doc)
        assert "_id" not in result
        assert result["name"] == "Alice"

    def test_no_id_field_unchanged(self, db_instance):
        doc = {"name": "Alice", "role": "manager"}
        result = db_instance._strip_id(doc)
        assert result == doc

    def test_returns_new_dict_not_mutating_original(self, db_instance):
        doc = {"_id": "x", "name": "Bob"}
        result = db_instance._strip_id(doc)
        assert "_id" in doc          # original not mutated
        assert "_id" not in result


# ===========================================================================
# get_employee
# ===========================================================================

class TestGetEmployee:
    def test_existing_user_returned(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find_one.return_value = {
            "_id": "abc", "user_id": "E101", "role": "employee", "clearance": "level_1"
        }
        result = db_instance.get_employee("E101")
        assert result is not None
        assert result["user_id"] == "E101"
        assert "_id" not in result

    def test_missing_user_returns_none(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find_one.return_value = None
        result = db_instance.get_employee("UNKNOWN")
        assert result is None

    def test_employee_with_only_partial_fields(self, db_instance, mongo_col_fresh):
        """Partial document — should still strip _id and return what's there."""
        mongo_col_fresh.find_one.return_value = {"_id": "x", "user_id": "E999"}
        result = db_instance.get_employee("E999")
        assert result["user_id"] == "E999"
        assert "_id" not in result


# ===========================================================================
# list_rules
# ===========================================================================

class TestListRules:
    def test_returns_only_enabled_rules(self, db_instance, mongo_col_fresh):
        enabled = [
            {"_id": "1", "rule_code": "R001", "enabled": True},
            {"_id": "2", "rule_code": "R002", "enabled": True},
        ]
        mongo_col_fresh.find.return_value = iter(enabled)
        results = db_instance.list_rules()
        assert len(results) == 2
        assert all("_id" not in r for r in results)

    def test_empty_rules_returns_empty_list(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find.return_value = iter([])
        assert db_instance.list_rules() == []

    def test_rules_queried_with_enabled_filter(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find.return_value = iter([])
        db_instance.list_rules()
        mongo_col_fresh.find.assert_called_once_with({"enabled": True})


# ===========================================================================
# get_risk_params
# ===========================================================================

class TestGetRiskParams:
    def test_known_event_type_returned(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find_one.return_value = {
            "_id": "x", "event_type": "financial_txn",
            "threat": 0.8, "vulnerability": 0.4, "impact": 0.9, "weight": 1.0
        }
        result = db_instance.get_risk_params("financial_txn")
        assert result["event_type"] == "financial_txn"
        assert result["threat"] == 0.8

    def test_unknown_event_type_returns_defaults(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find_one.return_value = None
        result = db_instance.get_risk_params("completely_unknown")
        # Should return default fallback
        assert result["event_type"] == "completely_unknown"
        assert "threat" in result
        assert result["threat"] == 0.5
        assert result["vulnerability"] == 0.5
        assert result["impact"] == 0.5
        assert result["weight"] == 1.0

    def test_partial_document_returned_cleanly(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find_one.return_value = {
            "_id": "y", "event_type": "security_alert",
            "threat": 1.0, "vulnerability": 0.8, "impact": 1.0, "weight": 1.0
        }
        result = db_instance.get_risk_params("security_alert")
        assert "_id" not in result


# ===========================================================================
# average_tvi
# ===========================================================================

class TestAverageTvi:
    def test_empty_collection_returns_default(self, db_instance, mongo_col_fresh):
        """No actions → should return the 0.2 fallback."""
        mongo_col_fresh.aggregate.return_value = iter([])
        result = db_instance.average_tvi()
        assert result == 0.2

    def test_single_action_correct_average(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.aggregate.return_value = iter([
            {"_id": None, "avg_tvi": 0.75}
        ])
        result = db_instance.average_tvi()
        assert result == 0.75

    def test_none_avg_tvi_falls_back(self, db_instance, mongo_col_fresh):
        """avg_tvi can be None if all tvi_score fields are null."""
        mongo_col_fresh.aggregate.return_value = iter([
            {"_id": None, "avg_tvi": None}
        ])
        result = db_instance.average_tvi()
        assert result == 0.2

    def test_returns_float(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.aggregate.return_value = iter([
            {"_id": None, "avg_tvi": 0.5}
        ])
        result = db_instance.average_tvi()
        assert isinstance(result, float)


# ===========================================================================
# count_actions / count_actions_by_status
# ===========================================================================

class TestCountActions:
    def test_count_actions_uses_count_documents(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.count_documents.return_value = 42
        result = db_instance.count_actions()
        assert result == 42

    def test_count_by_status_filters_correctly(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.count_documents.return_value = 7
        result = db_instance.count_actions_by_status("Approved")
        assert result == 7
        mongo_col_fresh.count_documents.assert_called_with({"status": "Approved"})

    def test_count_zero_returns_zero(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.count_documents.return_value = 0
        assert db_instance.count_actions() == 0


# ===========================================================================
# log_action / add_audit_log
# ===========================================================================

class TestLogging:
    def test_log_action_inserts_document(self, db_instance, mongo_col_fresh):
        doc = {"event_id": "e1", "status": "Approved"}
        db_instance.log_action(doc)
        mongo_col_fresh.insert_one.assert_called_once_with(doc)

    def test_add_audit_log_inserts_document(self, db_instance, mongo_col_fresh):
        log = {"event_id": "e1", "risk_level": "Low"}
        db_instance.add_audit_log(log)
        mongo_col_fresh.insert_one.assert_called_once_with(log)


# ===========================================================================
# list_actions / list_reports
# ===========================================================================

class TestListOperations:
    def test_list_actions_sorted_descending(self, db_instance, mongo_col_fresh):
        mongo_col_fresh.find.return_value = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([
            {"_id": "a", "event_id": "e1", "timestamp": "2026-01-01"},
        ]))
        mongo_col_fresh.find.return_value.sort.return_value = mock_cursor

        results = db_instance.list_actions()
        mongo_col_fresh.find.return_value.sort.assert_called_with("timestamp", -1)

    def test_list_reports_returns_list(self, db_instance, mongo_col_fresh):
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([]))
        # find() must return a MagicMock (not an iterator) so .sort() can be chained
        find_result = MagicMock()
        find_result.sort.return_value = mock_cursor
        mongo_col_fresh.find.return_value = find_result
        result = db_instance.list_reports()
        assert isinstance(result, list)
