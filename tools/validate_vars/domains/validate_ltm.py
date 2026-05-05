from __future__ import annotations

from .ltm.base import validate_base_objects
from .ltm.intents import validate_intent_and_virtuals
from .ltm.misc import validate_misc_objects


def validate_ltm(validator) -> None:
    objects = {
        "nodes": validator.objects.get("ltm_nodes", []),
        "profiles": validator.objects.get("ltm_profiles", []),
        "pools": validator.objects.get("ltm_pools", []),
        "monitors": validator.objects.get("ltm_monitors", []),
        "virtual_servers": validator.objects.get("ltm_virtual_servers", []),
        "rke2_server_intents": validator.objects.get("ltm_rke2_server_intents", []),
        "tls_client_ssl_profiles": validator.objects.get("tls_client_ssl_profiles", []),
        "tls_server_ssl_profiles": validator.objects.get("tls_server_ssl_profiles", []),
        "network_vlans": validator.objects.get("network_vlans", []),
        "persistence_profiles": validator.objects.get("ltm_persistence_profiles", []),
        "irules": validator.objects.get("ltm_irules", []),
        "data_groups": validator.objects.get("ltm_data_groups", []),
        "policies": validator.objects.get("ltm_policies", []),
    }
    state = validate_base_objects(validator, objects)
    validate_intent_and_virtuals(validator, objects, state)
    validate_misc_objects(validator, objects)
