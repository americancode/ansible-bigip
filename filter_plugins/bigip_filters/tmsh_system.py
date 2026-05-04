from __future__ import annotations

from .common import quote_tmsh


def build_management_route_tmsh_command(management, action="modify"):
    """Build a tmsh command string for a BIG-IP management route.

    Purpose:
        Generates the correct tmsh verb and arguments for showing, creating, or
        modifying a sys management-route object.

    Inputs:
        management (dict): Management route dict with keys like route_name and gateway.
        action (str): One of "show", "create", or "modify".

    Outputs:
        str|None: A ready-to-execute tmsh command, or None if inputs are invalid.

    Constraints:
        - Designed as a Jinja filter, so the management object is the first argument.
        - route_name defaults to "default" if not specified.
        - "show" uses the read-only "list" verb; others use "create" or "modify".
        - gateway is only appended when present.
    """
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
    """Build a tmsh command string to set the BIG-IP management IP address.

    Purpose:
        Generates a "modify sys management-ip" command for setting the device's
        out-of-band management address.

    Inputs:
        management (dict): Dict with an "address" key (e.g., "192.168.1.245/24").

    Outputs:
        str|None: A tmsh command string, or None if inputs are invalid.

    Constraints:
        - Only produces a "modify" command (management-ip is typically set once).
        - address must be non-empty to produce a valid command.
    """
    if not isinstance(management, dict):
        return None

    address = management.get("address")
    if address in (None, ""):
        return None
    return f"modify sys management-ip {address}"


def build_login_banner_tmsh_command(banner, action="modify"):
    """Build a tmsh command string for the BIG-IP login banner (gui-security-banner).

    Purpose:
        Generates tmsh commands to enable/disable and set the text of the web UI
        security banner.

    Inputs:
        banner (dict): Dict with optional "enabled" (bool) and "text" (str) keys.
        action (str): "delete" to disable the banner, or any other value to configure it.

    Outputs:
        str|None: A tmsh command string, or None if inputs are invalid.

    Constraints:
        - Designed as a Jinja filter, so the banner object is the first argument.
        - action "delete" simply disables the banner (ignores text).
        - Banner text is passed through quote_tmsh() for safe embedding.
        - "enabled" being None means the field is omitted from the command.
    """
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
