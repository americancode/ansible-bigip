from __future__ import annotations

from typing import Any

from .specs import IMPORT_SPECS, ImportSpec


class ImporterSpecialized:
    """Mixin for type-specific import handlers used by Importer."""

    def _import_waf_server_technologies(self, spec: ImportSpec) -> int:
        policies = self.conn.get_all(spec.endpoint)
        if not policies:
            return 0

        objects: list[dict[str, Any]] = []
        for policy in policies:
            policy_name = policy.get("name")
            if not policy_name:
                continue
            partition = policy.get("partition", "Common")
            tech_ref = policy.get("serverTechnologyReference", {})
            tech_link = tech_ref.get("link") if isinstance(tech_ref, dict) else None
            if not tech_link:
                continue
            try:
                technologies = self.conn.get_all(tech_link.split("/mgmt/tm/")[-1])
            except Exception:
                continue

            for technology in technologies:
                tech_name = technology.get("name")
                if not tech_name:
                    continue
                obj = {
                    "name": tech_name.split("/")[-1] if "/" in str(tech_name) else tech_name,
                    "policy_name": policy_name.split("/")[-1] if "/" in str(policy_name) else policy_name,
                }
                if partition != "Common":
                    obj["partition"] = partition
                objects.append(obj)

        return self._write_import_objects("waf_server_technologies", spec, objects)

    def _import_apm_sso_configs(self, spec: ImportSpec) -> int:
        items = self.conn.get_all(spec.endpoint)
        if not items:
            return 0

        objects: list[dict[str, Any]] = []
        for item in items:
            obj = self._transform_apm_sso_config(item)
            if obj:
                objects.append(obj)

        return self._write_import_objects("apm_sso_configs", spec, objects)

    def _import_apm_policy_nodes(self, spec: ImportSpec) -> int:
        policies = self.conn.get_all(spec.endpoint)
        if not policies:
            return 0

        objects: list[dict[str, Any]] = []
        for policy in policies:
            policy_name = policy.get("name")
            if not policy_name:
                continue
            partition = policy.get("partition") or policy.get("tmPartition") or "Common"
            items = policy.get("items", [])
            if not isinstance(items, list):
                continue

            for item in items:
                if not isinstance(item, dict):
                    continue
                node_name = item.get("name")
                if not node_name:
                    continue
                obj = {
                    "name": node_name.split("/")[-1] if "/" in str(node_name) else node_name,
                    "policy": policy_name.split("/")[-1] if "/" in str(policy_name) else policy_name,
                }
                node_type = item.get("type") or item.get("itemType") or item.get("item_type")
                if node_type:
                    obj["type"] = node_type
                properties = self._extract_apm_policy_node_properties(item)
                if properties:
                    obj["properties"] = properties
                if partition != "Common":
                    obj["partition"] = partition
                objects.append(obj)

        return self._write_import_objects("apm_policy_nodes", spec, objects)

    def _import_gtm_topology_records(self, spec: ImportSpec) -> int:
        records = self.conn.get_all(spec.endpoint)
        if not records:
            return 0

        objects: list[dict[str, Any]] = []
        for record in records:
            source = self._normalize_topology_side(record.get("source"))
            destination = self._normalize_topology_side(record.get("destination"))
            if not source or not destination:
                continue
            obj: dict[str, Any] = {
                "source": source,
                "destination": destination,
            }
            if record.get("weight") not in (None, ""):
                obj["weight"] = self._normalize_value("weight", record.get("weight"), spec)
            partition = record.get("partition", "Common")
            if partition != "Common":
                obj["partition"] = partition
            objects.append(obj)

        return self._write_import_objects("gtm_topology_records", spec, objects)
