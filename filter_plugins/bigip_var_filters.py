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


def _ensure_list(value):
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return value
    return [value]


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


def build_login_banner_tmsh_command(action, banner):
    if not isinstance(banner, dict):
        return None

    if action == "delete":
        return "modify sys global-settings gui-security-banner disabled"

    parts = ["modify", "sys", "global-settings"]
    enabled = banner.get("enabled")
    if enabled is not None:
        parts.extend(["gui-security-banner", "enabled" if bool(enabled) else "disabled"])
    if banner.get("text") not in (None, ""):
        parts.extend(["gui-security-banner-text", _quote_tmsh(banner["text"])])
    return " ".join(parts)


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


def compile_ltm_virtual_server_intent(virtual_server, pool_defaults=None, member_defaults=None, monitor_sets=None):
    if not isinstance(virtual_server, dict):
        return {"virtual_server": virtual_server, "pools": []}

    compiled_virtual_server = dict(virtual_server)
    compiled_pools = []
    pool = compiled_virtual_server.get("pool")

    if isinstance(pool, dict):
        virtual_partition = compiled_virtual_server.get("partition", "Common")
        normalized_pool = normalize_ltm_pool(pool, pool_defaults, member_defaults, monitor_sets)
        normalized_pool = dict(normalized_pool)
        normalized_pool.setdefault("partition", virtual_partition)
        compiled_pools.append(normalized_pool)

        if normalized_pool.get("partition", virtual_partition) == virtual_partition:
            compiled_virtual_server["pool"] = normalized_pool["name"]
        else:
            compiled_virtual_server["pool"] = _fq_name(normalized_pool.get("partition"), normalized_pool["name"])

    return {
        "virtual_server": compiled_virtual_server,
        "pools": compiled_pools,
    }


def compile_ltm_rke2_server_intent(intent, intent_defaults=None, pool_defaults=None, member_defaults=None, monitor_sets=None):
    if not isinstance(intent, dict):
        return {"virtual_servers": [], "pools": []}

    resolved_intent = dict(intent_defaults or {})
    resolved_intent.update(intent)

    partition = resolved_intent.get("partition", "Common")
    intent_name = resolved_intent.get("name")
    if not intent_name:
        return {"virtual_servers": [], "pools": []}

    control_plane_members = _normalize_members(resolved_intent.get("control_plane_members"), member_defaults) or []
    worker_members = _normalize_members(resolved_intent.get("worker_members"), member_defaults) or []
    worker_services = resolved_intent.get("worker_services") or {}

    base_virtual_server = {
        key: value
        for key, value in resolved_intent.items()
        if key
        not in {
            "__source_file",
            "name",
            "control_plane_vip",
            "control_plane_members",
            "worker_members",
            "worker_services",
            "kubeapi_monitors",
            "registration_monitors",
            "description_prefix",
            "state",
        }
    }
    base_virtual_server.setdefault("partition", partition)

    description_prefix = resolved_intent.get("description_prefix", str(intent_name).replace("_", " "))
    kubeapi_monitors = _expand_monitor_list(
        _ensure_list(resolved_intent.get("kubeapi_monitors", ["kubeapi_tcp"])),
        monitor_sets,
    )
    registration_monitors = _expand_monitor_list(
        _ensure_list(resolved_intent.get("registration_monitors", ["registration_tcp"])),
        monitor_sets,
    )

    state = resolved_intent.get("state")
    deleting = state == "absent"

    compiled_virtual_servers = []
    compiled_pools = []

    def build_members(source_members, port):
        members = []
        for member in source_members:
            if not isinstance(member, dict):
                continue
            compiled_member = dict(member)
            compiled_member["port"] = port
            members.append(compiled_member)
        return members

    def add_service(*, suffix, destination, destination_port, pool_name, monitors, members, description):
        virtual_server = dict(base_virtual_server)
        virtual_server["name"] = f"vs_{intent_name}_{suffix}"
        virtual_server["partition"] = partition
        virtual_server["pool"] = pool_name
        if deleting:
            virtual_server["state"] = "absent"
        else:
            virtual_server["destination"] = destination
            virtual_server["destination_port"] = destination_port
            virtual_server["description"] = description

        pool = dict(pool_defaults or {})
        pool.update(
            {
                "name": pool_name,
                "partition": partition,
            }
        )
        if deleting:
            pool["state"] = "absent"
        else:
            pool["monitors"] = monitors
            pool["members"] = members

        compiled_virtual_servers.append(virtual_server)
        compiled_pools.append(pool)

    add_service(
        suffix="kubeapi_6443",
        destination=resolved_intent.get("control_plane_vip"),
        destination_port=6443,
        pool_name=f"pool_{intent_name}_kubeapi_6443",
        monitors=kubeapi_monitors,
        members=build_members(control_plane_members, 6443),
        description=f"{description_prefix} Kubernetes API VIP",
    )
    add_service(
        suffix="registration_9345",
        destination=resolved_intent.get("control_plane_vip"),
        destination_port=9345,
        pool_name=f"pool_{intent_name}_registration_9345",
        monitors=registration_monitors,
        members=build_members(control_plane_members, 9345),
        description=f"{description_prefix} RKE2 supervisor registration VIP",
    )

    for service_name, service in worker_services.items():
        if not isinstance(service_name, str):
            continue
        service = service if isinstance(service, dict) else {}
        node_port = service.get("node_port")
        monitors = _expand_monitor_list(_ensure_list(service.get("monitors")), monitor_sets)
        add_service(
            suffix=f"{service_name}_443",
            destination=service.get("vip"),
            destination_port=443,
            pool_name=f"pool_{intent_name}_{service_name}_443",
            monitors=monitors,
            members=build_members(worker_members, node_port),
            description=service.get("description", f"{description_prefix} {service_name} VIP"),
        )

    return {
        "virtual_servers": compiled_virtual_servers,
        "pools": compiled_pools,
    }


def compile_gtm_wide_ip_intent(wide_ip, pool_defaults=None, member_defaults=None, monitor_sets=None, ltm_virtual_servers=None):
    if not isinstance(wide_ip, dict):
        return {"wide_ip": wide_ip, "pools": []}

    compiled_wide_ip = dict(wide_ip)
    compiled_pools = []
    compiled_pool_refs = []
    wide_ip_partition = compiled_wide_ip.get("partition", "Common")
    record_type = compiled_wide_ip.get("record_type", "a")

    for pool in compiled_wide_ip.get("pools", []) or []:
        if isinstance(pool, str):
            compiled_pool_refs.append({
                "name": pool,
                "partition": wide_ip_partition,
                "ratio": 1,
            })
            continue

        if not isinstance(pool, dict) or not pool.get("name"):
            continue

        if pool.get("members") is not None:
            normalized_pool = normalize_gtm_pool(pool, pool_defaults, member_defaults, monitor_sets, ltm_virtual_servers)
            normalized_pool = dict(normalized_pool)
            normalized_pool.setdefault("partition", wide_ip_partition)
            normalized_pool.setdefault("record_type", record_type)
            compiled_pools.append(normalized_pool)
            compiled_pool_refs.append({
                "name": normalized_pool["name"],
                "partition": normalized_pool.get("partition", wide_ip_partition),
                "ratio": pool.get("ratio", 1),
            })
            continue

        compiled_pool_refs.append({
            "name": pool["name"],
            "partition": pool.get("partition", wide_ip_partition),
            "ratio": pool.get("ratio", 1),
        })

    compiled_wide_ip["pools"] = compiled_pool_refs

    return {
        "wide_ip": compiled_wide_ip,
        "pools": compiled_pools,
    }


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
            "build_login_banner_tmsh_command": build_login_banner_tmsh_command,
            "compile_ltm_virtual_server_intent": compile_ltm_virtual_server_intent,
            "compile_ltm_rke2_server_intent": compile_ltm_rke2_server_intent,
            "compile_gtm_wide_ip_intent": compile_gtm_wide_ip_intent,
        }
