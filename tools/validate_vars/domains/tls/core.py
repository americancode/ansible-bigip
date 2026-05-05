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
        """Validate TLS domain objects: keys, certificates, CA bundles, SSL profiles.

        Purpose:
            Validates all TLS objects in the var tree against the repo's field model.
            Ensures keys have required fields (name, content), certificates link to valid keys,
            CA bundles are present, and SSL profiles reference valid certificates/keys.

        Side effects:
            Adds validation errors to validator.errors for any violations.
        """
        keys = validator.objects.get("tls_keys", [])
        certificates = validator.objects.get("tls_certificates", [])
        ca_bundles = validator.objects.get("tls_ca_bundles", [])
        client_ssl_profiles = validator.objects.get("tls_client_ssl_profiles", [])
        server_ssl_profiles = validator.objects.get("tls_server_ssl_profiles", [])

        active_key_names = set()
        active_certificate_names = set()
        active_ca_bundle_names = set()

        for obj in keys:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                validator.require_fields(obj, ["content"])
                active_key_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

        validator.check_duplicates(keys, lambda obj: ("tls_key", obj.partition, obj.data.get("name")), "TLS key")

        for obj in certificates:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                validator.require_fields(obj, ["content"])
                active_certificate_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

        validator.check_duplicates(certificates, lambda obj: ("tls_certificate", obj.partition, obj.data.get("name")), "TLS certificate")

        for obj in ca_bundles:
            validator.require_fields(obj, ["name"])
            if obj.effective_state != "absent":
                validator.require_fields(obj, ["content"])
                active_ca_bundle_names.add(validator.fq_name(obj.partition, str(obj.data["name"])))

        validator.check_duplicates(ca_bundles, lambda obj: ("tls_ca_bundle", obj.partition, obj.data.get("name")), "TLS CA bundle")

        known_cert_like_names = active_certificate_names | active_ca_bundle_names

        for obj in client_ssl_profiles:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            if obj.data.get("cert_key_chain") is not None and not isinstance(obj.data.get("cert_key_chain"), list):
                validator.error(obj.relpath, f"TLS client SSL profile `{obj.data.get('name')}` `cert_key_chain` must be a list")
            for index, chain in enumerate(obj.data.get("cert_key_chain", []) or []):
                if not isinstance(chain, dict):
                    validator.error(obj.relpath, f"TLS client SSL profile `{obj.data.get('name')}` cert_key_chain entry {index} must be a mapping")
                    continue
                validator.require_fields(chain, ["cert", "key"], obj.relpath, f"TLS client SSL profile `{obj.data.get('name')}` cert_key_chain entry {index}")
                validator.validate_named_or_fq_reference(obj.relpath, chain.get("cert"), obj.partition, active_certificate_names, "TLS client SSL certificate")
                validator.validate_named_or_fq_reference(obj.relpath, chain.get("key"), obj.partition, active_key_names, "TLS client SSL key")
                if chain.get("chain") is not None:
                    validator.validate_named_or_fq_reference(obj.relpath, chain.get("chain"), obj.partition, known_cert_like_names, "TLS client SSL chain")
            if obj.data.get("trusted_cert_authority") is not None:
                validator.validate_fq_or_common_reference(obj.relpath, obj.data.get("trusted_cert_authority"), known_cert_like_names, "TLS trusted cert authority")
            if obj.data.get("advertised_cert_authority") is not None:
                validator.validate_fq_or_common_reference(obj.relpath, obj.data.get("advertised_cert_authority"), known_cert_like_names, "TLS advertised cert authority")
            if obj.data.get("client_auth_crl") is not None and not isinstance(obj.data.get("client_auth_crl"), str):
                validator.error(obj.relpath, f"TLS client SSL profile `{obj.data.get('name')}` `client_auth_crl` must be a string")

        validator.check_duplicates(
            client_ssl_profiles,
            lambda obj: ("tls_client_ssl_profile", obj.partition, obj.data.get("name")),
            "TLS client SSL profile",
        )

        for obj in server_ssl_profiles:
            validator.require_fields(obj, ["name"])
            if obj.effective_state == "absent":
                continue
            if obj.data.get("certificate") is not None:
                validator.validate_named_or_fq_reference(obj.relpath, obj.data.get("certificate"), obj.partition, active_certificate_names, "TLS server SSL certificate")
            if obj.data.get("key") is not None:
                validator.validate_named_or_fq_reference(obj.relpath, obj.data.get("key"), obj.partition, active_key_names, "TLS server SSL key")
            if obj.data.get("chain") is not None:
                validator.validate_named_or_fq_reference(obj.relpath, obj.data.get("chain"), obj.partition, known_cert_like_names, "TLS server SSL chain")
            if obj.data.get("ca_file") is not None:
                validator.validate_fq_or_common_reference(obj.relpath, obj.data.get("ca_file"), known_cert_like_names, "TLS server SSL CA file")

        validator.check_duplicates(
            server_ssl_profiles,
            lambda obj: ("tls_server_ssl_profile", obj.partition, obj.data.get("name")),
            "TLS server SSL profile",
        )
