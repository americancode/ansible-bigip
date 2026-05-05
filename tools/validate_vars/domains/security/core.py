from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

from filter_plugins.bigip_var_filters import (
    compile_gtm_wide_ip_intent,
    compile_ltm_rke2_server_intent,
    compile_ltm_virtual_server_intent,
    normalize_gtm_pool,
    normalize_ltm_pool,
)

from ...constants import VARS_DIR
from ...models import LoadedObject

def validate_core(validator) -> None:
        address_lists = validator.objects.get("afm_address_lists", [])
        port_lists = validator.objects.get("afm_port_lists", [])
        rules = validator.objects.get("afm_rules", [])
        policies = validator.objects.get("afm_policies", [])

        active_address_list_names = set()
        for obj in address_lists:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                active_address_list_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
                addresses = obj.data.get("addresses")
                if addresses is not None and not isinstance(addresses, list):
                    validator.error(obj.relpath, f"AFM address list `{obj.data.get('name')}` `addresses` must be a list")
                address_ranges = obj.data.get("address_ranges")
                if address_ranges is not None and not isinstance(address_ranges, list):
                    validator.error(obj.relpath, f"AFM address list `{obj.data.get('name')}` `address_ranges` must be a list")
                address_lists_ref = obj.data.get("address_lists")
                if address_lists_ref is not None and not isinstance(address_lists_ref, list):
                    validator.error(obj.relpath, f"AFM address list `{obj.data.get('name')}` `address_lists` must be a list")
                geo_locations = obj.data.get("geo_locations")
                if geo_locations is not None and not isinstance(geo_locations, list):
                    validator.error(obj.relpath, f"AFM address list `{obj.data.get('name')}` `geo_locations` must be a list")
                fqdns = obj.data.get("fqdns")
                if fqdns is not None and not isinstance(fqdns, list):
                    validator.error(obj.relpath, f"AFM address list `{obj.data.get('name')}` `fqdns` must be a list")

        validator.check_duplicates(
            address_lists,
            lambda obj: ("afm_address_list", obj.partition, obj.data.get("name")),
            "AFM address list",
        )

        active_port_list_names = set()
        for obj in port_lists:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                active_port_list_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
                ports = obj.data.get("ports")
                if ports is not None and not isinstance(ports, list):
                    validator.error(obj.relpath, f"AFM port list `{obj.data.get('name')}` `ports` must be a list")
                port_ranges = obj.data.get("port_ranges")
                if port_ranges is not None and not isinstance(port_ranges, list):
                    validator.error(obj.relpath, f"AFM port list `{obj.data.get('name')}` `port_ranges` must be a list")
                port_lists_ref = obj.data.get("port_lists")
                if port_lists_ref is not None and not isinstance(port_lists_ref, list):
                    validator.error(obj.relpath, f"AFM port list `{obj.data.get('name')}` `port_lists` must be a list")

        validator.check_duplicates(
            port_lists,
            lambda obj: ("afm_port_list", obj.partition, obj.data.get("name")),
            "AFM port list",
        )

        active_rule_names = set()
        for obj in rules:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                active_rule_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
                action = obj.data.get("action")
                if action is not None and action not in ("accept", "drop", "reject", "continue"):
                    validator.error(obj.relpath, f"AFM rule `{obj.data.get('name')}` `action` must be one of accept, drop, reject, continue")
                source = obj.data.get("source")
                if source is not None and not isinstance(source, dict):
                    validator.error(obj.relpath, f"AFM rule `{obj.data.get('name')}` `source` must be a mapping")
                elif source is not None:
                    validator.validate_afm_rule_endpoint(source, obj.relpath, obj.data.get("name"), "source", obj.partition, active_address_list_names)
                destination = obj.data.get("destination")
                if destination is not None and not isinstance(destination, dict):
                    validator.error(obj.relpath, f"AFM rule `{obj.data.get('name')}` `destination` must be a mapping")
                elif destination is not None:
                    validator.validate_afm_rule_endpoint(destination, obj.relpath, obj.data.get("name"), "destination", obj.partition, active_address_list_names)

        validator.check_duplicates(
            rules,
            lambda obj: ("afm_rule", obj.partition, obj.data.get("name")),
            "AFM rule",
        )

        for obj in policies:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                rules_list = obj.data.get("rules")
                if rules_list is not None:
                    if not isinstance(rules_list, list):
                        validator.error(obj.relpath, f"AFM policy `{obj.data.get('name')}` `rules` must be a list")
                    else:
                        for rule_ref in rules_list:
                            if isinstance(rule_ref, str):
                                fq_rule = rule_ref if rule_ref.startswith("/") else validator.fq_name(obj.partition, rule_ref)
                                if fq_rule not in active_rule_names:
                                    validator.error(obj.relpath, f"AFM policy `{obj.data.get('name')}` references undefined rule `{fq_rule}`")

        validator.check_duplicates(
            policies,
            lambda obj: ("afm_policy", obj.partition, obj.data.get("name")),
            "AFM policy",
        )
