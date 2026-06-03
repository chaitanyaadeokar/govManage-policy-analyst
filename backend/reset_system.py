import os
import shutil
import json
from database import db

def reset_database():
    print("--- Cleaning MongoDB Collections ---")
    # All 16 collections to drop
    collections = [
        db.employees_col,
        db.policies_col,
        db.rule_engine_col,
        db.risk_parameters_col,
        db.actions_col,
        db.audit_logs_col,
        db.reports_col,
        db.policy_documents_col,
        db.policy_chunks_col,
        db.frameworks_col,
        db.risk_matrix_col,
        db.chat_sessions_col,
        db.trusted_sources_col,
        db.crawled_pages_col,
        db.risk_library_col,
        db.policy_packs_col
    ]
    
    for col in collections:
        count = col.count_documents({})
        col.delete_many({})
        print(f"Cleared {count} documents from {col.name}")
    
    print("Re-seeding default data...")
    db._seed_defaults_if_empty()
    db._seed_frameworks_if_empty()
    db._seed_risk_matrices_if_empty()
    db._seed_risk_library_if_empty()
    print("Database reset complete.")

def reset_vector_store():
    print("\n--- Cleaning ChromaDB Vector Store ---")
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    if os.path.exists(persist_dir):
        try:
            shutil.rmtree(persist_dir)
            print(f"Removed Chroma persist directory: {persist_dir}")
        except Exception as e:
            print(f"Failed to remove Chroma directory: {e}")
    else:
        print("Chroma persist directory not found. Skipping.")

def reset_feedback_logs():
    print("\n--- Resetting Micro-Agent Feedback Logs ---")
    log_path = os.path.join("agents_micro", "feedback_log.json")
    if os.path.exists(log_path):
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)
            print("Feedback log reset to empty list.")
        except Exception as e:
            print(f"Failed to reset feedback log: {e}")
    else:
        print("Feedback log file not found. Skipping.")

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
        reset_vector_store()
        reset_feedback_logs()
        reset_agent_queues()
        reset_agent_memory()
        print("\nSUCCESS: System is now fresh and ready for discovery!")
    else:
        print("Reset aborted.")
