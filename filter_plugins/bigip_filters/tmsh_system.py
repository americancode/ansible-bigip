from __future__ import annotations

from .common import quote_tmsh


def build_management_route_tmsh_command(action, management):
    if not isinstance(management, dict):
        return None

    route_name = management.get("route_name", "default")
    gateway = management.get("gateway")
    if not route_name:
        return None

    if action == "show":
        return f"list sys management-route {route_name} one-line"

    verb = "create" if action == "create" else "modify"
    parts = [verb, "sys", "management-route", str(route_name)]
    if gateway not in (None, ""):
        parts.extend(["gateway", str(gateway)])
    return " ".join(parts)


def build_management_ip_tmsh_command(management):
    if not isinstance(management, dict):
        return None

    address = management.get("address")
    if address in (None, ""):
        return None
    return f"modify sys management-ip {address}"


def build_login_banner_tmsh_command(action, banner):
    if not isinstance(banner, dict):
        return None

    if action == "delete":
        return "modify sys global-settings gui-security-banner disabled"

    parts = ["modify", "sys", "global-settings"]
    enabled = banner.get("enabled")
    if enabled is not None:
        parts.extend(["gui-security-banner", "enabled" if bool(enabled) else "disabled"])
    if banner.get("text") not in (None, ""):
        parts.extend(["gui-security-banner-text", quote_tmsh(banner["text"])])
    return " ".join(parts)
