from __future__ import annotations

from datetime import date
from tasks import parse_date_yyyy_mm_dd, urgency_score


STATUS_ICON = {
    "Pending": "[ ]",
    "In Progress": "[~]",
    "Done": "[x]",
    "Archived": "[-]",
    "Overdue": "[!]",
}

def _icon(status: str) -> str:
    return STATUS_ICON.get(status, "[?]")

def _clip(s: str, n: int) -> str:
    s = str(s)
    if len(s) <= n:
        return s
    return s[: max(0, n - 1)] + "…"

def render_table(tasks: list[dict], max_desc: int = 28) -> str:
    if not tasks:
        return "No tasks.\n"

    headers = ["ID", "S", "Title", "Category", "Pr", "Due", "Tags"]
    rows = []

    for t in tasks:
        tags = ", ".join(t.get("tags", []) or [])
        rows.append([
            str(t.get("id", "")),
            _icon(str(t.get("status", ""))),
            _clip(str(t.get("title", "")), 30),
            _clip(str(t.get("category", "")), 14),
            str(t.get("priority", ""))[:1].upper(),
            str(t.get("due_date", "")),
            _clip(tags, 20),
        ])

    # column widths
    widths = [len(h) for h in headers]
    for r in rows:
        for i, cell in enumerate(r):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(r):
        return " | ".join(r[i].ljust(widths[i]) for i in range(len(headers)))

    out = []
    out.append(fmt_row(headers))
    out.append("-" * (sum(widths) + 3 * (len(headers) - 1)))
    for r in rows:
        out.append(fmt_row(r))
    out.append("")
    return "\n".join(out)

def calendar_group(tasks: list[dict]) -> dict[str, list[dict]]:
    """
    Calendar-style view grouped by due date.
    """
    groups: dict[str, list[dict]] = {}
    for t in tasks:
        due = str(t.get("due_date", "")).strip()
        key = due if due else "No due date"
        groups.setdefault(key, []).append(t)

    # sort each group by urgency
    for k in list(groups.keys()):
        groups[k] = sorted(groups[k], key=lambda x: urgency_score(x), reverse=True)

    return dict(sorted(groups.items(), key=lambda kv: kv[0]))

def render_calendar(tasks: list[dict]) -> str:
    groups = calendar_group(tasks)
    out = []
    for k, items in groups.items():
        out.append(f"=== {k} ===")
        out.append(render_table(items).rstrip())
        out.append("")
    return "\n".join(out)

def daily_summary(tasks: list[dict]) -> str:
    today = date.today()
    today_str = today.isoformat()

    due_today = []
    overdue = []
    for t in tasks:
        due = parse_date_yyyy_mm_dd(t.get("due_date", ""))
        if due is None:
            continue
        if due == today and t.get("status") not in ["Done", "Archived"]:
            due_today.append(t)
        if due < today and t.get("status") not in ["Done", "Archived"]:
            overdue.append(t)

    out = []
    out.append("=== Daily Summary ===")
    out.append(f"Today: {today_str}")
    out.append("")
    out.append("Tasks due today:")
    out.append(render_table(due_today).rstrip())
    out.append("")
    out.append("Overdue tasks:")
    out.append(render_table(overdue).rstrip())
    out.append("")
    return "\n".join(out)
