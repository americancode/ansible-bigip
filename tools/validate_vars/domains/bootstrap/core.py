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
        """Validate bootstrap domain objects (licenses and management).

        Purpose:
            Checks that bootstrap licenses and management routes are correctly
            structured and conform to the bootstrap domain's limited model.

        Validates:
            - License objects: state must be present/latest/absent/revoked;
              accept_eula must be true for present/latest; addon_keys must be a list.
            - Management objects: address must be valid CIDR; gateway must be valid IP;
              route_name must not be empty if present.
            - Deletion trees are not supported for bootstrap objects.
        """
        licenses = validator.objects.get("bootstrap_licenses", [])
        management = validator.objects.get("bootstrap_management", [])

        for obj in licenses:
            if obj.from_deletions:
                validator.error(obj.relpath, "bootstrap license objects do not support deletion trees")
                continue
            state = str(obj.data.get("state", "present"))
            if state not in ("present", "latest", "absent", "revoked"):
                validator.error(obj.relpath, f"bootstrap license state `{state}` is unsupported")
            if state in ("present", "latest"):
                validator.require_fields(obj, ["license_key"])
                if obj.data.get("accept_eula") is not True:
                    validator.error(obj.relpath, "bootstrap license objects using `present` or `latest` must set `accept_eula: true`")
            addon_keys = obj.data.get("addon_keys")
            if addon_keys is not None and not isinstance(addon_keys, list):
                validator.error(obj.relpath, "`addon_keys` must be a list when provided")

        validator.check_duplicates(
            licenses,
            lambda obj: ("bootstrap_license", obj.data.get("license_key") or obj.relpath, obj.data.get("state", "present")),
            "bootstrap license object",
        )

        for obj in management:
            if obj.from_deletions:
                validator.error(obj.relpath, "bootstrap management objects do not support deletion trees")
                continue
            validator.require_fields(obj, ["address", "gateway"])
            try:
                ipaddress.ip_interface(str(obj.data.get("address")))
            except ValueError:
                validator.error(obj.relpath, f"bootstrap management address `{obj.data.get('address')}` must be a valid CIDR")
            try:
                ipaddress.ip_address(str(obj.data.get("gateway")))
            except ValueError:
                validator.error(obj.relpath, f"bootstrap management gateway `{obj.data.get('gateway')}` must be a valid IP address")
            route_name = obj.data.get("route_name")
            if route_name is not None and str(route_name).strip() == "":
                validator.error(obj.relpath, "bootstrap management `route_name` may not be empty")

        validator.check_duplicates(
            management,
            lambda obj: ("bootstrap_management", obj.data.get("route_name", "default")),
            "bootstrap management route",
        )
