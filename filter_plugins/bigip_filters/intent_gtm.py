from __future__ import annotations

from .transforms import normalize_gtm_pool


def _compile_inline_gtm_member_infrastructure(member, default_partition, wide_ip_partition):
    """Compile inline GTM member infrastructure into canonical datacenter/server objects.

    Purpose:
        Lets one application intent either reference existing GTM servers/datacenters or
        own them inline, while still emitting the same canonical `gtm_servers` and
        `gtm_datacenters` objects that runtime tasks already manage.

    Inputs:
        member (dict|Any): A GTM pool member entry from an inline pool.
        default_partition (str): Partition inherited from the containing GTM pool.
        wide_ip_partition (str): Partition inherited from the parent Wide IP.

    Outputs:
        tuple[dict|Any, list[dict], list[dict]]:
            - compiled member with inline ownership fields stripped and `server`
              rewritten to the emitted canonical server name when applicable
            - list of emitted canonical GTM servers
            - list of emitted canonical GTM datacenters

    Constraints:
        - `server_mode: reference` leaves the member server reference unchanged.
        - `server_mode: inline` expects `server` to be a mapping with a `name`.
        - Inline server ownership can in turn either reference a canonical
          datacenter (`datacenter_mode: reference`) or emit one inline
          (`datacenter_mode: inline`).
    """
    if not isinstance(member, dict):
        return member, [], []

    compiled_member = dict(member)
    compiled_servers = []
    compiled_datacenters = []
    member_partition = compiled_member.get("partition", default_partition or wide_ip_partition or "Common")
    server_mode = compiled_member.pop("server_mode", "reference")

    if server_mode != "inline":
        return compiled_member, compiled_servers, compiled_datacenters

    server_payload = compiled_member.get("server")
    if not isinstance(server_payload, dict):
        return compiled_member, compiled_servers, compiled_datacenters

    server_partition = server_payload.get("partition", member_partition)
    datacenter_mode = server_payload.pop("datacenter_mode", "reference")
    datacenter_ref = server_payload.pop("datacenter_ref", None)
    datacenter_payload = server_payload.pop("datacenter", None)

    compiled_server = dict(server_payload)
    compiled_server["partition"] = server_partition

    if datacenter_mode == "inline" and isinstance(datacenter_payload, dict):
        compiled_datacenter = dict(datacenter_payload)
        compiled_datacenter["partition"] = compiled_datacenter.get("partition", server_partition)
        compiled_server["datacenter"] = compiled_datacenter.get("name")
        compiled_datacenters.append(compiled_datacenter)
    elif datacenter_mode == "reference" and datacenter_ref not in (None, ""):
        compiled_server["datacenter"] = datacenter_ref

    compiled_servers.append(compiled_server)
    compiled_member["server"] = compiled_server.get("name")

    return compiled_member, compiled_servers, compiled_datacenters


def compile_gtm_application_intent(application_intent, pool_defaults=None, member_defaults=None, monitor_sets=None, ltm_virtual_servers=None):
    """Compile a GTM application intent into canonical Wide IP and pool objects.

    Purpose:
        Allows one application intent to own a canonical GTM Wide IP and choose
        whether each referenced pool is canonical-by-reference or inline-owned.
        Inline pools are normalized (monitors expanded, members resolved against
        LTM virtual servers) and emitted as separate canonical GTM pool objects.
        Inline pool members can either reference canonical GTM servers/datacenters
        or own those supporting objects inline.

    Inputs:
        application_intent (dict|None): Application-intent dict with a `pools`
            list. Each pool entry must declare `pool_mode: reference|inline`.
        pool_defaults (dict|None): Defaults applied to inline pools.
        member_defaults (dict|None): Defaults applied to pool members.
        monitor_sets (dict|None): Monitor alias mapping for pool monitor expansion.
        ltm_virtual_servers (dict|None): Lookup map of LTM virtual servers for
            GTM member resolution.

    Outputs:
        dict: {"wide_ip": dict, "pools": list[dict], "servers": list[dict], "datacenters": list[dict]}
            - wide_ip: The canonical Wide IP with "pools" replaced by a list of pool references
              (with partition and ratio).
            - pools: A list of normalized inline pool objects (if any).
            - servers: Canonical GTM servers emitted by inline-owned members.
            - datacenters: Canonical GTM datacenters emitted by inline-owned servers.

    Constraints:
        - `pool_mode: reference` requires `pool_ref` and emits no canonical pool.
        - `pool_mode: inline` requires nested `pool` mapping and emits one
          canonical GTM pool object.
        - Inline pools inherit the Wide IP partition and record_type if not set.
        - Inline member ownership is explicit:
          `server_mode: reference|inline` and inline servers use
          `datacenter_mode: reference|inline`.
    """
    if not isinstance(application_intent, dict):
        return {"wide_ip": application_intent, "pools": [], "servers": [], "datacenters": []}

    compiled_wide_ip = dict(application_intent)
    compiled_pools = []
    compiled_servers = []
    compiled_datacenters = []
    compiled_pool_refs = []
    wide_ip_partition = compiled_wide_ip.get("partition", "Common")
    record_type = compiled_wide_ip.get("record_type", "a")

    for pool_binding in compiled_wide_ip.get("pools", []) or []:
        if not isinstance(pool_binding, dict):
            continue

        pool_mode = pool_binding.get("pool_mode")
        pool_ratio = pool_binding.get("ratio", 1)

        if pool_mode == "reference":
            pool_ref = pool_binding.get("pool_ref")
            if not isinstance(pool_ref, str) or not pool_ref:
                continue
            compiled_pool_ref = {
                "name": pool_ref,
                "ratio": pool_ratio,
            }
            if pool_binding.get("partition") not in (None, ""):
                compiled_pool_ref["partition"] = pool_binding.get("partition")
            compiled_pool_refs.append(compiled_pool_ref)
            continue

        if pool_mode != "inline":
            continue

        pool = pool_binding.get("pool")
        if not isinstance(pool, dict) or not pool.get("name"):
            continue

        pool_with_compiled_members = dict(pool)
        pool_partition = pool_with_compiled_members.get("partition", wide_ip_partition)
        compiled_members = []
        for member in pool_with_compiled_members.get("members", []) or []:
            compiled_member, emitted_servers, emitted_datacenters = _compile_inline_gtm_member_infrastructure(
                member,
                pool_partition,
                wide_ip_partition,
            )
            compiled_members.append(compiled_member)
            compiled_servers.extend(emitted_servers)
            compiled_datacenters.extend(emitted_datacenters)
        pool_with_compiled_members["members"] = compiled_members

        normalized_pool = normalize_gtm_pool(pool_with_compiled_members, pool_defaults, member_defaults, monitor_sets, ltm_virtual_servers)
        normalized_pool = dict(normalized_pool)
        normalized_pool.setdefault("partition", wide_ip_partition)
        normalized_pool.setdefault("record_type", record_type)
        compiled_pools.append(normalized_pool)
        compiled_pool_ref = {
            "name": normalized_pool["name"],
            "ratio": pool_ratio,
        }
        if pool_binding.get("partition") not in (None, ""):
            compiled_pool_ref["partition"] = pool_binding.get("partition")
        compiled_pool_refs.append(compiled_pool_ref)

    compiled_wide_ip["pools"] = compiled_pool_refs

    return {
        "wide_ip": compiled_wide_ip,
        "pools": compiled_pools,
        "servers": compiled_servers,
        "datacenters": compiled_datacenters,
    }
