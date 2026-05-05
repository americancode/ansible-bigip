from __future__ import annotations


def validate_misc_objects(validator, objects: dict[str, list]) -> None:
    persistence_profiles = objects["persistence_profiles"]
    irules = objects["irules"]
    data_groups = objects["data_groups"]
    policies = objects["policies"]

    supported_persistence_types = {"cookie", "source_addr", "universal"}
    for obj in persistence_profiles:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state == "absent":
            continue
        ptype = str(obj.data.get("type"))
        if ptype not in supported_persistence_types:
            validator.error(obj.relpath, f"LTM persistence profile `{obj.data.get('name')}` type `{ptype}` is unsupported; use one of {sorted(supported_persistence_types)}")
    validator.check_duplicates(
        persistence_profiles,
        lambda obj: ("ltm_persistence_profile", obj.partition, obj.data.get("name")),
        "LTM persistence profile",
    )

    for obj in irules:
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent" and not obj.data.get("rule"):
            validator.error(obj.relpath, f"LTM iRule `{obj.data.get('name')}` must define `rule`")
    validator.check_duplicates(irules, lambda obj: ("ltm_irule", obj.partition, obj.data.get("name")), "LTM iRule")

    supported_data_group_types = {"string", "ip", "integer"}
    for obj in data_groups:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state == "absent":
            continue
        dgtype = str(obj.data.get("type"))
        if dgtype not in supported_data_group_types:
            validator.error(obj.relpath, f"LTM data group `{obj.data.get('name')}` type `{dgtype}` is unsupported; use one of {sorted(supported_data_group_types)}")
    validator.check_duplicates(data_groups, lambda obj: ("ltm_data_group", obj.partition, obj.data.get("name")), "LTM data group")

    for obj in policies:
        validator.require_fields(obj, ["name"])
    validator.check_duplicates(policies, lambda obj: ("ltm_policy", obj.partition, obj.data.get("name")), "LTM policy")
