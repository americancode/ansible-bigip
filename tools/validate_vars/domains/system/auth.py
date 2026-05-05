from __future__ import annotations

from ...models import LoadedObject


def validate_auth_objects(validator, objects: dict[str, list]) -> None:
    auth_ldap = objects["auth_ldap"]
    auth_tacacs = objects["auth_tacacs"]
    auth_radius_servers = objects["auth_radius_servers"]
    auth_radius = objects["auth_radius"]

    active_radius_server_names = set()
    for obj in auth_radius_servers:
        validator.validate_target_selectors(obj, label=f"system RADIUS server `{obj.data.get('name')}`")
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue
        validator.require_fields(obj, ["ip"])
        active_radius_server_names.add(validator.fq_name(str(obj.data.get("partition", "Common")), str(obj.data["name"])))
    validator.check_targeted_identity_collisions(
        auth_radius_servers,
        identity_func=lambda obj: ("system_radius_server", obj.data.get("partition", "Common"), obj.data.get("name")),
        label="system RADIUS server",
    )

    active_system_auth_sources = []
    for obj in auth_ldap:
        target_hosts, target_groups = validator.validate_target_selectors(obj, label=f"system LDAP auth `{obj.data.get('name')}`")
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue
        if obj.data.get("use_for_auth") is True:
            active_system_auth_sources.append(("ldap", obj, target_hosts, target_groups))
    validator.check_targeted_identity_collisions(auth_ldap, identity_func=lambda obj: ("system_auth_ldap", obj.data.get("name")), label="system LDAP auth")

    for obj in auth_tacacs:
        target_hosts, target_groups = validator.validate_target_selectors(obj, label="system TACACS auth object")
        if obj.effective_state == "absent":
            continue
        use_for_auth = obj.data.get("use_for_auth")
        if use_for_auth is True:
            active_system_auth_sources.append(("tacacs", obj, target_hosts, target_groups))
    validator.check_targeted_identity_collisions(auth_tacacs, identity_func=lambda obj: ("system_auth_tacacs",), label="system TACACS auth object")

    for obj in auth_radius:
        target_hosts, target_groups = validator.validate_target_selectors(obj, label="system RADIUS auth object")
        if obj.effective_state == "absent":
            continue
        servers = obj.data.get("servers")
        if isinstance(servers, list):
            for server in servers:
                if isinstance(server, str):
                    normalized_server = server if server.startswith("/") else validator.fq_name("Common", server)
                    if normalized_server not in active_radius_server_names:
                        validator.error(obj.relpath, f"system RADIUS auth references undefined RADIUS server `{normalized_server}`")
        if obj.data.get("use_for_auth") is True:
            active_system_auth_sources.append(("radius", obj, target_hosts, target_groups))
    validator.check_targeted_identity_collisions(auth_radius, identity_func=lambda obj: ("system_auth_radius",), label="system RADIUS auth object")

    active_auth_targets: dict[str, tuple[str, LoadedObject]] = {}
    grouped_auth_sources = [entry for entry in active_system_auth_sources if entry[2] or entry[3]]
    if len(grouped_auth_sources) > 1 and any(target_groups for _, _, _, target_groups in grouped_auth_sources):
        conflicting_obj = grouped_auth_sources[1][1]
        validator.error(conflicting_obj.relpath, "multiple management-plane auth sources with `use_for_auth: true` cannot use `target_groups`; use disjoint `target_hosts` instead")
    else:
        for auth_type, obj, target_hosts, _ in active_system_auth_sources:
            for host in target_hosts:
                if host in active_auth_targets:
                    existing_type, existing_obj = active_auth_targets[host]
                    validator.error(obj.relpath, f"only one management-plane auth source can set `use_for_auth: true` for target host `{host}`; conflicts with {existing_type} in {existing_obj.relpath}")
                else:
                    active_auth_targets[host] = (auth_type, obj)
