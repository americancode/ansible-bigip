from __future__ import annotations

from .transforms import normalize_gtm_pool


def compile_gtm_wide_ip_intent(wide_ip, pool_defaults=None, member_defaults=None, monitor_sets=None, ltm_virtual_servers=None):
    if not isinstance(wide_ip, dict):
        return {"wide_ip": wide_ip, "pools": []}

    compiled_wide_ip = dict(wide_ip)
    compiled_pools = []
    compiled_pool_refs = []
    wide_ip_partition = compiled_wide_ip.get("partition", "Common")
    record_type = compiled_wide_ip.get("record_type", "a")

    for pool in compiled_wide_ip.get("pools", []) or []:
        if isinstance(pool, str):
            compiled_pool_refs.append({
                "name": pool,
                "partition": wide_ip_partition,
                "ratio": 1,
            })
            continue

        if not isinstance(pool, dict) or not pool.get("name"):
            continue

        if pool.get("members") is not None:
            normalized_pool = normalize_gtm_pool(pool, pool_defaults, member_defaults, monitor_sets, ltm_virtual_servers)
            normalized_pool = dict(normalized_pool)
            normalized_pool.setdefault("partition", wide_ip_partition)
            normalized_pool.setdefault("record_type", record_type)
            compiled_pools.append(normalized_pool)
            compiled_pool_refs.append({
                "name": normalized_pool["name"],
                "partition": normalized_pool.get("partition", wide_ip_partition),
                "ratio": pool.get("ratio", 1),
            })
            continue

        compiled_pool_refs.append({
            "name": pool["name"],
            "partition": pool.get("partition", wide_ip_partition),
            "ratio": pool.get("ratio", 1),
        })

    compiled_wide_ip["pools"] = compiled_pool_refs

    return {
        "wide_ip": compiled_wide_ip,
        "pools": compiled_pools,
    }
