from __future__ import annotations

import os
from storage import save_state
from tasks import create_task

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    tasks = []
    categories = [
        {"id": "c1a2b3c4", "name": "School", "description": "Assignments and exams", "color": "blue"},
        {"id": "d4e5f6a7", "name": "Work", "description": "Client work and deliverables", "color": "green"},
        {"id": "b7c8d9e0", "name": "Personal", "description": "Personal errands", "color": "yellow"},
    ]
    activity = []

    create_task(tasks, {
        "title": "Finish term project",
        "description": "Implement CLI + persistence + tests",
        "category": "School",
        "priority": "High",
        "due_date": "",
        "tags": ["python", "deadline"]
    })
    create_task(tasks, {
        "title": "Prepare weekly plan",
        "description": "List next week priorities",
        "category": "Personal",
        "priority": "Medium",
        "due_date": "",
        "tags": ["planning"]
    })
    create_task(tasks, {
        "title": "Client email follow-up",
        "description": "Send updated proposal",
        "category": "Work",
        "priority": "High",
        "due_date": "",
        "tags": ["email", "client"]
    })

    save_state(BASE_DIR, tasks, categories, activity)
    print("Sample data generated into data/ folder.")

if __name__ == "__main__":
    main()
