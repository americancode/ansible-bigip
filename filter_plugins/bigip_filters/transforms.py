from __future__ import annotations

from .common import fq_name


def expand_monitor_list(monitors, monitor_sets):
    """Expand monitor alias names into their full BIG-IP monitor references.

    Purpose:
        Allows var files to use short alias names (e.g., "http_tcp") that resolve
        to one or more fully-qualified monitor paths via a monitor_sets dictionary.

    Inputs:
        monitors (list|None): List of monitor references; may be alias strings or
            already-qualified paths (e.g., "/Common/http").
        monitor_sets (dict|None): Mapping of alias name to a single monitor path
            or list of monitor paths.

    Outputs:
        list: Expanded list where alias strings are replaced by their resolved value(s).

    Constraints:
        - Aliases only resolve for plain strings that do NOT start with "/" (to avoid
          mistakenly expanding already-qualified paths).
        - Returns the original list unchanged if monitors is falsy.
    """
    if not monitors:
        return monitors

    expanded = []
    aliases = monitor_sets or {}
    for monitor in monitors:
        if isinstance(monitor, str) and not monitor.startswith("/") and monitor in aliases:
            alias_value = aliases[monitor]
            if isinstance(alias_value, list):
                expanded.extend(alias_value)
            else:
                expanded.append(alias_value)
        else:
            expanded.append(monitor)
    return expanded


def normalize_members(members, member_defaults):
    """Apply per-pool member defaults to each pool member.

    Purpose:
        Merges pool-level member_defaults into every member dict so that common
        fields (e.g., partition, connection_limit) don't need to be repeated.

    Inputs:
        members (list|None): List of member dicts.
        member_defaults (dict|None): Default fields to apply to each member.

    Outputs:
        list: New list of member dicts with defaults merged in (member fields win).

    Constraints:
        - Returns the original value if members is falsy.
        - Defaults are applied via dict unpacking; explicit member fields override.
    """
    if not members:
        return members
    defaults = member_defaults or {}
    return [dict(defaults, **member) for member in members]


def resolve_gtm_members(members, pool_partition, ltm_virtual_servers):
    """Resolve GTM pool member references against known LTM virtual servers.

    Purpose:
        GTM pool members reference LTM virtual servers by name. This function looks up
        the referenced LTM virtual server and copies its destination address/port
        into the member if not already specified.

    Inputs:
        members (list|None): List of GTM member dicts. Each may contain
            ltm_virtual_server/virtual_server and ltm_partition/partition keys.
        pool_partition (str|None): The partition of the GTM pool (used as default).
        ltm_virtual_servers (dict|None): Lookup map of LTM virtual servers keyed by
            fully-qualified name (e.g., "/Common/vs_myapp").

    Outputs:
        list: Member dicts with address and port filled in from the referenced LTM
        virtual server when available.

    Constraints:
        - Non-dict members are passed through unchanged.
        - Only fills address/port if they are missing from the member dict.
        - Uses fq_name() to build the lookup key from ltm_partition and ltm_name.
    """
    if not members:
        return members

    resolved_members = []
    lookup = ltm_virtual_servers or {}
    default_partition = pool_partition or "Common"

    for member in members:
        if not isinstance(member, dict):
            resolved_members.append(member)
            continue

        resolved = dict(member)
        ltm_name = resolved.get("ltm_virtual_server", resolved.get("virtual_server"))
        ltm_partition = resolved.get("ltm_partition", resolved.get("partition", default_partition))
        ltm_ref = fq_name(ltm_partition, ltm_name)
        ltm_virtual = lookup.get(ltm_ref)

        if ltm_virtual is not None:
            if resolved.get("address") in (None, ""):
                resolved["address"] = ltm_virtual.get("destination")
            if resolved.get("port") in (None, ""):
                resolved["port"] = ltm_virtual.get("destination_port")

        resolved_members.append(resolved)

    return resolved_members


def normalize_ltm_pool(pool, pool_defaults=None, member_defaults=None, monitor_sets=None):
    """Normalize an LTM pool definition by applying defaults and expanding monitors/members.

    Purpose:
        Ensures a pool object is fully shaped for runtime tasks: merges pool-level defaults,
        expands monitor aliases, and applies member defaults.

    Inputs:
        pool (dict|None): The raw pool object from var files.
        pool_defaults (dict|None): Default fields for the pool itself (e.g., partition,
            monitor_type).
        member_defaults (dict|None): Default fields applied to each member.
        monitor_sets (dict|None): Monitor alias mapping for expand_monitor_list.

    Outputs:
        dict: Normalized pool dict with defaults merged, monitors expanded, and members
        normalized.

    Constraints:
        - Pool-level defaults are applied first, then pool fields override them.
        - Returns the input unchanged if it is not a dict.
    """
    if not isinstance(pool, dict):
        return pool

    normalized = dict(pool_defaults or {})
    normalized.update(pool)

    if "monitors" in normalized:
        normalized["monitors"] = expand_monitor_list(normalized.get("monitors"), monitor_sets)

    if "members" in normalized:
        normalized["members"] = normalize_members(normalized.get("members"), member_defaults)

    return normalized


def normalize_gtm_pool(pool, pool_defaults=None, member_defaults=None, monitor_sets=None, ltm_virtual_servers=None):
    """Normalize a GTM pool definition by applying defaults and resolving members/monitors.

    Purpose:
        Shapes a GTM pool for runtime use: merges pool defaults, expands monitor aliases
        (both monitors and default_monitors), normalizes members, and resolves LTM virtual
        server references for each member.

    Inputs:
        pool (dict|None): The raw GTM pool object from var files.
        pool_defaults (dict|None): Default fields for the pool.
        member_defaults (dict|None): Default fields applied to each member.
        monitor_sets (dict|None): Monitor alias mapping.
        ltm_virtual_servers (dict|None): Lookup map of LTM virtual servers for member
            resolution.

    Outputs:
        dict: Normalized GTM pool with all references resolved and defaults applied.

    Constraints:
        - Returns the input unchanged if it is not a dict.
        - Member resolution requires ltm_virtual_servers to be populated (typically
          done in the GTM prep flow by collecting compiled LTM virtual servers).
    """
    if not isinstance(pool, dict):
        return pool

    normalized = dict(pool_defaults or {})
    normalized.update(pool)

    if "monitors" in normalized:
        normalized["monitors"] = expand_monitor_list(normalized.get("monitors"), monitor_sets)
    if "default_monitors" in normalized:
        normalized["default_monitors"] = expand_monitor_list(normalized.get("default_monitors"), monitor_sets)

    if "members" in normalized:
        normalized["members"] = normalize_members(normalized.get("members"), member_defaults)
        normalized["members"] = resolve_gtm_members(
            normalized.get("members"),
            normalized.get("partition", "Common"),
            ltm_virtual_servers,
        )

    return normalized
