from __future__ import annotations

from .tls.core import validate_core


def validate_tls(validator) -> None:
    validate_core(validator)
