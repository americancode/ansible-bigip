from __future__ import annotations

from .bootstrap.core import validate_core


def validate_bootstrap(validator) -> None:
    validate_core(validator)
