from __future__ import annotations

import os
import json
from datetime import datetime


# REQUIRED
def log_activity(log_path: str, event: dict) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# REQUIRED
def load_activity(log_path: str) -> list:
    if not os.path.exists(log_path):
        return []
    out = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                # ignore bad lines
                pass
    return out


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


# REQUIRED
def productivity_stats(tasks: list, activity_log: list) -> dict:
    """
    Must include:
      - tasks completed per week
      - average completion time
      - category trends
    """
    done = []
    for t in tasks:
        if str(t.get("status", "")).strip().lower() == "done":
            done.append(t)

    completed_per_week: dict[str, int] = {}
    total_seconds = 0.0
    count_durations = 0

    for t in done:
        created = _parse_iso(t.get("created_at"))
        completed = _parse_iso(t.get("completed_at"))
        if completed:
            iso = completed.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
            completed_per_week[key] = completed_per_week.get(key, 0) + 1
        if created and completed:
            total_seconds += (completed - created).total_seconds()
            count_durations += 1

    avg_completion_hours = None
    if count_durations > 0:
        avg_completion_hours = round((total_seconds / count_durations) / 3600, 2)

    category_trends: dict[str, dict[str, int]] = {}
    # trend: counts by status per category
    for t in tasks:
        cat = str(t.get("category", "Uncategorized")).strip() or "Uncategorized"
        st = str(t.get("status", "Pending")).strip() or "Pending"
        category_trends.setdefault(cat, {})
        category_trends[cat][st] = category_trends[cat].get(st, 0) + 1

    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(done),
        "completed_per_week": completed_per_week,
        "avg_completion_time_hours": avg_completion_hours,
        "category_trends": category_trends,
        "activity_events": len(activity_log),
    }


# REQUIRED
def export_report(report: dict, filename: str) -> str:
    os.makedirs("reports", exist_ok=True)
    path = os.path.join("reports", filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return path


def make_event(action: str, task_id: str | None = None, summary: str | None = None) -> dict:
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "action": action,
        "task_id": task_id,
        "summary": summary or "",
    }
