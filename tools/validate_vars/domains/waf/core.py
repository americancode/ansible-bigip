from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

from filter_plugins.bigip_var_filters import (
    compile_gtm_wide_ip_intent,
    compile_ltm_rke2_server_intent,
    compile_ltm_virtual_server_intent,
    normalize_gtm_pool,
    normalize_ltm_pool,
)

from ...constants import VARS_DIR
from ...models import LoadedObject

def validate_core(validator) -> None:
        policies = validator.objects.get("waf_policies", [])
        server_technologies = validator.objects.get("waf_server_technologies", [])

        supported_templates = {
            "Comprehensive", "Fundamental", "Vulnerability Assessment Baseline",
            "Rapid Deployment", "OWA Exchange 2007 (https)",
            "OWA Exchange 2007 (http)", "SharePoint 2007 (https)",
            "SharePoint 2007 (http)", "Drupal", "Joomla", "Wordpress",
        }

        active_policy_names = set()
        for obj in policies:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                if obj.partition != "Common":
                    validator.error(obj.relpath, f"WAF policy `{obj.data.get('name')}` must use partition `Common`; the current runtime tasks do not consume a partition field")
                active_policy_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))
                template = obj.data.get("template")
                if template is not None and template not in supported_templates:
                    validator.error(obj.relpath, f"WAF policy `{obj.data.get('name')}` template `{template}` is not a supported built-in template")
                active = obj.data.get("active")
                if active is not None and not isinstance(active, bool):
                    validator.error(obj.relpath, f"WAF policy `{obj.data.get('name')}` `active` must be a boolean")
                apply = obj.data.get("apply")
                if apply is not None and not isinstance(apply, bool):
                    validator.error(obj.relpath, f"WAF policy `{obj.data.get('name')}` `apply` must be a boolean")

        validator.check_duplicates(
            policies,
            lambda obj: ("waf_policy", obj.partition, obj.data.get("name")),
            "WAF policy",
        )

        for obj in server_technologies:
            validator.require_fields(obj, ["name", "policy_name"])
            if obj.effective_state == "absent":
                continue
            if obj.partition != "Common":
                validator.error(obj.relpath, f"WAF server technology `{obj.data.get('name')}` must use partition `Common`; the current runtime tasks do not consume a partition field")
            fq_policy = obj.data["policy_name"] if str(obj.data["policy_name"]).startswith("/") else validator.fq_name(obj.partition, str(obj.data["policy_name"]))
            if fq_policy not in active_policy_names:
                validator.error(obj.relpath, f"WAF server technology `{obj.data.get('name')}` references undefined policy `{fq_policy}`")

        validator.check_duplicates(
            server_technologies,
            lambda obj: ("waf_server_technology", obj.data.get("policy_name"), obj.data.get("name")),
            "WAF server technology",
        )
