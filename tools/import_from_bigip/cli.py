from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    import requests  # noqa: F401
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    raise SystemExit(1)

from .connection import BigIPConnection
from .importer import Importer
from .specs import SUPPORTED_TYPES


def main() -> int:
    """CLI entry point for import-from-bigip.

    Purpose:
        Query a live BIG-IP device and import its configuration into
        repository var tree format as YAML files.

    Outputs:
        Returns 0 on success, non-zero on error.
        Writes YAML files to the specified output directory.

    Example:
        F5_HOST=10.1.1.1 F5_PASSWORD=secret python tools/import-from-bigip.py --out /tmp/vars
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Import live BIG-IP configuration into repository var tree format.",
    )
    parser.add_argument("--out", required=True, help="Output directory for generated var files")
    parser.add_argument("--types", nargs="+", choices=sorted(SUPPORTED_TYPES), help="Object types to import (default: all)")
    args = parser.parse_args()

    conn = BigIPConnection.from_env()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    importer = Importer(conn, out_dir)
    results = importer.run(types=args.types)

    total = sum(c for c in results.values() if c > 0)
    errors = sum(1 for c in results.values() if c < 0)
    skipped = sum(1 for c in results.values() if c == 0)

    print(f"\nImport complete: {total} objects written, {skipped} types empty, {errors} errors.")
    return 1 if errors else 0

