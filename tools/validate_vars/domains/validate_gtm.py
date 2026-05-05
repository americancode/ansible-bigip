from __future__ import annotations

from .gtm.base import validate_base_objects
from .gtm.topology import validate_topology
from .gtm.wide_ips import validate_wide_ips


def validate_gtm(validator) -> None:
    objects = {
        "datacenters": validator.objects.get("gtm_datacenters", []),
        "servers": validator.objects.get("gtm_servers", []),
        "pools": validator.objects.get("gtm_pools", []),
        "wide_ips": validator.objects.get("gtm_wide_ips", []),
        "topology_regions": validator.objects.get("gtm_topology_regions", []),
        "topology_records": validator.objects.get("gtm_topology_records", []),
        "monitors": validator.objects.get("gtm_monitors", []),
        "ltm_virtual_servers": validator.objects.get("ltm_virtual_servers", []),
    }
    state = validate_base_objects(validator, objects)
    validate_wide_ips(validator, objects["wide_ips"], state)
    validate_topology(validator, objects["topology_regions"], objects["topology_records"])
