"""Traçage optionnel du moteur NGAP pour le debug."""

import json
import os
from datetime import datetime


DEBUG_ENABLED = os.environ.get("NGAP_DEBUG", "").strip().lower() in ("1", "true", "yes")
_trace_buffer = []


def trace(event, **data):
    if not DEBUG_ENABLED:
        return
    entry = {
        "event": event,
        "timestamp": datetime.now().isoformat(timespec="milliseconds"),
        **data,
    }
    _trace_buffer.append(entry)
    print(f"[ngap-debug] {json.dumps(entry, ensure_ascii=False)}")


def get_trace():
    result = list(_trace_buffer)
    _trace_buffer.clear()
    return result


def clear_trace():
    _trace_buffer.clear()
