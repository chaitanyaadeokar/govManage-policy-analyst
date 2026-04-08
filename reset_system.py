import os
import shutil
import json
from database import db

def reset_database():
    print("--- Cleaning MongoDB Collections ---")
    # Collections to drop
    collections = [
        db.employees_col,
        db.policies_col,
        db.rule_engine_col,
        db.risk_parameters_col,
        db.actions_col,
        db.audit_logs_col,
        db.reports_col
    ]
    
    for col in collections:
        count = col.count_documents({})
        col.delete_many({})
        print(f"Cleared {count} documents from {col.name}")
    
    print("Re-seeding default data...")
    db._seed_defaults_if_empty()
    print("Database reset complete.")

def reset_agent_queues():
    print("\n--- Cleaning Agent Shared Queues ---")
    base_dir = os.path.join("agents_micro", "shared_queues")
    if not os.path.exists(base_dir):
        print("Shared queues directory not found. Skipping.")
        return

    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if os.path.isdir(folder_path):
            # Clean root of folder
            for f in os.listdir(folder_path):
                file_path = os.path.join(folder_path, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Clean processed subfolder if exists
            processed_path = os.path.join(folder_path, "processed")
            if os.path.exists(processed_path):
                shutil.rmtree(processed_path)
                os.makedirs(processed_path)
            
            print(f"Cleared queue: {folder}")

def reset_agent_memory():
    print("\n--- Resetting Agent Shared Memory ---")
    memory_path = os.path.join("agents_micro", "shared_memory.json")
    empty_memory = {
        "episodic_memory": [],
        "semantic_memory": {
            "risk_patterns": {},
            "fraud_indicators": [],
            "policy_conflicts": [],
            "user_behavior_baselines": {}
        }
    }
    with open(memory_path, 'w') as f:
        json.dump(empty_memory, f, indent=4)
    print("Shared memory reset to empty slate.")

if __name__ == "__main__":
    print("==============================================")
    print("    GOV-MANAGE SYSTEM COMPLETE RESET        ")
    print("==============================================\n")
    
    confirm = input("Are you sure you want to WIPE all data? (y/N): ")
    if confirm.lower() == 'y':
        reset_database()
        reset_agent_queues()
        reset_agent_memory()
        print("\nSUCCESS: System is now fresh and ready for discovery!")
    else:
        print("Reset aborted.")
