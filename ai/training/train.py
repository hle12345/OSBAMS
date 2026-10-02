"""Training pipeline for explainable regressors — EXPERIMENTAL.  Trains ONLY when the data qualifies:
  * labels must come from full-discharge ground truth (capacity retention measured with a PASS measurement quality), and
  * at least `min_batteries` distinct batteries are present (default 30; provisional), and
  * the split is by battery identity (no leakage).
Synthetic data is accepted only with allow_synthetic=True (pipeline testing); the registry entry is then marked synthetic and
must never be cited as a health result."""
from __future__ import annotations

import uuid
from typing import Optional, Sequence

from ai.evaluation.split import group_split, regression_metrics
from ai.features.extract import FEATURE_VERSION, to_vector
from ai.models import zoo
from ai.model_registry import registry

MIN_BATTERIES_PROVISIONAL = 30


class InsufficientData(RuntimeError):
    pass


def train(records: Sequence[dict], feature_names: Sequence[str], target: str = "capacity_retention_pct", model_type: str = "linear",
          dataset_version: str = "unknown", test_protocol: str = "unknown", min_batteries: int = MIN_BATTERIES_PROVISIONAL,
          allow_synthetic: bool = False, synthetic: bool = False, seed: int = 0, registry_path: Optional[str] = None):
    """records: [{anon_battery_id, chemistry, measurement_quality, features{...}, target_value}] -> (model, registry entry)."""
    if synthetic and not allow_synthetic:
        raise InsufficientData("dataset is synthetic; pass allow_synthetic=True for pipeline testing only")
    rows = []
    for r in records:
        x = to_vector(r["features"], feature_names)
        y = r.get("target_value")
        if x is None or y is None:
            continue
        if not synthetic and r.get("measurement_quality") != "PASS":
            continue
        rows.append((r["anon_battery_id"], r.get("chemistry") or "unknown", x, y))
    groups = [g for g, *_ in rows]
    n_bat = len(set(groups))
    if n_bat < min_batteries:
        raise InsufficientData(f"{n_bat} usable batteries < required {min_batteries}: not enough validated/labelled data to train")
    tr, te = group_split(groups, seed=seed)
    model = zoo.make(model_type, seed)
    model.fit([rows[i][2] for i in tr], [rows[i][3] for i in tr])
    yt = [rows[i][3] for i in te]
    metrics = regression_metrics(yt, list(model.predict([rows[i][2] for i in te])))
    entry = registry.record({
        "model_id": f"{model_type}-{uuid.uuid4().hex[:8]}", "model_type": model_type, "target": target,
        "dataset_version": dataset_version, "feature_version": FEATURE_VERSION, "features": list(feature_names),
        "training_battery_count": len({groups[i] for i in tr}), "test_battery_count": len({groups[i] for i in te}),
        "chemistry_coverage": sorted({rows[i][1] for i in tr}), "test_protocol": test_protocol,
        "validation_metrics": metrics, "explanation": zoo.explain(model, feature_names), "synthetic": synthetic,
        "limitations": ["experimental / research stage", "not a validated state-of-health", "split by battery identity, single split",
                        "valid only inside the chemistry and feature range seen in training"]
                       + (["SYNTHETIC DATA: pipeline test only, no health meaning"] if synthetic else [])},
        registry_path)
    return model, entry
