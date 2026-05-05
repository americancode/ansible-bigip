from __future__ import annotations

from ...models import LoadedObject


def validate_auth_objects(validator, objects: dict[str, list]) -> None:
    auth_ldap = objects["auth_ldap"]
    auth_tacacs = objects["auth_tacacs"]
    auth_radius_servers = objects["auth_radius_servers"]
    auth_radius = objects["auth_radius"]
    auth_remote_roles = objects["auth_remote_roles"]
    active_partition_names = {"all", "Common"}

    for obj in validator.objects.get("system_partitions", []):
        if obj.effective_state != "absent" and obj.data.get("name"):
            active_partition_names.add(str(obj.data["name"]))

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

    roles_requiring_all_partitions = {"administrator", "auditor", "resource-administrator"}
    for obj in auth_remote_roles:
        validator.validate_target_selectors(obj, label=f"system remote auth role `{obj.data.get('name')}`")
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue

        validator.require_fields(obj, ["line_order", "attribute_string"])

        partition_access = obj.data.get("partition_access")
        if partition_access is not None and not isinstance(partition_access, str):
            validator.error(obj.relpath, f"system remote auth role `{obj.data.get('name')}` field `partition_access` must be a string")
        elif isinstance(partition_access, str) and partition_access not in active_partition_names:
            validator.error(
                obj.relpath,
                f"system remote auth role `{obj.data.get('name')}` references undefined partition access `{partition_access}`",
            )

        line_order = obj.data.get("line_order")
        if line_order is not None and not isinstance(line_order, int):
            validator.error(obj.relpath, f"system remote auth role `{obj.data.get('name')}` field `line_order` must be an integer")

        remote_access = obj.data.get("remote_access")
        if remote_access is not None and not isinstance(remote_access, bool):
            validator.error(obj.relpath, f"system remote auth role `{obj.data.get('name')}` field `remote_access` must be a boolean")

        assigned_role = obj.data.get("assigned_role")
        if assigned_role in roles_requiring_all_partitions and partition_access not in (None, "all"):
            validator.error(
                obj.relpath,
                f"system remote auth role `{obj.data.get('name')}` with assigned_role `{assigned_role}` must use `partition_access: all`",
            )

    validator.check_targeted_identity_collisions(
        auth_remote_roles,
        identity_func=lambda obj: ("system_auth_remote_role", obj.data.get("name")),
        label="system remote auth role",
    )
