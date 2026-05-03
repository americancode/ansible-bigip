from __future__ import annotations

from pathlib import Path

import yaml

from .common import deep_merge_dicts


class AnsibleVarLoader(yaml.SafeLoader):
    pass


def construct_ansible_tag(loader, tag_suffix, node):
    """YAML constructor that passes through Ansible-style tags (!) unchanged.

    Purpose:
        Allows the AnsibleVarLoader to parse YAML files that use Ansible-specific
        tags (e.g., !vault, !unsafe) without raising errors, by treating them as
        their underlying scalar/sequence/mapping type.

    Inputs:
        loader (yaml.Loader): The YAML loader instance.
        tag_suffix (str): The tag suffix after the "!" prefix.
        node (yaml.Node): The YAML node being constructed.

    Outputs:
        The constructed Python object (str, list, or dict depending on node type).

    Constraints:
        - Raises TypeError for unsupported node types.
    """
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    raise TypeError(f"Unsupported YAML node type: {type(node)!r}")


AnsibleVarLoader.add_multi_constructor("!", construct_ansible_tag)


def discover_yaml_fragments(root_path):
    """Recursively discover all YAML fragment files under a directory, excluding settings.yml.

    Purpose:
        Used by prep flows to find all var-tree fragment files (e.g., pool definitions,
        virtual server definitions) that should be loaded and aggregated.

    Inputs:
        root_path (str|None): The root directory path to search.

    Outputs:
        list[str]: Sorted list of absolute file paths to YAML files (excluding settings.yml).

    Constraints:
        - Returns empty list if root_path is None, empty, or does not exist.
        - Excludes settings.yml files (those are handled by load_settings_hierarchy).
    """
    if root_path in (None, ""):
        return []

    root_dir = Path(str(root_path))
    if not root_dir.exists():
        return []

    return sorted(
        str(path)
        for path in root_dir.rglob("*.yml")
        if path.is_file() and path.name != "settings.yml"
    )


def load_settings_hierarchy(source_file, settings_root):
    """Load and merge settings.yml files from source_file's directory up to settings_root.

    Purpose:
        Implements hierarchical multi-level settings.yml inheritance. A fragment file
        deep in the tree inherits defaults from settings.yml files at each parent level.

    Inputs:
        source_file (str|None): The path to the fragment file being processed.
        settings_root (str|None): The root directory of the var tree (e.g., vars/ltm).

    Outputs:
        dict: Merged settings dictionary with higher-level settings taking precedence
        (closer to root wins over deeper settings).

    Constraints:
        - Returns {} if either input is None/empty or source_file is outside settings_root.
        - Settings are merged in order from deepest to shallowest (root last, so it wins).
        - Uses AnsibleVarLoader to support Ansible YAML tags.
    """
    if source_file in (None, "") or settings_root in (None, ""):
        return {}

    source_dir = Path(str(source_file)).resolve().parent
    root_dir = Path(str(settings_root)).resolve()

    try:
        source_dir.relative_to(root_dir)
    except ValueError:
        return {}

    chain = []
    current = source_dir
    while True:
        chain.append(current / "settings.yml")
        if current == root_dir:
            break
        if root_dir not in current.parents:
            break
        current = current.parent

    merged = {}
    for settings_path in reversed(chain):
        if not settings_path.exists():
            continue
        payload = yaml.load(settings_path.read_text(), Loader=AnsibleVarLoader)
        if isinstance(payload, dict):
            merged = deep_merge_dicts(merged, payload)
    return merged


def aggregate_settings_fragments(
    include_results,
    settings_root,
    fragment_var_name,
    collection_key,
    defaults_key=None,
    absent=False,
):
    """Aggregate YAML fragment payloads and merge each with its directory-level defaults.

    Purpose:
        Central prep helper that takes Ansible include_vars results, extracts the fragment
        objects, merges each with directory defaults from settings.yml, and returns a flat
        list ready for runtime tasks.

    Inputs:
        include_results (list[dict]|None): Output from Ansible include_vars tasks; each dict
            should have an "item" (source file path) and "ansible_facts".
        settings_root (str): The root of the var tree for settings hierarchy lookups.
        fragment_var_name (str): The Ansible facts key that holds the fragment payload
            (e.g., "ltm_pools").
        collection_key (str): The key within the payload that holds the list of objects
            (e.g., "pools").
        defaults_key (str|None): Key within the merged settings to use as defaults
            (e.g., "pool_defaults").
        absent (bool): If True, force state: absent on every aggregated object (for deletion
            classification).

    Outputs:
        list[dict]: Flat list of merged objects, each inheriting directory defaults and
        optionally marked as absent.

    Constraints:
        - Skips non-dict results and non-dict items.
        - Directory defaults are merged first, then the fragment item's fields override them.
    """
    aggregated = []

    for result in include_results or []:
        if not isinstance(result, dict):
            continue

        source_file = result.get("item")
        ansible_facts = result.get("ansible_facts") or {}
        fragment_payload = ansible_facts.get(fragment_var_name) or {}
        fragment_items = fragment_payload.get(collection_key) or []
        settings_payload = load_settings_hierarchy(source_file, settings_root)
        directory_defaults = (
            settings_payload.get(defaults_key, {}) if defaults_key else {}
        )

        for item in fragment_items:
            if not isinstance(item, dict):
                continue
            merged = deep_merge_dicts(directory_defaults, item)
            if absent:
                merged = deep_merge_dicts(merged, {"state": "absent"})
            aggregated.append(merged)

    return aggregated
