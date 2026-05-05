from __future__ import annotations

import argparse
import json
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

from .checker import DriftChecker
from .connection import BigIPConnection
from .var_tree import VarTreeLoader


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare live BIG-IP state against declared var tree state.")
    parser.add_argument("--types", nargs="+", help="Object types to check (e.g., ltm_nodes ltm_pools)")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    args = parser.parse_args()

    conn = BigIPConnection.from_env()
    loader = VarTreeLoader()
    loader.load()
    if not loader.objects:
        print("No objects found in var trees.")
        return 1

    checker = DriftChecker(conn, loader)
    report = checker.run(types=args.types)

    if args.json:
        print(
            json.dumps(
                {
                    "missing_from_git": [
                        {"type": e.object_type, "name": e.name, "partition": e.partition, "detail": e.detail}
                        for e in report.missing_from_git
                    ],
                    "missing_from_device": [
                        {"type": e.object_type, "name": e.name, "partition": e.partition, "detail": e.detail}
                        for e in report.missing_from_device
                    ],
                    "value_drift": [
                        {"type": e.object_type, "name": e.name, "partition": e.partition, "detail": e.detail}
                        for e in report.value_drift
                    ],
                    "unchanged": report.unchanged,
                },
                indent=2,
            )
        )
    else:
        print(report.summarize())

    return 1 if report.has_drift else 0
