from __future__ import annotations


def fq_name(partition, name):
    """Build a fully-qualified BIG-IP object name.

    Purpose:
        Ensures object names are partition-scoped for proper BIG-IP API/CLI references.

    Inputs:
        partition (str): The BIG-IP partition (e.g., "Common", "prod").
        name (str): The object name, possibly already qualified.

    Outputs:
        str or None: Fully-qualified name like "/Common/my-pool", or None if name is not a string.

    Constraints:
        - If name already starts with "/", it is returned unchanged (assumed already qualified).
        - Defaults to "Common" partition if partition is falsy.
    """
    if not isinstance(name, str):
        return None
    if name.startswith("/"):
        return name
    return f"/{partition or 'Common'}/{name}"


def quote_tmsh(value):
    """Escape and quote a value for safe use in tmsh command strings.

    Purpose:
        Wraps values in double quotes and escapes backslashes and embedded quotes
        so the result can be embedded in a tmsh command without parsing errors.

    Inputs:
        value (any): The value to quote; converted to string via str().

    Outputs:
        str: A double-quoted, escaped string suitable for tmsh.

    Constraints:
        - Replaces backslash with double-backslash, then escapes double quotes.
    """
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def ensure_list(value):
    """Coerce a value to a list.

    Purpose:
        Normalizes inputs so callers always receive a list, even when a single
        value or None/empty is provided.

    Inputs:
        value (any): The value to coerce.

    Outputs:
        list: An empty list if value is None or empty string; the original list
        if already a list; otherwise a single-element list.

    Constraints:
        - Empty string "" is treated as "no value" and returns [].
    """
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


def deep_merge_dicts(base, overlay):
    """Recursively merge two dictionaries, with overlay values taking precedence.

    Purpose:
        Provides hierarchical settings inheritance by deeply merging nested dicts.
        Used by settings.py to layer directory-level settings.yml files.

    Inputs:
        base (dict|None): The base dictionary (lower priority).
        overlay (dict|None): The overlay dictionary (higher priority).

    Outputs:
        dict: A new merged dictionary. Nested dicts are merged recursively;
        scalar/sequence values in overlay overwrite base.

    Constraints:
        - None inputs are treated as {}.
        - Only dict-on-dict conflicts are merged; all other types are replaced.
    """
    merged = dict(base or {})
    for key, value in (overlay or {}).items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge_dicts(existing, value)
        else:
            merged[key] = value
    return merged
