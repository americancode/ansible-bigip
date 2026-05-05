from __future__ import annotations

from .waf.core import validate_core


def validate_waf(validator) -> None:
    validate_core(validator)
