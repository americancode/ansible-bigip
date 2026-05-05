from __future__ import annotations

from filter_plugins.bigip_var_filters import compile_gtm_wide_ip_intent

from ...constants import VARS_DIR


def validate_wide_ips(validator, wide_ips: list, state: dict[str, object]) -> None:
    compiled_gtm_datacenters: list[tuple[object, dict]] = []
    compiled_gtm_servers: list[tuple[object, dict]] = []
    compiled_gtm_pools: list[tuple[object, dict]] = []
    compiled_gtm_wide_ips: list[tuple[object, dict]] = []

    active_ltm_virtual_servers = state["active_ltm_virtual_servers"]
    for obj in wide_ips:
        validator.require_fields(obj, ["name"])
        wide_ip_pools = obj.data.get("pools")
        if wide_ip_pools is None or not isinstance(wide_ip_pools, list) or not wide_ip_pools:
            validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` must define a non-empty `pools` list")
            continue
        for pool_index, pool in enumerate(wide_ip_pools):
            if isinstance(pool, str):
                continue
            if not isinstance(pool, dict):
                validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` pool {pool_index} must be a string or mapping")
                continue
            if "name" not in pool:
                validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` pool {pool_index} must define `name`")
                continue
            if validator.is_inline_gtm_pool(pool):
                members = pool.get("members")
                if not isinstance(members, list) or not members:
                    validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline pool `{pool.get('name')}` must define a non-empty `members` list")
                    continue
                for member_index, member in enumerate(members):
                    if not isinstance(member, dict):
                        validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline pool `{pool.get('name')}` member {member_index} must be a mapping")
                        continue
                    server_mode = member.get("server_mode")
                    if server_mode not in {"inline", "reference"}:
                        validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline pool `{pool.get('name')}` member {member_index} must define `server_mode: inline` or `server_mode: reference`")
                        continue
                    if server_mode == "reference":
                        server_reference = member.get("server")
                        if not isinstance(server_reference, str) or not server_reference:
                            validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline pool `{pool.get('name')}` member {member_index} must define string `server` when `server_mode` is `reference`")
                        continue
                    server_payload = member.get("server")
                    if not isinstance(server_payload, dict):
                        validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline pool `{pool.get('name')}` member {member_index} must define mapping `server` when `server_mode` is `inline`")
                        continue
                    validator.require_fields(server_payload, ["name"], obj.relpath, f"GTM inline server for Wide IP `{obj.data.get('name')}` member {member_index}")
                    datacenter_mode = server_payload.get("datacenter_mode")
                    if datacenter_mode not in {"inline", "reference"}:
                        validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` inline server `{server_payload.get('name')}` must define `datacenter_mode: inline` or `datacenter_mode: reference`")
                        continue
                    if datacenter_mode == "reference":
                        if server_payload.get("datacenter_ref") in (None, ""):
                            validator.error(obj.relpath, f"GTM inline server `{server_payload.get('name')}` must define `datacenter_ref` when `datacenter_mode` is `reference`")
                        if server_payload.get("datacenter") is not None:
                            validator.error(obj.relpath, f"GTM inline server `{server_payload.get('name')}` cannot define inline `datacenter` when `datacenter_mode` is `reference`")
                        continue
                    datacenter_payload = server_payload.get("datacenter")
                    if not isinstance(datacenter_payload, dict):
                        validator.error(obj.relpath, f"GTM inline server `{server_payload.get('name')}` must define mapping `datacenter` when `datacenter_mode` is `inline`")
                        continue
                    validator.require_fields(datacenter_payload, ["name"], obj.relpath, f"GTM inline datacenter for server `{server_payload.get('name')}`")
                continue

            unsupported = sorted(set(pool) - {"name", "ratio"})
            if unsupported:
                validator.error(obj.relpath, f"GTM Wide IP `{obj.data.get('name')}` pool reference `{pool.get('name')}` contains unsupported keys: {', '.join(unsupported)}")

        settings_payload = validator.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "gtm" / "intents")
        compiled_service = compile_gtm_wide_ip_intent(
            obj.data,
            settings_payload.get("gtm_pool_defaults", {}),
            settings_payload.get("gtm_member_defaults", {}),
            settings_payload.get("gtm_monitor_sets", {}),
            active_ltm_virtual_servers,
        )
        compiled_gtm_wide_ips.append((obj, compiled_service.get("wide_ip", {})))
        for datacenter in compiled_service.get("datacenters", []) or []:
            compiled_gtm_datacenters.append((obj, datacenter))
        for server in compiled_service.get("servers", []) or []:
            compiled_gtm_servers.append((obj, server))
        for normalized_pool in compiled_service.get("pools", []) or []:
            compiled_gtm_pools.append((obj, normalized_pool))

    validator.check_duplicates(
        wide_ips,
        lambda obj: ("gtm_wide_ip", obj.partition, obj.data.get("name"), obj.data.get("record_type", "a")),
        "GTM Wide IP",
    )

    _validate_compiled_intents(validator, compiled_gtm_datacenters, compiled_gtm_servers, compiled_gtm_pools, compiled_gtm_wide_ips, state)


def _validate_compiled_intents(validator, compiled_gtm_datacenters, compiled_gtm_servers, compiled_gtm_pools, compiled_gtm_wide_ips, state) -> None:
    compiled_datacenter_names = set()
    for source_obj, datacenter in compiled_gtm_datacenters:
        datacenter_name = datacenter.get("name")
        if datacenter_name in (None, ""):
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiled an unnamed datacenter")
            continue
        datacenter_partition = str(datacenter.get("partition", source_obj.partition))
        fq_datacenter_name = validator.fq_name(datacenter_partition, str(datacenter_name))
        if fq_datacenter_name in state["canonical_datacenter_names"]:
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiles datacenter `{fq_datacenter_name}` that already exists in canonical `gtm_datacenters` trees")
            continue
        if fq_datacenter_name in compiled_datacenter_names:
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiles duplicate datacenter `{fq_datacenter_name}`")
            continue
        compiled_datacenter_names.add(fq_datacenter_name)
        if datacenter.get("state") != "absent":
            state["active_datacenter_names"].add(fq_datacenter_name)

    compiled_server_names = set()
    for source_obj, server in compiled_gtm_servers:
        server_name = server.get("name")
        if server_name in (None, ""):
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiled an unnamed server")
            continue
        server_partition = str(server.get("partition", source_obj.partition))
        fq_server_name = validator.fq_name(server_partition, str(server_name))
        if fq_server_name in state["canonical_server_names"] or fq_server_name in compiled_server_names:
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiles duplicate server `{fq_server_name}`")
            continue
        compiled_server_names.add(fq_server_name)
        if server.get("state") != "absent":
            validator.require_fields(server, ["datacenter"], source_obj.relpath, f"GTM inline server `{server_name}`")
            fq_datacenter = validator.fq_name(server_partition, str(server.get("datacenter")))
            if fq_datacenter not in state["active_datacenter_names"]:
                validator.error(source_obj.relpath, f"GTM inline server `{server_name}` references undefined datacenter `{fq_datacenter}`")
            if not server.get("address") and not server.get("devices"):
                validator.error(source_obj.relpath, f"GTM inline server `{server_name}` must define `address` or `devices`")
            state["active_server_names"].add(fq_server_name)

    compiled_pool_names = set()
    for source_obj, normalized_pool in compiled_gtm_pools:
        pool_name = normalized_pool.get("name")
        if pool_name in (None, ""):
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiled an unnamed pool")
            continue
        pool_partition = str(normalized_pool.get("partition", source_obj.partition))
        record_type = str(normalized_pool.get("record_type", "a"))
        fq_pool_name = validator.fq_gtm_pool_name(pool_partition, record_type, str(pool_name))
        if fq_pool_name in state["canonical_pool_names"] or fq_pool_name in compiled_pool_names:
            validator.error(source_obj.relpath, f"GTM Wide IP `{source_obj.data.get('name')}` compiles duplicate pool `{fq_pool_name}`")
            continue
        compiled_pool_names.add(fq_pool_name)
        if normalized_pool.get("state") == "absent":
            continue
        state["active_pool_names"].add(fq_pool_name)
        for monitor in normalized_pool.get("monitors", normalized_pool.get("default_monitors", [])) or []:
            validator.validate_monitor_reference(source=source_obj.relpath, reference=monitor, known_monitors=state["active_monitor_names"], kind="GTM pool monitor")
        validator.validate_gtm_pool_members(
            source=source_obj.relpath,
            pool_name=normalized_pool.get("name"),
            pool_partition=pool_partition,
            members=normalized_pool.get("members"),
            active_server_names=state["active_server_names"],
            active_monitor_names=state["active_monitor_names"],
            active_ltm_virtual_servers=state["active_ltm_virtual_servers"],
        )

    for source_obj, compiled_wide_ip in compiled_gtm_wide_ips:
        if compiled_wide_ip.get("state") == "absent":
            continue
        record_type = str(compiled_wide_ip.get("record_type", "a"))
        for pool in compiled_wide_ip.get("pools", []) or []:
            if not isinstance(pool, dict) or pool.get("name") in (None, ""):
                continue
            pool_partition = str(pool.get("partition", source_obj.partition))
            pool_ref = validator.fq_gtm_pool_name(pool_partition, record_type, str(pool["name"]))
            if pool_ref not in state["active_pool_names"]:
                validator.error(source_obj.relpath, f"GTM Wide IP `{compiled_wide_ip.get('name')}` references undefined pool `{pool_ref}`")
