from __future__ import annotations

from dataclasses import dataclass, field

from typing import Any

@dataclass
class ImportSpec:
    """Specification for importing a BIG-IP object type.

    Purpose:
        Defines how to query a BIG-IP REST endpoint and how to transform
        the response into repository var tree format.

    Attributes:
        endpoint (str): The BIG-IP REST API path (e.g., "ltm/pool").
        top_key (str): The YAML top-level key name for the output file.
        output_dir (str): Relative path under vars/ for output files.
        extract (dict[str, str]): Mapping of repo field names to BIG-IP API field names.

    Example:
        ImportSpec(
            endpoint="ltm/pool",
            top_key="ltm_pools",
            output_dir="ltm/pools",
            extract={"name": "name", "monitor": "monitor"}
        )
    """
    endpoint: str
    top_key: str
    output_dir: str
    extract: dict[str, str] = field(default_factory=dict)


IMPORT_SPECS: dict[str, ImportSpec] = {
    "system_partitions": ImportSpec(
        endpoint="auth/partition",
        top_key="system_partitions",
        output_dir="system/partitions",
        extract={
            "name": "name",
            "description": "description",
            "route_domain": "defaultRouteDomain",
        },
    ),
    "ltm_nodes": ImportSpec(
        endpoint="ltm/node",
        top_key="ltm_nodes",
        output_dir="ltm/nodes",
        extract={
            "name": "name",
            "address": "address",
            "description": "description",
            "connection_limit": "connectionLimit",
            "rate_limit": "rateLimit",
        },
    ),
    "ltm_pools": ImportSpec(
        endpoint="ltm/pool",
        top_key="ltm_pools",
        output_dir="ltm/pools",
        extract={
            "name": "name",
            "description": "description",
            "lb_method": "loadBalancingMode",
            "min_active_members": "minActiveMembers",
        },
    ),
    "ltm_virtual_servers": ImportSpec(
        endpoint="ltm/virtual",
        top_key="ltm_virtual_servers",
        output_dir="ltm/virtual_servers",
        extract={
            "name": "name",
            "description": "description",
            "destination": "destination",
            "protocol": "ipProtocol",
            "enabled": "enabled",
        },
    ),
    "ltm_monitors": ImportSpec(
        endpoint="ltm/monitor",
        top_key="ltm_monitors",
        output_dir="ltm/monitors",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "ltm_profiles": ImportSpec(
        endpoint="ltm/profile",
        top_key="ltm_profiles",
        output_dir="ltm/profiles",
        extract={
            "name": "name",
            "description": "description",
            "type": "kind",
        },
    ),
    "ltm_irules": ImportSpec(
        endpoint="ltm/rule",
        top_key="ltm_irules",
        output_dir="ltm/irules",
        extract={
            "name": "name",
            "rule": "apiAnonymous",
        },
    ),
    "ltm_data_groups": ImportSpec(
        endpoint="ltm/data-group",
        top_key="ltm_data_groups",
        output_dir="ltm/data_groups",
        extract={
            "name": "name",
            "type": "type",
        },
    ),
    "ltm_policies": ImportSpec(
        endpoint="ltm/policy",
        top_key="ltm_policies",
        output_dir="ltm/policies",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "ltm_persistence_profiles": ImportSpec(
        endpoint="ltm/profile/persistence",
        top_key="ltm_persistence_profiles",
        output_dir="ltm/persistence",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "gtm_datacenters": ImportSpec(
        endpoint="gtm/datacenter",
        top_key="gtm_datacenters",
        output_dir="gtm/datacenters",
        extract={
            "name": "name",
            "location": "location",
            "contact": "contact",
        },
    ),
    "gtm_servers": ImportSpec(
        endpoint="gtm/server",
        top_key="gtm_servers",
        output_dir="gtm/servers",
        extract={
            "name": "name",
            "datacenter": "dataCenter",
            "description": "description",
        },
    ),
    "gtm_pools": ImportSpec(
        endpoint="gtm/pool",
        top_key="gtm_pools",
        output_dir="gtm/pools",
        extract={
            "name": "name",
            "description": "description",
            "lb_method": "loadBalancingMode",
        },
    ),
    "gtm_wide_ips": ImportSpec(
        endpoint="gtm/wideip",
        top_key="gtm_wide_ips",
        output_dir="gtm/intents/applications",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "gtm_monitors": ImportSpec(
        endpoint="gtm/monitor",
        top_key="gtm_monitors",
        output_dir="gtm/monitors",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "network_vlans": ImportSpec(
        endpoint="net/vlan",
        top_key="bigip_vlans",
        output_dir="network/vlans",
        extract={
            "name": "name",
            "tag": "tag",
            "mtu": "mtu",
            "description": "description",
        },
    ),
    "network_self_ips": ImportSpec(
        endpoint="net/self",
        top_key="bigip_self_ips",
        output_dir="network/self_ips",
        extract={
            "name": "name",
            "address": "address",
            "vlan": "vlan",
            "description": "description",
        },
    ),
    "network_routes": ImportSpec(
        endpoint="net/route",
        top_key="bigip_routes",
        output_dir="network/routes",
        extract={
            "name": "name",
            "destination": "network",
            "netmask": "netmask",
            "gateway_address": "gw",
        },
    ),
    "network_route_domains": ImportSpec(
        endpoint="net/route-domain",
        top_key="bigip_route_domains",
        output_dir="network/route_domains",
        extract={
            "name": "name",
            "id": "id",
            "description": "description",
        },
    ),
    "network_trunks": ImportSpec(
        endpoint="net/trunk",
        top_key="bigip_trunks",
        output_dir="network/trunks",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "network_snat_translations": ImportSpec(
        endpoint="ltm/snat-translation",
        top_key="bigip_snat_translations",
        output_dir="network/snat_translations",
        extract={
            "name": "name",
            "address": "address",
            "arp": "arp",
            "connection_limit": "connectionLimit",
            "description": "description",
            "ip_idle_timeout": "ipIdleTimeout",
            "tcp_idle_timeout": "tcpIdleTimeout",
            "udp_idle_timeout": "udpIdleTimeout",
            "traffic_group": "trafficGroup",
        },
    ),
    "network_snats": ImportSpec(
        endpoint="ltm/snatpool",
        top_key="bigip_snat_pools",
        output_dir="network/snats",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "network_nats": ImportSpec(
        endpoint="ltm/nat",
        top_key="bigip_nats",
        output_dir="network/nats",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "gtm_topology_regions": ImportSpec(
        endpoint="gtm/region",
        top_key="gtm_topology_regions",
        output_dir="gtm/regions",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "gtm_topology_records": ImportSpec(
        endpoint="gtm/topology",
        top_key="gtm_topology_records",
        output_dir="gtm/topology",
        extract={},
    ),
    "afm_address_lists": ImportSpec(
        endpoint="security/firewall/address-list",
        top_key="afm_address_lists",
        output_dir="security/afm/address_lists",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "afm_port_lists": ImportSpec(
        endpoint="security/firewall/port-list",
        top_key="afm_port_lists",
        output_dir="security/afm/port_lists",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "waf_policies": ImportSpec(
        endpoint="asm/policies",
        top_key="waf_policies",
        output_dir="security/waf/policies",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "waf_server_technologies": ImportSpec(
        endpoint="asm/policies",
        top_key="waf_server_technologies",
        output_dir="security/waf/server_technologies",
        extract={},
    ),
    "apm_acls": ImportSpec(
        endpoint="access/policy/acl",
        top_key="apm_acls",
        output_dir="security/apm/acls",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_auth_servers": ImportSpec(
        endpoint="auth/remote-server",
        top_key="apm_auth_servers",
        output_dir="security/apm/auth_servers",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_sso_configs": ImportSpec(
        endpoint="apm/sso",
        top_key="apm_sso_configs",
        output_dir="security/apm/sso_configs",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_resources": ImportSpec(
        endpoint="apm/resource",
        top_key="apm_resources",
        output_dir="security/apm/resources",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_access_profiles": ImportSpec(
        endpoint="access/profile",
        top_key="apm_access_profiles",
        output_dir="security/apm/access_profiles",
        extract={
            "name": "name",
            "description": "description",
            "default_access_policy": "defaultAccessPolicy",
            "default_per_session_policy": "defaultPerSessionPolicy",
            "sso_configuration": "ssoConfiguration",
            "domain": "domain",
            "agent_cap": "agentCap",
            "session_timeout": "sessionTimeout",
            "idle_timeout": "idleTimeout",
            "max_sessions": "maxSessions",
            "cookie_fallback": "cookieFallback",
        },
    ),
    "apm_per_session_policies": ImportSpec(
        endpoint="access/per-session-policy",
        top_key="apm_per_session_policies",
        output_dir="security/apm/per_session_policies",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_macros": ImportSpec(
        endpoint="access/macro",
        top_key="apm_macros",
        output_dir="security/apm/macros",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "apm_policy_nodes": ImportSpec(
        endpoint="apm/policy/access-policy",
        top_key="apm_policy_nodes",
        output_dir="security/apm/policy_nodes",
        extract={},
    ),
    "tls_keys": ImportSpec(
        endpoint="sys/crypto/key",
        top_key="tls_keys",
        output_dir="tls/keys",
        extract={
            "name": "name",
        },
    ),
    "tls_certificates": ImportSpec(
        endpoint="sys/crypto/cert",
        top_key="tls_certificates",
        output_dir="tls/certificates",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "tls_ca_bundles": ImportSpec(
        endpoint="sys/crypto/ca-bundle",
        top_key="tls_ca_bundles",
        output_dir="tls/ca_bundles",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "tls_client_ssl_profiles": ImportSpec(
        endpoint="ltm/profile/client-ssl",
        top_key="tls_client_ssl_profiles",
        output_dir="tls/client_ssl_profiles",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
    "tls_server_ssl_profiles": ImportSpec(
        endpoint="ltm/profile/server-ssl",
        top_key="tls_server_ssl_profiles",
        output_dir="tls/server_ssl_profiles",
        extract={
            "name": "name",
            "description": "description",
        },
    ),
}

SUPPORTED_TYPES = set(IMPORT_SPECS.keys())

BUILTIN_MONITORS = {
    "gateway_icmp", "http", "https", "https_443", "tcp", "tcp_half_open",
    "tcp_echo", "udp", "icmp", "ftp", "smtp", "imap", "pop3", "ldap",
    "sip", "mysql", "postgresql", "oracle", "radius", "snmp_dca",
    "snmp_dca_base", "real_server", "wap_gateway", "dns",
}

BUILTIN_PROFILES = {
    "tcp", "udp", "fastL4", "fasthttp", "http", "http2", "oneconnect",
    "clientssl", "serverssl", "dns", "ftp", "smtp",
}

