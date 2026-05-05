from __future__ import annotations


def validate_core_objects(validator, objects: dict[str, list]) -> tuple[set[str], set[str]]:
    auth_servers = objects["auth_servers"]
    sso_configs = objects["sso_configs"]
    resources = objects["resources"]
    access_profiles = objects["access_profiles"]
    per_session_policies = objects["per_session_policies"]
    macros = objects["macros"]
    policy_nodes = objects["policy_nodes"]

    active_auth_server_names = set()
    supported_auth_types = {"active_directory", "ldap", "radius", "tacacs", "rsa_securid", "cert", "localdb", "saml", "oauth"}
    for obj in auth_servers:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state == "absent":
            continue
        auth_type = obj.data.get("type")
        if auth_type not in supported_auth_types:
            validator.error(obj.relpath, f"APM auth server `{obj.data.get('name')}` `type` must be one of {sorted(supported_auth_types)}")
        active_auth_server_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    validator.check_duplicates(auth_servers, lambda obj: ("apm_auth_server", obj.partition, obj.data.get("name")), "APM auth server")

    active_sso_names = set()
    supported_sso_types = {"kerberos", "form_based", "http_basic", "ntlm", "saml", "oauth", "citrix", "domain_join"}
    for obj in sso_configs:
        validator.require_fields(obj, ["name", "type"])
        if obj.effective_state == "absent":
            continue
        sso_type = obj.data.get("type")
        if sso_type not in supported_sso_types:
            validator.error(obj.relpath, f"APM SSO config `{obj.data.get('name')}` `type` must be one of {sorted(supported_sso_types)}")
        active_sso_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
    validator.check_duplicates(sso_configs, lambda obj: ("apm_sso_config", obj.partition, obj.data.get("name")), "APM SSO config")

    supported_resource_types = {"network_access", "webtop", "remote_desktop", "portal_access"}
    for obj in resources:
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue
        resource_type = obj.data.get("type")
        if resource_type is not None and resource_type not in supported_resource_types:
            validator.error(obj.relpath, f"APM resource `{obj.data.get('name')}` `type` must be one of {sorted(supported_resource_types)}")
    validator.check_duplicates(resources, lambda obj: ("apm_resource", obj.partition, obj.data.get("name")), "APM resource")

    active_access_policy_names = {validator.fq_name(obj.partition, str(obj.data.get("policy"))) for obj in policy_nodes if obj.effective_state != "absent" and obj.data.get("policy")}
    active_per_session_policy_names = {validator.fq_name(obj.partition, str(obj.data.get("name"))) for obj in per_session_policies if obj.effective_state != "absent" and obj.data.get("name")}
    for obj in access_profiles:
        validator.require_fields(obj, ["name"])
        if obj.effective_state == "absent":
            continue
        access_policy_ref = obj.data.get("default_access_policy")
        if isinstance(access_policy_ref, str) and access_policy_ref and not access_policy_ref.startswith("/"):
            fq_access_policy = validator.fq_name(obj.partition, access_policy_ref)
            if fq_access_policy not in active_access_policy_names:
                validator.error(obj.relpath, f"APM access profile `{obj.data.get('name')}` references undefined access policy `{fq_access_policy}`")
        per_session_ref = obj.data.get("default_per_session_policy")
        if isinstance(per_session_ref, str) and per_session_ref and not per_session_ref.startswith("/"):
            fq_per_session = validator.fq_name(obj.partition, per_session_ref)
            if fq_per_session not in active_per_session_policy_names:
                validator.error(obj.relpath, f"APM access profile `{obj.data.get('name')}` references undefined per-session policy `{fq_per_session}`")
    validator.check_duplicates(access_profiles, lambda obj: ("apm_access_profile", obj.partition, obj.data.get("name")), "APM access profile")

    for obj in per_session_policies:
        validator.require_fields(obj, ["name"])
    validator.check_duplicates(per_session_policies, lambda obj: ("apm_per_session_policy", obj.partition, obj.data.get("name")), "APM per-session policy")

    for obj in macros:
        validator.require_fields(obj, ["name"])
    validator.check_duplicates(macros, lambda obj: ("apm_macro", obj.partition, obj.data.get("name")), "APM macro")

    return active_auth_server_names, active_sso_names
