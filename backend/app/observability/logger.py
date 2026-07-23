import json
import os
import datetime
from typing import Dict, Any

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "events.log")

def log_event(event_type: str, payload: Dict[str, Any], trace_id: str = "default_trace", latency_ms: int = 0, cache_hit: bool = True) -> None:
    """
    Appends structured JSON-L entries to events.log with trace_id, latency_ms, and cache_hit.
    """
    log_entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "trace_id": trace_id,
        "event": event_type,
        "latency_ms": latency_ms,
        "cache_hit": cache_hit,
        "payload": payload
    }
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[ObservabilityLogger] Error writing to events.log: {e}")
