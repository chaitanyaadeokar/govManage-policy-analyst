"""
test_api_routes.py
------------------
Integration tests for Flask API routes using the test client.
All external services (DB, LLM, ChromaDB) are mocked.
"""
from __future__ import annotations

import json
import io
import pytest
from unittest.mock import MagicMock, patch


# ===========================================================================
# Health-check
# ===========================================================================

class TestHealthCheck:
    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_json_structure(self, client):
        data = client.get("/").get_json()
        assert "status" in data
        assert "modes" in data
        assert isinstance(data["modes"], list)

    def test_root_has_correct_modes(self, client):
        data = client.get("/").get_json()
        for mode in ["minimum", "rule_engine", "advanced", "agentic"]:
            assert mode in data["modes"]


# ===========================================================================
# GET /api/kpis
# ===========================================================================

class TestKpis:
    def test_kpis_returns_200(self, client, mock_db):
        mock_db.count_actions.return_value = 10
        mock_db.count_actions_by_status.return_value = 8
        mock_db.average_tvi.return_value = 0.4
        mock_db.list_policies.return_value = [{"policy_id": "P1"}]
        mock_db.count_trusted_sources.return_value = 3

        resp = client.get("/api/kpis")
        assert resp.status_code == 200

    def test_kpis_fields_present(self, client, mock_db):
        mock_db.count_actions.return_value = 5
        mock_db.count_actions_by_status.return_value = 5
        mock_db.average_tvi.return_value = 0.2
        mock_db.list_policies.return_value = []
        mock_db.count_trusted_sources.return_value = 0

        data = client.get("/api/kpis").get_json()
        for key in ["active_policies", "compliance_pct", "crawled_sources", "risk_index"]:
            assert key in data, f"Missing key: {key}"

    def test_kpis_zero_actions_compliance_100(self, client, mock_db):
        """Edge: no actions → compliance should default to 100%."""
        mock_db.count_actions.return_value = 0
        mock_db.count_actions_by_status.return_value = 0
        mock_db.average_tvi.return_value = 0.0
        mock_db.list_policies.return_value = []
        mock_db.count_trusted_sources.return_value = 0

        data = client.get("/api/kpis").get_json()
        assert data["compliance_pct"] == 100.0

    def test_kpis_risk_index_clamped(self, client, mock_db):
        """Risk index must always be 0-100."""
        mock_db.count_actions.return_value = 1
        mock_db.count_actions_by_status.return_value = 0
        mock_db.average_tvi.return_value = 2.0   # out-of-range TVI
        mock_db.list_policies.return_value = []
        mock_db.count_trusted_sources.return_value = 0

        data = client.get("/api/kpis").get_json()
        assert 0 <= data["risk_index"] <= 100


# ===========================================================================
# GET /api/transactions
# ===========================================================================

class TestTransactions:
    def test_returns_list(self, client, mock_db):
        mock_db.list_actions.return_value = []
        resp = client.get("/api/transactions")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_returns_populated_list(self, client, mock_db):
        mock_db.list_actions.return_value = [
            {"event_id": "abc", "status": "Approved", "risk_level": "Low"}
        ]
        data = client.get("/api/transactions").get_json()
        assert len(data) == 1
        assert data[0]["event_id"] == "abc"


# ===========================================================================
# POST /api/trigger
# ===========================================================================

class TestTriggerEvent:

    # --- Input validation --------------------------------------------------

    def test_missing_body_returns_400(self, client, mock_db):
        resp = client.post("/api/trigger", data="not json",
                           content_type="text/plain")
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client, mock_db):
        resp = client.post("/api/trigger",
                           data=json.dumps({}),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_invalid_mode_returns_400(self, client, mock_db):
        payload = {
            "event_type": "financial_txn",
            "payload": {"user_id": "E101", "amount": 100},
            "mode": "INVALID_MODE",
        }
        resp = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_missing_event_type_returns_400(self, client, mock_db):
        payload = {"payload": {"user_id": "E101"}, "mode": "minimum"}
        resp = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 400

    def test_payload_not_dict_returns_400(self, client, mock_db):
        payload = {
            "event_type": "financial_txn",
            "payload": "not_a_dict",
            "mode": "minimum",
        }
        resp = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 400

    # --- Minimum mode -------------------------------------------------------

    def test_minimum_mode_returns_200(self, client, mock_db):
        mock_db.get_employee.return_value = {
            "user_id": "E202", "role": "manager", "clearance": "level_2"
        }
        mock_db.get_risk_params.return_value = {
            "event_type": "financial_txn",
            "threat": 0.5, "vulnerability": 0.5, "impact": 0.5, "weight": 1.0
        }
        mock_db.log_action.return_value = None
        mock_db.add_audit_log.return_value = None

        payload = {
            "event_type": "financial_txn",
            "payload": {"user_id": "E202", "amount": 500},
            "mode": "minimum",
        }
        resp = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "event_id" in data
        assert "status" in data
        assert "risk_level" in data

    def test_minimum_mode_approved_for_safe_transaction(self, client, mock_db):
        mock_db.get_employee.return_value = {
            "user_id": "E202", "role": "manager", "clearance": "level_2"
        }
        mock_db.get_risk_params.return_value = {
            "event_type": "financial_txn",
            "threat": 0.1, "vulnerability": 0.1, "impact": 0.1, "weight": 1.0
        }
        mock_db.log_action.return_value = None
        mock_db.add_audit_log.return_value = None

        payload = {
            "event_type": "financial_txn",
            "payload": {"user_id": "E202", "amount": 100},
            "mode": "minimum",
        }
        data = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json").get_json()
        assert data["status"] == "Approved"

    def test_unknown_user_blocked_in_minimum_mode(self, client, mock_db):
        mock_db.get_employee.return_value = None
        mock_db.get_risk_params.return_value = {
            "event_type": "financial_txn",
            "threat": 0.5, "vulnerability": 0.5, "impact": 0.5, "weight": 1.0
        }
        mock_db.log_action.return_value = None
        mock_db.add_audit_log.return_value = None

        payload = {
            "event_type": "financial_txn",
            "payload": {"user_id": "UNKNOWN_USER", "amount": 100},
            "mode": "minimum",
        }
        data = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json").get_json()
        assert data["status"] == "Blocked"

    # --- Rule engine mode ---------------------------------------------------

    def test_rule_engine_mode_returns_200(self, client, mock_db):
        mock_db.get_employee.return_value = {
            "user_id": "E101", "role": "employee", "clearance": "level_1"
        }
        mock_db.get_risk_params.return_value = {
            "event_type": "policy_upload",
            "threat": 0.3, "vulnerability": 0.5, "impact": 0.6, "weight": 1.0
        }
        mock_db.list_rules.return_value = []  # no rules
        mock_db.log_action.return_value = None
        mock_db.add_audit_log.return_value = None

        payload = {
            "event_type": "policy_upload",
            "payload": {"user_id": "E101"},
            "mode": "rule_engine",
        }
        resp = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json")
        assert resp.status_code == 200

    # --- Mode response shape ------------------------------------------------

    def test_response_has_all_required_fields(self, client, mock_db):
        mock_db.get_employee.return_value = {
            "user_id": "E101", "role": "employee", "clearance": "level_1"
        }
        mock_db.get_risk_params.return_value = {
            "event_type": "policy_upload",
            "threat": 0.3, "vulnerability": 0.5, "impact": 0.6, "weight": 1.0
        }
        mock_db.list_rules.return_value = []
        mock_db.log_action.return_value = None
        mock_db.add_audit_log.return_value = None

        payload = {
            "event_type": "policy_upload",
            "payload": {"user_id": "E101"},
            "mode": "rule_engine",
        }
        data = client.post("/api/trigger",
                           data=json.dumps(payload),
                           content_type="application/json").get_json()

        required = ["event_id", "path_taken", "action_taken", "status",
                    "tvi_score", "risk_level", "rules_used", "audit_trace", "mode"]
        for field in required:
            assert field in data, f"Missing field: {field}"

    # --- Agentic mode timeout -----------------------------------------------

    def test_agentic_mode_timeout_returns_504(self, client, mock_db):
        """Agentic mode: if result file never appears → 504 after timeout."""
        with (
            patch("time.sleep"),               # don't actually sleep
            patch("os.path.exists", return_value=False),   # file never arrives
            patch("os.makedirs"),
            patch("builtins.open", MagicMock()),
            patch("json.dump"),
        ):
            payload = {
                "event_type": "financial_txn",
                "payload": {"user_id": "E101", "amount": 100},
                "mode": "agentic",
            }
            resp = client.post("/api/trigger",
                               data=json.dumps(payload),
                               content_type="application/json")
            assert resp.status_code == 504
            data = resp.get_json()
            assert "timeout" in data.get("error", "").lower()


# ===========================================================================
# GET /api/agent-status
# ===========================================================================

class TestAgentStatus:
    def test_returns_200(self, client, mock_db):
        mock_db.get_active_agent_statuses.return_value = []
        resp = client.get("/api/agent-status")
        assert resp.status_code == 200

    def test_response_has_activities_and_total(self, client, mock_db):
        mock_db.get_active_agent_statuses.return_value = [
            {"queue": "1_inbox", "message": "Processing event", "timestamp": 1234567}
        ]
        data = client.get("/api/agent-status").get_json()
        assert "activities" in data
        assert "total_active" in data
        assert data["total_active"] == 1

    def test_empty_activities_total_is_zero(self, client, mock_db):
        mock_db.get_active_agent_statuses.return_value = []
        data = client.get("/api/agent-status").get_json()
        assert data["total_active"] == 0


# ===========================================================================
# GET /api/reports
# ===========================================================================

class TestReports:
    def test_returns_list(self, client, mock_db):
        mock_db.list_reports.return_value = []
        resp = client.get("/api/reports")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)


# ===========================================================================
# GET /api/masters (policy list)
# ===========================================================================

class TestMasters:
    def test_returns_list(self, client, mock_db):
        mock_db.list_policies.return_value = [
            {"policy_id": "P001", "name": "Test Policy", "sector": "Finance", "risk": "High"}
        ]
        data = client.get("/api/masters").get_json()
        assert isinstance(data, list)
        assert data[0]["id"] == "P001"

    def test_missing_policy_id_defaults_to_na(self, client, mock_db):
        mock_db.list_policies.return_value = [{"name": "Unnamed"}]
        data = client.get("/api/masters").get_json()
        assert data[0]["id"] == "NA"


# ===========================================================================
# POST /api/policies/upload  (file upload)
# ===========================================================================

class TestPolicyUpload:
    def test_no_file_field_returns_400(self, client, mock_db):
        resp = client.post("/api/policies/upload", data={})
        assert resp.status_code == 400

    def test_unsupported_extension_returns_415(self, client, mock_db):
        data = {
            "file": (io.BytesIO(b"content"), "document.xyz"),
            "name": "Test",
        }
        resp = client.post("/api/policies/upload",
                           data=data, content_type="multipart/form-data")
        assert resp.status_code == 415

    def test_empty_filename_returns_400(self, client, mock_db):
        data = {"file": (io.BytesIO(b""), "")}
        resp = client.post("/api/policies/upload",
                           data=data, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_valid_txt_upload(self, client, mock_db):
        """A valid .txt upload should return 201 and a document_id."""
        mock_db.add_policy_document.return_value = None

        with patch("app.parse_file", return_value="Sample policy text content"),\
             patch("app.chunk_text", return_value=["chunk1", "chunk2"]),\
             patch("app._chroma_ok", False):

            data = {
                "file": (io.BytesIO(b"Sample policy text content"), "policy.txt"),
                "name": "Test Policy",
                "sector": "Finance",
                "risk": "High",
            }
            resp = client.post("/api/policies/upload",
                               data=data, content_type="multipart/form-data")
            assert resp.status_code == 201
            result = resp.get_json()
            assert "document_id" in result

    def test_empty_file_content_returns_422(self, client, mock_db):
        with patch("app.parse_file", return_value=""),\
             patch("app.chunk_text", return_value=[]):

            data = {
                "file": (io.BytesIO(b""), "empty.txt"),
                "name": "Empty",
            }
            resp = client.post("/api/policies/upload",
                               data=data, content_type="multipart/form-data")
            assert resp.status_code == 422


# ===========================================================================
# GET /api/compliance/frameworks
# ===========================================================================

class TestComplianceFrameworks:
    def test_returns_list(self, client, mock_db):
        mock_db.list_frameworks.return_value = [
            {"framework_id": "ISO_27001", "name": "ISO 27001", "control_count": 12}
        ]
        resp = client.get("/api/compliance/frameworks")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert data[0]["framework_id"] == "ISO_27001"

    def test_missing_framework_returns_404(self, client, mock_db):
        mock_db.get_framework.return_value = None
        resp = client.get("/api/compliance/frameworks/NONEXISTENT")
        assert resp.status_code == 404


# ===========================================================================
# GET /api/risk/library
# ===========================================================================

class TestRiskLibrary:
    def test_returns_list(self, client, mock_db):
        mock_db.list_risk_library.return_value = []
        resp = client.get("/api/risk/library")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_missing_risk_returns_404(self, client, mock_db):
        mock_db.get_risk_library_item.return_value = None
        resp = client.get("/api/risk/library/RISK-INVALID")
        assert resp.status_code == 404
