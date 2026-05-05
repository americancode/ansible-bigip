from __future__ import annotations

import re

from filter_plugins.bigip_var_filters import compile_ltm_rke2_server_intent, compile_ltm_virtual_server_intent

from ...constants import VARS_DIR


def validate_intent_and_virtuals(validator, objects: dict[str, list], state: dict[str, object]) -> None:
    rke2_server_intents = objects["rke2_server_intents"]
    virtual_servers = objects["virtual_servers"]
    network_vlans = objects["network_vlans"]

    active_node_names = state["active_node_names"]
    active_monitor_names = state["active_monitor_names"]
    active_profile_names = state["active_profile_names"]
    active_pool_names = state["active_pool_names"]
    canonical_pool_names = state["canonical_pool_names"]

    compiled_rke2_pools: list[tuple[object, dict]] = []
    compiled_rke2_virtual_servers: list[tuple[object, dict]] = []

    allowed_rke2_service_name = re.compile(r"^[A-Za-z0-9_-]+$")
    for obj in rke2_server_intents:
        validator.require_fields(obj, ["name"])
        services = obj.data.get("services")
        if not isinstance(services, list) or not services:
            validator.error(obj.relpath, f"RKE2 server intent `{obj.data.get('name')}` `services` must be a non-empty list")
            continue
        service_names_seen = set()
        for index, service in enumerate(services):
            if not isinstance(service, dict):
                validator.error(obj.relpath, f"RKE2 server intent `{obj.data.get('name')}` service entry {index} must be a mapping")
                continue
            service_name = service.get("name")
            if not isinstance(service_name, str) or not allowed_rke2_service_name.match(service_name):
                validator.error(obj.relpath, f"RKE2 server intent `{obj.data.get('name')}` service entry {index} `name` must match `[A-Za-z0-9_-]+`")
            elif service_name in service_names_seen:
                validator.error(obj.relpath, f"RKE2 server intent `{obj.data.get('name')}` has duplicate service name `{service_name}`")
            else:
                service_names_seen.add(service_name)
            pool_mode = service.get("pool_mode")
            if pool_mode not in {"inline", "reference"}:
                validator.error(obj.relpath, f"RKE2 server intent `{obj.data.get('name')}` service `{service_name}` must define `pool_mode: inline` or `pool_mode: reference`")
                continue
        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "ltm" / "intents")
        compiled_service = compile_ltm_rke2_server_intent(
            obj.data,
            settings_payload.get("ltm_rke2_server_intent_defaults", {}),
            settings_payload.get("ltm_pool_defaults", {}),
            settings_payload.get("ltm_member_defaults", {}),
            settings_payload.get("ltm_monitor_sets", {}),
        )
        for pool in compiled_service.get("pools", []) or []:
            compiled_rke2_pools.append((obj, pool))
        for virtual_server in compiled_service.get("virtual_servers", []) or []:
            compiled_rke2_virtual_servers.append((obj, virtual_server))
    validator.check_duplicates(rke2_server_intents, lambda obj: ("ltm_rke2_server_intent", obj.partition, obj.data.get("name")), "LTM RKE2 server intent")

    compiled_pool_names = set()
    for source_obj, normalized_pool in compiled_rke2_pools:
        pool_name = normalized_pool.get("name")
        if pool_name in (None, ""):
            validator.error(source_obj.relpath, f"RKE2 server intent `{source_obj.data.get('name')}` compiled an unnamed pool")
            continue
        pool_partition = str(normalized_pool.get("partition", source_obj.partition))
        fq_pool_name = validator.fq_name(pool_partition, str(pool_name))
        if fq_pool_name in canonical_pool_names or fq_pool_name in compiled_pool_names:
            validator.error(source_obj.relpath, f"RKE2 server intent `{source_obj.data.get('name')}` compiles duplicate pool `{fq_pool_name}`")
            continue
        compiled_pool_names.add(fq_pool_name)
        if normalized_pool.get("state") != "absent":
            active_pool_names.add(fq_pool_name)
            validator.validate_ltm_pool_members(source_obj.relpath, pool_name, pool_partition, normalized_pool.get("members"), active_node_names)

    active_vlan_names = {
        validator.fq_name(obj.partition, str(obj.data["name"]))
        for obj in network_vlans
        if obj.effective_state != "absent" and obj.data.get("name")
    }
    _validate_virtual_servers(validator, virtual_servers, active_pool_names, active_profile_names, active_monitor_names, active_node_names, active_vlan_names)
    _validate_compiled_virtual_servers(validator, compiled_rke2_virtual_servers, virtual_servers, active_pool_names, active_profile_names, active_vlan_names)


def _validate_virtual_servers(validator, virtual_servers, active_pool_names, active_profile_names, active_monitor_names, active_node_names, active_vlan_names) -> None:
    for obj in virtual_servers:
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue
        validator.require_fields(obj, ["destination", "destination_port", "pool"])
        profiles = obj.data.get("profiles")
        if isinstance(profiles, list):
            for profile_reference in profiles:
                validator.validate_profile_reference(source=obj.relpath, reference=profile_reference, default_partition=obj.partition, known_profiles=active_profile_names, kind="LTM virtual server profile")
        elif profiles is not None:
            validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` `profiles` must be a list")
        pool = obj.data.get("pool")
        if isinstance(pool, str):
            pool_ref = validator.normalize_pool_reference(pool, obj.partition)
            if pool_ref not in active_pool_names:
                validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` references undefined pool `{pool_ref}`")
            continue
        if not isinstance(pool, dict):
            validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` pool must be a string reference or embedded pool mapping")
            continue
        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "ltm" / "virtual_servers")
        compiled_service = compile_ltm_virtual_server_intent(
            obj.data,
            settings_payload.get("ltm_pool_defaults", {}),
            settings_payload.get("ltm_member_defaults", {}),
            settings_payload.get("ltm_monitor_sets", {}),
        )
        normalized_pool = (compiled_service.get("pools") or [None])[0]
        if normalized_pool is None or not normalized_pool.get("name"):
            validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` embedded pool must define `name`")
            continue
        pool_partition = str(normalized_pool.get("partition", obj.partition))
        active_pool_names.add(validator.fq_name(pool_partition, str(normalized_pool["name"])))
        validator.validate_ltm_pool_members(obj.relpath, normalized_pool.get("name"), pool_partition, normalized_pool.get("members"), active_node_names)
    validator.check_duplicates(virtual_servers, lambda obj: ("ltm_virtual_server", obj.partition, obj.data.get("name")), "LTM virtual server")


def _validate_compiled_virtual_servers(validator, compiled_rke2_virtual_servers, virtual_servers, active_pool_names, active_profile_names, active_vlan_names) -> None:
    canonical_virtual_server_names = {validator.fq_name(obj.partition, str(obj.data["name"])) for obj in virtual_servers if obj.data.get("name")}
    active_virtual_server_names = {validator.fq_name(obj.partition, str(obj.data["name"])) for obj in virtual_servers if obj.effective_state != "absent" and obj.data.get("name")}
    compiled_virtual_server_names = set()
    for source_obj, virtual_server in compiled_rke2_virtual_servers:
        name = virtual_server.get("name")
        if name in (None, ""):
            validator.error(source_obj.relpath, f"RKE2 server intent `{source_obj.data.get('name')}` compiled an unnamed virtual server")
            continue
        vs_partition = str(virtual_server.get("partition", source_obj.partition))
        fq_virtual_name = validator.fq_name(vs_partition, str(name))
        if fq_virtual_name in canonical_virtual_server_names or fq_virtual_name in compiled_virtual_server_names:
            validator.error(source_obj.relpath, f"RKE2 server intent `{source_obj.data.get('name')}` compiles duplicate virtual server `{fq_virtual_name}`")
            continue
        compiled_virtual_server_names.add(fq_virtual_name)
        if virtual_server.get("state") == "absent":
            continue
        if fq_virtual_name in active_virtual_server_names:
            validator.error(source_obj.relpath, f"RKE2 server intent `{source_obj.data.get('name')}` compiles duplicate virtual server `{fq_virtual_name}`")
            continue
        active_virtual_server_names.add(fq_virtual_name)
        pool_ref = validator.normalize_pool_reference(virtual_server.get("pool"), vs_partition)
        if pool_ref not in active_pool_names:
            validator.error(source_obj.relpath, f"RKE2 compiled virtual server `{name}` references undefined pool `{pool_ref}`")
