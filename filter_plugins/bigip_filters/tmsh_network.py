from __future__ import annotations

from .common import fq_name, quote_tmsh


def build_nat_tmsh_command(action, nat):
    """Build a tmsh command string for an LTM NAT (Network Address Translation) object.

    Purpose:
        Generates the correct tmsh verb and arguments for showing, creating, modifying,
        or deleting an ltm nat object.

    Inputs:
        action (str): One of "show", "create", "modify", or "delete".
        nat (dict): NAT object dict with fields like name, partition, originating_address,
            translation_address, traffic_group, vlans, etc.

    Outputs:
        str|None: A ready-to-execute tmsh command, or None if inputs are invalid.

    Constraints:
        - name is required; returns None if missing.
        - Uses fq_name() to fully qualify the NAT name with its partition.
        - "show" returns a read-only "list" command; "delete" returns a delete command.
        - VLAN handling: if vlans list is non-empty, uses "replace-all-with" syntax;
          if empty, uses "vlans none"; if vlans_default is truthy, uses "vlans default".
        - Boolean fields (enabled, arp) emit explicit "enabled"/"disabled" or "arp"/"no-arp".
        - Description is passed through quote_tmsh() for safe embedding.
    """
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
