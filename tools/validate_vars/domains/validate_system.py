from __future__ import annotations

from .system.auth import validate_auth_objects
from .system.core import validate_core_objects
from .system.login_config import validate_login_and_config


def validate_system(validator) -> None:
    objects = {
        "hostnames": validator.objects.get("system_hostnames", []),
        "dns_settings": validator.objects.get("system_dns", []),
        "ntp_settings": validator.objects.get("system_ntp", []),
        "provisioning": validator.objects.get("system_provisioning", []),
        "partitions": validator.objects.get("system_partitions", []),
        "users": validator.objects.get("system_users", []),
        "auth_ldap": validator.objects.get("system_auth_ldap", []),
        "auth_tacacs": validator.objects.get("system_auth_tacacs", []),
        "auth_radius_servers": validator.objects.get("system_auth_radius_servers", []),
        "auth_radius": validator.objects.get("system_auth_radius", []),
        "login_banners": validator.objects.get("system_login_banners", []),
        "config": validator.objects.get("system_config", []),
    }
    validate_core_objects(validator, objects)
    validate_auth_objects(validator, objects)
    validate_login_and_config(validator, objects)
