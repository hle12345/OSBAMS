"""services/calibration.py — two-point-or-more linear calibration of the voltage and current channels.

Philosophy (literature takeaway: "low cost only means something if calibration and limitations are documented"):
calibrate against a reference instrument at known points, BEFORE and OUTSIDE a battery test; never during one.

    corrected = gain * raw + offset          (separately for voltage [V] and current [A])

The profile is stored with its fit residuals, the reference instrument, operator and temperature, so every test can
reference a calibration id.  Nothing here talks to hardware: it works on lists of (reference, raw) pairs.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Iterable, Optional

# Sanity bounds on a fitted gain: a gain far from 1 means a wrong reference value, a swapped channel or a wiring fault,
# not a "calibration".  PROVISIONAL — tighten after the first real calibration runs.
GAIN_MIN, GAIN_MAX = 0.90, 1.10
VOLTAGE_POINTS_V = (30.0, 34.0, 38.0, 42.0, 44.0)          # suggested reference points (see docs/rev2/VALIDATION_AND_CALIBRATION_PLAN.md)
CURRENT_POINTS_A = (0.0, 1.0, 2.0, 5.0, 8.0, 10.0)


class CalibrationError(ValueError):
    pass


@dataclass(frozen=True)
class CalPoint:
    reference: float          # value read from the reference instrument
    raw: float                # value reported by the OSBAMS channel being calibrated


@dataclass(frozen=True)
class CalFit:
    gain: float
    offset: float
    n: int
    rmse: float               # RMS residual after correction, in channel units
    max_abs_residual: float   # worst |corrected - reference|, in channel units
    max_residual_pct: Optional[float]   # worst |residual| as % of the reference (points with |ref| >= 1e-9 only)

    def apply(self, raw: float) -> float:
        return self.gain * raw + self.offset


IDENTITY = CalFit(gain=1.0, offset=0.0, n=0, rmse=0.0, max_abs_residual=0.0, max_residual_pct=None)


def fit_linear(points: Iterable[CalPoint], gain_bounds=(GAIN_MIN, GAIN_MAX)) -> CalFit:
    """Ordinary least squares of reference on raw. Needs >= 2 points with distinct raw values."""
    pts = list(points)
    if len(pts) < 2:
        raise CalibrationError("need at least 2 calibration points")
    n = len(pts)
    mx = sum(p.raw for p in pts) / n
    my = sum(p.reference for p in pts) / n
    sxx = sum((p.raw - mx) ** 2 for p in pts)
    if sxx < 1e-12:
        raise CalibrationError("calibration points must span different raw values")
    gain = sum((p.raw - mx) * (p.reference - my) for p in pts) / sxx
    offset = my - gain * mx
    lo, hi = gain_bounds
    if not (lo <= gain <= hi):
        raise CalibrationError(f"fitted gain {gain:.4f} outside {lo}..{hi}: check the reference values and wiring")
    res = [(gain * p.raw + offset) - p.reference for p in pts]
    rmse = math.sqrt(sum(r * r for r in res) / n)
    pct = [abs(r) / abs(p.reference) * 100.0 for r, p in zip(res, pts) if abs(p.reference) > 1e-9]
    return CalFit(gain=gain, offset=offset, n=n, rmse=rmse, max_abs_residual=max(abs(r) for r in res),
                  max_residual_pct=max(pct) if pct else None)


def residual_table(points: Iterable[CalPoint], fit: CalFit) -> list:
    """Per-point table for the calibration report: reference, raw, corrected, error, error %."""
    rows = []
    for p in points:
        c = fit.apply(p.raw)
        err = c - p.reference
        rows.append(dict(reference=p.reference, raw=p.raw, corrected=c, error=err,
                         error_pct=(err / p.reference * 100.0) if abs(p.reference) > 1e-9 else None))
    return rows


def zero_offset(raw_samples_at_zero: Iterable[float]) -> tuple:
    """Mean and sample standard deviation of the current channel with NO current flowing."""
    v = list(raw_samples_at_zero)
    if len(v) < 2:
        raise CalibrationError("need at least 2 zero-current samples")
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))
    return m, sd


def make_calibration_id(on: Optional[date] = None, seq: int = 1) -> str:
    return f"CAL-{(on or date.today()).isoformat()}-{seq:02d}"


@dataclass
class CalibrationProfile:
    calibration_id: str
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    voltage: CalFit = IDENTITY
    current: CalFit = IDENTITY
    zero_current_offset_a: Optional[float] = None       # mean raw current with no current flowing
    reference_instrument: str = ""
    operator: str = ""
    temperature_c: Optional[float] = None
    notes: str = ""

    def apply_voltage(self, raw_v: float) -> float:
        return self.voltage.apply(raw_v)

    def apply_current(self, raw_a: float) -> float:
        return self.current.apply(raw_a)

    @property
    def age_days(self) -> float:
        return (datetime.now() - datetime.fromisoformat(self.created)).total_seconds() / 86400.0

    def to_dict(self) -> dict:
        return dict(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, d: dict) -> "CalibrationProfile":
        d = dict(d)
        d["voltage"] = CalFit(**d["voltage"])
        d["current"] = CalFit(**d["current"])
        return cls(**d)

    @classmethod
    def from_json(cls, s: str) -> "CalibrationProfile":
        return cls.from_dict(json.loads(s))
