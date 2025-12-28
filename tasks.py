from __future__ import annotations

from datetime import datetime, date, timedelta
import uuid


# -------------------------
# Helpers
# -------------------------
PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Done", "Archived", "Overdue"]

def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")

def _new_id() -> str:
    return uuid.uuid4().hex[:8]

def parse_date_yyyy_mm_dd(s: str | None) -> date | None:
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    try:
        y, m, d = s.split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None

def normalize_priority(p: str | None) -> str:
    if not p:
        return "Medium"
    p2 = p.strip().lower()
    if p2 in ["low", "l"]:
        return "Low"
    if p2 in ["medium", "med", "m"]:
        return "Medium"
    if p2 in ["high", "h"]:
        return "High"
    return "Medium"

def normalize_status(s: str | None) -> str:
    if not s:
        return "Pending"
    x = s.strip().lower()
    if x in ["pending", "p", "todo", "to-do"]:
        return "Pending"
    if x in ["in progress", "progress", "ip", "doing"]:
        return "In Progress"
    if x in ["done", "completed", "complete", "d"]:
        return "Done"
    if x in ["archived", "archive", "a"]:
        return "Archived"
    if x in ["overdue", "late", "o"]:
        return "Overdue"
    return "Pending"

def ensure_unique_id(tasks: list[dict], task_id: str) -> str:
    existing = {t.get("id") for t in tasks}
    out = task_id
    while out in existing:
        out = _new_id()
    return out

def _find_task(tasks: list[dict], task_id: str) -> dict | None:
    for t in tasks:
        if t.get("id") == task_id:
            return t
    return None

def _ensure_task_defaults(task: dict) -> dict:
    # Ensure required fields exist
    for k in ["id", "title", "description", "category", "priority", "status", "due_date", "created_at", "updated_at"]:
        task.setdefault(k, "")

    # Optional but used by requirements/UX
    task.setdefault("tags", [])
    task.setdefault("subtasks", [])
    task.setdefault("completed_at", None)
    task.setdefault("archived_at", None)

    # Normalize formats
    task["priority"] = normalize_priority(task.get("priority"))
    task["status"] = normalize_status(task.get("status"))
    if task.get("due_date") is None:
        task["due_date"] = ""
    task["due_date"] = str(task["due_date"]).strip()

    if not isinstance(task["tags"], list):
        task["tags"] = []
    if not isinstance(task["subtasks"], list):
        task["subtasks"] = []

    return task


# -------------------------
# REQUIRED FUNCTIONS (tasks.py)
# -------------------------
def create_task(tasks: list, task_data: dict) -> dict:
    title = str(task_data.get("title", "")).strip()
    if title == "":
        title = "Untitled"

    task = {
        "id": ensure_unique_id(tasks, _new_id()),
        "title": title,
        "description": str(task_data.get("description", "")).strip(),
        "category": str(task_data.get("category", "Uncategorized")).strip() or "Uncategorized",
        "priority": normalize_priority(str(task_data.get("priority", "Medium"))),
        "status": normalize_status(str(task_data.get("status", "Pending"))),
        "due_date": str(task_data.get("due_date", "")).strip(),  # YYYY-MM-DD or ""
        "created_at": _now_iso(),
        "updated_at": _now_iso(),

        # extra
        "tags": list(task_data.get("tags", [])) if isinstance(task_data.get("tags", []), list) else [],
        "subtasks": [],
        "completed_at": None,
        "archived_at": None,
    }

    _ensure_task_defaults(task)

    tasks.append(task)
    return task


def update_task(tasks: list, task_id: str, updates: dict) -> dict | None:
    t = _find_task(tasks, task_id)
    if t is None:
        return None

    for k in ["title", "description", "category", "priority", "status", "due_date"]:
        if k in updates:
            val = updates[k]
            if isinstance(val, str):
                val = val.strip()

            if k == "priority":
                t["priority"] = normalize_priority(str(val))
            elif k == "status":
                t["status"] = normalize_status(str(val))
            elif k == "due_date":
                t["due_date"] = str(val).strip()
            elif k == "category":
                t["category"] = str(val).strip() or "Uncategorized"
            elif k == "title":
                t["title"] = str(val).strip() or "Untitled"
            else:
                t[k] = str(val)

    t["updated_at"] = _now_iso()

    # completion timestamps
    if t["status"] == "Done" and not t.get("completed_at"):
        t["completed_at"] = _now_iso()
    if t["status"] != "Done":
        t["completed_at"] = None

    # archive timestamps
    if t["status"] == "Archived" and not t.get("archived_at"):
        t["archived_at"] = _now_iso()
    if t["status"] != "Archived":
        t["archived_at"] = None

    _ensure_task_defaults(t)
    return t


def delete_task(tasks: list, task_id: str) -> bool:
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            tasks.pop(i)
            return True
    return False


def mark_task_status(tasks: list, task_id: str, status: str) -> dict | None:
    return update_task(tasks, task_id, {"status": status})


def add_subtask(tasks: list, task_id: str, subtask_data: dict) -> dict | None:
    t = _find_task(tasks, task_id)
    if t is None:
        return None

    title = str(subtask_data.get("title", "")).strip()
    if title == "":
        title = "Untitled subtask"

    st = {
        "id": _new_id(),
        "title": title,
        "status": normalize_status(str(subtask_data.get("status", "Pending"))),
        "created_at": _now_iso(),
    }

    t.setdefault("subtasks", []).append(st)
    t["updated_at"] = _now_iso()
    _ensure_task_defaults(t)
    return t


def filter_tasks(
    tasks: list,
    *,
    status: str | None = None,
    category: str | None = None,
    due_before: str | None = None
) -> list:
    """
    Required signature in PDF.

    Supports:
      - status exact match (case-insensitive)
      - category exact match (case-insensitive)
      - due_before:
          * "YYYY-MM-DD" : due <= date
          * "YYYY-MM-DD..YYYY-MM-DD" : inclusive range
          * "" / None : ignored
    """
    out = [ _ensure_task_defaults(dict(t)) for t in tasks ]  # shallow normalize

    if status:
        s = status.strip().lower()
        out = [t for t in out if str(t.get("status", "")).strip().lower() == s]

    if category:
        c = category.strip().lower()
        out = [t for t in out if str(t.get("category", "")).strip().lower() == c]

    if due_before:
        raw = due_before.strip()
        if ".." in raw:
            a, b = raw.split("..", 1)
            da = parse_date_yyyy_mm_dd(a.strip())
            db = parse_date_yyyy_mm_dd(b.strip())
            if da and db:
                def ok_range(t):
                    d = parse_date_yyyy_mm_dd(t.get("due_date", ""))
                    return d is not None and da <= d <= db
                out = [t for t in out if ok_range(t)]
        else:
            db = parse_date_yyyy_mm_dd(raw)
            if db:
                def ok_before(t):
                    d = parse_date_yyyy_mm_dd(t.get("due_date", ""))
                    return d is not None and d <= db
                out = [t for t in out if ok_before(t)]

    return out


def search_tasks(tasks: list, query: str) -> list:
    q = (query or "").strip().lower()
    if q == "":
        return []
    out = []
    for t in tasks:
        title = str(t.get("title", "")).lower()
        desc = str(t.get("description", "")).lower()
        if q in title or q in desc:
            out.append(_ensure_task_defaults(dict(t)))
    return out


def summarize_by_category(tasks: list) -> dict:
    summary: dict[str, int] = {}
    for t in tasks:
        c = str(t.get("category", "Uncategorized")).strip() or "Uncategorized"
        summary[c] = summary.get(c, 0) + 1
    return summary


def upcoming_tasks(tasks: list, within_days: int) -> list:
    today = date.today()
    out = []
    for t in tasks:
        d = parse_date_yyyy_mm_dd(t.get("due_date", ""))
        if d is None:
            continue
        diff = (d - today).days
        if 0 <= diff <= int(within_days):
            out.append(_ensure_task_defaults(dict(t)))
    return out


# -------------------------
# Extra features required by spec (priority filter, tags, bulk reassignment, overdue)
# -------------------------
def update_overdue_tasks(tasks: list) -> list[dict]:
    """
    Automatically mark overdue tasks and return list of tasks that were changed.
    Rule: due_date < today AND status not Done/Archived => set status Overdue
    If it was Overdue and now due_date is in the future => set back to Pending
    """
    today = date.today()
    changed = []

    for t in tasks:
        _ensure_task_defaults(t)
        st = t.get("status")
        due = parse_date_yyyy_mm_dd(t.get("due_date", ""))

        if due is not None:
            if due < today and st not in ["Done", "Archived"]:
                if st != "Overdue":
                    t["status"] = "Overdue"
                    t["updated_at"] = _now_iso()
                    changed.append(t)
            else:
                # if no longer overdue
                if st == "Overdue" and due >= today:
                    t["status"] = "Pending"
                    t["updated_at"] = _now_iso()
                    changed.append(t)

    return changed


def filter_tasks_advanced(
    tasks: list[dict],
    *,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    due_after: str | None = None,
    due_before: str | None = None,
) -> list[dict]:
    out = [_ensure_task_defaults(dict(t)) for t in tasks]

    if status:
        s = status.strip().lower()
        out = [t for t in out if str(t.get("status", "")).lower() == s]

    if category:
        c = category.strip().lower()
        out = [t for t in out if str(t.get("category", "")).lower() == c]

    if priority:
        p = normalize_priority(priority).lower()
        out = [t for t in out if str(t.get("priority", "")).lower() == p]

    if tag:
        tg = tag.strip().lower()
        def has_tag(t):
            return any(str(x).lower() == tg for x in (t.get("tags") or []))
        out = [t for t in out if has_tag(t)]

    da = parse_date_yyyy_mm_dd(due_after)
    db = parse_date_yyyy_mm_dd(due_before)
    if da or db:
        def ok_date(t):
            d = parse_date_yyyy_mm_dd(t.get("due_date", ""))
            if d is None:
                return False
            if da and d < da:
                return False
            if db and d > db:
                return False
            return True
        out = [t for t in out if ok_date(t)]

    return out


def set_task_tags(tasks: list[dict], task_id: str, tags: list[str]) -> dict | None:
    t = _find_task(tasks, task_id)
    if t is None:
        return None
    clean = []
    seen = set()
    for x in tags:
        s = str(x).strip()
        if s == "":
            continue
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        clean.append(s)
    t["tags"] = clean
    t["updated_at"] = _now_iso()
    _ensure_task_defaults(t)
    return t


def bulk_reassign_tag(tasks: list[dict], old_tag: str, new_tag: str) -> int:
    old = old_tag.strip().lower()
    new = new_tag.strip()
    if old == "" or new == "":
        return 0

    cnt = 0
    for t in tasks:
        _ensure_task_defaults(t)
        tags = t.get("tags", [])
        changed = False
        out = []
        for tg in tags:
            if str(tg).strip().lower() == old:
                out.append(new)
                changed = True
            else:
                out.append(tg)
        # unique
        uniq = []
        seen = set()
        for x in out:
            k = str(x).strip().lower()
            if k == "" or k in seen:
                continue
            seen.add(k)
            uniq.append(str(x).strip())
        if changed:
            t["tags"] = uniq
            t["updated_at"] = _now_iso()
            cnt += 1
    return cnt


def urgency_score(task: dict) -> int:
    """
    Higher = more urgent.
    - Overdue => big
    - Due soon => bigger
    - High priority => bigger
    """
    _ensure_task_defaults(task)
    score = 0

    st = task.get("status")
    if st == "Overdue":
        score += 1000
    if st == "Pending":
        score += 50
    if st == "In Progress":
        score += 80
    if st == "Done":
        score -= 100
    if st == "Archived":
        score -= 200

    pr = task.get("priority")
    if pr == "High":
        score += 100
    elif pr == "Medium":
        score += 50
    elif pr == "Low":
        score += 10

    d = parse_date_yyyy_mm_dd(task.get("due_date", ""))
    if d is not None:
        diff = (d - date.today()).days
        if diff < 0:
            score += 500
        else:
            score += max(0, 200 - diff * 10)

    return score


def sort_by_urgency(tasks: list[dict]) -> list[dict]:
    return sorted(tasks, key=lambda t: urgency_score(t), reverse=True)
