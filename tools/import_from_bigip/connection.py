from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class BigIPConnection:
    host: str
    username: str
    password: str
    port: int = 443

    @property
    def base_url(self) -> str:
        return f"https://{self.host}:{self.port}/mgmt/tm"

    @classmethod
    def from_env(cls) -> "BigIPConnection":
        host = os.environ.get("F5_HOST")
        if not host:
            print("ERROR: F5_HOST environment variable is required.", file=sys.stderr)
            sys.exit(1)
        password = os.environ.get("F5_PASSWORD")
        if not password:
            print("ERROR: F5_PASSWORD environment variable is required.", file=sys.stderr)
            sys.exit(1)
        return cls(
            host=host,
            username=os.environ.get("F5_USERNAME") or os.environ.get("F5_USER", "admin"),
            password=password,
            port=int(os.environ.get("F5_SERVER_PORT") or os.environ.get("F5_PORT", "443")),
        )

    def get_all(self, uri: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/{uri}"
        params = {"$top": 1000}
        items: list[dict[str, Any]] = []

        while url:
            resp = requests.get(url, auth=(self.username, self.password), params=params, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            items.extend(data.get("items", []))
            url = data.get("nextSelfLink")
            params = {}

        return items
