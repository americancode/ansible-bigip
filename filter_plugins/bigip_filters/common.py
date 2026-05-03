from __future__ import annotations


def fq_name(partition, name):
    if not isinstance(name, str):
        return None
    if name.startswith("/"):
        return name
    return f"/{partition or 'Common'}/{name}"


def quote_tmsh(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def ensure_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def deep_merge_dicts(base, overlay):
    merged = dict(base or {})
    for key, value in (overlay or {}).items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(existing, value)
        else:
            merged[key] = value
    return merged
