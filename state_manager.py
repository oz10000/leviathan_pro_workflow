import json
import os

STATE_FILE = "last_signal.json"
HISTORY_FILE = "audit_history.json"


def save_last_signal(signal):
    with open(STATE_FILE, "w") as f:
        json.dump(signal, f, default=str)


def load_last_signal():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return None


def append_audit_result(audit_entry):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            history = json.load(f)
    history.append(audit_entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2, default=str)
