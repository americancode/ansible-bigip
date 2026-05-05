from __future__ import annotations

from .network.core import validate_core


def validate_network(validator) -> None:
    validate_core(validator)
