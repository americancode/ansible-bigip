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
        Turns one cluster intent (under vars/ltm/intents/clusters/) into the canonical
        LTM objects the runtime playbook already manages:
        - 2 control-plane virtual servers on the shared control-plane VIP (ports 6443 and 9345)
        - N worker-service virtual servers on port 443, each backed by a worker NodePort pool

    Inputs:
        intent (dict|None): The cluster intent dict with keys like name, partition,
            control_plane_vip, control_plane_members, worker_members, worker_services,
            kubeapi_monitors, registration_monitors, description_prefix.
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
        - control_plane_members and worker_members are normalized via normalize_members.
        - Generated object names follow the pattern:
            vs_{intent_name}_{suffix} and pool_{intent_name}_{suffix}.
        - Delete support: if intent state is "absent", all generated objects also get
          state: absent for symmetric delete.
        - Intent-only keys (e.g., control_plane_vip, worker_members) are consumed here
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

    # Normalize member inputs once so the generated pools inherit the same member-default logic
    # used by first-class canonical pool authoring.
    control_plane_members = normalize_members(resolved_intent.get("control_plane_members"), member_defaults) or []
    worker_members = normalize_members(resolved_intent.get("worker_members"), member_defaults) or []
    worker_services = resolved_intent.get("worker_services") or {}

    # Carry forward only the fields that are valid on the emitted canonical virtual servers.
    # Intent-only keys such as worker member lists and service maps are consumed here, not by runtime tasks.
    base_virtual_server = {
        key: value
        for key, value in resolved_intent.items()
        if key
        not in {
            "__source_file",
            "name",
            "control_plane_vip",
            "control_plane_members",
            "worker_members",
            "worker_services",
            "kubeapi_monitors",
            "registration_monitors",
            "description_prefix",
            "state",
        }
    }
    base_virtual_server.setdefault("partition", partition)

    description_prefix = resolved_intent.get("description_prefix", str(intent_name).replace("_", " "))
    kubeapi_monitors = expand_monitor_list(
        ensure_list(resolved_intent.get("kubeapi_monitors", ["kubeapi_tcp"])),
        monitor_sets,
    )
    registration_monitors = expand_monitor_list(
        ensure_list(resolved_intent.get("registration_monitors", ["registration_tcp"])),
        monitor_sets,
    )

    state = resolved_intent.get("state")
    deleting = state == "absent"

    compiled_virtual_servers = []
    compiled_pools = []

    def build_members(source_members, port):
        """Reuse the declared member objects but rewrite the port for the generated pool.

        The same control-plane members feed both 6443 and 9345, and worker members
        are reused for each worker service with its own NodePort.
        """
        members = []
        for member in source_members:
            if not isinstance(member, dict):
                continue
            compiled_member = dict(member)
            compiled_member["port"] = port
            members.append(compiled_member)
        return members

    def add_service(*, suffix, destination, destination_port, pool_name, monitors, members, description):
        """Every generated service emits one canonical virtual server and one canonical pool.

        Delete support stays symmetric by emitting the same names with state: absent.
        """
        virtual_server = dict(base_virtual_server)
        virtual_server["name"] = f"vs_{intent_name}_{suffix}"
        virtual_server["partition"] = partition
        virtual_server["pool"] = pool_name
        if deleting:
            virtual_server["state"] = "absent"
        else:
            virtual_server["destination"] = destination
            virtual_server["destination_port"] = destination_port
            virtual_server["description"] = description

        pool = dict(pool_defaults or {})
        pool.update(
            {
                "name": pool_name,
                "partition": partition,
            }
        )
        if deleting:
            pool["state"] = "absent"
        else:
            pool["monitors"] = monitors
            pool["members"] = members

        compiled_virtual_servers.append(virtual_server)
        compiled_pools.append(pool)

    add_service(
        suffix="kubeapi_6443",
        destination=resolved_intent.get("control_plane_vip"),
        destination_port=6443,
        pool_name=f"pool_{intent_name}_kubeapi_6443",
        monitors=kubeapi_monitors,
        members=build_members(control_plane_members, 6443),
        description=f"{description_prefix} Kubernetes API VIP",
    )
    add_service(
        suffix="registration_9345",
        destination=resolved_intent.get("control_plane_vip"),
        destination_port=9345,
        pool_name=f"pool_{intent_name}_registration_9345",
        monitors=registration_monitors,
        members=build_members(control_plane_members, 9345),
        description=f"{description_prefix} RKE2 supervisor registration VIP",
    )

    for service_name, service in worker_services.items():
        if not isinstance(service_name, str):
            continue
        service = service if isinstance(service, dict) else {}
        node_port = service.get("node_port")
        # Worker services front 443 externally but forward to a configurable NodePort internally.
        monitors = expand_monitor_list(ensure_list(service.get("monitors")), monitor_sets)
        add_service(
            suffix=f"{service_name}_443",
            destination=service.get("vip"),
            destination_port=443,
            pool_name=f"pool_{intent_name}_{service_name}_443",
            monitors=monitors,
            members=build_members(worker_members, node_port),
            description=service.get("description", f"{description_prefix} {service_name} VIP"),
        )

    return {
        "virtual_servers": compiled_virtual_servers,
        "pools": compiled_pools,
    }
