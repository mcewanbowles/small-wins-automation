"""Single-writer state record for the Strategist.

One file, one schema. Everything the Strategist remembers lives here:
goal settings, task completions (the dopamine ledger), streaks, and the
currently issued plan so "what was I supposed to do today?" survives a
restart. Migrate-on-read: missing keys get defaults, never a crash.
"""
from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path

STATE_PATH = Path(os.environ.get(
    "SF_STRATEGIST_STATE",
    Path(__file__).resolve().parent.parent / "config" / "strategist_state.json",
))

SCHEMA_VERSION = 1

DEFAULTS = {
    "schema_version": SCHEMA_VERSION,
    "goal": {
        "weekly_revenue_target": 2000.0,
        "currency": "USD",
        "deadline_weeks": 26,
        "started_on": None,          # set on first run
        "baseline_weekly_revenue": 0.0,
    },
    "streak": {"current": 0, "best": 0, "last_win_date": None},
    "wins": [],                      # [{date, task_id, label}]
    "today": None,                   # {date, tasks:[{id,label,kind,est_min,done}]}
    "research": {"last_run": None, "findings": []},
    "uploads": [],                   # [{date, title, expected_weekly}] fed by tracker later
}


def _default() -> dict:
    # deep-copy so callers can't mutate DEFAULTS
    return json.loads(json.dumps(DEFAULTS))


def load() -> dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    merged = _default()
    for key, val in data.items():
        if isinstance(val, dict) and isinstance(merged.get(key), dict):
            merged[key].update(val)
        else:
            merged[key] = val
    if merged["goal"]["started_on"] is None:
        merged["goal"]["started_on"] = date.today().isoformat()
        save(merged)
    return merged


def save(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=STATE_PATH.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
        os.replace(tmp, STATE_PATH)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def record_win(state: dict, task_id: str, label: str) -> dict:
    today = date.today().isoformat()
    state["wins"].append({"date": today, "task_id": task_id, "label": label})
    last = state["streak"]["last_win_date"]
    if last != today:
        yesterday = date.fromordinal(date.today().toordinal() - 1).isoformat()
        state["streak"]["current"] = (
            state["streak"]["current"] + 1 if last == yesterday else 1
        )
        state["streak"]["best"] = max(state["streak"]["best"], state["streak"]["current"])
        state["streak"]["last_win_date"] = today
    return state


def mark_done(state: dict, task_id: str) -> tuple[dict, dict | None]:
    """Mark a task in today's plan done. Returns (state, completed_task|None)."""
    today = state.get("today") or {}
    for task in today.get("tasks", []):
        if task["id"] == task_id and not task.get("done"):
            task["done"] = True
            task["done_at"] = datetime.now().isoformat(timespec="seconds")
            record_win(state, task_id, task["label"])
            if task_id == "teacherstore-test":
                state.setdefault("marketplace_tests", {})["teacherstore_done"] = True
            save(state)
            return state, task
    save(state)
    return state, None
