from __future__ import annotations

from filter_plugins.bigip_var_filters import normalize_ltm_pool

from ...constants import VARS_DIR


def validate_base_objects(validator, objects: dict[str, list]) -> dict[str, object]:
    nodes = objects["nodes"]
    profiles = objects["profiles"]
    pools = objects["pools"]
    monitors = objects["monitors"]
    tls_client_ssl_profiles = objects["tls_client_ssl_profiles"]
    tls_server_ssl_profiles = objects["tls_server_ssl_profiles"]

    active_node_names = set()
    for obj in nodes:
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent":
            if not obj.data.get("address") and not obj.data.get("fqdn"):
                validator.error(obj.relpath, f"LTM node `{obj.data.get('name')}` must define either `address` or `fqdn`")
            active_node_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    validator.check_duplicates(nodes, lambda obj: ("ltm_node", obj.partition, obj.data.get("name")), "LTM node")

    active_monitor_names = set()
    for obj in monitors:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state != "absent":
            active_monitor_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    validator.check_duplicates(monitors, lambda obj: ("ltm_monitor", obj.partition, obj.data.get("name")), "LTM monitor")

    supported_profile_types = {"tcp", "udp", "fastl4", "http", "http2", "oneconnect"}
    active_profile_names = set()
    for obj in tls_client_ssl_profiles + tls_server_ssl_profiles:
        if obj.effective_state != "absent" and obj.data.get("name"):
            active_profile_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    for obj in profiles:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state == "absent":
            continue
        profile_type = str(obj.data.get("type"))
        if profile_type not in supported_profile_types:
            validator.error(obj.relpath, f"LTM profile `{obj.data.get('name')}` type `{profile_type}` is unsupported; use one of {sorted(supported_profile_types)}")
            continue
        active_profile_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    validator.check_duplicates(profiles, lambda obj: ("ltm_profile", obj.partition, obj.data.get("name")), "LTM profile")

    active_pool_names = set()
    canonical_pool_names = set()
    for obj in pools:
        validator.require_fields(obj, ["name"])
        if obj.data.get("name") not in (None, ""):
            canonical_pool_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
        if obj.effective_state == "absent":
            continue
        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "ltm" / "pools")
        normalized_pool = normalize_ltm_pool(
            obj.data,
            settings_payload.get("ltm_pool_defaults", {}),
            settings_payload.get("ltm_member_defaults", {}),
            settings_payload.get("ltm_monitor_sets", {}),
        )
        active_pool_names.add(validator.fq_name(obj.partition, str(normalized_pool["name"])))
        monitors_list = normalized_pool.get("monitors", [])
        if monitors_list is not None and not isinstance(monitors_list, list):
            validator.error(obj.relpath, f"LTM pool `{normalized_pool.get('name')}` `monitors` must be a list")
        else:
            for monitor in monitors_list or []:
                validator.validate_monitor_reference(source=obj.relpath, reference=monitor, known_monitors=active_monitor_names, kind="LTM pool monitor")
        validator.validate_ltm_pool_members(obj.relpath, normalized_pool.get("name"), obj.partition, normalized_pool.get("members"), active_node_names)
    validator.check_duplicates(pools, lambda obj: ("ltm_pool", obj.partition, obj.data.get("name")), "LTM pool")

    return {
        "active_node_names": active_node_names,
        "active_monitor_names": active_monitor_names,
        "active_profile_names": active_profile_names,
        "active_pool_names": active_pool_names,
        "canonical_pool_names": canonical_pool_names,
    }
