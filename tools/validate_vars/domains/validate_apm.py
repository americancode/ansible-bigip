from __future__ import annotations

from .apm.core import validate_core_objects
from .apm.policy import validate_policy_nodes


def validate_apm(validator) -> None:
    objects = {
        "acls": validator.objects.get("apm_acls", []),
        "auth_servers": validator.objects.get("apm_auth_servers", []),
        "sso_configs": validator.objects.get("apm_sso_configs", []),
        "resources": validator.objects.get("apm_resources", []),
        "policy_nodes": validator.objects.get("apm_policy_nodes", []),
        "access_profiles": validator.objects.get("apm_access_profiles", []),
        "per_session_policies": validator.objects.get("apm_per_session_policies", []),
        "macros": validator.objects.get("apm_macros", []),
    }
    active_auth_server_names, active_sso_names = validate_core_objects(validator, objects)
    validate_policy_nodes(validator, objects["policy_nodes"], active_auth_server_names, active_sso_names)
