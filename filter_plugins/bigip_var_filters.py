from __future__ import annotations

try:
    from .bigip_filters import (
        build_login_banner_tmsh_command,
        build_management_ip_tmsh_command,
        build_management_route_tmsh_command,
        build_nat_tmsh_command,
        classify_operations,
        compile_gtm_wide_ip_intent,
        compile_ltm_rke2_server_intent,
        compile_ltm_virtual_server_intent,
        expand_monitor_list,
        load_settings_hierarchy,
        normalize_gtm_pool,
        normalize_ltm_pool,
        resolve_gtm_members,
    )
except ImportError:
    from bigip_filters import (
        build_login_banner_tmsh_command,
        build_management_ip_tmsh_command,
        build_management_route_tmsh_command,
        build_nat_tmsh_command,
        classify_operations,
        compile_gtm_wide_ip_intent,
        compile_ltm_rke2_server_intent,
        compile_ltm_virtual_server_intent,
        expand_monitor_list,
        load_settings_hierarchy,
        normalize_gtm_pool,
        normalize_ltm_pool,
        resolve_gtm_members,
    )


class FilterModule(object):
    """Thin Ansible filter entrypoint that exposes the split helper modules."""

    def filters(self):
        return {
            "normalize_ltm_pool": normalize_ltm_pool,
            "normalize_gtm_pool": normalize_gtm_pool,
            "expand_monitor_list": expand_monitor_list,
            "resolve_gtm_members": resolve_gtm_members,
            "build_nat_tmsh_command": build_nat_tmsh_command,
            "classify_operations": classify_operations,
            "build_management_route_tmsh_command": build_management_route_tmsh_command,
            "build_management_ip_tmsh_command": build_management_ip_tmsh_command,
            "build_login_banner_tmsh_command": build_login_banner_tmsh_command,
            "load_settings_hierarchy": load_settings_hierarchy,
            "compile_ltm_virtual_server_intent": compile_ltm_virtual_server_intent,
            "compile_ltm_rke2_server_intent": compile_ltm_rke2_server_intent,
            "compile_gtm_wide_ip_intent": compile_gtm_wide_ip_intent,
        }
