from __future__ import annotations


def classify_operations(active_objects, deletion_objects=None):
    """Split active and deletion objects into present/absent buckets for apply/delete playbook phases.

    Purpose:
        Used by tasks/manage.yml to separate objects into delete-first and apply-second
        ordering. Objects from /deletions trees and any with state: absent are routed
        to the delete bucket; all others go to present.

    Inputs:
        active_objects (list[dict]|None): Objects from the main var tree (vars/<domain>/<type>/).
        deletion_objects (list[dict]|None): Objects from the deletions tree (vars/<domain>/deletions/<type>/).

    Outputs:
        dict: {"delete": [..], "present": [..]} with mutually exclusive lists.

    Constraints:
        - Non-dict items are skipped silently.
        - state: "absent" is the only trigger for the delete bucket; everything else
          (including missing state) is treated as present.
    """
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
