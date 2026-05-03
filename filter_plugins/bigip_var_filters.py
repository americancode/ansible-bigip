from __future__ import annotations


def _fq_name(partition, name):
    if not isinstance(name, str):
        return None
    if name.startswith("/"):
        return name
    return f"/{partition or 'Common'}/{name}"


def _quote_tmsh(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _expand_monitor_list(monitors, monitor_sets):
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


def _normalize_members(members, member_defaults):
    if not members:
        return members
    defaults = member_defaults or {}
    return [dict(defaults, **member) for member in members]


def _resolve_gtm_members(members, pool_partition, ltm_virtual_servers):
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
        ltm_ref = _fq_name(ltm_partition, ltm_name)
        ltm_virtual = lookup.get(ltm_ref)

        if ltm_virtual is not None:
            if resolved.get("address") in (None, ""):
                resolved["address"] = ltm_virtual.get("destination")
            if resolved.get("port") in (None, ""):
                resolved["port"] = ltm_virtual.get("destination_port")

        resolved_members.append(resolved)

    return resolved_members


def build_nat_tmsh_command(action, nat):
    if not isinstance(nat, dict):
        return None

    partition = nat.get("partition", "Common")
    name = nat.get("name")
    if not name:
        return None
    fq_name = _fq_name(partition, name)

    if action == "show":
        return f"list ltm nat {fq_name} one-line"
    if action == "delete":
        return f"delete ltm nat {fq_name}"

    verb = "create" if action == "create" else "modify"
    parts = [verb, "ltm", "nat", fq_name]

    if nat.get("originating_address") not in (None, ""):
        parts.extend(["originating-address", str(nat["originating_address"])])
    if nat.get("translation_address") not in (None, ""):
        parts.extend(["translation-address", str(nat["translation_address"])])
    if nat.get("traffic_group") not in (None, ""):
        parts.extend(["traffic-group", str(nat["traffic_group"])])
    if nat.get("auto_lasthop") not in (None, ""):
        parts.extend(["auto-lasthop", str(nat["auto_lasthop"])])
    if nat.get("description") not in (None, ""):
        parts.extend(["description", _quote_tmsh(nat["description"])])
    if nat.get("enabled") is not None:
        parts.append("enabled" if bool(nat["enabled"]) else "disabled")
    if nat.get("arp") is not None:
        parts.append("arp" if bool(nat["arp"]) else "no-arp")

    vlans = nat.get("vlans")
    if isinstance(vlans, list):
        if vlans:
            parts.extend(["vlans", "replace-all-with", "{", " ".join(vlans), "}"])
            if nat.get("vlans_enabled") is not None:
                parts.append("vlans-enabled" if bool(nat["vlans_enabled"]) else "vlans-disabled")
        else:
            parts.extend(["vlans", "none"])
    elif nat.get("vlans_default"):
        parts.extend(["vlans", "default"])

    return " ".join(parts)


def build_management_route_tmsh_command(action, management):
    if not isinstance(management, dict):
        return None

    route_name = management.get("route_name", "default")
    gateway = management.get("gateway")
    if not route_name:
        return None

    if action == "show":
        return f"list sys management-route {route_name} one-line"

    verb = "create" if action == "create" else "modify"
    parts = [verb, "sys", "management-route", str(route_name)]
    if gateway not in (None, ""):
        parts.extend(["gateway", str(gateway)])
    return " ".join(parts)


def build_management_ip_tmsh_command(management):
    if not isinstance(management, dict):
        return None

    address = management.get("address")
    if address in (None, ""):
        return None
    return f"modify sys management-ip {address}"


def normalize_ltm_pool(pool, pool_defaults=None, member_defaults=None, monitor_sets=None):
    if not isinstance(pool, dict):
        return pool

    normalized = dict(pool_defaults or {})
    normalized.update(pool)

    if "monitors" in normalized:
        normalized["monitors"] = _expand_monitor_list(normalized.get("monitors"), monitor_sets)

    if "members" in normalized:
        normalized["members"] = _normalize_members(normalized.get("members"), member_defaults)

    return normalized


def normalize_gtm_pool(pool, pool_defaults=None, member_defaults=None, monitor_sets=None, ltm_virtual_servers=None):
    if not isinstance(pool, dict):
        return pool

    normalized = dict(pool_defaults or {})
    normalized.update(pool)

    if "monitors" in normalized:
        normalized["monitors"] = _expand_monitor_list(normalized.get("monitors"), monitor_sets)
    if "default_monitors" in normalized:
        normalized["default_monitors"] = _expand_monitor_list(normalized.get("default_monitors"), monitor_sets)

    if "members" in normalized:
        normalized["members"] = _normalize_members(normalized.get("members"), member_defaults)
        normalized["members"] = _resolve_gtm_members(
            normalized.get("members"),
            normalized.get("partition", "Common"),
            ltm_virtual_servers,
        )

    return normalized


class FilterModule(object):
    def filters(self):
        return {
            "normalize_ltm_pool": normalize_ltm_pool,
            "normalize_gtm_pool": normalize_gtm_pool,
            "expand_monitor_list": _expand_monitor_list,
            "resolve_gtm_members": _resolve_gtm_members,
            "build_nat_tmsh_command": build_nat_tmsh_command,
            "build_management_route_tmsh_command": build_management_route_tmsh_command,
            "build_management_ip_tmsh_command": build_management_ip_tmsh_command,
        }
