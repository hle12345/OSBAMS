"""services/dataset_export.py — versioned, exportable OSBAMS dataset (CSV + JSON).

Dataset schema id: osbams-dataset/0.1 (EXPERIMENTAL).  Documentation: docs/rev2/DATASET_SCHEMA.md.
Two tables:
  * tests.csv    one row per test: battery metadata (anonymized id), protocol/firmware/PCB/calibration versions, results,
                 capacity retention, DCIR, validation and measurement-quality fields
  * samples.csv  one row per stored sample: timestamps, voltage, independent ADC voltage (when recorded), current, power,
                 temperature, flags
The battery id is anonymized with a salted hash so datasets can be shared; the salt stays with the contributor.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from typing import Optional

from db.database import get_connection

DATASET_SCHEMA = "osbams-dataset/0.1"
TEST_PROTOCOL_VERSION = "osbams-test-protocol/0.1"

TEST_COLUMNS = ["dataset_schema", "anon_battery_id", "test_id", "test_type", "test_protocol_version", "started_at", "ended_at",
                "chemistry", "nominal_voltage_v", "rated_capacity_ah", "cell_config",
                "capacity_ah", "energy_wh", "discharge_time_s", "capacity_retention_pct", "retention_label",
                "dcir_mohm", "initial_ocv_v", "voltage_sag_mv", "max_temp_c",
                "ah_ina", "ah_mcu", "ah_pi", "wh_ina", "wh_mcu", "wh_pi", "integration_disagreement_ah_pct",
                "capacity_validation_status", "sample_count", "missing_sample_count",
                "calibration_id", "firmware_version", "pcb_revision", "measurement_quality", "stop_reason"]
SAMPLE_COLUMNS = ["dataset_schema", "anon_battery_id", "test_id", "tick_ms", "voltage_v", "voltage_adc_v", "current_a", "power_w",
                  "temp_c", "flags"]
RETENTION_LABEL = "Capacity retention vs rated (not validated SOH)"


def anonymize(osbams_id: str, salt: str) -> str:
    if not salt:
        raise ValueError("a non-empty salt is required to anonymize battery ids")
    return "anon-" + hashlib.sha256(f"{salt}|{osbams_id}".encode()).hexdigest()[:12]


def _num(v, scale=1.0):
    return "" if v is None else round(v * scale, 6)


def export_dataset(out_dir: str, salt: str, battery_ids: Optional[list] = None) -> dict:
    """Write tests.csv, samples.csv and dataset.json (manifest) into out_dir. Returns counts."""
    os.makedirs(out_dir, exist_ok=True)
    conn = get_connection()
    try:
        q = "SELECT * FROM batteries" + ("" if battery_ids is None else f" WHERE battery_id IN ({','.join('?' * len(battery_ids))})")
        batteries = [dict(r) for r in conn.execute(q, battery_ids or [])]
        n_tests = n_samples = 0
        with open(os.path.join(out_dir, "tests.csv"), "w", newline="") as ft, \
                open(os.path.join(out_dir, "samples.csv"), "w", newline="") as fs:
            wt, ws = csv.writer(ft), csv.writer(fs)
            wt.writerow(TEST_COLUMNS)
            ws.writerow(SAMPLE_COLUMNS)
            for b in batteries:
                anon = anonymize(b["osbams_id"], salt)
                for t in conn.execute("SELECT * FROM tests WHERE battery_id=? ORDER BY test_id", (b["battery_id"],)):
                    t = dict(t)
                    n_tests += 1
                    wt.writerow([DATASET_SCHEMA, anon, t["test_id"], t.get("test_type"), TEST_PROTOCOL_VERSION, t.get("started_at"),
                                 t.get("ended_at"), b.get("chemistry"), _num(b.get("nominal_voltage")), _num(b.get("capacity_rated_ah")),
                                 b.get("cell_config"), _num(t.get("capacity_ah")), _num(t.get("energy_wh")),
                                 _num(t.get("discharge_time_s")), _num(t.get("capacity_retention_pct")),
                                 RETENTION_LABEL if t.get("capacity_retention_pct") is not None else "",
                                 _num(t.get("internal_resistance_mohm")), _num(t.get("initial_ocv_v")), t.get("voltage_sag_mv") or "",
                                 _num(t.get("max_temp_c")), _num(t.get("ah_ina")), _num(t.get("ah_mcu")), _num(t.get("ah_pi")),
                                 _num(t.get("wh_ina")), _num(t.get("wh_mcu")), _num(t.get("wh_pi")),
                                 _num(t.get("integration_disagreement_ah_pct")), t.get("capacity_validation_status") or "",
                                 t.get("sample_count") or "", t.get("missing_sample_count") or "", t.get("calibration_id") or "",
                                 t.get("firmware_version") or "", t.get("pcb_revision") or "", t.get("measurement_quality") or "",
                                 t.get("stop_reason") or ""])
                    for r in conn.execute("SELECT * FROM readings WHERE test_id=? ORDER BY tick_ms", (t["test_id"],)):
                        r = dict(r)
                        n_samples += 1
                        ws.writerow([DATASET_SCHEMA, anon, t["test_id"], r["tick_ms"], r["voltage_mv"] / 1000.0,
                                     _num(r.get("voltage_adc_mv"), 0.001), r["current_ma"] / 1000.0, r["power_mw"] / 1000.0,
                                     r["temp_c10"] / 10.0, r.get("flags") if r.get("flags") is not None else ""])
    finally:
        conn.close()
    manifest = {"schema": DATASET_SCHEMA, "test_protocol_version": TEST_PROTOCOL_VERSION, "tests": n_tests, "samples": n_samples,
                "batteries": len(batteries), "experimental": True,
                "notes": ["thresholds and quality limits are provisional", "capacity retention is not validated SOH",
                          "empty cell = not available (never zero)"],
                "test_columns": TEST_COLUMNS, "sample_columns": SAMPLE_COLUMNS}
    with open(os.path.join(out_dir, "dataset.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return {"tests": n_tests, "samples": n_samples, "batteries": len(batteries)}
