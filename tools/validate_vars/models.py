from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import ROOT


@dataclass(frozen=True)
class TreeSpec:
    name: str
    active_dir: Path
    deletion_dir: Path
    top_key: str
    settings_key: str
    extra_settings_keys: tuple[str, ...] = ()


@dataclass
class LoadedObject:
    tree: TreeSpec
    source_file: Path
    defaults: dict[str, Any]
    data: dict[str, Any]
    from_deletions: bool

    @property
    def relpath(self) -> str:
        return str(self.source_file.relative_to(ROOT))

    @property
    def effective_state(self) -> str:
        if self.from_deletions:
            return "absent"
        return str(self.data.get("state", "present"))

    @property
    def partition(self) -> str:
        return str(self.data.get("partition", self.defaults.get("partition", "Common")))
