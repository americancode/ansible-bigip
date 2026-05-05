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
        """Validate network domain objects: VLAns, self IPs, route domains, routes, SNATs, NATs, trunks.

        Purpose:
            Checks structural correctness and cross-object references for all
            network-level objects.

        Validates:
            - VLANS: name required; interfaces must be a list if present.
            - Route domains: name and id required; VLAN references must exist;
              parent must be a valid route domain ID; routing_protocol must be a list.
            - Self IPs: name, address, netmask, vlan required (if not absent);
              referenced VLAN must exist; route domain in address must be defined.
            - SNAT translations, SNAT pools, trunks, NATs: structure and field types.
        """
        vlans = validator.objects.get("network_vlans", [])
        self_ips = validator.objects.get("network_self_ips", [])
        route_domains = validator.objects.get("network_route_domains", [])
        routes = validator.objects.get("network_routes", [])
        snat_translations = validator.objects.get("network_snat_translations", [])
        snat_pools = validator.objects.get("network_snat_pools", [])
        trunks = validator.objects.get("network_trunks", [])
        nats = validator.objects.get("network_nats", [])

        active_vlan_names = set()

        for obj in vlans:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                active_vlan_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
                interfaces = obj.data.get("interfaces")
                if interfaces is not None and not isinstance(interfaces, list):
                    validator.error(obj.relpath, "`interfaces` must be a list")

        active_route_domain_ids = {0}

        for obj in route_domains:
            if obj.effective_state == "absent":
                continue
            route_domain_id = obj.data.get("id")
            if isinstance(route_domain_id, int):
                active_route_domain_ids.add(route_domain_id)

        for obj in route_domains:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            validator.require_fields(obj, ["id"])
            route_domain_id = obj.data.get("id")
            if route_domain_id is not None:
                if not isinstance(route_domain_id, int):
                    validator.error(obj.relpath, f"route domain `{obj.data.get('name')}` `id` must be an integer")
            vlans_list = obj.data.get("vlans")
            if vlans_list is not None and not isinstance(vlans_list, list):
                validator.error(obj.relpath, f"route domain `{obj.data.get('name')}` `vlans` must be a list")
            for vlan in vlans_list or []:
                validator.validate_named_or_fq_reference(
                    obj.relpath,
                    vlan,
                    obj.partition,
                    active_vlan_names,
                    "route domain VLAN",
                )
            routing_protocol = obj.data.get("routing_protocol")
            if routing_protocol is not None and not isinstance(routing_protocol, list):
                validator.error(obj.relpath, f"route domain `{obj.data.get('name')}` `routing_protocol` must be a list")
            parent = obj.data.get("parent")
            if parent not in (None, ""):
                parent_id = validator.normalize_route_domain_id(parent)
                if parent_id is None:
                    validator.error(obj.relpath, f"route domain `{obj.data.get('name')}` `parent` must be an integer route domain ID")

        for obj in self_ips:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                validator.require_fields(obj, ["address", "netmask", "vlan"])
                validator.validate_named_or_fq_reference(
                    obj.relpath,
                    obj.data.get("vlan"),
                    obj.partition,
                    active_vlan_names,
                    "self IP VLAN",
                )
                route_domain_id = validator.extract_route_domain_id(obj.data.get("address"))
                if route_domain_id is not None and route_domain_id not in active_route_domain_ids:
                    validator.error(obj.relpath, f"self IP `{obj.data.get('name')}` references undefined route domain `{route_domain_id}` in `address`")

        active_snat_translation_names = set()

        for obj in snat_translations:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                validator.require_fields(obj, ["address"])
                active_snat_translation_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

        for obj in snat_pools:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            members = obj.data.get("members")
            if not isinstance(members, list) or not members:
                validator.error(obj.relpath, f"SNAT pool `{obj.data.get('name')}` must define a non-empty `members` list")
                continue
            for member in members:
                if not isinstance(member, str):
                    validator.error(obj.relpath, f"SNAT pool `{obj.data.get('name')}` member references must be strings")
                    continue
                if validator.is_ip_address(member):
                    continue
                validator.validate_named_or_fq_reference(
                    obj.relpath,
                    member,
                    obj.partition,
                    active_snat_translation_names,
                    "SNAT pool member",
                )

        for obj in routes:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            validator.require_fields(obj, ["destination", "netmask"])
            if not any(obj.data.get(field) not in (None, "") for field in ("gateway_address", "pool")) and not bool(obj.data.get("reject")):
                validator.error(obj.relpath, f"static route `{obj.data.get('name')}` must define `gateway_address`, `pool`, or `reject: true`")
            if obj.data.get("vlan") is not None:
                validator.validate_named_or_fq_reference(
                    obj.relpath,
                    obj.data.get("vlan"),
                    obj.partition,
                    active_vlan_names,
                    "static route VLAN",
                )
            route_domain = obj.data.get("route_domain")
            if route_domain is not None:
                if not isinstance(route_domain, int):
                    validator.error(obj.relpath, f"static route `{obj.data.get('name')}` `route_domain` must be an integer")
                elif route_domain not in active_route_domain_ids:
                    validator.error(obj.relpath, f"static route `{obj.data.get('name')}` references undefined route domain `{route_domain}`")

        for obj in trunks:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            interfaces = obj.data.get("interfaces")
            if not isinstance(interfaces, list) or not interfaces:
                validator.error(obj.relpath, f"trunk `{obj.data.get('name')}` must define a non-empty `interfaces` list")
            if obj.data.get("lacp_enabled") is False and obj.data.get("lacp_mode") not in (None, ""):
                validator.error(obj.relpath, f"trunk `{obj.data.get('name')}` sets `lacp_mode` while `lacp_enabled` is false")
            if obj.data.get("lacp_enabled") is False and obj.data.get("lacp_timeout") not in (None, ""):
                validator.error(obj.relpath, f"trunk `{obj.data.get('name')}` sets `lacp_timeout` while `lacp_enabled` is false")

        for obj in nats:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            validator.require_fields(obj, ["originating_address", "translation_address"])
            nat_vlans = obj.data.get("vlans")
            if nat_vlans is not None and not isinstance(nat_vlans, list):
                validator.error(obj.relpath, f"NAT `{obj.data.get('name')}` `vlans` must be a list")
            for vlan in nat_vlans or []:
                validator.validate_named_or_fq_reference(
                    obj.relpath,
                    vlan,
                    obj.partition,
                    active_vlan_names,
                    "NAT VLAN",
                )

        validator.check_duplicates(vlans, lambda obj: ("vlan", obj.partition, obj.data.get("name")), "VLAN")
        validator.check_duplicates(route_domains, lambda obj: ("route_domain", obj.partition, obj.data.get("name")), "route domain")
        validator.check_duplicates(
            route_domains,
            lambda obj: ("route_domain_id", obj.data.get("id")),
            "route domain ID",
        )
        validator.check_duplicates(self_ips, lambda obj: ("self_ip", obj.partition, obj.data.get("name")), "self IP")
        validator.check_duplicates(routes, lambda obj: ("static_route", obj.partition, obj.data.get("name")), "static route")
        validator.check_duplicates(
            snat_translations,
            lambda obj: ("snat_translation", obj.partition, obj.data.get("name")),
            "SNAT translation",
        )
        validator.check_duplicates(snat_pools, lambda obj: ("snat_pool", obj.partition, obj.data.get("name")), "SNAT pool")
        validator.check_duplicates(trunks, lambda obj: ("trunk", obj.data.get("name")), "trunk")
        validator.check_duplicates(nats, lambda obj: ("nat", obj.partition, obj.data.get("name")), "NAT")
