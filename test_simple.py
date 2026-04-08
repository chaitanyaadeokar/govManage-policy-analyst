"""
Simple test to verify the agentic system works.
"""
import json
from agents import process_governance_event

print("="*60)
print("SIMPLE TEST - Financial Transaction")
print("="*60)

event = {
    "event_id": "simple-test-001",
    "event_type": "financial_txn",
    "payload": {
        "user_id": "E101",
        "amount": 1500,
        "vendor": "Test Corp",
        "description": "Test transaction"
    }
}

print("\nProcessing event...")
print(f"User: E101 (Alice - employee)")
print(f"Amount: $1500")
print(f"Expected: Should be blocked (exceeds $1000 threshold, needs manager)")

try:
    result = process_governance_event(event)
    
    print("\n" + "="*60)
    print("RESULT:")
    print("="*60)
    print(f"Status: {result.get('status', 'Unknown')}")
    print(f"Action: {result.get('action_taken', 'Unknown')}")
    print(f"Path: {result.get('path_taken', 'Unknown')}")
    print(f"Risk Level: {result.get('risk_level', 'Unknown')}")
    print(f"TVI Score: {result.get('tvi_score', 'Unknown')}")
    print(f"\nReasoning: {result.get('reasoning', 'No reasoning provided')}")
    
    print("\n" + "="*60)
    print("SUCCESS!" if result.get('status') else "COMPLETED")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print("ERROR:")
    print("="*60)
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
