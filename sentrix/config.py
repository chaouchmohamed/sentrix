"""Loads config/sentrix.yaml. Every rule/correlator/responder imports this. No magic numbers elsewhere (FR-22)."""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path

import yaml

_DEFAULT = Path(__file__).resolve().parent.parent / "config" / "sentrix.yaml"


@lru_cache(maxsize=1)
def load_config(path: str | None = None) -> dict:
    cfg_path = Path(path or os.environ.get("SENTRIX_CONFIG", _DEFAULT))
    with cfg_path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get(path: str, default=None):
    """Dotted lookup: get('detection.r01_brute_force.threshold')."""
    node = load_config()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return default
        node = node[part]
    return node

