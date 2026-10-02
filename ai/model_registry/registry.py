"""Model registry: an append-only JSON-lines record of every trained model and what it was trained on.  The registry never
asserts that a model is validated; `limitations` and `synthetic` make the standing of each entry explicit."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

REGISTRY_SCHEMA = "osbams-model-registry/0.1"
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "registry.jsonl")
REQUIRED = ("model_id", "model_type", "dataset_version", "feature_version", "training_battery_count", "chemistry_coverage",
            "test_protocol", "validation_metrics", "limitations", "synthetic")


def record(entry: dict, path: Optional[str] = None) -> dict:
    miss = [k for k in REQUIRED if k not in entry]
    if miss:
        raise ValueError(f"registry entry missing {miss}")
    e = dict(entry, schema=REGISTRY_SCHEMA, registered_at=datetime.now().isoformat(timespec="seconds"))
    with open(path or DEFAULT_PATH, "a") as f:
        f.write(json.dumps(e, sort_keys=True) + "\n")
    return e


def load(path: Optional[str] = None) -> list:
    p = path or DEFAULT_PATH
    return [] if not os.path.exists(p) else [json.loads(x) for x in open(p) if x.strip()]
