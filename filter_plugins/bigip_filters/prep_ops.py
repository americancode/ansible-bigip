from __future__ import annotations


def classify_operations(active_objects, deletion_objects=None):
    combined = list(active_objects or []) + list(deletion_objects or [])
    delete_items = []
    present_items = []

    for item in combined:
        if not isinstance(item, dict):
            continue
        state = item.get("state")
        if state == "absent":
            delete_items.append(item)
        else:
            present_items.append(item)

    return {
        "delete": delete_items,
        "present": present_items,
    }
