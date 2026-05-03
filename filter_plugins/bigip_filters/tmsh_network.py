from __future__ import annotations

from .common import fq_name, quote_tmsh


def build_nat_tmsh_command(action, nat):
    if not isinstance(nat, dict):
        return None

    partition = nat.get("partition", "Common")
    name = nat.get("name")
    if not name:
        return None
    fq_nat_name = fq_name(partition, name)

    if action == "show":
        return f"list ltm nat {fq_nat_name} one-line"
    if action == "delete":
        return f"delete ltm nat {fq_nat_name}"

    verb = "create" if action == "create" else "modify"
    parts = [verb, "ltm", "nat", fq_nat_name]

    if nat.get("originating_address") not in (None, ""):
        parts.extend(["originating-address", str(nat["originating_address"])])
    if nat.get("translation_address") not in (None, ""):
        parts.extend(["translation-address", str(nat["translation_address"])])
    if nat.get("traffic_group") not in (None, ""):
        parts.extend(["traffic-group", str(nat["traffic_group"])])
    if nat.get("auto_lasthop") not in (None, ""):
        parts.extend(["auto-lasthop", str(nat["auto_lasthop"])])
    if nat.get("description") not in (None, ""):
        parts.extend(["description", quote_tmsh(nat["description"])])
    if nat.get("enabled") is not None:
        parts.append("enabled" if bool(nat["enabled"]) else "disabled")
    if nat.get("arp") is not None:
        parts.append("arp" if bool(nat["arp"]) else "no-arp")

    vlans = nat.get("vlans")
    if isinstance(vlans, list):
        if vlans:
            parts.extend(["vlans", "replace-all-with", "{", " ".join(vlans), "}"])
            if nat.get("vlans_enabled") is not None:
                parts.append("vlans-enabled" if bool(nat["vlans_enabled"]) else "vlans-disabled")
        else:
            parts.extend(["vlans", "none"])
    elif nat.get("vlans_default"):
        parts.extend(["vlans", "default"])

    return " ".join(parts)
