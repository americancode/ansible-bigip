from __future__ import annotations

from .ha.core import validate_core


def validate_ha(validator) -> None:
    validate_core(validator)
