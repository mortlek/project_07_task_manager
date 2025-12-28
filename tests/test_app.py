from __future__ import annotations

import os
import json

from storage import save_state, load_state, backup_state
from tasks import create_task, filter_tasks, validate_task_schema  # validate_task_schema is in storage, not tasks


def test_create_task_required_fields(tmp_path):
    base = str(tmp_path)
    tasks = []
    categories = []
    activity = []
    t = create_task(tasks, {"title": "A", "description": "B", "category": "C", "priority": "High", "due_date": ""})
    save_state(base, tasks, categories, activity)

    tasks2, categories2, activity2 = load_state(base)

    assert len(tasks2) == 1
    assert "id" in tasks2[0]
    assert "title" in tasks2[0]
    assert "created_at" in tasks2[0]
    assert "updated_at" in tasks2[0]


def test_filter_by_status(tmp_path):
    tasks = []
    create_task(tasks, {"title": "T1", "status": "Pending"})
    create_task(tasks, {"title": "T2", "status": "Done"})
    create_task(tasks, {"title": "T3", "status": "Pending"})

    res = filter_tasks(tasks, status="Pending")
    assert len(res) == 2


def test_backup_restore_on_corrupt(tmp_path):
    base = str(tmp_path)
    backup_dir = os.path.join(base, "backups")

    tasks = []
    categories = []
    activity = []
    create_task(tasks, {"title": "X", "category": "Uncategorized"})

    save_state(base, tasks, categories, activity)
    backup_state(base, backup_dir)

    # corrupt tasks.json
    tasks_path = os.path.join(base, "data", "tasks.json")
    with open(tasks_path, "w", encoding="utf-8") as f:
        f.write('{"not":"a list"}')  # invalid schema (not list)

    # load_state should restore from backup (valid)
    tasks2, categories2, activity2 = load_state(base)
    assert isinstance(tasks2, list)
    assert len(tasks2) == 1
    assert "id" in tasks2[0]
