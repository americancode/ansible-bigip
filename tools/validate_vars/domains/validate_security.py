from __future__ import annotations

from .security.core import validate_core


def validate_security(validator) -> None:
    validate_core(validator)
