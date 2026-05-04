from __future__ import annotations


def _normalize_target_list(value):
    """Normalize target selector values into a clean list of strings.

    Purpose:
        Converts the optional `target_hosts` / `target_groups` fields into a
        predictable list form for runtime matching and prep-time logging.

    Inputs:
        value (Any): The raw selector value from a var object.

    Outputs:
        list[str]: A list of non-empty string selectors.

    Constraints:
        - Non-list inputs are treated as empty for runtime filtering.
        - Validation is responsible for rejecting malformed selector types.
    """
    if not isinstance(value, list):
        return []
    normalized = []
    for entry in value:
        if isinstance(entry, str) and entry:
            normalized.append(entry)
    return normalized


def _target_label(item):
    """Build a readable label for prep-time target filtering summaries.

    Purpose:
        Gives `system/prep.yml` an operator-facing identifier for matched and
        skipped objects without hard-coding object-family-specific labels in YAML.
    """
    if not isinstance(item, dict):
        return str(item)
    if isinstance(item.get("source"), str) and item.get("source") and isinstance(item.get("destination"), str) and item.get("destination"):
        return f"{item['source']} -> {item['destination']}"
    if isinstance(item.get("device_group"), str) and item.get("device_group") and isinstance(item.get("name"), str) and item.get("name"):
        return f"{item['device_group']}/{item['name']}"
    if isinstance(item.get("server"), str) and item.get("server") and isinstance(item.get("virtual_server"), str) and item.get("virtual_server"):
        return f"{item['server']}/{item['virtual_server']}"
    if isinstance(item.get("partition"), str) and item.get("partition") and isinstance(item.get("name"), str) and item.get("name"):
        return f"{item['partition']}/{item['name']}"
    for key in ("name", "hostname", "module", "address", "destination"):
        value = item.get(key)
        if value not in (None, ""):
            return str(value)
    if "save" in item:
        return f"save={item.get('save', True)}"
    source_file = item.get("__source_file")
    if isinstance(source_file, str) and source_file:
        return source_file
    return "unnamed-object"


def audit_object_label(item):
    """Build a stable, operator-facing label for audit-mode output.

    Purpose:
        Reuses the same identity heuristics as prep-time targeting summaries so
        audit mode can print concise object identities without leaking full raw
        object payloads or secrets.

    Inputs:
        item (Any): A runtime object, scalar, or derived loop item.

    Outputs:
        str: A readable identity string for audit/debug output.
    """
    if isinstance(item, (list, tuple)):
        return " | ".join(audit_object_label(part) for part in item)
    return _target_label(item)


def split_targeted_objects(objects, inventory_hostname, group_names=None, match_without_selectors=True):
    """Split objects into matched and skipped buckets for the current inventory host.

    Purpose:
        System-domain objects can declare `target_hosts` and/or `target_groups`.
        This helper evaluates those selectors against the current Ansible host
        context so prep can publish only the objects that should apply to the
        current BIG-IP and log what was skipped.

    Inputs:
        objects (list[dict]|None): Raw objects from a var tree.
        inventory_hostname (str|None): Current Ansible inventory host name.
        group_names (list[str]|None): Current Ansible group membership.

    Outputs:
        dict: {
            "matched": list[dict],
            "skipped": list[dict],
            "matched_labels": list[str],
            "skipped_labels": list[str],
        }

    Constraints:
        - Objects without selectors either match every host or no host depending on
          `match_without_selectors`.
        - The returned objects have selector metadata stripped so runtime modules
          only see fields they actually consume.
        - Validation is responsible for enforcing selector presence and shape.
    """
    matched = []
    skipped = []
    matched_labels = []
    skipped_labels = []
    current_host = str(inventory_hostname or "")
    current_groups = {str(group) for group in (group_names or [])}

    for item in objects or []:
        if not isinstance(item, dict):
            continue

        target_hosts = _normalize_target_list(item.get("target_hosts"))
        target_groups = _normalize_target_list(item.get("target_groups"))
        selector_parts = []
        if target_hosts:
            selector_parts.append(f"hosts={','.join(target_hosts)}")
        if target_groups:
            selector_parts.append(f"groups={','.join(target_groups)}")
        if not selector_parts:
            selector_parts.append("no-selectors")

        label = f"{_target_label(item)} [{'; '.join(selector_parts)}]"
        runtime_item = {k: v for k, v in item.items() if k not in {"target_hosts", "target_groups"}}

        if not target_hosts and not target_groups:
            if match_without_selectors:
                matched.append(runtime_item)
                matched_labels.append(label)
            else:
                skipped.append(runtime_item)
                skipped_labels.append(label)
            continue

        host_match = current_host in target_hosts
        group_match = any(group in current_groups for group in target_groups)
        if host_match or group_match:
            matched.append(runtime_item)
            matched_labels.append(label)
        else:
            skipped.append(runtime_item)
            skipped_labels.append(label)

    return {
        "matched": matched,
        "skipped": skipped,
        "matched_labels": matched_labels,
        "skipped_labels": skipped_labels,
    }
