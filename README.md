Terminal Task Manager (Python)

A terminal-based task manager. Supports creating/updating/deleting tasks, subtasks, search/filtering, calendar-style view, category and tag management, activity logging + analytics reports, JSON persistence, and daily backups.

Requirements:

* Python 3.10+

Run:
python3 main.py

Sample data (optional):
python3 generate_sample_data.py
python3 main.py

Tests:
python3 -m pip install pytest
python3 -m pytest -q

Data & backups:
The app creates these automatically:

* data/tasks.json
* data/categories.json
* data/activity.log
* backups/state_YYYYMMDD.json
* reports/report_*.json

Note: data/, backups/, reports/ folders are ignored by .gitignore and not committed.

Features:

* Task CRUD + subtask support
* Status tracking (Pending / In Progress / Done / Archived) + automatic Overdue marking
* Keyword search (title/description)
* Filters: status, category, priority, tag, due date range
* Calendar view (grouped by due date)
* Categories: add/update/delete (deleting a category moves tasks to Uncategorized)
* Tags per task + bulk tag reassignment
* Persistent storage + daily backups
* Corrupt restore: invalid tasks.json restores the latest valid backup automatically
* Activity logging + analytics report export (reports/)