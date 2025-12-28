from __future__ import annotations

import json
import os
import uuid


def _new_id() -> str:
    return uuid.uuid4().hex[:8]


# REQUIRED
def load_categories(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


# REQUIRED
def save_categories(path: str, categories: list) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


def _name_exists(categories: list[dict], name: str, ignore_id: str | None = None) -> bool:
    target = name.strip().lower()
    for c in categories:
        if ignore_id and c.get("id") == ignore_id:
            continue
        if str(c.get("name", "")).strip().lower() == target:
            return True
    return False


# REQUIRED
def add_category(categories: list, category_data: dict) -> dict | None:
    name = str(category_data.get("name", "")).strip()
    if name == "":
        name = "Unnamed"

    if _name_exists(categories, name):
        return None

    cat = {
        "id": _new_id(),
        "name": name,
        "description": str(category_data.get("description", "")).strip(),
        "color": str(category_data.get("color", "")).strip(),  # textual
    }
    categories.append(cat)
    return cat


# REQUIRED
def update_category(categories: list, category_id: str, updates: dict) -> dict | None:
    for c in categories:
        if c.get("id") == category_id:
            if "name" in updates:
                new_name = str(updates["name"]).strip() or "Unnamed"
                if _name_exists(categories, new_name, ignore_id=category_id):
                    return None
                c["name"] = new_name
            if "description" in updates:
                c["description"] = str(updates["description"]).strip()
            if "color" in updates:
                c["color"] = str(updates["color"]).strip()
            return c
    return None


# REQUIRED
def delete_category(categories: list, category_id: str, tasks: list) -> bool:
    idx = None
    deleted_name = None
    for i, c in enumerate(categories):
        if c.get("id") == category_id:
            idx = i
            deleted_name = c.get("name")
            break
    if idx is None:
        return False

    categories.pop(idx)

    # move tasks to Uncategorized
    if deleted_name:
        for t in tasks:
            if str(t.get("category", "")).strip() == str(deleted_name).strip():
                t["category"] = "Uncategorized"

    return True
