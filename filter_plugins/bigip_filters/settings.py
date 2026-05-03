from __future__ import annotations

from pathlib import Path

import yaml

from .common import deep_merge_dicts


class AnsibleVarLoader(yaml.SafeLoader):
    pass


def construct_ansible_tag(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    raise TypeError(f"Unsupported YAML node type: {type(node)!r}")


AnsibleVarLoader.add_multi_constructor("!", construct_ansible_tag)


def load_settings_hierarchy(source_file, settings_root):
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
