"""services/battery_passport.py — the Battery Passport: one persistent record per battery, built from the database.

Schema id: osbams-passport/0.1  (EXPERIMENTAL; versioned so exports stay comparable).  Persistent id: OSB-000001 style
(older rows keep their original id).  The passport contains identity, nameplate data, every test with the calibration used,
capacity / energy / DCIR / temperature / measurement quality, firmware and PCB revision, and a trend block computed from
repeated tests.  Trends are descriptive only — they are NOT a validated state-of-health.
"""
from __future__ import annotations

import json
from typing import Optional

from db.database import get_connection

PASSPORT_SCHEMA = "osbams-passport/0.1"
NOT_SOH = ("Capacity retention is measured usable capacity / rated capacity; it is not a validated cell-level state of health.")

_BATTERY_FIELDS = ("battery_id", "osbams_id", "intake_date", "source_type", "brand", "manufacturer", "model", "serial_number",
                   "chemistry", "nominal_voltage", "max_charge_voltage", "cutoff_voltage", "capacity_rated_ah",
                   "energy_rated_wh", "cell_config", "series_count", "parallel_count", "connector_type", "profile_key",
                   "connector_condition", "physical_condition", "safety_status", "physical_notes", "passport_notes")
_TEST_FIELDS = ("test_id", "started_at", "ended_at", "test_type", "capacity_ah", "energy_wh", "discharge_time_s", "max_temp_c",
                "min_voltage_mv", "initial_ocv_v", "resting_voltage_after_v", "voltage_sag_mv", "internal_resistance_mohm",
                "rated_capacity_ah", "capacity_retention_pct", "stop_reason", "calibration_id", "firmware_version",
                "pcb_revision", "measurement_quality", "capacity_validation_status", "integration_disagreement_ah_pct",
                "ah_ina", "ah_mcu", "ah_pi", "wh_ina", "wh_mcu", "wh_pi", "sample_count", "missing_sample_count")


def _row(conn, sql, args=()):
    r = conn.execute(sql, args).fetchone()
    return None if r is None else dict(r)


def trend(tests: list) -> dict:
    """Descriptive degradation trend from repeated capacity tests (oldest first): change in capacity and DCIR per test."""
    cap = [t for t in tests if t.get("test_type") != "dcir" and t.get("capacity_ah")]
    out = {"n_capacity_tests": len(cap), "note": NOT_SOH}
    if len(cap) >= 2:
        first, last = cap[0]["capacity_ah"], cap[-1]["capacity_ah"]
        out.update(first_capacity_ah=first, last_capacity_ah=last, capacity_change_pct=(last - first) / first * 100.0)
    dc = [t["internal_resistance_mohm"] for t in tests if t.get("internal_resistance_mohm")]
    if len(dc) >= 2:
        out.update(first_dcir_mohm=dc[0], last_dcir_mohm=dc[-1], dcir_change_pct=(dc[-1] - dc[0]) / dc[0] * 100.0)
    return out


def build_passport(battery_id: int) -> Optional[dict]:
    conn = get_connection()
    try:
        b = _row(conn, "SELECT * FROM batteries WHERE battery_id=?", (battery_id,))
        if b is None:
            return None
        tests = [dict(r) for r in conn.execute("SELECT * FROM tests WHERE battery_id=? ORDER BY test_id ASC", (battery_id,))]
    finally:
        conn.close()
    out_tests = []
    for t in tests:
        rec = {k: t.get(k) for k in _TEST_FIELDS}
        rec["measurement_quality_detail"] = json.loads(t["quality_json"]) if t.get("quality_json") else None
        rec["dcir_conditions"] = json.loads(t["dcir_conditions_json"]) if t.get("dcir_conditions_json") else None
        out_tests.append(rec)
    return {"schema": PASSPORT_SCHEMA, "id": b["osbams_id"],
            "battery": {k: b.get(k) for k in _BATTERY_FIELDS}, "tests": out_tests, "trend": trend(tests),
            "disclaimer": NOT_SOH}
