from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DriftEntry:
    object_type: str
    name: str
    partition: str = "Common"
    status: str = ""
    detail: str = ""


@dataclass
class DriftReport:
    missing_from_git: list[DriftEntry] = field(default_factory=list)
    missing_from_device: list[DriftEntry] = field(default_factory=list)
    value_drift: list[DriftEntry] = field(default_factory=list)
    unchanged: int = 0

    def summarize(self) -> str:
        lines = []
        if self.missing_from_git:
            lines.append(f"\nON DEVICE BUT NOT IN GIT ({len(self.missing_from_git)}):")
            for e in self.missing_from_git:
                lines.append(f"  [{e.object_type}] /{e.partition}/{e.name}")
        if self.missing_from_device:
            lines.append(f"\nIN GIT BUT NOT ON DEVICE ({len(self.missing_from_device)}):")
            for e in self.missing_from_device:
                lines.append(f"  [{e.object_type}] /{e.partition}/{e.name}")
        if self.value_drift:
            lines.append(f"\nVALUE DRIFT ({len(self.value_drift)}):")
            for e in self.value_drift:
                lines.append(f"  [{e.object_type}] /{e.partition}/{e.name}: {e.detail}")
        lines.append(
            f"\nSummary: {len(self.missing_from_git)} not in git, "
            f"{len(self.missing_from_device)} not on device, "
            f"{len(self.value_drift)} drifted, {self.unchanged} unchanged."
        )
        return "\n".join(lines)

    @property
    def has_drift(self) -> bool:
        return bool(self.missing_from_git or self.missing_from_device or self.value_drift)
