from __future__ import annotations


def validate_topology(validator, topology_regions: list, topology_records: list) -> None:
    active_region_names = set()
    for obj in topology_regions:
        validator.require_fields(obj, ["name"])
        if obj.effective_state != "absent":
            active_region_names.add(str(obj.data["name"]))
            region_members = obj.data.get("region_members")
            if region_members is not None:
                if not isinstance(region_members, list):
                    validator.error(obj.relpath, f"topology region `{obj.data.get('name')}` `region_members` must be a list")
                else:
                    validator.validate_topology_members(region_members, obj.relpath, f"topology region `{obj.data.get('name')}`")

    validator.check_duplicates(
        topology_regions,
        lambda obj: ("gtm_topology_region", obj.data.get("name")),
        "GTM topology region",
    )

    for obj in topology_records:
        if obj.effective_state == "absent":
            continue
        validator.require_fields(obj, ["source", "destination"])
        source_members = obj.data.get("source")
        destination_members = obj.data.get("destination")
        if source_members is not None:
            if not isinstance(source_members, list) or not source_members:
                validator.error(obj.relpath, f"topology record `{validator._topology_record_id(obj)}` `source` must be a non-empty list")
            else:
                validator.validate_topology_members(source_members, obj.relpath, f"topology record `{validator._topology_record_id(obj)}` source")
        if destination_members is not None:
            if not isinstance(destination_members, list) or not destination_members:
                validator.error(obj.relpath, f"topology record `{validator._topology_record_id(obj)}` `destination` must be a non-empty list")
            else:
                validator.validate_topology_members(destination_members, obj.relpath, f"topology record `{validator._topology_record_id(obj)}` destination")
        for member in (source_members or []) + (destination_members or []):
            if isinstance(member, dict):
                region_ref = member.get("region")
                if region_ref is not None and str(region_ref) not in active_region_names:
                    validator.error(obj.relpath, f"topology record `{validator._topology_record_id(obj)}` references undefined region `{region_ref}`")
        weight = obj.data.get("weight")
        if weight is not None and (not isinstance(weight, int) or weight < 0):
            validator.error(obj.relpath, f"topology record `{validator._topology_record_id(obj)}` `weight` must be a non-negative integer")

    validator.check_duplicates(
        topology_records,
        lambda obj: ("gtm_topology_record", validator._topology_record_id(obj)),
        "GTM topology record",
    )
