from __future__ import annotations

from typing import Any

import yaml


class AnsibleVarLoader(yaml.SafeLoader):
    """YAML loader that accepts Ansible-style custom tags."""


def construct_ansible_tag(loader: AnsibleVarLoader, tag_suffix: str, node: yaml.Node) -> Any:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    raise TypeError(f"Unsupported YAML node type: {type(node)!r}")


AnsibleVarLoader.add_multi_constructor("!", construct_ansible_tag)
