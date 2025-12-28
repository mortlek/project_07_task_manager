from __future__ import annotations

import os
import json
from datetime import datetime
from typing import Any


def _ensure_dirs(base_dir: str) -> None:
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "reports"), exist_ok=True)


def _safe_read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# REQUIRED
def validate_task_schema(tasks: list) -> bool:
    required = {
        "id", "title", "description", "category", "priority", "status",
        "due_date", "created_at", "updated_at"
    }
    if not isinstance(tasks, list):
        return False
    for t in tasks:
        if not isinstance(t, dict):
            return False
        for k in required:
            if k not in t:
                return False
    return True


def _read_activity_log(path: str) -> list:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def _write_activity_log(path: str, activity_log: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ev in activity_log:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def _latest_valid_backup(backup_dir: str) -> dict | None:
    """
    Backup format: backups/state_YYYYMMDD.json OR backups/state_YYYYMMDD_HHMMSS.json
    Content: {"tasks": [...], "categories": [...], "activity": [...]}
    """
    if not os.path.exists(backup_dir):
        return None

    candidates = []
    for name in os.listdir(backup_dir):
        if name.startswith("state_") and name.endswith(".json"):
            candidates.append(os.path.join(backup_dir, name))
    candidates.sort(reverse=True)  # newest first by filename

    for path in candidates:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tasks = data.get("tasks", [])
            if validate_task_schema(tasks):
                return data
        except Exception:
            continue
    return None


def _restore_from_backup(base_dir: str, backup_data: dict) -> tuple[list, list, list]:
    tasks = backup_data.get("tasks", [])
    categories = backup_data.get("categories", [])
    activity = backup_data.get("activity", [])

    tasks_path = os.path.join(base_dir, "data", "tasks.json")
    cats_path = os.path.join(base_dir, "data", "categories.json")
    log_path = os.path.join(base_dir, "data", "activity.log")

    _write_json(tasks_path, tasks)
    _write_json(cats_path, categories)
    _write_activity_log(log_path, activity)

    return tasks, categories, activity


# REQUIRED
def load_state(base_dir: str) -> tuple[list, list, list]:
    _ensure_dirs(base_dir)

    tasks_path = os.path.join(base_dir, "data", "tasks.json")
    cats_path = os.path.join(base_dir, "data", "categories.json")
    log_path = os.path.join(base_dir, "data", "activity.log")
    backup_dir = os.path.join(base_dir, "backups")

    tasks = _safe_read_json(tasks_path, [])
    categories = _safe_read_json(cats_path, [])
    activity = _read_activity_log(log_path)

    # If tasks file corrupt or schema invalid: restore most recent valid backup
    if tasks != [] and not validate_task_schema(tasks):
        backup = _latest_valid_backup(backup_dir)
        if backup is not None:
            return _restore_from_backup(base_dir, backup)
        # no valid backup: start clean
        return [], categories if isinstance(categories, list) else [], activity

    # If tasks.json is unreadable (safe_read_json returns default []), that's okay.
    if not isinstance(categories, list):
        categories = []
    if not isinstance(activity, list):
        activity = []

    return tasks, categories, activity


# REQUIRED
def save_state(base_dir: str, tasks: list, categories: list, activity_log: list) -> None:
    _ensure_dirs(base_dir)

    tasks_path = os.path.join(base_dir, "data", "tasks.json")
    cats_path = os.path.join(base_dir, "data", "categories.json")
    log_path = os.path.join(base_dir, "data", "activity.log")

    _write_json(tasks_path, tasks)
    _write_json(cats_path, categories)
    _write_activity_log(log_path, activity_log)


# REQUIRED
def backup_state(base_dir: str, backup_dir: str) -> list[str]:
    """
    Daily snapshot: creates at most one backup per day by default name state_YYYYMMDD.json.
    If file exists, returns [].
    """
    _ensure_dirs(base_dir)
    os.makedirs(backup_dir, exist_ok=True)

    today = datetime.now().strftime("%Y%m%d")
    backup_path = os.path.join(backup_dir, f"state_{today}.json")
    if os.path.exists(backup_path):
        return []

    tasks_path = os.path.join(base_dir, "data", "tasks.json")
    cats_path = os.path.join(base_dir, "data", "categories.json")
    log_path = os.path.join(base_dir, "data", "activity.log")

    tasks = _safe_read_json(tasks_path, [])
    categories = _safe_read_json(cats_path, [])
    activity = _read_activity_log(log_path)

    payload = {"tasks": tasks, "categories": categories, "activity": activity}

    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return [backup_path]
