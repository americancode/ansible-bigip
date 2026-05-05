#!/usr/bin/env python3
"""Compatibility shim for drift-check package entrypoint."""

from __future__ import annotations

from tools.drift_check.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
