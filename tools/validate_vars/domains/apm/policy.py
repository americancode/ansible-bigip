from __future__ import annotations


def validate_policy_nodes(validator, policy_nodes: list, active_auth_server_names: set[str], active_sso_names: set[str]) -> None:
    supported_node_types = {
        "logon_page", "ad_auth", "ldap_auth", "kerberos_auth",
        "kcd_sso", "branch", "allow", "deny", "fallback",
        "macro", "variable_assign", "ad_query",
    }
    sso_ref_keys = {"kerberos_sso_object", "sso_config", "saml_sso", "oauth_sso", "form_based_sso", "http_basic_sso", "ntlm_sso"}
    for obj in policy_nodes:
        validator.require_fields(obj, ["name", "policy"])
        if obj.effective_state == "absent":
            continue
        node_type = obj.data.get("type")
        if node_type is not None and node_type not in supported_node_types:
            validator.error(obj.relpath, f"APM policy node `{obj.data.get('name')}` `type` must be one of {sorted(supported_node_types)}")
        properties = obj.data.get("properties")
        if properties is not None and not isinstance(properties, dict):
            validator.error(obj.relpath, f"APM policy node `{obj.data.get('name')}` `properties` must be a mapping")
            continue
        if node_type in ("ad_auth", "ad_query") and properties and "ad_server" in properties:
            ad_ref = properties["ad_server"]
            fq_ad = ad_ref if str(ad_ref).startswith("/") else validator.fq_name(obj.partition, str(ad_ref))
            if fq_ad not in active_auth_server_names:
                validator.error(obj.relpath, f"APM policy node `{obj.data.get('name')}` references undefined auth server `{fq_ad}`")
        if node_type == "ldap_auth" and properties and "ldap_server" in properties:
            ldap_ref = properties["ldap_server"]
            fq_ldap = ldap_ref if str(ldap_ref).startswith("/") else validator.fq_name(obj.partition, str(ldap_ref))
            if fq_ldap not in active_auth_server_names:
                validator.error(obj.relpath, f"APM policy node `{obj.data.get('name')}` references undefined auth server `{fq_ldap}`")
        if node_type in ("kcd_sso", "kerberos_auth") and properties:
            for key in sso_ref_keys:
                if key in properties:
                    sso_ref = properties[key]
                    fq_sso = sso_ref if str(sso_ref).startswith("/") else validator.fq_name(obj.partition, str(sso_ref))
                    if fq_sso not in active_sso_names:
                        validator.error(obj.relpath, f"APM policy node `{obj.data.get('name')}` references undefined SSO config `{fq_sso}`")
    validator.check_duplicates(
        policy_nodes,
        lambda obj: ("apm_policy_node", obj.partition, obj.data.get("policy"), obj.data.get("name")),
        "APM policy node",
    )
