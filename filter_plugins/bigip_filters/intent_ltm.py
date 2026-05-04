from __future__ import annotations

from .common import ensure_list, fq_name
from .transforms import expand_monitor_list, normalize_ltm_pool, normalize_members


def compile_ltm_virtual_server_intent(virtual_server, pool_defaults=None, member_defaults=None, monitor_sets=None):
    """Compile an LTM virtual server intent that embeds an inline pool definition.

    Purpose:
        Allows a virtual server to declare its pool inline (as a dict) rather than
        referencing a separately defined pool. The inline pool is normalized and
        emitted as a separate canonical pool object.

    Inputs:
        virtual_server (dict|None): Virtual server dict, optionally containing a
            "pool" key that is a pool dict (not just a name string).
        pool_defaults (dict|None): Defaults applied to the inline pool.
        member_defaults (dict|None): Defaults applied to the inline pool's members.
        monitor_sets (dict|None): Monitor alias mapping for pool monitor expansion.

    Outputs:
        dict: {"virtual_server": dict, "pools": list[dict]}
            - virtual_server: The virtual server with "pool" replaced by a name reference.
            - pools: A list containing the normalized inline pool (if any).

    Constraints:
        - If pool is already a string (name reference), it is left unchanged and
          no pool is emitted.
        - The pool's partition defaults to the virtual server's partition.
        - If the pool's partition differs from the virtual server's, the pool reference
          is fully qualified via fq_name().
    """
    if not isinstance(virtual_server, dict):
        return {"virtual_server": virtual_server, "pools": []}

    compiled_virtual_server = dict(virtual_server)
    compiled_pools = []
    pool = compiled_virtual_server.get("pool")

    if isinstance(pool, dict):
        virtual_partition = compiled_virtual_server.get("partition", "Common")
        normalized_pool = normalize_ltm_pool(pool, pool_defaults, member_defaults, monitor_sets)
        normalized_pool = dict(normalized_pool)
        normalized_pool.setdefault("partition", virtual_partition)
        compiled_pools.append(normalized_pool)

        if normalized_pool.get("partition", virtual_partition) == virtual_partition:
            compiled_virtual_server["pool"] = normalized_pool["name"]
        else:
            compiled_virtual_server["pool"] = fq_name(normalized_pool.get("partition"), normalized_pool["name"])

    return {
        "virtual_server": compiled_virtual_server,
        "pools": compiled_pools,
    }


def compile_ltm_rke2_server_intent(intent, intent_defaults=None, pool_defaults=None, member_defaults=None, monitor_sets=None):
    """Compile a higher-level RKE2 cluster intent into canonical LTM virtual servers and pools.

    Purpose:
        Turns one cluster intent (under vars/ltm/intents/clusters/) into canonical
        LTM virtual servers and pools using a service-first schema where each
        service embeds one `virtual_server` and one `pool` mapping.

    Inputs:
        intent (dict|None): Cluster intent dict with keys like name, partition,
            and services (list of service mappings).
        intent_defaults (dict|None): Compiler-level defaults from settings.yml hierarchy.
        pool_defaults (dict|None): Defaults applied to every generated pool.
        member_defaults (dict|None): Defaults applied to every generated pool member.
        monitor_sets (dict|None): Monitor alias mapping for monitor expansion.

    Outputs:
        dict: {"virtual_servers": list[dict], "pools": list[dict]}
            - virtual_servers: Generated canonical virtual server objects.
            - pools: Generated canonical pool objects.

    Constraints:
        - intent.name is required; returns empty lists if missing.
        - Each service must define `virtual_server.name` and `pool.name`.
        - `pool.members` are normalized via normalize_members(member_defaults).
        - `pool.monitors` aliases are expanded via monitor_sets.
        - Delete support: if intent state is "absent", all generated objects also get
          state: absent for symmetric delete.
        - Intent-only keys (e.g., services, state) are consumed here
          and NOT passed through to the emitted virtual servers.
    """
    if not isinstance(intent, dict):
        return {"virtual_servers": [], "pools": []}

    # Apply compiler-level defaults first, then let the explicit intent object win.
    resolved_intent = dict(intent_defaults or {})
    resolved_intent.update(intent)

    partition = resolved_intent.get("partition", "Common")
    intent_name = resolved_intent.get("name")
    if not intent_name:
        return {"virtual_servers": [], "pools": []}

    services = resolved_intent.get("services") or []

    # Carry forward only the fields that are valid on the emitted canonical virtual servers.
    # Intent-only keys such as worker member lists and service maps are consumed here, not by runtime tasks.
    base_virtual_server = {
        key: value
        for key, value in resolved_intent.items()
        if key
        not in {
            "__source_file",
            "name",
            "services",
            "state",
        }
    }
    base_virtual_server.setdefault("partition", partition)

    state = resolved_intent.get("state")
    deleting = state == "absent"

    compiled_virtual_servers = []
    compiled_pools = []

    def add_service(*, virtual_server_payload, pool_payload):
        """Every generated service emits one canonical virtual server and one canonical pool.

        Delete support stays symmetric by emitting the same names with state: absent.
        """
        virtual_server = dict(base_virtual_server)
        virtual_server.update(virtual_server_payload)
        virtual_server["partition"] = partition
        virtual_server["pool"] = pool_payload.get("name")
        if deleting:
            virtual_server["state"] = "absent"
        else:
            virtual_server["destination"] = virtual_server_payload.get("vip")
            virtual_server["destination_port"] = virtual_server_payload.get("port")

        pool = dict(pool_defaults or {})
        pool.update(pool_payload)
        pool["partition"] = partition
        if deleting:
            pool["state"] = "absent"
        else:
            pool["monitors"] = expand_monitor_list(ensure_list(pool.get("monitors")), monitor_sets)
            pool["members"] = normalize_members(pool.get("members"), member_defaults)

        compiled_virtual_servers.append(virtual_server)
        compiled_pools.append(pool)

    for service in services:
        if not isinstance(service, dict):
            continue
        service_virtual_server = service.get("virtual_server")
        service_pool = service.get("pool")
        if not isinstance(service_virtual_server, dict) or not isinstance(service_pool, dict):
            continue
        add_service(
            virtual_server_payload=service_virtual_server,
            pool_payload=service_pool,
        )

    return {
        "virtual_servers": compiled_virtual_servers,
        "pools": compiled_pools,
    }
