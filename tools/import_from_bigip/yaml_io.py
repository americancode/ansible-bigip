from __future__ import annotations

from typing import Any

import yaml


class VarTreeDumper(yaml.Dumper):
    def increase_indent(self, flow: bool = False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


def str_representer(dumper: yaml.Dumper, data: str) -> yaml.Node:
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


VarTreeDumper.add_representer(str, str_representer)
