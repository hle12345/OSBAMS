"""Feature definitions (version osbams-features/0.1) — EXPERIMENTAL.

Two feature groups:
  * test-level   : from a completed full-discharge test row (dataset tests.csv): retention, DCIR, sag, temperature, Wh, duration
  * quick-test   : from a short OCV -> small step -> larger step -> recovery sequence (docs/rev2/QUICK_HEALTH_TEST_RESEARCH.md)
A missing quantity is None (never 0).  Features describe measurements; they are not health claims.
"""
from __future__ import annotations

import csv
from typing import Iterable, Optional, Sequence

FEATURE_VERSION = "osbams-features/0.1"

TEST_FEATURES = ["capacity_retention_pct", "dcir_mohm", "voltage_sag_mv", "temp_rise_c", "delivered_wh", "discharge_duration_s"]
QUICK_FEATURES = ["ocv_v", "dv_di_mohm", "immediate_sag_mv", "recovery_slope_mv_per_s", "dynamic_resistance_mohm", "temp_c",
                  "response_time_ms"]


def _f(x) -> Optional[float]:
    if x is None or x == "":
        return None
    return float(x)


def from_test_row(row: dict, temp_rise_c: Optional[float] = None) -> dict:
    """row: one dict from dataset tests.csv (or the tests table).  temp_rise_c comes from samples if available."""
    return {
        "capacity_retention_pct": _f(row.get("capacity_retention_pct")),
        "dcir_mohm": _f(row.get("dcir_mohm", row.get("internal_resistance_mohm"))),
        "voltage_sag_mv": _f(row.get("voltage_sag_mv")),
        "temp_rise_c": temp_rise_c,
        "delivered_wh": _f(row.get("energy_wh")),
        "discharge_duration_s": _f(row.get("discharge_time_s")),
    }


def temp_rise_from_samples(samples: Sequence[dict]) -> Optional[float]:
    """max(temp) - first temp over a samples.csv slice for one test; None if no temperature."""
    t = [_f(s.get("temp_c")) for s in samples]
    t = [x for x in t if x is not None]
    return None if len(t) < 2 else max(t) - t[0]


def load_test_features(tests_csv: str, samples_csv: Optional[str] = None) -> list:
    """-> [{anon_battery_id, test_id, chemistry, quality, features{...}}] from an exported dataset directory's files."""
    rises = {}
    if samples_csv:
        by = {}
        for s in csv.DictReader(open(samples_csv)):
            by.setdefault((s["anon_battery_id"], s["test_id"]), []).append(s)
        rises = {k: temp_rise_from_samples(v) for k, v in by.items()}
    out = []
    for r in csv.DictReader(open(tests_csv)):
        out.append({"anon_battery_id": r["anon_battery_id"], "test_id": r["test_id"], "chemistry": r.get("chemistry"),
                    "measurement_quality": r.get("measurement_quality") or None,
                    "features": from_test_row(r, rises.get((r["anon_battery_id"], r["test_id"])))})
    return out


def quick_test_features(ocv_v: Optional[float], small: Optional[dict], large: Optional[dict], recovery: Optional[Sequence] = None,
                        temp_c: Optional[float] = None) -> dict:
    """small/large: {'i_a','v_loaded_v','v_immediate_v','t_response_ms'} for each load step; recovery: [(t_s, v_v), ...] after the
    large step is released.  dv_di = (v_small - v_large)/(i_large - i_small): the slope between the two steps (mOhm)."""
    out = {k: None for k in QUICK_FEATURES}
    out["ocv_v"], out["temp_c"] = ocv_v, temp_c
    if small and large and large["i_a"] > small["i_a"]:
        out["dv_di_mohm"] = (small["v_loaded_v"] - large["v_loaded_v"]) / (large["i_a"] - small["i_a"]) * 1000.0
    if ocv_v is not None and large and large.get("v_immediate_v") is not None:
        out["immediate_sag_mv"] = (ocv_v - large["v_immediate_v"]) * 1000.0
    if ocv_v is not None and large and large["i_a"] > 0:
        out["dynamic_resistance_mohm"] = (ocv_v - large["v_loaded_v"]) / large["i_a"] * 1000.0
    if large and large.get("t_response_ms") is not None:
        out["response_time_ms"] = float(large["t_response_ms"])
    if recovery and len(recovery) >= 2:
        (t0, v0), (t1, v1) = recovery[0], recovery[-1]
        if t1 > t0:
            out["recovery_slope_mv_per_s"] = (v1 - v0) / (t1 - t0) * 1000.0
    return out


def to_vector(features: dict, names: Iterable[str]) -> Optional[list]:
    """Model input row, or None if any requested feature is unavailable (models never impute silently)."""
    v = [features.get(n) for n in names]
    return None if any(x is None for x in v) else v
