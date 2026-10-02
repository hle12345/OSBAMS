"""services/quality.py — measurement-quality report attached to every completed test.

Turns "OSBAMS measured 8.4 Ah" into a traceable result: which calibration was applied, how large the zero-current offset
was, whether the independent measurements agreed, whether samples were missing.  Items that cannot be evaluated (for
example the independent ADC channel under protocol v1, which does not carry it) are listed as NOT AVAILABLE and are not
silently passed.

ALL LIMITS BELOW ARE PROVISIONAL PLACEHOLDERS.  They are to be set from the reference-instrument validation
(docs/rev2/VALIDATION_AND_CALIBRATION_PLAN.md) — do not read them as validated specifications.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional

from services import charge_integration as ci
from services.calibration import CalibrationProfile

PASS = "PASS"
REVIEW = "REVIEW REQUIRED"


@dataclass(frozen=True)
class QualityLimits:
    max_zero_offset_a: float = 0.010
    max_cal_residual_pct: float = 0.5
    max_cal_age_days: float = 90.0
    max_adc_ina_disagreement_v: float = 0.5
    max_missing_fraction: float = 0.001
    max_integration_disagreement_pct: float = ci.DEFAULT_WARN_PCT
    require_adc_crosscheck: bool = False      # becomes True once the firmware reports the ADC channel (protocol v2)


@dataclass
class QualityItem:
    name: str
    value: Optional[float]
    limit: Optional[float]
    unit: str
    ok: Optional[bool]        # None = not available
    note: str = ""


@dataclass
class MeasurementQuality:
    status: str
    calibration_id: Optional[str]
    items: list = field(default_factory=list)
    reasons: list = field(default_factory=list)

    def lines(self) -> list:
        out = [f"Measurement quality: {self.status}", f"Calibration profile: {self.calibration_id or 'NONE'}"]
        for it in self.items:
            val = "not available" if it.value is None else f"{it.value:.4g} {it.unit}".strip()
            flag = "n/a" if it.ok is None else ("ok" if it.ok else "OUT OF LIMIT")
            out.append(f"  {it.name}: {val} [{flag}]" + (f" - {it.note}" if it.note else ""))
        out += [f"  REASON: {r}" for r in self.reasons]
        return out

    def to_dict(self) -> dict:
        return dict(status=self.status, calibration_id=self.calibration_id, reasons=list(self.reasons),
                    items=[dict(name=i.name, value=i.value, limit=i.limit, unit=i.unit, ok=i.ok, note=i.note) for i in self.items])


def assess(calibration: Optional[CalibrationProfile], totals: Optional[Mapping[str, Optional[float]]] = None,
           adc_ina_max_diff_v: Optional[float] = None, total_frames: int = 0, missing_frames: int = 0,
           limits: QualityLimits = QualityLimits()) -> MeasurementQuality:
    items, reasons = [], []

    def add(name, value, limit, unit, ok, note=""):
        items.append(QualityItem(name, value, limit, unit, ok, note))
        if ok is False:
            reasons.append(f"{name} out of limit")

    if calibration is None:
        reasons.append("no calibration profile applied")
        add("Calibration age", None, limits.max_cal_age_days, "days", None, "no calibration")
        add("Zero-current offset", None, limits.max_zero_offset_a, "A", None, "no calibration")
    else:
        age = calibration.age_days
        add("Calibration age", age, limits.max_cal_age_days, "days", age <= limits.max_cal_age_days)
        for label, fit in (("Voltage calibration residual", calibration.voltage), ("Current calibration residual", calibration.current)):
            pct = fit.max_residual_pct
            add(label, pct, limits.max_cal_residual_pct, "%", None if pct is None else pct <= limits.max_cal_residual_pct,
                "" if pct is not None else "no non-zero reference points")
        z = calibration.zero_current_offset_a
        add("Zero-current offset", None if z is None else abs(z), limits.max_zero_offset_a, "A",
            None if z is None else abs(z) <= limits.max_zero_offset_a)
    ok = None if adc_ina_max_diff_v is None else adc_ina_max_diff_v <= limits.max_adc_ina_disagreement_v
    add("ADC vs INA228 maximum disagreement", adc_ina_max_diff_v, limits.max_adc_ina_disagreement_v, "V", ok,
        "independent ADC channel not reported by this firmware/protocol" if ok is None else "")
    if ok is None and limits.require_adc_crosscheck:
        reasons.append("ADC cross-check required but not available")
    if total_frames > 0:
        frac = missing_frames / total_frames
        add("Missing samples", float(missing_frames), None, f"of {total_frames}", frac <= limits.max_missing_fraction,
            f"{frac * 100:.4f} %")
    else:
        add("Missing samples", None, None, "", None, "frame counters not provided")
    if totals:
        ag = ci.compare(totals, limits.max_integration_disagreement_pct)
        add("Integration agreement", ag.max_disagreement_pct, limits.max_integration_disagreement_pct, "%",
            None if ag.status == "INSUFFICIENT" else ag.status == "OK",
            ", ".join(f"{k} {v:.4f} Ah" for k, v in ag.totals.items()))
        if ag.status == ci.WARNING:
            reasons.append(ci.WARNING)
    else:
        add("Integration agreement", None, limits.max_integration_disagreement_pct, "%", None, "no independent totals")
    status = PASS if not reasons and calibration is not None else REVIEW
    return MeasurementQuality(status=status, calibration_id=None if calibration is None else calibration.calibration_id,
                              items=items, reasons=reasons)
