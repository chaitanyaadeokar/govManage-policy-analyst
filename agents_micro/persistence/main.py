import os
import sys
import json
import time
import shutil
from datetime import datetime, timezone
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add root directory to sys.path for database import
FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(FILE_PATH)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database import db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED_QUEUES = os.path.join(BASE_DIR, "shared_queues")
INBOX_DIR = os.path.join(SHARED_QUEUES, "6_feedback")
COMPLETION_DIR = os.path.join(SHARED_QUEUES, "7_complete")
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")

os.makedirs(COMPLETION_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

class PersistenceHandler(FileSystemEventHandler):
    def process_file(self, filepath):
        try:
            time.sleep(0.5)
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            event_id = data.get('event_id', 'unknown')
            print(f"[Persistence Agent] Processing finale for {event_id}...")
            
            # Map Micro-Agent result to MongoDB docs
            now = datetime.now(timezone.utc).isoformat()
            path_taken = data.get('path_taken', 'Review Path').strip()
            
            # 1. Action Record
            action_doc = {
                "event_id": event_id,
                "status": "Approved" if "Safe" in path_taken else "Review",
                "path_taken": path_taken,
                "action_taken": data.get('action_taken', 'Flagged for Review'),
                "risk_level": data.get('risk_level', 'Medium'),
                "tvi_score": data.get('tvi_score', 0.5),
                "audit_trace": data.get('audit_trace', []),
                "timestamp": now
            }
            db.log_action(action_doc)
            
            # 2. Audit Record
            audit_doc = {
                "event_id": event_id,
                "risk_level": data.get('risk_level', 'Medium'),
                "tvi_score": data.get('tvi_score', 0.5),
                "path_taken": path_taken,
                "action_taken": data.get('action_taken', 'Flagged for Review'),
                "audit_trace": data.get('audit_trace', []),
                "ai_explanation": data.get('reasoning'),
                "timestamp": now,
                "event_type": data.get('event_type', 'financial_txn')
            }
            db.add_audit_log(audit_doc)
            
            # 3. Report Record
            report_doc = {
                "event_id": event_id,
                "summary": data.get('reasoning', 'No summary provided.'),
                "governance_summary": f"Micro-Agent Resolution: {data.get('action_taken')}",
                "final_action": data.get('action_taken'),
                "audit_trace": data.get('audit_trace', []),
                "timestamp": now
            }
            db.add_report(report_doc)
            
            # 3. Write Completion Token for API
            token_path = os.path.join(COMPLETION_DIR, f"{event_id}.json")
            with open(token_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            shutil.move(filepath, os.path.join(PROCESSED_DIR, os.path.basename(filepath)))
            print(f"[Persistence Agent] Successfully persisted and tokenized {event_id}")
            
        except Exception as e:
            print(f"[Persistence Agent ERROR] {e}")

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.json'):
            self.process_file(event.src_path)

if __name__ == "__main__":
    print(f"--- Starting Database Persistence Agent ---")
    print(f"Monitoring output from Feedback: {INBOX_DIR}")
    event_handler = PersistenceHandler()
    observer = Observer()
    observer.schedule(event_handler, path=INBOX_DIR, recursive=False)
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
