from __future__ import annotations

from filter_plugins.bigip_var_filters import normalize_gtm_pool

from ...constants import VARS_DIR


def validate_base_objects(validator, objects: dict[str, list]) -> dict[str, set[str] | dict[str, dict[str, object]]]:
    datacenters = objects["datacenters"]
    monitors = objects["monitors"]
    servers = objects["servers"]
    pools = objects["pools"]
    ltm_virtual_servers = objects["ltm_virtual_servers"]

    active_datacenter_names = set()
    for obj in datacenters:
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent":
            active_datacenter_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

    validator.check_duplicates(datacenters, lambda obj: ("gtm_datacenter", obj.partition, obj.data.get("name")), "GTM datacenter")
    canonical_datacenter_names = {
        validator.fq_name(obj.partition, str(obj.data["name"]))
        for obj in datacenters
        if obj.data.get("name")
    }

    active_monitor_names = set()
    for obj in monitors:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state != "absent":
            active_monitor_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

    validator.check_duplicates(monitors, lambda obj: ("gtm_monitor", obj.partition, obj.data.get("name")), "GTM monitor")

    active_server_names = set()
    for obj in servers:
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent":
            validator.require_fields(obj, ["datacenter"])
            if not obj.data.get("address") and not obj.data.get("devices"):
                validator.error(obj.relpath, f"GTM server `{obj.data.get('name')}` must define `address` or `devices`")
            fq_datacenter = validator.fq_name(obj.partition, str(obj.data["datacenter"]))
            if fq_datacenter not in active_datacenter_names:
                validator.error(obj.relpath, f"GTM server `{obj.data.get('name')}` references undefined datacenter `{fq_datacenter}`")
            active_server_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

    validator.check_duplicates(servers, lambda obj: ("gtm_server", obj.partition, obj.data.get("name")), "GTM server")
    canonical_server_names = {
        validator.fq_name(obj.partition, str(obj.data["name"]))
        for obj in servers
        if obj.data.get("name")
    }

    active_pool_names = set()
    canonical_pool_names = set()
    active_ltm_virtual_servers = validator.build_ltm_virtual_server_lookup(ltm_virtual_servers)
    for obj in pools:
        validator.require_fields(obj, ["name"])
        if obj.data.get("name") not in (None, ""):
            canonical_pool_names.add(
                validator.fq_gtm_pool_name(
                    obj.partition,
                    str(obj.data.get("record_type", "a")),
                    str(obj.data["name"]),
                )
            )
        if obj.effective_state == "absent":
            continue

        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "gtm" / "pools")
        normalized_pool = normalize_gtm_pool(
            obj.data,
            settings_payload.get("gtm_pool_defaults", {}),
            settings_payload.get("gtm_member_defaults", {}),
            settings_payload.get("gtm_monitor_sets", {}),
            active_ltm_virtual_servers,
        )
        record_type = str(normalized_pool.get("record_type", "a"))
        active_pool_names.add(validator.fq_gtm_pool_name(obj.partition, record_type, str(normalized_pool["name"])))
        for monitor in normalized_pool.get("monitors", normalized_pool.get("default_monitors", [])) or []:
            validator.validate_monitor_reference(
                source=obj.relpath,
                reference=monitor,
                known_monitors=active_monitor_names,
                kind="GTM pool monitor",
            )
        validator.validate_gtm_pool_members(
            source=obj.relpath,
            pool_name=normalized_pool.get("name"),
            pool_partition=obj.partition,
            members=normalized_pool.get("members"),
            active_server_names=active_server_names,
            active_monitor_names=active_monitor_names,
            active_ltm_virtual_servers=active_ltm_virtual_servers,
        )

    validator.check_duplicates(
        pools,
        lambda obj: ("gtm_pool", obj.partition, obj.data.get("name"), obj.data.get("record_type", "a")),
        "GTM pool",
    )

    return {
        "active_datacenter_names": active_datacenter_names,
        "canonical_datacenter_names": canonical_datacenter_names,
        "active_monitor_names": active_monitor_names,
        "active_server_names": active_server_names,
        "canonical_server_names": canonical_server_names,
        "active_pool_names": active_pool_names,
        "canonical_pool_names": canonical_pool_names,
        "active_ltm_virtual_servers": active_ltm_virtual_servers,
    }
