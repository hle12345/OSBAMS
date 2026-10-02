"""Rule-based, non-ML health triage baseline — EXPERIMENTAL / RESEARCH STAGE.

Outputs one of REUSE_CANDIDATE / MONITOR / RETEST_REQUIRED / RECYCLE_CANDIDATE with REASON CODES.  Every threshold is PROVISIONAL
and configurable: none has been validated against reference-instrument data or a labelled battery set.  This is a screening aid,
not a safety certification and not a state-of-health measurement.  Missing inputs or a non-PASS measurement quality can only
produce RETEST_REQUIRED — never a favourable outcome.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

REUSE, MONITOR, RETEST, RECYCLE = "REUSE_CANDIDATE", "MONITOR", "RETEST_REQUIRED", "RECYCLE_CANDIDATE"
THRESHOLDS_STATUS = "PROVISIONAL"


@dataclass(frozen=True)
class Thresholds:
    reuse_min_retention_pct: float = 80.0
    recycle_max_retention_pct: float = 50.0
    reuse_max_dcir_mohm: float = 150.0          # placeholder for a ~36 V pack; depends strongly on pack size
    recycle_min_dcir_mohm: float = 400.0
    reuse_max_sag_mv: float = 2500.0
    reuse_max_temp_rise_c: float = 15.0
    recycle_min_temp_rise_c: float = 30.0
    min_discharge_duration_s: float = 600.0     # a very short discharge means the capacity figure is not representative
    require_quality_pass: bool = True
    status: str = THRESHOLDS_STATUS


@dataclass
class Assessment:
    outcome: str
    reasons: list = field(default_factory=list)
    thresholds_status: str = THRESHOLDS_STATUS
    disclaimer: str = "Experimental screening aid; thresholds provisional; not a validated state-of-health."


REQUIRED = ("capacity_retention_pct", "dcir_mohm")


def assess(features: dict, measurement_quality: Optional[str] = "PASS", th: Thresholds = Thresholds()) -> Assessment:
    f = features
    missing = [k for k in REQUIRED if f.get(k) is None]
    if missing:
        return Assessment(RETEST, [f"MISSING_{k.upper()}" for k in missing])
    reasons = []
    if th.require_quality_pass and measurement_quality != "PASS":
        reasons.append("MEASUREMENT_QUALITY_NOT_PASS" if measurement_quality else "MEASUREMENT_QUALITY_UNKNOWN")
    d = f.get("discharge_duration_s")
    if d is not None and d < th.min_discharge_duration_s:
        reasons.append("DISCHARGE_TOO_SHORT")
    if reasons:
        return Assessment(RETEST, reasons)
    ret, dcir = f["capacity_retention_pct"], f["dcir_mohm"]
    rise, sag = f.get("temp_rise_c"), f.get("voltage_sag_mv")
    rec = []
    if ret < th.recycle_max_retention_pct: rec.append("RETENTION_VERY_LOW")
    if dcir > th.recycle_min_dcir_mohm: rec.append("DCIR_VERY_HIGH")
    if rise is not None and rise > th.recycle_min_temp_rise_c: rec.append("TEMP_RISE_EXCESSIVE")
    if rec:
        return Assessment(RECYCLE, rec)
    mon = []
    if ret < th.reuse_min_retention_pct: mon.append("RETENTION_BELOW_REUSE")
    if dcir > th.reuse_max_dcir_mohm: mon.append("DCIR_ABOVE_REUSE")
    if sag is not None and sag > th.reuse_max_sag_mv: mon.append("VOLTAGE_SAG_HIGH")
    if rise is not None and rise > th.reuse_max_temp_rise_c: mon.append("TEMP_RISE_HIGH")
    if mon:
        return Assessment(MONITOR, mon)
    ok = ["RETENTION_OK", "DCIR_OK"]
    for name, val in (("VOLTAGE_SAG", sag), ("TEMP_RISE", rise)):
        ok.append(f"{name}_OK" if val is not None else f"{name}_NOT_AVAILABLE")
    return Assessment(REUSE, ok)
