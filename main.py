from __future__ import annotations

import os

from storage import load_state, save_state, backup_state
from tasks import (
    create_task, update_task, delete_task, mark_task_status, add_subtask,
    search_tasks, summarize_by_category, upcoming_tasks,
    update_overdue_tasks, filter_tasks_advanced, set_task_tags, bulk_reassign_tag,
    parse_date_yyyy_mm_dd, normalize_priority, normalize_status, sort_by_urgency
)
from categories import add_category, update_category, delete_category
from activity import log_activity, load_activity, productivity_stats, export_report, make_event
from views import render_table, render_calendar, daily_summary


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def input_non_empty(prompt: str, default: str | None = None) -> str:
    while True:
        s = input(prompt).strip()
        if s != "":
            return s
        if default is not None:
            return default
        print("Please enter a value.")


def input_due_date(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s == "":
            return ""
        d = parse_date_yyyy_mm_dd(s)
        if d is None:
            print("Invalid date. Use YYYY-MM-DD or blank.")
            continue
        return d.isoformat()


def input_priority(prompt: str) -> str:
    while True:
        s = input(prompt).strip()
        if s == "":
            return "Medium"
        p = normalize_priority(s)
        if p not in ["Low", "Medium", "High"]:
            print("Priority must be Low/Medium/High.")
            continue
        return p


def pick_task_id(tasks: list[dict]) -> str:
    print(render_table(tasks))
    return input_non_empty("Task id: ")


def main():
    # load state + activity
    tasks, categories, activity = load_state(BASE_DIR)

    # daily backup snapshot (once per day)
    backup_state(BASE_DIR, os.path.join(BASE_DIR, "backups"))

    # auto mark overdue + notify
    changed = update_overdue_tasks(tasks)
    if changed:
        for t in changed:
            log_activity(os.path.join(BASE_DIR, "data", "activity.log"),
                         make_event("auto_overdue", t.get("id"), t.get("title")))
        # keep in memory activity list too
        for t in changed:
            activity.append(make_event("auto_overdue", t.get("id"), t.get("title")))
        save_state(BASE_DIR, tasks, categories, activity)

    # startup daily summary
    print(daily_summary(tasks))

    while True:
        print("--- MENU ---")
        print("1) Add task")
        print("2) View pending (quick)")
        print("3) View all tasks")
        print("4) Update task")
        print("5) Mark task status")
        print("6) Add subtask")
        print("7) Delete or archive task")
        print("8) Search tasks")
        print("9) Filter (status/category/priority/tag/date range)")
        print("10) Calendar view (group by due date)")
        print("11) Categories (add/update/delete)")
        print("12) Tags (edit tags / bulk reassign)")
        print("13) Analytics report (export to reports/)")
        print("14) Backup now")
        print("0) Exit")

        choice = input("Select: ").strip()

        if choice == "1":
            title = input_non_empty("Title: ")
            desc = input("Description: ").strip()
            cat = input("Category (blank=Uncategorized): ").strip() or "Uncategorized"
            pr = input_priority("Priority (Low/Medium/High) [blank=Medium]: ")
            due = input_due_date("Due date (YYYY-MM-DD or blank): ")
            tags_raw = input("Tags (comma separated, blank none): ").strip()
            tags = []
            if tags_raw:
                tags = [x.strip() for x in tags_raw.split(",") if x.strip()]

            t = create_task(tasks, {
                "title": title,
                "description": desc,
                "category": cat,
                "priority": pr,
                "due_date": due,
                "tags": tags
            })

            ev = make_event("create_task", t["id"], t["title"])
            activity.append(ev)
            log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)

            save_state(BASE_DIR, tasks, categories, activity)
            print("Added:\n" + render_table([t]))

        elif choice == "2":
            pending = filter_tasks_advanced(tasks, status="Pending")
            pending = sort_by_urgency(pending)
            print(render_table(pending))

        elif choice == "3":
            all_sorted = sort_by_urgency(tasks)
            print(render_table(all_sorted))

        elif choice == "4":
            tid = pick_task_id(tasks)
            print("Leave blank to skip fields.")
            new_title = input("New title: ").strip()
            new_desc = input("New description: ").strip()
            new_cat = input("New category: ").strip()
            new_pr = input("New priority (Low/Medium/High): ").strip()
            new_due = input("New due date (YYYY-MM-DD): ").strip()

            updates = {}
            if new_title:
                updates["title"] = new_title
            if new_desc:
                updates["description"] = new_desc
            if new_cat:
                updates["category"] = new_cat
            if new_pr:
                updates["priority"] = new_pr
            if new_due:
                if parse_date_yyyy_mm_dd(new_due) is None:
                    print("Invalid date. Update cancelled.")
                    continue
                updates["due_date"] = new_due

            t = update_task(tasks, tid, updates)
            if t is None:
                print("Task not found.")
                continue

            ev = make_event("update_task", t["id"], "updated")
            activity.append(ev)
            log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)

            save_state(BASE_DIR, tasks, categories, activity)
            print("Updated:\n" + render_table([t]))

        elif choice == "5":
            tid = pick_task_id(tasks)
            st = input_non_empty("Status (Pending/In Progress/Done/Archived): ")
            st = normalize_status(st)
            t = mark_task_status(tasks, tid, st)
            if t is None:
                print("Task not found.")
                continue

            ev = make_event("mark_status", t["id"], t["status"])
            activity.append(ev)
            log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)

            save_state(BASE_DIR, tasks, categories, activity)
            print("Status updated:\n" + render_table([t]))

        elif choice == "6":
            tid = pick_task_id(tasks)
            title = input_non_empty("Subtask title: ")
            t = add_subtask(tasks, tid, {"title": title})
            if t is None:
                print("Task not found.")
                continue

            ev = make_event("add_subtask", tid, title)
            activity.append(ev)
            log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)

            save_state(BASE_DIR, tasks, categories, activity)
            print("Added subtask.\n" + render_table([t]))

        elif choice == "7":
            tid = pick_task_id(tasks)
            ans = input("Delete task? (y/n) If 'n' you can archive instead: ").strip().lower()
            if ans in ["y", "yes"]:
                # confirm
                sure = input("Are you sure? (y/n): ").strip().lower()
                if sure not in ["y", "yes"]:
                    print("Cancelled.")
                    continue
                ok = delete_task(tasks, tid)
                if ok:
                    ev = make_event("delete_task", tid, "deleted")
                    activity.append(ev)
                    log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                    save_state(BASE_DIR, tasks, categories, activity)
                    print("Deleted.")
                else:
                    print("Task not found.")
            else:
                # archive option
                t = mark_task_status(tasks, tid, "Archived")
                if t is None:
                    print("Task not found.")
                    continue
                ev = make_event("archive_task", tid, "archived")
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print("Archived:\n" + render_table([t]))

        elif choice == "8":
            q = input_non_empty("Keyword: ")
            res = search_tasks(tasks, q)
            res = sort_by_urgency(res)
            print(render_table(res))

        elif choice == "9":
            st = input("Status (blank skip): ").strip() or None
            cat = input("Category (blank skip): ").strip() or None
            pr = input("Priority Low/Medium/High (blank skip): ").strip() or None
            tg = input("Tag (blank skip): ").strip() or None
            da = input("Due AFTER YYYY-MM-DD (blank skip): ").strip() or None
            db = input("Due BEFORE YYYY-MM-DD (blank skip): ").strip() or None

            # validate dates if entered
            if da and parse_date_yyyy_mm_dd(da) is None:
                print("Invalid due_after date.")
                continue
            if db and parse_date_yyyy_mm_dd(db) is None:
                print("Invalid due_before date.")
                continue

            res = filter_tasks_advanced(tasks, status=st, category=cat, priority=pr, tag=tg, due_after=da, due_before=db)
            res = sort_by_urgency(res)
            print(render_table(res))

        elif choice == "10":
            print(render_calendar(sort_by_urgency(tasks)))

        elif choice == "11":
            print("Categories:")
            for c in categories:
                print(f"- {c.get('id')} | {c.get('name')} | {c.get('color')} | {c.get('description')}")
            print("a) add, u) update, d) delete, x) back")
            sub = input("Select: ").strip().lower()
            if sub == "a":
                name = input_non_empty("Name: ")
                desc = input("Description: ").strip()
                color = input("Color (text): ").strip()
                c = add_category(categories, {"name": name, "description": desc, "color": color})
                if c is None:
                    print("Category name already exists.")
                    continue
                ev = make_event("add_category", c["id"], c["name"])
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print("Added category.")
            elif sub == "u":
                cid = input_non_empty("Category id: ")
                new_name = input("New name (blank skip): ").strip()
                new_desc = input("New description (blank skip): ").strip()
                new_color = input("New color (blank skip): ").strip()
                updates = {}
                if new_name:
                    updates["name"] = new_name
                if new_desc:
                    updates["description"] = new_desc
                if new_color:
                    updates["color"] = new_color
                if not updates:
                    print("Nothing to update.")
                    continue
                c = update_category(categories, cid, updates)
                if c is None:
                    print("Update failed (not found or duplicate name).")
                    continue
                ev = make_event("update_category", cid, "updated")
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print("Updated category.")
            elif sub == "d":
                cid = input_non_empty("Category id to delete: ")
                ok = delete_category(categories, cid, tasks)
                if not ok:
                    print("Not found.")
                    continue
                ev = make_event("delete_category", cid, "deleted")
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print("Deleted category. Related tasks moved to Uncategorized.")
            else:
                continue

        elif choice == "12":
            print("a) edit tags of a task")
            print("b) bulk reassign tag (old -> new)")
            sub = input("Select: ").strip().lower()
            if sub == "a":
                tid = pick_task_id(tasks)
                raw = input("Tags (comma separated): ").strip()
                tags = [x.strip() for x in raw.split(",") if x.strip()]
                t = set_task_tags(tasks, tid, tags)
                if t is None:
                    print("Task not found.")
                    continue
                ev = make_event("set_tags", tid, ",".join(tags))
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print("Updated tags:\n" + render_table([t]))
            elif sub == "b":
                old = input_non_empty("Old tag: ")
                new = input_non_empty("New tag: ")
                n = bulk_reassign_tag(tasks, old, new)
                ev = make_event("bulk_reassign_tag", None, f"{old} -> {new} ({n} tasks)")
                activity.append(ev)
                log_activity(os.path.join(BASE_DIR, "data", "activity.log"), ev)
                save_state(BASE_DIR, tasks, categories, activity)
                print(f"Reassigned on {n} task(s).")
            else:
                continue

        elif choice == "13":
            # reload activity from log to be safe
            activity = load_activity(os.path.join(BASE_DIR, "data", "activity.log"))
            report = productivity_stats(tasks, activity)
            filename = f"report_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            path = export_report(report, filename)
            print("Report exported:", path)

        elif choice == "14":
            created = backup_state(BASE_DIR, os.path.join(BASE_DIR, "backups"))
            if created:
                print("Backup created:", created[0])
            else:
                print("Backup already exists for today.")

        elif choice == "0":
            print("Bye.")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
