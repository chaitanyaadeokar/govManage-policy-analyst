"""
test_risk_engine.py
-------------------
Unit tests for the pure-function risk engine helpers in app.py.
All tests are fully offline (no DB, no LLM, no network).
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Import helpers under test
# We need to import from app.py without triggering all the side effects,
# so we patch MongoClient + scheduler before importing.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def _patch_for_module():
    col = MagicMock()
    col.count_documents.return_value = 1
    col.find.return_value = iter([])
    col.find_one.return_value = None
    col.insert_one.return_value = MagicMock()
    col.insert_many.return_value = MagicMock()
    col.update_one.return_value = MagicMock(upserted_id=None)
    col.aggregate.return_value = iter([])
    db_obj = MagicMock()
    db_obj.__getitem__ = lambda self, k: col
    client = MagicMock()
    client.__getitem__ = lambda self, k: db_obj

    with (
        patch("pymongo.MongoClient", return_value=client),
        patch("database.MongoClient", return_value=client),
        patch("scheduler.start_scheduler", return_value=False),
        patch.dict("sys.modules", {
            "chromadb": MagicMock(),
            "chromadb.utils": MagicMock(),
            "chromadb.utils.embedding_functions": MagicMock(),
            "firecrawl": MagicMock(),
            "tavily": MagicMock(),
        }),
    ):
        yield


# Lazy import so patches are active first
def get_helpers():
    from app import (
        _clearance_to_level,
        _risk_from_tvi,
        _normalize_payload,
        _build_decision,
        _evaluate_minimum_rules,
    )
    return (
        _clearance_to_level,
        _risk_from_tvi,
        _normalize_payload,
        _build_decision,
        _evaluate_minimum_rules,
    )


# ===========================================================================
# _clearance_to_level
# ===========================================================================

class TestClearanceToLevel:
    def test_level_0(self):
        fn, *_ = get_helpers()
        assert fn("level_0") == 0

    def test_level_1(self):
        fn, *_ = get_helpers()
        assert fn("level_1") == 1

    def test_level_2(self):
        fn, *_ = get_helpers()
        assert fn("level_2") == 2

    def test_level_3(self):
        fn, *_ = get_helpers()
        assert fn("level_3") == 3

    def test_empty_string(self):
        fn, *_ = get_helpers()
        assert fn("") == 0

    def test_none_input(self):
        fn, *_ = get_helpers()
        assert fn(None) == 0  # type: ignore[arg-type]

    def test_no_underscore(self):
        fn, *_ = get_helpers()
        assert fn("manager") == 0

    def test_non_integer_suffix(self):
        fn, *_ = get_helpers()
        assert fn("level_abc") == 0

    def test_multiple_underscores(self):
        """Only the last segment after the final underscore is used."""
        fn, *_ = get_helpers()
        assert fn("clearance_level_2") == 2

    def test_integer_type(self):
        fn, *_ = get_helpers()
        assert fn(42) == 0  # type: ignore[arg-type]


# ===========================================================================
# _risk_from_tvi
# ===========================================================================

class TestRiskFromTvi:
    @pytest.mark.parametrize("score,expected", [
        (0.0, "Low"),
        (0.3, "Low"),      # boundary — inclusive
        (0.301, "Medium"),
        (0.5, "Medium"),
        (0.7, "Medium"),   # boundary — inclusive
        (0.701, "High"),
        (1.0, "High"),
    ])
    def test_boundaries(self, score, expected):
        _, fn, *_ = get_helpers()
        assert fn(score) == expected

    def test_negative_returns_low(self):
        _, fn, *_ = get_helpers()
        assert fn(-0.5) == "Low"

    def test_above_one_returns_high(self):
        _, fn, *_ = get_helpers()
        assert fn(1.5) == "High"

    def test_exact_zero_point_three(self):
        _, fn, *_ = get_helpers()
        assert fn(0.3) == "Low"

    def test_exact_zero_point_seven(self):
        _, fn, *_ = get_helpers()
        assert fn(0.7) == "Medium"


# ===========================================================================
# _normalize_payload
# ===========================================================================

class TestNormalizePayload:
    def test_none_values_stripped(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"user_id": "E101", "extra": None})
        assert "extra" not in result
        assert result["user_id"] == "E101"

    def test_string_whitespace_trimmed(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"user_id": "  E101  ", "note": "  hello world  "})
        assert result["user_id"] == "E101"
        assert result["note"] == "hello world"

    def test_amount_string_coerced_to_float(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"amount": "1500.50"})
        assert result["amount"] == 1500.50
        assert isinstance(result["amount"], float)

    def test_amount_already_float(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"amount": 999.99})
        assert result["amount"] == 999.99

    def test_amount_integer_coerced(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"amount": 500})
        assert result["amount"] == 500.0

    def test_invalid_amount_defaults_to_zero(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"amount": "not-a-number"})
        assert result["amount"] == 0.0

    def test_empty_payload(self):
        _, _, fn, *_ = get_helpers()
        assert fn({}) == {}

    def test_nested_non_string_preserved(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"user_id": "E101", "meta": {"key": "val"}})
        assert result["meta"] == {"key": "val"}

    def test_boolean_values_preserved(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"active": True, "verified": False})
        assert result["active"] is True
        assert result["verified"] is False

    def test_amount_zero_string(self):
        _, _, fn, *_ = get_helpers()
        result = fn({"amount": "0"})
        assert result["amount"] == 0.0


# ===========================================================================
# _build_decision
# ===========================================================================

class TestBuildDecision:
    """Tests (path, action_text, status) tuples from _build_decision."""

    def _bd(self, *args):
        _, _, _, fn, _ = get_helpers()
        return fn(*args)

    def test_safe_path_when_no_failures(self):
        path, action, status = self._bd(0.1, "Low", [])
        assert path == "Safe Path"
        assert status == "Approved"

    def test_review_path_medium_risk_no_blocks(self):
        path, action, status = self._bd(0.5, "Medium", [])
        assert path == "Review Path"
        assert status == "Review"

    def test_review_path_high_risk_no_blocks(self):
        path, action, status = self._bd(0.8, "High", [])
        assert path == "Review Path"
        assert status == "Review"

    def test_block_path_when_block_check_fails(self):
        failed = [{"action_on_fail": "block"}]
        path, action, status = self._bd(0.1, "Low", failed)
        assert path == "Block Path"
        assert status == "Blocked"

    def test_block_overrides_high_risk(self):
        """A block check beats high risk — should still be Block Path."""
        failed = [{"action_on_fail": "block"}]
        path, action, status = self._bd(0.9, "High", failed)
        assert path == "Block Path"

    def test_review_from_review_check(self):
        failed = [{"action_on_fail": "review"}]
        path, action, status = self._bd(0.2, "Low", failed)
        assert path == "Review Path"
        assert status == "Review"

    def test_block_dominates_mixed_checks(self):
        """Mixed block + review → Block wins."""
        failed = [
            {"action_on_fail": "review"},
            {"action_on_fail": "block"},
        ]
        path, _, status = self._bd(0.5, "Medium", failed)
        assert path == "Block Path"
        assert status == "Blocked"

    def test_empty_failed_checks_low_risk_approved(self):
        path, _, status = self._bd(0.1, "Low", [])
        assert status == "Approved"

    def test_check_with_missing_action_on_fail(self):
        """A rule with no action_on_fail should not crash."""
        failed = [{"rule_code": "R999"}]  # no action_on_fail key
        path, _, status = self._bd(0.1, "Low", failed)
        # No block or review action → should be approved (safe path)
        assert status == "Approved"


# ===========================================================================
# _evaluate_minimum_rules
# ===========================================================================

class TestEvaluateMinimumRules:
    def _eval(self, *args):
        *_, fn = get_helpers()
        return fn(*args)

    # --- R004: unknown user -----------------------------------------------

    def test_unknown_user_blocked(self):
        failed = self._eval("financial_txn", {"amount": 100}, None)
        codes = [f["rule_code"] for f in failed]
        assert "R004" in codes

    def test_known_user_no_r004(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("policy_upload", {"amount": 0}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R004" not in codes

    # --- R001: high-value financial transaction by non-manager -----------

    def test_high_amount_employee_blocked(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("financial_txn", {"amount": 2000}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" in codes

    def test_high_amount_manager_allowed(self):
        emp = {"user_id": "E202", "role": "manager", "clearance": "level_2"}
        failed = self._eval("financial_txn", {"amount": 2000}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" not in codes

    def test_low_amount_employee_allowed(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("financial_txn", {"amount": 500}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" not in codes

    def test_exact_threshold_not_blocked(self):
        """Amount == 1000 should NOT trigger R001 (must be > 1000)."""
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("financial_txn", {"amount": 1000}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" not in codes

    def test_just_over_threshold_blocked(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("financial_txn", {"amount": 1000.01}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" in codes

    # --- R002: vendor financial transaction ---------------------------------

    def test_vendor_financial_blocked(self):
        emp = {"user_id": "V100", "role": "vendor", "clearance": "level_0"}
        failed = self._eval("financial_txn", {"amount": 50}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R002" in codes

    def test_vendor_other_event_not_r002(self):
        emp = {"user_id": "V100", "role": "vendor", "clearance": "level_0"}
        failed = self._eval("policy_upload", {"amount": 0}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R002" not in codes

    # --- R003: security alert clearance -------------------------------------

    def test_low_clearance_security_alert(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("security_alert", {}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R003" in codes

    def test_level_2_clearance_no_r003(self):
        emp = {"user_id": "E202", "role": "manager", "clearance": "level_2"}
        failed = self._eval("security_alert", {}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R003" not in codes

    def test_level_0_clearance_security_alert(self):
        emp = {"user_id": "V100", "role": "vendor", "clearance": "level_0"}
        failed = self._eval("security_alert", {}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R003" in codes

    # --- Combined scenarios ---------------------------------------------------

    def test_vendor_high_amount_multiple_failures(self):
        """Vendor + high amount → both R001 and R002 should fire."""
        emp = {"user_id": "V100", "role": "vendor", "clearance": "level_0"}
        failed = self._eval("financial_txn", {"amount": 5000}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" in codes
        assert "R002" in codes

    def test_zero_amount_low_risk_employee(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("financial_txn", {"amount": 0}, emp)
        codes = [f["rule_code"] for f in failed]
        assert "R001" not in codes
        assert "R002" not in codes

    def test_unknown_event_type_no_rules_fired(self):
        emp = {"user_id": "E101", "role": "employee", "clearance": "level_1"}
        failed = self._eval("custom_event", {"amount": 50}, emp)
        codes = [f["rule_code"] for f in failed]
        # No specific rules for custom_event
        assert "R001" not in codes
        assert "R002" not in codes
        assert "R003" not in codes
