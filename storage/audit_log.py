import json
import os
from datetime import datetime, timezone

LOG_FILE = "audit_log.json"

def write_log(entry: dict):
    """Append a new entry to the audit log."""
    logs = read_log()
    logs.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def read_log():
    """Read all entries from the audit log."""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def create_entry(content_id: str, creator_id: str,
                 attribution: str, confidence: float,
                 groq_score: float, stylometric_score: float) -> dict:
    """Create a structured log entry."""
    return {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attribution": attribution,
        "confidence": confidence,
        "groq_score": groq_score,
        "stylometric_score": stylometric_score,
        "status": "classified"
    }