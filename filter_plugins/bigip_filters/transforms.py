from __future__ import annotations

from .common import fq_name


def expand_monitor_list(monitors, monitor_sets):
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
    if not members:
        return members
    defaults = member_defaults or {}
    return [dict(defaults, **member) for member in members]


def resolve_gtm_members(members, pool_partition, ltm_virtual_servers):
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
