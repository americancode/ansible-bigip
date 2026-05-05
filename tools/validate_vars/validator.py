from __future__ import annotations

import sys
import ipaddress
from pathlib import Path
import re
from typing import Any

import yaml


from .ansible_yaml import AnsibleVarLoader
from .constants import ROOT, VARS_DIR, ensure_repo_root_on_path
from .models import LoadedObject, TreeSpec
from .tree_specs import build_tree_specs

ensure_repo_root_on_path()

from filter_plugins.bigip_var_filters import (
    compile_gtm_wide_ip_intent,
    compile_ltm_virtual_server_intent,
    load_settings_hierarchy,
    normalize_gtm_pool,
    normalize_ltm_pool,
)



from .domains.validate_common import validate_common as domain_validate_common
from .domains.validate_bootstrap import validate_bootstrap as domain_validate_bootstrap
from .domains.validate_network import validate_network as domain_validate_network
from .domains.validate_system import validate_system as domain_validate_system
from .domains.validate_ha import validate_ha as domain_validate_ha
from .domains.validate_tls import validate_tls as domain_validate_tls
from .domains.validate_ltm import validate_ltm as domain_validate_ltm
from .domains.validate_gtm import validate_gtm as domain_validate_gtm
from .domains.validate_security import validate_security as domain_validate_security
from .domains.validate_waf import validate_waf as domain_validate_waf
from .domains.validate_apm import validate_apm as domain_validate_apm

class Validator:
    """Orchestrates offline validation of all var trees against the repo's field model.

    Purpose:
        Loads all object trees defined in tree_specs, runs domain-specific
        validation (bootstrap, network, system, ha, tls, ltm, gtm, security),
        and collects errors for any violations.

    Attributes:
        errors (list[str]): Accumulated error messages.
        objects (dict): Loaded objects keyed by tree name (e.g., "ltm_pools").
        settings_cache (dict): Cache of loaded settings.yml payloads.
        tree_specs (list[TreeSpec]): All registered var tree specifications.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.objects: dict[str, list[LoadedObject]] = {}
        self.settings_cache: dict[Path, dict[str, Any]] = {}
        self.tree_specs = build_tree_specs()

    def run(self) -> int:
        """Execute the full validation suite and return an exit code.

        Purpose:
            Entry point for the validation tool. Loads all object trees, then runs
            domain-specific validation (bootstrap, network, system, ha, tls, ltm, gtm,
            security, waf, apm). Prints errors to stderr.

        Returns:
            int: 0 if validation passed, 1 if any errors were found.
        """
        self.validate_common()

        for spec in self.tree_specs:
            self.load_tree(spec, from_deletions=False)
            self.load_tree(spec, from_deletions=True)

        self.validate_bootstrap()
        self.validate_network()
        self.validate_system()
        self.validate_ha()
        self.validate_tls()
        self.validate_ltm()
        self.validate_gtm()
        self.validate_security()
        self.validate_waf()
        self.validate_apm()

        if self.errors:
            for error in self.errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"Validation failed with {len(self.errors)} error(s).", file=sys.stderr)
            return 1

        print("Validation passed.")
        return 0

    def validate_common(self) -> None:
        domain_validate_common(self)

    def validate_bootstrap(self) -> None:
        domain_validate_bootstrap(self)

    def load_tree(self, spec: TreeSpec, *, from_deletions: bool) -> None:
        """Load and register objects from a single var tree directory.

        Purpose:
            Walks the active or deletions directory for a TreeSpec, loads each
            YAML file, and registers valid objects into self.objects.

        Inputs:
            spec (TreeSpec): The tree specification to load.
            from_deletions (bool): If True, load from the deletions directory.

        Side effects:
            - Registers LoadedObject instances into self.objects[spec.name].
            - Validates settings.yml files and object structure.
        """
        base_dir = spec.deletion_dir if from_deletions else spec.active_dir
        if not base_dir.exists():
            return

        for path in sorted(base_dir.rglob("*.yml")):
            if path.name == "settings.yml":
                self.validate_settings_file(path, spec)
                continue

            payload = self.load_yaml(path)
            if not isinstance(payload, dict):
                self.error(path, "must contain a mapping")
                continue

            unknown = sorted(set(payload) - {spec.top_key})
            if unknown:
                self.error(path, f"contains unsupported keys: {', '.join(unknown)}")

            entries = payload.get(spec.top_key)
            if entries is None:
                self.error(path, f"must define `{spec.top_key}`")
                continue
            if not isinstance(entries, list):
                self.error(path, f"`{spec.top_key}` must be a list")
                continue

            if spec.name in {"ltm_inline_virtual_server_intents"}:
                hierarchy_root = (VARS_DIR / "ltm" / "deletions" / "intents") if from_deletions else (VARS_DIR / "ltm" / "intents")
                hierarchy_payload = self.load_settings_hierarchy_payload(path, hierarchy_root)
                defaults = hierarchy_payload.get(spec.settings_key, {}) if isinstance(hierarchy_payload.get(spec.settings_key, {}), dict) else {}
            else:
                defaults = self.load_directory_defaults(path.parent / "settings.yml", spec)
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    self.error(path, f"`{spec.top_key}[{index}]` must be a mapping")
                    continue
                if from_deletions and "state" in entry and entry["state"] != "absent":
                    self.error(path, f"`{spec.top_key}[{index}]` in deletions may only use `state: absent`")
                self.objects.setdefault(spec.name, []).append(
                    LoadedObject(
                        tree=spec,
                        source_file=path,
                        defaults=defaults,
                        data=entry,
                        from_deletions=from_deletions,
                    )
                )

    def validate_settings_file(self, path: Path, spec: TreeSpec) -> None:
        payload = self.load_yaml(path)
        if not isinstance(payload, dict):
            self.error(path, "must contain a mapping")
            return

        allowed_keys = {spec.settings_key, *spec.extra_settings_keys}
        unknown = sorted(set(payload) - allowed_keys)
        if unknown:
            self.error(path, f"contains unsupported keys: {', '.join(unknown)}")

        defaults = payload.get(spec.settings_key)
        if defaults is not None and not isinstance(defaults, dict):
            self.error(path, f"`{spec.settings_key}` must be a mapping")

        # Guard against hanging settings files: the settings file should apply to at least
        # one object fragment either as a direct sibling or anywhere below this directory.
        has_direct_object_sibling = any(
            candidate.is_file()
            and candidate.suffix == ".yml"
            and candidate.name != "settings.yml"
            for candidate in path.parent.iterdir()
        )
        has_object_descendant = any(
            candidate.is_file()
            and candidate.suffix == ".yml"
            and candidate.name != "settings.yml"
            for candidate in path.parent.rglob("*.yml")
        )
        if not has_direct_object_sibling and not has_object_descendant:
            self.error(
                path,
                "is hanging: no direct object-file siblings and no object-file descendants in this subtree",
            )

    def load_directory_defaults(self, path: Path, spec: TreeSpec) -> dict[str, Any]:
        if not path.exists():
            return {}
        payload = self.load_yaml(path)
        if not isinstance(payload, dict):
            return {}
        defaults = payload.get(spec.settings_key, {})
        return defaults if isinstance(defaults, dict) else {}

    def load_settings_payload(self, path: Path) -> dict[str, Any]:
        if path in self.settings_cache:
            return self.settings_cache[path]
        if not path.exists():
            self.settings_cache[path] = {}
            return {}
        payload = self.load_yaml(path)
        if not isinstance(payload, dict):
            self.settings_cache[path] = {}
            return {}
        self.settings_cache[path] = payload
        return payload

    def load_settings_hierarchy_payload(self, source_file: Path, root_dir: Path) -> dict[str, Any]:
        cache_key = Path(str(root_dir)) / f".hierarchy::{source_file.resolve()}"
        if cache_key in self.settings_cache:
            return self.settings_cache[cache_key]
        payload = load_settings_hierarchy(str(source_file), str(root_dir))
        payload = payload if isinstance(payload, dict) else {}
        self.settings_cache[cache_key] = payload
        return payload

    def validate_network(self) -> None:
        domain_validate_network(self)

    def validate_system(self) -> None:
        domain_validate_system(self)

    def validate_ha(self) -> None:
        domain_validate_ha(self)

    def validate_tls(self) -> None:
        domain_validate_tls(self)

    def validate_ltm(self) -> None:
        domain_validate_ltm(self)

    def validate_ltm_pool_members(
        self,
        source: str,
        pool_name: Any,
        pool_partition: str,
        members: Any,
        active_node_names: set[str],
    ) -> None:
        if members is None:
            return
        if not isinstance(members, list):
            self.error(source, f"LTM pool `{pool_name}` members must be a list")
            return

        for idx, member in enumerate(members):
            if not isinstance(member, dict):
                self.error(source, f"LTM pool `{pool_name}` member {idx} must be a mapping")
                continue
            self.require_fields(member, ["port"], source, f"LTM pool `{pool_name}` member {idx}")
            if not member.get("host") and not member.get("address") and not member.get("fqdn"):
                self.error(source, f"LTM pool `{pool_name}` member {idx} must define one of `host`, `address`, or `fqdn`")
            member_name = member.get("name")
            if member_name:
                fq_node = self.fq_name(str(member.get("partition", pool_partition)), str(member_name))
                if fq_node not in active_node_names:
                    self.error(source, f"LTM pool `{pool_name}` member `{member_name}` references undefined node `{fq_node}`")

    def validate_gtm(self) -> None:
        domain_validate_gtm(self)

    def validate_security(self) -> None:
        domain_validate_security(self)

    def validate_afm_rule_endpoint(
        self,
        endpoint: dict[str, Any],
        source: str,
        rule_name: Any,
        kind: str,
        default_partition: str,
        active_address_list_names: set[str],
    ) -> None:
        address_lists = endpoint.get("address_lists")
        if address_lists is not None:
            if not isinstance(address_lists, list):
                self.error(source, f"AFM rule `{rule_name}` `{kind}.address_lists` must be a list")
            else:
                for al_ref in address_lists:
                    if isinstance(al_ref, str):
                        fq_al = al_ref if al_ref.startswith("/") else self.fq_name(default_partition, al_ref)
                        if fq_al not in active_address_list_names:
                            self.error(source, f"AFM rule `{rule_name}` `{kind}` references undefined address list `{fq_al}`")
        port_lists = endpoint.get("port_lists")
        if port_lists is not None and not isinstance(port_lists, list):
            self.error(source, f"AFM rule `{rule_name}` `{kind}.port_lists` must be a list")
        addresses = endpoint.get("addresses")
        if addresses is not None and not isinstance(addresses, list):
            self.error(source, f"AFM rule `{rule_name}` `{kind}.addresses` must be a list")

    def validate_waf(self) -> None:
        domain_validate_waf(self)

    def validate_apm(self) -> None:
        domain_validate_apm(self)

    @staticmethod
    def _topology_record_id(obj: LoadedObject) -> str:
        source = obj.data.get("source", [])
        destination = obj.data.get("destination", [])
        return f"source={source} destination={destination}"

    def validate_topology_members(self, members: list, source: str, context: str) -> None:
        allowed_keys = {"continent", "country", "datacenter", "subnet", "isp", "region", "pool", "negate"}
        for idx, member in enumerate(members):
            if not isinstance(member, dict):
                self.error(source, f"{context} member {idx} must be a mapping")
                continue
            location_keys = {"continent", "country", "datacenter", "subnet", "isp", "region", "pool"}
            used_location_keys = set(member) & location_keys
            if not used_location_keys and "negate" not in member:
                self.error(source, f"{context} member {idx} must define at least one of: {', '.join(sorted(location_keys))}")
            unsupported = set(member) - allowed_keys
            if unsupported:
                self.error(source, f"{context} member {idx} contains unsupported keys: {', '.join(sorted(unsupported))}")

    def validate_gtm_pool_members(
        self,
        *,
        source: str,
        pool_name: Any,
        pool_partition: str,
        members: Any,
        active_server_names: set[str],
        active_monitor_names: set[str],
        active_ltm_virtual_servers: dict[str, dict[str, Any]],
    ) -> None:
        if members is None:
            return
        if not isinstance(members, list):
            self.error(source, f"GTM pool `{pool_name}` members must be a list")
            return
        if not members:
            self.error(source, f"GTM pool `{pool_name}` must define a non-empty `members` list")
            return

        for member_index, member in enumerate(members):
            if not isinstance(member, dict):
                self.error(source, f"GTM pool `{pool_name}` member {member_index} must be a mapping")
                continue
            self.require_fields(member, ["server", "virtual_server"], source, f"GTM member {member_index}")
            self.validate_gtm_member_ltm_reference(
                source=source,
                pool_name=pool_name,
                member_index=member_index,
                pool_partition=pool_partition,
                member=member,
                active_ltm_virtual_servers=active_ltm_virtual_servers,
            )
            if member.get("state") != "absent":
                self.require_fields(member, ["address", "port"], source, f"GTM member {member_index}")
            server_partition = str(member.get("partition", pool_partition))
            server_name = member.get("server")
            if server_name is not None:
                fq_server = self.fq_name(server_partition, str(server_name))
                if fq_server not in active_server_names:
                    self.error(source, f"GTM member `{server_name}` references undefined server `{fq_server}`")
            for monitor in member.get("monitors", []) or []:
                self.validate_monitor_reference(
                    source=source,
                    reference=monitor,
                    known_monitors=active_monitor_names,
                    kind="GTM member monitor",
                )

    def validate_gtm_member_ltm_reference(
        self,
        *,
        source: str,
        pool_name: Any,
        member_index: int,
        pool_partition: str,
        member: dict[str, Any],
        active_ltm_virtual_servers: dict[str, dict[str, Any]],
    ) -> None:
        if member.get("address") not in (None, "") and member.get("port") not in (None, ""):
            return

        ltm_name = member.get("ltm_virtual_server", member.get("virtual_server"))
        if ltm_name in (None, ""):
            return

        ltm_partition = str(member.get("ltm_partition", member.get("partition", pool_partition)))
        fq_ltm_virtual = ltm_name if isinstance(ltm_name, str) and ltm_name.startswith("/") else self.fq_name(ltm_partition, str(ltm_name))
        if fq_ltm_virtual not in active_ltm_virtual_servers:
            self.error(
                source,
                f"GTM pool `{pool_name}` member {member_index} cannot resolve repo-known LTM virtual `{fq_ltm_virtual}`",
            )

    def build_ltm_virtual_server_lookup(self, virtual_servers: list[LoadedObject]) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for obj in virtual_servers:
            if obj.effective_state == "absent":
                continue
            name = obj.data.get("name")
            destination = obj.data.get("destination")
            destination_port = obj.data.get("destination_port")
            if name in (None, "") or destination in (None, "") or destination_port in (None, ""):
                continue
            lookup[self.fq_name(obj.partition, str(name))] = {
                "destination": destination,
                "destination_port": destination_port,
            }
        for obj in self.objects.get("ltm_inline_virtual_server_intents", []):
            if obj.effective_state == "absent":
                continue
            settings_payload = self.load_settings_hierarchy_payload(obj.source_file, VARS_DIR / "ltm" / "intents")
            compiled_service = compile_ltm_virtual_server_intent(
                obj.data,
                settings_payload.get("ltm_pool_defaults", {}),
                settings_payload.get("ltm_member_defaults", {}),
                settings_payload.get("ltm_monitor_sets", {}),
            )
            virtual_server = compiled_service.get("virtual_server", {})
            if not isinstance(virtual_server, dict):
                continue
            name = virtual_server.get("name")
            destination = virtual_server.get("destination")
            destination_port = virtual_server.get("destination_port")
            partition = str(virtual_server.get("partition", obj.partition))
            if name in (None, "") or destination in (None, "") or destination_port in (None, ""):
                continue
            lookup[self.fq_name(partition, str(name))] = {
                "destination": destination,
                "destination_port": destination_port,
            }
        return lookup

    def validate_monitor_reference(
        self,
        *,
        source: str,
        reference: Any,
        known_monitors: set[str],
        kind: str,
    ) -> None:
        if not isinstance(reference, str):
            self.error(source, f"{kind} reference must be a string")
            return
        if not reference.startswith("/"):
            self.error(source, f"{kind} reference `{reference}` must be fully qualified, for example `/Common/name`")
            return
        partition, _, name = reference.strip("/").partition("/")
        if not partition or not name:
            self.error(source, f"{kind} reference `{reference}` is not a valid fully-qualified object name")
            return
        if partition != "Common" and reference not in known_monitors:
            self.error(source, f"{kind} reference `{reference}` does not match a declared custom monitor")
        if partition == "Common" and reference in known_monitors:
            return

    def validate_named_or_fq_reference(
        self,
        source: str,
        reference: Any,
        default_partition: str,
        known_objects: set[str],
        kind: str,
    ) -> None:
        """Validate a cross-object reference by name or fully-qualified path.

        Purpose:
            Validates that a reference string matches a declared object in the known set.
            Supports both short names (converted to FQ format) and FQ references (e.g., "/Common/pool1").

        Inputs:
            source (str): The source file/line for error messages.
            reference (Any): The reference value to validate (should be a string).
            default_partition (str): Partition to use for short-name resolution.
            known_objects (set[str]): Set of valid FQ object names to match against.
            kind (str): Type name for error messages (e.g., "pool", "profile").

        Side effects:
            Adds validation error to self.errors if reference is invalid.
        """
        if not isinstance(reference, str):
            self.error(source, f"{kind} reference must be a string")
            return
        fq_reference = reference if reference.startswith("/") else self.fq_name(default_partition, reference)
        if fq_reference not in known_objects:
            self.error(source, f"{kind} reference `{reference}` does not match a declared object")

    def validate_profile_reference(
        self,
        *,
        source: str,
        reference: Any,
        default_partition: str,
        known_profiles: set[str],
        kind: str,
    ) -> None:
        builtin_profile_names = {
            "tcp",
            "udp",
            "fastL4",
            "fasthttp",
            "http",
            "http2",
            "oneconnect",
            "clientssl",
            "serverssl",
        }
        if not isinstance(reference, str):
            self.error(source, f"{kind} reference must be a string")
            return
        if reference.startswith("/Common/"):
            return
        fq_reference = reference if reference.startswith("/") else self.fq_name(default_partition, reference)
        if reference in builtin_profile_names:
            return
        if fq_reference not in known_profiles:
            self.error(source, f"{kind} reference `{reference}` does not match a declared custom profile or a `/Common/...` built-in profile")

    def validate_fq_or_common_reference(
        self,
        source: str,
        reference: Any,
        known_objects: set[str],
        kind: str,
    ) -> None:
        if not isinstance(reference, str):
            self.error(source, f"{kind} reference must be a string")
            return
        if not reference.startswith("/"):
            self.error(source, f"{kind} reference `{reference}` must be fully qualified, for example `/Common/name`")
            return
        if reference.startswith("/Common/") and reference not in known_objects:
            return
        if reference not in known_objects:
            self.error(source, f"{kind} reference `{reference}` does not match a declared object")

    def check_duplicates(
        self,
        objects: list[LoadedObject],
        key_func,
        label: str,
    ) -> None:
        """Detect duplicate object definitions across the var tree.

        Purpose:
            Ensures no two objects in the same tree share the same identity
            (e.g., same name + partition).

        Inputs:
            objects (list[LoadedObject]): Objects to check.
            key_func (callable): Function that takes a LoadedObject and returns
                a tuple key (e.g., (type, partition, name)).
            label (str): Human-readable label for error messages.

        Side effects:
            Calls self.error() for each duplicate found.
        """
        seen: dict[tuple[Any, ...], list[LoadedObject]] = {}
        for obj in objects:
            key = key_func(obj)
            if any(part is None for part in key):
                continue
            seen.setdefault(key, []).append(obj)

        for key, dupes in seen.items():
            if len(dupes) < 2:
                continue

            selector_sets = [
                self.validate_target_selectors(
                    obj,
                    label=f"{label} `{key[1:]}`",
                    allow_absent=True,
                )
                for obj in dupes
            ]

            if any(not target_hosts and not target_groups for target_hosts, target_groups in selector_sets):
                self.error(dupes[1].relpath, f"{label} `{key[1:]}` duplicates {dupes[0].relpath}")
                continue

            if any(target_groups for _, target_groups in selector_sets):
                self.error(
                    dupes[1].relpath,
                    f"{label} `{key[1:]}` has multiple declarations using `target_groups`; use disjoint `target_hosts` instead",
                )
                continue

            seen_hosts: dict[str, LoadedObject] = {}
            for obj, (target_hosts, _) in zip(dupes, selector_sets):
                for host in target_hosts:
                    if host in seen_hosts:
                        self.error(
                            obj.relpath,
                            f"{label} `{key[1:]}` targets host `{host}` more than once; first declared in {seen_hosts[host].relpath}",
                        )
                    else:
                        seen_hosts[host] = obj

    def require_fields(
        self,
        obj: LoadedObject | dict[str, Any],
        fields: list[str],
        source: str | None = None,
        label: str | None = None,
    ) -> None:
        """Check that required fields are present and non-empty in an object.

        Purpose:
            Fails validation if any required field is missing, None, or empty string.

        Inputs:
            obj (LoadedObject | dict): The object to check.
            fields (list[str]): List of required field names.
            source (str|None): Override source path for error messages.
            label (str|None): Override label for error messages.

        Side effects:
            Calls self.error() for each missing field.
        """
        data = obj.data if isinstance(obj, LoadedObject) else obj
        source_ref = obj.relpath if isinstance(obj, LoadedObject) else (source or "<unknown>")
        prefix = label or "object"
        for field in fields:
            if data.get(field) in (None, ""):
                self.error(source_ref, f"{prefix} must define `{field}`")

    def validate_target_selectors(
        self,
        obj: LoadedObject,
        *,
        label: str,
        require_single_host: bool = False,
        allow_absent: bool = False,
    ) -> tuple[set[str], set[str]]:
        """Validate `target_hosts` / `target_groups` selectors on a scoped system object.

        Purpose:
            System-domain objects can be targeted to explicit inventory hosts or
            inventory groups. This helper validates selector presence and shape so
            offline validation can reject unsafe or ambiguous declarations before
            runtime filtering happens.

        Inputs:
            obj (LoadedObject): The scoped object being validated.
            label (str): Human-readable label for error messages.
            require_single_host (bool): When true, require exactly one host target
                and forbid `target_groups`.

        Outputs:
            tuple[set[str], set[str]]: Normalized host and group selector sets.
        """
        target_hosts_raw = obj.data.get("target_hosts")
        target_groups_raw = obj.data.get("target_groups")

        target_hosts: set[str] = set()
        target_groups: set[str] = set()

        if target_hosts_raw is not None:
            if not isinstance(target_hosts_raw, list) or not target_hosts_raw:
                self.error(obj.relpath, f"{label} `target_hosts` must be a non-empty list when defined")
            else:
                for idx, host in enumerate(target_hosts_raw):
                    if not isinstance(host, str) or not host:
                        self.error(obj.relpath, f"{label} `target_hosts[{idx}]` must be a non-empty string")
                    else:
                        if host in target_hosts:
                            self.error(obj.relpath, f"{label} duplicates `target_hosts` entry `{host}`")
                        target_hosts.add(host)

        if target_groups_raw is not None:
            if not isinstance(target_groups_raw, list) or not target_groups_raw:
                self.error(obj.relpath, f"{label} `target_groups` must be a non-empty list when defined")
            else:
                for idx, group in enumerate(target_groups_raw):
                    if not isinstance(group, str) or not group:
                        self.error(obj.relpath, f"{label} `target_groups[{idx}]` must be a non-empty string")
                    else:
                        if group in target_groups:
                            self.error(obj.relpath, f"{label} duplicates `target_groups` entry `{group}`")
                        target_groups.add(group)

        if not allow_absent and not target_hosts and not target_groups:
            self.error(obj.relpath, f"{label} must define at least one of `target_hosts` or `target_groups`")

        if require_single_host:
            if target_groups:
                self.error(obj.relpath, f"{label} must not define `target_groups`; use exactly one `target_hosts` entry")
            if len(target_hosts) != 1:
                self.error(obj.relpath, f"{label} must define exactly one `target_hosts` entry")

        return target_hosts, target_groups

    def check_targeted_identity_collisions(
        self,
        objects: list[LoadedObject],
        *,
        identity_func,
        label: str,
    ) -> None:
        """Reject ambiguous targeted declarations that could affect the same BIG-IP.

        Purpose:
            Allows one logical object identity to appear more than once only when
            validation can prove the declarations are disjoint by explicit
            `target_hosts`. If any declaration for the same identity uses
            `target_groups`, validation rejects multiple declarations because group
            overlap cannot be proven offline.
        """
        grouped: dict[tuple[Any, ...], list[tuple[LoadedObject, set[str], set[str]]]] = {}
        for obj in objects:
            if any(part is None for part in identity_func(obj)):
                continue
            target_hosts, target_groups = self.validate_target_selectors(obj, label=f"{label} `{identity_func(obj)[1:]}`")
            grouped.setdefault(identity_func(obj), []).append((obj, target_hosts, target_groups))

        for identity, scoped_objects in grouped.items():
            if len(scoped_objects) < 2:
                continue
            if any(target_groups for _, _, target_groups in scoped_objects):
                conflict_obj = scoped_objects[1][0]
                self.error(
                    conflict_obj.relpath,
                    f"{label} `{identity[1:]}` has multiple declarations while using `target_groups`; use disjoint `target_hosts` for per-device variants",
                )
                continue

            seen_hosts: dict[str, LoadedObject] = {}
            for obj, target_hosts, _ in scoped_objects:
                for host in target_hosts:
                    if host in seen_hosts:
                        self.error(
                            obj.relpath,
                            f"{label} `{identity[1:]}` targets host `{host}` more than once; first declared in {seen_hosts[host].relpath}",
                        )
                    else:
                        seen_hosts[host] = obj

    def fq_name(self, partition: str, name: str) -> str:
        return f"/{partition}/{name}"

    def normalize_pool_reference(self, reference: str, default_partition: str) -> str:
        if reference.startswith("/"):
            return reference
        return self.fq_name(default_partition, reference)

    def fq_gtm_pool_name(self, partition: str, record_type: str, name: str) -> str:
        return f"/{partition}/{record_type}/{name}"

    def normalize_gtm_pool_reference(self, reference: str, default_partition: str, record_type: str) -> str:
        if reference.startswith("/"):
            parts = reference.strip("/").split("/", 2)
            if len(parts) == 3:
                return reference
            if len(parts) == 2:
                return f"/{parts[0]}/{record_type}/{parts[1]}"
            return f"/{default_partition}/{record_type}/{reference.strip('/')}"
        return self.fq_gtm_pool_name(default_partition, record_type, reference)

    def is_inline_gtm_pool(self, pool: dict[str, Any]) -> bool:
        return "members" in pool or "monitors" in pool or "default_monitors" in pool

    def load_yaml(self, path: Path) -> Any:
        try:
            with path.open("r", encoding="utf-8") as handle:
                return yaml.load(handle, Loader=AnsibleVarLoader) or {}
        except yaml.YAMLError as exc:
            self.error(path, f"failed to parse YAML: {exc}")
            return {}
        except OSError as exc:
            self.error(path, f"failed to read file: {exc}")
            return {}

    def error(self, source: Path | str, message: str) -> None:
        rel = str(source.relative_to(ROOT)) if isinstance(source, Path) else source
        self.errors.append(f"{rel}: {message}")

    def validate_ip_like(self, source: Path | str, value: Any, label: str) -> None:
        if not isinstance(value, str):
            self.error(source, f"{label} must be a string")
            return
        if value == "management-ip":
            return
        try:
            ipaddress.ip_address(value)
        except ValueError:
            self.error(source, f"{label} must be a valid IPv4 or IPv6 address")

    def normalize_route_domain_id(self, value: Any) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return None

    def extract_route_domain_id(self, value: Any) -> int | None:
        if not isinstance(value, str):
            return None
        match = re.search(r"%(\d+)$", value)
        if match is None:
            return None
        return int(match.group(1))

    def is_ip_address(self, value: str) -> bool:
        try:
            ipaddress.ip_address(value)
        except ValueError:
            return False
        return True
