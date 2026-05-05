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
        """Validate high-availability domain objects: device trust, device groups, traffic groups, HA groups, config sync.

        Purpose:
            Checks that HA objects are correctly structured and cross-referenced.

        Validates:
            - Device trusts: peer addresses and credentials.
            - Device groups: name, type, members.
            - Device group members: member references and state.
            - Traffic groups: name, auto-failback, ha-group references.
            - HA groups: name, type, members, thresholds.
            - Config sync actions: target device and state.
            - Device connectivity: management IPs (delete not supported).
        """
        trusts = validator.objects.get("ha_device_trusts", [])
        groups = validator.objects.get("ha_device_groups", [])
        members = validator.objects.get("ha_device_group_members", [])
        traffic_groups = validator.objects.get("ha_traffic_groups", [])
        device_connectivity = validator.objects.get("ha_device_connectivity", [])
        ha_groups = validator.objects.get("ha_groups", [])
        configsync_actions = validator.objects.get("ha_configsync_actions", [])

        active_group_names = set()
        active_ha_group_names = set()

        active_device_connectivity = [obj for obj in device_connectivity if obj.effective_state != "absent"]
        if len(active_device_connectivity) > 1:
            validator.error(
                active_device_connectivity[1].relpath,
                "HA device connectivity is device-local and supports only one active declaration per target BIG-IP",
            )

        for obj in device_connectivity:
            if obj.from_deletions:
                validator.error(obj.relpath, "HA device connectivity does not support deletion trees; use desired replacement values instead")
            if obj.effective_state == "absent":
                validator.error(obj.relpath, "HA device connectivity does not support `state: absent`")

            if not any(
                obj.data.get(field) is not None
                for field in (
                    "config_sync_ip",
                    "mirror_primary_address",
                    "mirror_secondary_address",
                    "unicast_failover",
                    "failover_multicast",
                    "multicast_interface",
                    "multicast_address",
                    "multicast_port",
                    "cluster_mirroring",
                )
            ):
                validator.error(obj.relpath, "HA device connectivity must define at least one managed field")

            for field in ("config_sync_ip", "mirror_primary_address", "mirror_secondary_address"):
                value = obj.data.get(field)
                if value is not None:
                    validator.validate_ip_like(obj.relpath, value, f"HA device connectivity `{field}`")

            cluster_mirroring = obj.data.get("cluster_mirroring")
            if cluster_mirroring is not None and cluster_mirroring not in ("between-clusters", "within-cluster"):
                validator.error(obj.relpath, "`cluster_mirroring` must be `between-clusters` or `within-cluster`")

            failover_multicast = obj.data.get("failover_multicast")
            if failover_multicast is not None and not isinstance(failover_multicast, bool):
                validator.error(obj.relpath, "`failover_multicast` must be a boolean")

            multicast_address = obj.data.get("multicast_address")
            if multicast_address is not None:
                validator.validate_ip_like(obj.relpath, multicast_address, "HA device connectivity `multicast_address`")

            multicast_port = obj.data.get("multicast_port")
            if multicast_port is not None:
                if not isinstance(multicast_port, int):
                    validator.error(obj.relpath, "`multicast_port` must be an integer")
                elif multicast_port < 0 or multicast_port > 65535:
                    validator.error(obj.relpath, "`multicast_port` must be between 0 and 65535")

            unicast_failover = obj.data.get("unicast_failover")
            if unicast_failover is not None:
                if not isinstance(unicast_failover, list):
                    validator.error(obj.relpath, "`unicast_failover` must be a list")
                else:
                    for idx, entry in enumerate(unicast_failover):
                        if not isinstance(entry, dict):
                            validator.error(obj.relpath, f"`unicast_failover[{idx}]` must be a mapping")
                            continue
                        if not entry.get("address"):
                            validator.error(obj.relpath, f"`unicast_failover[{idx}]` must define `address`")
                        else:
                            validator.validate_ip_like(
                                obj.relpath,
                                entry.get("address"),
                                f"HA device connectivity `unicast_failover[{idx}].address`",
                            )
                        port = entry.get("port")
                        if port is not None:
                            if not isinstance(port, int):
                                validator.error(obj.relpath, f"`unicast_failover[{idx}].port` must be an integer")
                            elif port < 0 or port > 65535:
                                validator.error(obj.relpath, f"`unicast_failover[{idx}].port` must be between 0 and 65535")

        for obj in ha_groups:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            active_ha_group_names.add(str(obj.data["name"]))

            active_bonus = obj.data.get("active_bonus")
            if active_bonus is not None:
                if not isinstance(active_bonus, int):
                    validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `active_bonus` must be an integer")
                elif active_bonus < 0:
                    validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `active_bonus` must be zero or greater")

            enable = obj.data.get("enable")
            if enable is not None and not isinstance(enable, bool):
                validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `enable` must be a boolean")

            for field, name_key in (("pools", "pool_name"), ("trunks", "trunk_name")):
                members_list = obj.data.get(field)
                if members_list is None:
                    continue
                if not isinstance(members_list, list):
                    validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}` must be a list")
                    continue
                for idx, member in enumerate(members_list):
                    if not isinstance(member, dict):
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}]` must be a mapping")
                        continue
                    if not member.get(name_key):
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}]` must define `{name_key}`")
                    if member.get("weight") is None:
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}]` must define `weight`")
                    elif not isinstance(member.get("weight"), int):
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}].weight` must be an integer")
                    attribute = member.get("attribute")
                    if attribute is not None and attribute != "percent-up-members":
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}].attribute` must be `percent-up-members`")
                    minimum_threshold = member.get("minimum_threshold")
                    if minimum_threshold is not None and not isinstance(minimum_threshold, int):
                        validator.error(obj.relpath, f"HA group `{obj.data.get('name')}` `{field}[{idx}].minimum_threshold` must be an integer")

        validator.check_duplicates(ha_groups, lambda obj: ("ha_group", obj.data.get("name")), "HA group")

        for obj in trusts:
            validator.require_fields(obj, ["peer_server"])
            if obj.data.get("type") not in (None, "peer", "subordinate"):
                validator.error(obj.relpath, f"HA device trust `{obj.data.get('peer_server')}` has unsupported `type`")

        validator.check_duplicates(
            trusts,
            lambda obj: ("ha_device_trust", obj.data.get("peer_server"), obj.data.get("peer_hostname")),
            "HA device trust",
        )

        for obj in groups:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            active_group_names.add(str(obj.data["name"]))
            if obj.data.get("type") not in (None, "sync-failover", "sync-only"):
                validator.error(obj.relpath, f"HA device group `{obj.data.get('name')}` has unsupported `type`")

        validator.check_duplicates(groups, lambda obj: ("ha_device_group", obj.data.get("name")), "HA device group")

        for obj in members:
            validator.require_fields(obj, ["device_group", "name"])
            if obj.effective_state != "absent" and str(obj.data["device_group"]) not in active_group_names:
                validator.error(obj.relpath, f"HA device group member `{obj.data.get('name')}` references undefined device group `{obj.data.get('device_group')}`")

        validator.check_duplicates(
            members,
            lambda obj: ("ha_device_group_member", obj.data.get("device_group"), obj.data.get("name")),
            "HA device group member",
        )

        for obj in traffic_groups:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            if obj.data.get("auto_failback_time") is not None and obj.data.get("auto_failback") is None:
                validator.error(obj.relpath, f"HA traffic group `{obj.data.get('name')}` sets `auto_failback_time` without `auto_failback`")
            if obj.data.get("ha_group") not in (None, "") and obj.data.get("ha_order") not in (None, ""):
                validator.error(obj.relpath, f"HA traffic group `{obj.data.get('name')}` cannot set both `ha_group` and `ha_order`")
            if obj.data.get("ha_group") not in (None, "") and str(obj.data.get("ha_group")) not in active_ha_group_names:
                validator.error(obj.relpath, f"HA traffic group `{obj.data.get('name')}` references undefined HA group `{obj.data.get('ha_group')}`")

        validator.check_duplicates(
            traffic_groups,
            lambda obj: ("ha_traffic_group", obj.partition, obj.data.get("name")),
            "HA traffic group",
        )

        for obj in configsync_actions:
            validator.require_fields(obj, ["device_group"])
            if obj.from_deletions:
                validator.error(obj.relpath, "HA config sync actions do not support deletion trees")
            push = bool(obj.data.get("sync_device_to_group"))
            pull = bool(obj.data.get("sync_group_to_device"))
            if push == pull:
                validator.error(obj.relpath, "HA config sync action must set exactly one of `sync_device_to_group` or `sync_group_to_device`")
            if str(obj.data.get("device_group")) not in active_group_names:
                validator.error(obj.relpath, f"HA config sync action references undefined device group `{obj.data.get('device_group')}`")
