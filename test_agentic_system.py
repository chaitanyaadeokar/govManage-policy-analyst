"""
Test script for the agentic governance system.
Demonstrates autonomous multi-agent reasoning.
"""
import json
from agents import process_governance_event


def test_financial_transaction():
    """Test financial transaction processing."""
    print("\n" + "="*80)
    print("TEST 1: Financial Transaction - High Amount by Employee")
    print("="*80)
    
    event = {
        "event_id": "test-001",
        "event_type": "financial_txn",
        "payload": {
            "user_id": "E101",  # Alice - employee, level_1
            "amount": 1500,
            "vendor": "Acme Corp",
            "description": "Software license purchase"
        }
    }
    
    result = process_governance_event(event)
    print_result(result)


def test_vendor_transaction():
    """Test vendor attempting financial transaction (should block)."""
    print("\n" + "="*80)
    print("TEST 2: Vendor Financial Transaction (Should Block)")
    print("="*80)
    
    event = {
        "event_id": "test-002",
        "event_type": "financial_txn",
        "payload": {
            "user_id": "V100",  # Vendor - should be blocked
            "amount": 500,
            "vendor": "External Vendor",
            "description": "Attempted transaction"
        }
    }
    
    result = process_governance_event(event)
    print_result(result)


def test_security_alert():
    """Test security alert processing."""
    print("\n" + "="*80)
    print("TEST 3: Security Alert - Director Access")
    print("="*80)
    
    event = {
        "event_id": "test-003",
        "event_type": "security_alert",
        "payload": {
            "user_id": "E303",  # Charlie - director, level_3
            "alert_type": "critical",
            "resource": "production_database",
            "action": "schema_modification"
        }
    }
    
    result = process_governance_event(event)
    print_result(result)


def test_unknown_user():
    """Test unknown user (should block)."""
    print("\n" + "="*80)
    print("TEST 4: Unknown User (Should Block)")
    print("="*80)
    
    event = {
        "event_id": "test-004",
        "event_type": "financial_txn",
        "payload": {
            "user_id": "UNKNOWN999",
            "amount": 100,
            "vendor": "Test Vendor",
            "description": "Suspicious transaction"
        }
    }
    
    result = process_governance_event(event)
    print_result(result)


def test_manager_high_amount():
    """Test manager with high amount (should approve)."""
    print("\n" + "="*80)
    print("TEST 5: Manager High Amount Transaction (Should Approve)")
    print("="*80)
    
    event = {
        "event_id": "test-005",
        "event_type": "financial_txn",
        "payload": {
            "user_id": "E202",  # Bob - manager, level_2
            "amount": 1500,
            "vendor": "Enterprise Software Inc",
            "description": "Annual license renewal"
        }
    }
    
    result = process_governance_event(event)
    print_result(result)


def print_result(result):
    """Pretty print result."""
    print(f"\n📋 DECISION SUMMARY:")
    print(f"   Event ID: {result['event_id']}")
    print(f"   Status: {result['status']}")
    print(f"   Action: {result['action_taken']}")
    print(f"   Path: {result['path_taken']}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   TVI Score: {result['tvi_score']}")
    print(f"   Confidence: {result.get('confidence', 'N/A')}")
    
    print(f"\n💭 REASONING:")
    print(f"   {result['reasoning']}")
    
    print(f"\n🔍 AUDIT TRACE:")
    for trace in result.get('audit_trace', []):
        print(f"   • {trace}")
    
    print(f"\n🤖 AGENT FINDINGS:")
    for agent_name, findings in result.get('agent_findings', {}).items():
        print(f"   {agent_name}:")
        print(f"      - Recommendation: {findings.get('recommendation', 'N/A')}")
        print(f"      - Tool Calls: {findings.get('tool_calls_made', 0)}")
        if 'error' in findings:
            print(f"      - Error: {findings['error']}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("AGENTIC GOVERNANCE SYSTEM - TEST SUITE")
    print("Testing autonomous multi-agent reasoning with ReAct loops")
    print("="*80)
    
    try:
        test_financial_transaction()
        test_vendor_transaction()
        test_security_alert()
        test_unknown_user()
        test_manager_high_amount()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
