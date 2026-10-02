"""services/capacity_validation.py — three-way capacity / energy cross-check at test completion.

Three independent results, compared when a test ends:
    1. INA228 hardware accumulators           (protocol v2 fields Q_ina_uAh / E_ina_uWh; NA when unsupported)
    2. STM32 timestamp-based integration       (protocol v2 fields Q_mcu_uAh / E_mcu_uWh)
    3. Raspberry Pi reconstruction             (integrates the stored timestamped samples — available with protocol v1 too)

Like-for-like rule: the device accumulators integrate the device's own (uncalibrated) readings, so the Pi reconstruction used
for the AGREEMENT is made from the RAW samples as received.  The calibrated Pi result is reported separately and is the one
used for capacity retention.  Threshold: PROVISIONAL (default 1 %), configurable, to be set from bench validation.
Missing data is reported as unavailable — never as agreement.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Optional

from services import charge_integration as ci
from services.protocol_v2 import OsbamsSampleV2, SS_ACCUM_INVALID

PROVISIONAL_WARN_PCT = ci.DEFAULT_WARN_PCT
WARNING = ci.WARNING


@dataclass
class TrackerSummary:
    frames: int
    missing_frames: int
    acq_gap: int                       # acquisitions the STM32 made that never produced a frame (acq_count vs frames)
    accumulator_reset: bool            # an accumulator went backwards / ACCUM_INVALID seen
    q_ina_ah: Optional[float]
    q_mcu_ah: Optional[float]
    e_ina_wh: Optional[float]
    e_mcu_wh: Optional[float]
    pi_raw: ci.Integration
    pi_calibrated: Optional[ci.Integration]
    max_adc_ina_diff_v: Optional[float]


class AccumulatorTracker:
    """Feed every received sample (v1 or v2); read the summary at the end of the test."""

    def __init__(self, calibration=None):
        self.cal = calibration
        self._raw, self._cal = [], []
        self._first = None             # first frame carrying device totals
        self._last = None
        self._prev_seq: Optional[int] = None
        self._first_acq: Optional[int] = None
        self._last_acq: Optional[int] = None
        self.frames = self.missing = 0
        self.reset = False
        self._max_diff: Optional[float] = None

    def add(self, s: OsbamsSampleV2) -> None:
        b = s.base
        self.frames += 1
        if self._prev_seq is not None and b.sequence > self._prev_seq + 1:
            self.missing += b.sequence - self._prev_seq - 1
        self._prev_seq = b.sequence
        self._raw.append((b.time_s, b.voltage_v, b.current_a))
        if self.cal is not None:
            self._cal.append((b.time_s, self.cal.apply_voltage(b.voltage_v), self.cal.apply_current(b.current_a)))
        if s.v_adc_mv is not None:
            d = abs(s.v_adc_mv - b.voltage_mv) / 1000.0
            self._max_diff = d if self._max_diff is None else max(self._max_diff, d)
        if s.acq_count is not None:
            if self._first_acq is None:
                self._first_acq = s.acq_count
            self._last_acq = s.acq_count
        if s.sensor_status is not None and s.sensor_status & SS_ACCUM_INVALID:
            self.reset = True
        if s.has_device_totals:
            if self._first is None:
                self._first = s
            elif self._last is not None and any(
                    (getattr(s, n) is not None and getattr(self._last, n) is not None
                     and abs(getattr(s, n)) < abs(getattr(self._last, n)))
                    for n in ("q_ina_uah", "q_mcu_uah", "e_ina_uwh", "e_mcu_uwh")):
                self.reset = True            # |total| decrease => reset/overflow: flag, never silently re-baseline (sign-agnostic: shunt polarity may be negative)
            self._last = s

    def summary(self, gap_s: Optional[float] = None) -> TrackerSummary:
        def delta(name, scale):
            if self._first is None or self._last is None:
                return None
            a, b = getattr(self._first, name), getattr(self._last, name)
            return None if a is None or b is None else abs(b - a) / scale
        acq_gap = 0
        if self._first_acq is not None and self._last_acq is not None:
            acq_gap = max(0, (self._last_acq - self._first_acq + 1) - self.frames)
        return TrackerSummary(
            frames=self.frames, missing_frames=self.missing, acq_gap=acq_gap, accumulator_reset=self.reset,
            q_ina_ah=delta("q_ina_uah", 1e6), q_mcu_ah=delta("q_mcu_uah", 1e6),
            e_ina_wh=delta("e_ina_uwh", 1e6), e_mcu_wh=delta("e_mcu_uwh", 1e6),
            pi_raw=ci.integrate(self._raw, gap_s), pi_calibrated=ci.integrate(self._cal, gap_s) if self._cal else None,
            max_adc_ina_diff_v=self._max_diff)


@dataclass
class CapacityValidation:
    ah: dict                           # {"INA228":..., "STM32":..., "Pi":...}  (None = unavailable)
    wh: dict
    disagreement_ah_pct: Optional[float]
    disagreement_wh_pct: Optional[float]
    status: str                        # "OK" | CAPACITY_VALIDATION_WARNING | "INSUFFICIENT"
    sample_count: int
    missing_sample_count: int
    warn_pct: float
    calibrated_pi_ah: Optional[float] = None
    calibrated_pi_wh: Optional[float] = None
    calibration_id: Optional[str] = None
    firmware_version: Optional[str] = None
    pcb_revision: Optional[str] = None
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)


def validate(summary: TrackerSummary, warn_pct: float = PROVISIONAL_WARN_PCT, calibration_id: Optional[str] = None,
             firmware_version: Optional[str] = None, pcb_revision: Optional[str] = None) -> CapacityValidation:
    ah = {"INA228": summary.q_ina_ah, "STM32": summary.q_mcu_ah, "Pi": summary.pi_raw.ah if summary.frames else None}
    wh = {"INA228": summary.e_ina_wh, "STM32": summary.e_mcu_wh, "Pi": summary.pi_raw.wh if summary.frames else None}
    a, w = ci.compare(ah, warn_pct), ci.compare(wh, warn_pct)
    notes = []
    status = a.status
    if w.status == ci.WARNING or a.status == ci.WARNING:
        status = ci.WARNING
    elif a.status == "INSUFFICIENT" and w.status == "INSUFFICIENT":
        status = "INSUFFICIENT"
        notes.append("only one total available (protocol v1 or accumulators NA): agreement cannot be assessed")
    if summary.accumulator_reset:
        status = ci.WARNING
        notes.append("device accumulator decreased or flagged invalid during the test (reset/overflow)")
    if summary.missing_frames:
        notes.append(f"{summary.missing_frames} frame(s) missing by sequence number")
    if summary.acq_gap:
        notes.append(f"{summary.acq_gap} STM32 acquisition(s) never reached the Pi (acq_count vs frames)")
    return CapacityValidation(
        ah=ah, wh=wh, disagreement_ah_pct=a.max_disagreement_pct, disagreement_wh_pct=w.max_disagreement_pct, status=status,
        sample_count=summary.frames, missing_sample_count=summary.missing_frames, warn_pct=warn_pct,
        calibrated_pi_ah=None if summary.pi_calibrated is None else summary.pi_calibrated.ah,
        calibrated_pi_wh=None if summary.pi_calibrated is None else summary.pi_calibrated.wh,
        calibration_id=calibration_id, firmware_version=firmware_version, pcb_revision=pcb_revision, notes=notes)
