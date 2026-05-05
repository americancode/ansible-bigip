from __future__ import annotations

from filter_plugins.bigip_var_filters import compile_ltm_virtual_server_intent

from ...constants import VARS_DIR


def validate_intent_and_virtuals(validator, objects: dict[str, list], state: dict[str, object]) -> None:
    inline_virtual_server_intents = objects["inline_virtual_server_intents"]
    virtual_servers = objects["virtual_servers"]
    network_vlans = objects["network_vlans"]

    active_node_names = state["active_node_names"]
    active_monitor_names = state["active_monitor_names"]
    active_profile_names = state["active_profile_names"]
    active_pool_names = state["active_pool_names"]
    canonical_pool_names = state["canonical_pool_names"]

    compiled_inline_pools: list[tuple[object, dict]] = []
    compiled_inline_virtual_servers: list[tuple[object, dict]] = []

    for obj in inline_virtual_server_intents:
        validator.require_fields(obj, ["name"])
        pool_mode = obj.data.get("pool_mode", "inline")
        if pool_mode not in {"inline", "reference"}:
            validator.error(
                obj.relpath,
                f"LTM inline virtual-server intent `{obj.data.get('name')}` must define `pool_mode: inline` or `pool_mode: reference`",
            )
            continue
        if pool_mode == "reference" and obj.data.get("pool_ref") in (None, "") and obj.data.get("pool") in (None, ""):
            validator.error(
                obj.relpath,
                f"LTM inline virtual-server intent `{obj.data.get('name')}` with `pool_mode: reference` must define `pool_ref`",
            )
            continue
        if pool_mode == "inline" and not isinstance(obj.data.get("pool"), dict):
            validator.error(
                obj.relpath,
                f"LTM inline virtual-server intent `{obj.data.get('name')}` with `pool_mode: inline` must define embedded `pool` mapping",
            )
            continue
        if obj.effective_state != "absent":
            validator.require_fields(obj, ["destination", "destination_port"])
        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "ltm" / "intents")
        compiled_service = compile_ltm_virtual_server_intent(
            obj.data,
            settings_payload.get("ltm_pool_defaults", {}),
            settings_payload.get("ltm_member_defaults", {}),
            settings_payload.get("ltm_monitor_sets", {}),
        )
        compiled_virtual_server = compiled_service.get("virtual_server")
        compiled_pool = (compiled_service.get("pools") or [None])[0]
        compiled_inline_virtual_servers.append((obj, compiled_virtual_server))
        if pool_mode == "inline":
            if not isinstance(compiled_pool, dict) or not compiled_pool.get("name"):
                validator.error(obj.relpath, f"LTM inline virtual-server intent `{obj.data.get('name')}` pool must define embedded `pool.name`")
                continue
            compiled_inline_pools.append((obj, compiled_pool))
    validator.check_duplicates(
        inline_virtual_server_intents,
        lambda obj: ("ltm_inline_virtual_server_intent", obj.partition, obj.data.get("name")),
        "LTM inline virtual-server intent",
    )

    compiled_pool_names = set()
    for source_obj, normalized_pool in compiled_inline_pools:
        pool_name = normalized_pool.get("name")
        pool_partition = str(normalized_pool.get("partition", source_obj.partition))
        fq_pool_name = validator.fq_name(pool_partition, str(pool_name))
        if fq_pool_name in canonical_pool_names or fq_pool_name in compiled_pool_names:
            validator.error(
                source_obj.relpath,
                f"LTM inline virtual-server intent `{source_obj.data.get('name')}` compiles duplicate pool `{fq_pool_name}`",
            )
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
    _validate_virtual_servers(validator, virtual_servers, active_pool_names, active_profile_names, active_vlan_names)
    _validate_compiled_inline_virtual_servers(validator, compiled_inline_virtual_servers, virtual_servers, active_pool_names, active_profile_names, active_vlan_names)


def _validate_virtual_servers(validator, virtual_servers, active_pool_names, active_profile_names, active_vlan_names) -> None:
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
        if not isinstance(pool, str):
            validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` pool must be a string reference")
            continue
        pool_ref = validator.normalize_pool_reference(pool, obj.partition)
        if pool_ref not in active_pool_names:
            validator.error(obj.relpath, f"virtual server `{obj.data.get('name')}` references undefined pool `{pool_ref}`")
    validator.check_duplicates(virtual_servers, lambda obj: ("ltm_virtual_server", obj.partition, obj.data.get("name")), "LTM virtual server")


def _validate_compiled_inline_virtual_servers(
    validator,
    compiled_inline_virtual_servers,
    virtual_servers,
    active_pool_names,
    active_profile_names,
    active_vlan_names,
) -> None:
    canonical_virtual_server_names = {validator.fq_name(obj.partition, str(obj.data["name"])) for obj in virtual_servers if obj.data.get("name")}
    active_virtual_server_names = {validator.fq_name(obj.partition, str(obj.data["name"])) for obj in virtual_servers if obj.effective_state != "absent" and obj.data.get("name")}
    compiled_virtual_server_names = set()
    for source_obj, virtual_server in compiled_inline_virtual_servers:
        name = virtual_server.get("name")
        if name in (None, ""):
            validator.error(source_obj.relpath, f"LTM inline virtual-server intent `{source_obj.data.get('name')}` compiled an unnamed virtual server")
            continue
        vs_partition = str(virtual_server.get("partition", source_obj.partition))
        fq_virtual_name = validator.fq_name(vs_partition, str(name))
        if fq_virtual_name in canonical_virtual_server_names or fq_virtual_name in compiled_virtual_server_names:
            validator.error(source_obj.relpath, f"LTM inline virtual-server intent `{source_obj.data.get('name')}` compiles duplicate virtual server `{fq_virtual_name}`")
            continue
        compiled_virtual_server_names.add(fq_virtual_name)
        if virtual_server.get("state") == "absent":
            continue
        if fq_virtual_name in active_virtual_server_names:
            validator.error(source_obj.relpath, f"LTM inline virtual-server intent `{source_obj.data.get('name')}` compiles duplicate virtual server `{fq_virtual_name}`")
            continue
        active_virtual_server_names.add(fq_virtual_name)
        pool_ref = validator.normalize_pool_reference(virtual_server.get("pool"), vs_partition)
        if pool_ref not in active_pool_names:
            validator.error(source_obj.relpath, f"LTM inline compiled virtual server `{name}` references undefined pool `{pool_ref}`")

