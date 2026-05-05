from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .ansible_yaml import AnsibleVarLoader
from .constants import VARS_DIR


LOAD_SPECS: tuple[tuple[str, Path, str], ...] = (
    ("system_partitions", VARS_DIR / "system" / "partitions", "system_partitions"),
    ("system_auth_remote_roles", VARS_DIR / "system" / "auth" / "remote_roles", "system_auth_remote_roles"),
    ("ltm_nodes", VARS_DIR / "ltm" / "nodes", "ltm_nodes"),
    ("ltm_monitors", VARS_DIR / "ltm" / "monitors", "ltm_monitors"),
    ("ltm_pools", VARS_DIR / "ltm" / "pools", "ltm_pools"),
    ("ltm_virtual_servers", VARS_DIR / "ltm" / "virtual_servers", "ltm_virtual_servers"),
    ("ltm_profiles", VARS_DIR / "ltm" / "profiles", "ltm_profiles"),
    ("ltm_persistence_profiles", VARS_DIR / "ltm" / "persistence", "ltm_persistence_profiles"),
    ("ltm_irules", VARS_DIR / "ltm" / "irules", "ltm_irules"),
    ("ltm_data_groups", VARS_DIR / "ltm" / "data_groups", "ltm_data_groups"),
    ("ltm_policies", VARS_DIR / "ltm" / "policies", "ltm_policies"),
    ("gtm_datacenters", VARS_DIR / "gtm" / "datacenters", "gtm_datacenters"),
    ("gtm_servers", VARS_DIR / "gtm" / "servers", "gtm_servers"),
    ("gtm_pools", VARS_DIR / "gtm" / "pools", "gtm_pools"),
    ("gtm_wide_ips", VARS_DIR / "gtm" / "intents" / "applications", "gtm_wide_ips"),
    ("gtm_topology_regions", VARS_DIR / "gtm" / "regions", "gtm_topology_regions"),
    ("gtm_topology_records", VARS_DIR / "gtm" / "topology", "gtm_topology_records"),
    ("gtm_monitors", VARS_DIR / "gtm" / "monitors", "gtm_monitors"),
    ("network_vlans", VARS_DIR / "network" / "vlans", "bigip_vlans"),
    ("network_self_ips", VARS_DIR / "network" / "self_ips", "bigip_self_ips"),
    ("network_routes", VARS_DIR / "network" / "routes", "bigip_routes"),
    ("network_route_domains", VARS_DIR / "network" / "route_domains", "bigip_route_domains"),
    ("network_trunks", VARS_DIR / "network" / "trunks", "bigip_trunks"),
    ("network_snat_translations", VARS_DIR / "network" / "snat_translations", "bigip_snat_translations"),
    ("network_snats", VARS_DIR / "network" / "snats", "bigip_snat_pools"),
    ("network_nats", VARS_DIR / "network" / "nats", "bigip_nats"),
    ("afm_address_lists", VARS_DIR / "security" / "afm" / "address_lists", "afm_address_lists"),
    ("afm_port_lists", VARS_DIR / "security" / "afm" / "port_lists", "afm_port_lists"),
    ("afm_rules", VARS_DIR / "security" / "afm" / "rules", "afm_rules"),
    ("afm_policies", VARS_DIR / "security" / "afm" / "policies", "afm_policies"),
    ("waf_policies", VARS_DIR / "security" / "waf" / "policies", "waf_policies"),
    ("apm_acls", VARS_DIR / "security" / "apm" / "acls", "apm_acls"),
    ("apm_auth_servers", VARS_DIR / "security" / "apm" / "auth_servers", "apm_auth_servers"),
    ("apm_sso_configs", VARS_DIR / "security" / "apm" / "sso_configs", "apm_sso_configs"),
    ("apm_resources", VARS_DIR / "security" / "apm" / "resources", "apm_resources"),
    ("apm_access_profiles", VARS_DIR / "security" / "apm" / "access_profiles", "apm_access_profiles"),
    ("apm_per_session_policies", VARS_DIR / "security" / "apm" / "per_session_policies", "apm_per_session_policies"),
    ("apm_macros", VARS_DIR / "security" / "apm" / "macros", "apm_macros"),
    ("apm_policy_nodes", VARS_DIR / "security" / "apm" / "policy_nodes", "apm_policy_nodes"),
    ("tls_keys", VARS_DIR / "tls" / "keys", "tls_keys"),
    ("tls_certificates", VARS_DIR / "tls" / "certificates", "tls_certificates"),
    ("tls_ca_bundles", VARS_DIR / "tls" / "ca_bundles", "tls_ca_bundles"),
    ("tls_client_ssl_profiles", VARS_DIR / "tls" / "client_ssl_profiles", "tls_client_ssl_profiles"),
    ("tls_server_ssl_profiles", VARS_DIR / "tls" / "server_ssl_profiles", "tls_server_ssl_profiles"),
)


class VarTreeLoader:
    def __init__(self) -> None:
        self.objects: dict[str, list[dict[str, Any]]] = {}

    def load(self) -> None:
        for key, directory, top_key in LOAD_SPECS:
            self._load_simple_tree(key, directory, top_key)

    def _load_simple_tree(self, key: str, directory: Path, top_key: str) -> None:
        if not directory.exists():
            return
        objects: list[dict[str, Any]] = []
        for path in sorted(directory.rglob("*.yml")):
            if path.name == "settings.yml":
                continue
            try:
                with path.open("r") as f:
                    payload = yaml.load(f, Loader=AnsibleVarLoader) or {}
                entries = payload.get(top_key, [])
                if isinstance(entries, list):
                    objects.extend(entries)
            except (yaml.YAMLError, OSError):
                continue
        if objects:
            self.objects[key] = objects
