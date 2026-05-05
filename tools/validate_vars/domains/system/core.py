from __future__ import annotations


def validate_core_objects(validator, objects: dict[str, list]) -> None:
    hostnames = objects["hostnames"]
    dns_settings = objects["dns_settings"]
    ntp_settings = objects["ntp_settings"]
    provisioning = objects["provisioning"]
    partitions = objects["partitions"]
    users = objects["users"]

    for obj in hostnames:
        validator.validate_target_selectors(obj, label="system hostname object", require_single_host=True)
        if obj.effective_state != "absent":
            validator.require_fields(obj, ["hostname"])
    validator.check_targeted_identity_collisions(hostnames, identity_func=lambda obj: ("system_hostname",), label="system hostname object")

    for obj in dns_settings:
        validator.validate_target_selectors(obj, label="system DNS object")
        if obj.effective_state != "absent":
            if not obj.data.get("name_servers") and not obj.data.get("search") and obj.data.get("cache") is None and obj.data.get("ip_version") is None:
                validator.error(obj.relpath, "system DNS object must define at least one of `name_servers`, `search`, `cache`, or `ip_version`")
    validator.check_targeted_identity_collisions(dns_settings, identity_func=lambda obj: ("system_dns",), label="system DNS object")

    for obj in ntp_settings:
        validator.validate_target_selectors(obj, label="system NTP object")
        if obj.effective_state != "absent" and not obj.data.get("ntp_servers") and not obj.data.get("timezone"):
            validator.error(obj.relpath, "system NTP object must define `ntp_servers` or `timezone`")
    validator.check_targeted_identity_collisions(ntp_settings, identity_func=lambda obj: ("system_ntp",), label="system NTP object")

    for obj in provisioning:
        validator.validate_target_selectors(obj, label=f"system provisioning module `{obj.data.get('module')}`")
        validator.require_fields(obj, ["module"])
        if obj.effective_state != "absent" and obj.data.get("module") != "mgmt" and not obj.data.get("level"):
            validator.error(obj.relpath, f"system provisioning module `{obj.data.get('module')}` should define `level`")
    validator.check_targeted_identity_collisions(provisioning, identity_func=lambda obj: ("system_provisioning", obj.data.get("module")), label="system provisioning module")

    for obj in partitions:
        validator.validate_target_selectors(obj, label=f"system partition `{obj.data.get('name')}`")
        validator.require_fields(obj, ["name"])
        if obj.data.get("partition") is not None:
            validator.error(obj.relpath, f"system partition `{obj.data.get('name')}` must not define `partition`; the object itself is the partition")
    validator.check_targeted_identity_collisions(partitions, identity_func=lambda obj: ("system_partition", obj.data.get("name")), label="system partition")

    for obj in users:
        validator.validate_target_selectors(obj, label=f"system user `{obj.data.get('name')}`")
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent":
            if obj.data.get("name") != "root" and not obj.data.get("partition_access"):
                validator.error(obj.relpath, f"system user `{obj.data.get('name')}` must define `partition_access`")
    validator.check_targeted_identity_collisions(users, identity_func=lambda obj: ("system_user", obj.data.get("name")), label="system user")
