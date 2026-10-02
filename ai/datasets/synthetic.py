"""SYNTHETIC battery records for exercising the AI pipeline when no real data exist.  The numbers come from a simple made-up
relation (resistance rises and capacity falls with an 'age' variable, plus noise).  They are NOT battery physics, NOT measurements
and carry no health meaning.  Rows are labelled measurement_quality=SYNTHETIC."""
from __future__ import annotations

import csv
import random

SYNTHETIC_DATASET_VERSION = "synthetic-0.1"


def generate(n_batteries: int = 40, tests_per_battery: int = 2, seed: int = 0) -> list:
    rng = random.Random(seed)
    out = []
    for b in range(n_batteries):
        age = rng.uniform(0.0, 1.0)
        for t in range(tests_per_battery):
            ret = 100.0 - 55.0 * age + rng.gauss(0, 2)
            dcir = 60.0 + 300.0 * age + rng.gauss(0, 10)
            out.append({"anon_battery_id": f"syn-{b:04d}", "test_id": f"{b}-{t}", "chemistry": "NMC", "measurement_quality": "SYNTHETIC",
                        "target_value": ret,
                        "features": {"capacity_retention_pct": ret, "dcir_mohm": dcir, "voltage_sag_mv": 1000 + 2500 * age + rng.gauss(0, 100),
                                     "temp_rise_c": 5 + 25 * age + rng.gauss(0, 1.5), "delivered_wh": 190 * ret / 100,
                                     "discharge_duration_s": 6000 * ret / 100}})
    return out


def quick_features(records: list) -> list:
    """Quick-test style features derived (synthetically) from the same latent age, for pipeline tests of the quick-test model."""
    out = []
    for r in records:
        f = r["features"]
        out.append(dict(r, features={"dv_di_mohm": f["dcir_mohm"] * 0.9, "immediate_sag_mv": f["voltage_sag_mv"] * 0.4,
                                     "dynamic_resistance_mohm": f["dcir_mohm"]}))
    return out


def write_csv(path: str, records: list) -> None:
    cols = ["anon_battery_id", "test_id", "chemistry", "measurement_quality", "capacity_retention_pct", "dcir_mohm", "voltage_sag_mv",
            "temp_rise_c", "delivered_wh", "discharge_duration_s"]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in records:
            w.writerow([r["anon_battery_id"], r["test_id"], r["chemistry"], r["measurement_quality"]] + [round(r["features"][c], 4) for c in cols[4:]])


if __name__ == "__main__":
    write_csv("synthetic_sample.csv", generate())
