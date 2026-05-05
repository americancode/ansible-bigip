from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any

from filter_plugins.bigip_var_filters import (
    compile_gtm_application_intent,
    compile_ltm_rke2_server_intent,
    compile_ltm_virtual_server_intent,
    normalize_gtm_pool,
    normalize_ltm_pool,
)

from ...constants import VARS_DIR
from ...models import LoadedObject

def validate_core(validator) -> None:
        """Validate vars/common.yml for required fields.

        Purpose:
            Ensures the repo-wide provider variable is defined and is a mapping.

        Validates:
            - vars/common.yml must exist and be a mapping.
            - "provider" key must be present and be a dict.
        """
        path = VARS_DIR / "common.yml"
        payload = validator.load_yaml(path)
        if not isinstance(payload, dict):
            validator.error(path, "must contain a mapping")
            return
        if "provider" not in payload:
            validator.error(path, "must define `provider`")
        elif not isinstance(payload["provider"], dict):
            validator.error(path, "`provider` must be a mapping")

        for tree_name, objects in validator.objects.items():
            for obj in objects:
                if "target_hosts" in obj.data or "target_groups" in obj.data:
                    validator.validate_target_selectors(
                        obj,
                        label=f"{tree_name} object",
                        allow_absent=True,
                    )
