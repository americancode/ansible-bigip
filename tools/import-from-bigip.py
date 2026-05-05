#!/usr/bin/env python3
"""Compatibility shim for import-from-bigip package entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from import_from_bigip.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
