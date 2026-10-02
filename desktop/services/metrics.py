"""services/metrics.py — capacity retention, repeatability statistics and the standardized DCIR pulse calculation."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Sequence

RETENTION_NOTE = ("Capacity retention vs the rated capacity entered in the battery profile. This is an experimental "
                  "pack-level assessment and is not equivalent to a validated cell-level state-of-health estimate.")


def capacity_retention_pct(measured_ah: float, rated_ah: Optional[float]) -> Optional[float]:
    """measured usable capacity / rated capacity * 100 (None when no rated capacity is known)."""
    if not rated_ah or rated_ah <= 0:
        return None
    return measured_ah / rated_ah * 100.0


@dataclass(frozen=True)
class Repeatability:
    n: int
    mean: float
    sample_std: float
    cv_pct: float             # sample standard deviation / mean * 100
    max_dev_pct: float        # worst |x_i - mean| / mean * 100  (the "+/- x %" figure)
    spread_pct: float         # (max - min) / mean * 100


def repeatability(values: Sequence[float]) -> Repeatability:
    """Repeatability of the same pack measured under the same conditions (use >= 3 runs)."""
    v = [float(x) for x in values]
    if len(v) < 2:
        raise ValueError("need at least 2 runs")
    mean = sum(v) / len(v)
    if mean == 0:
        raise ValueError("mean is zero")
    sd = math.sqrt(sum((x - mean) ** 2 for x in v) / (len(v) - 1))
    return Repeatability(n=len(v), mean=mean, sample_std=sd, cv_pct=abs(sd / mean) * 100.0,
                         max_dev_pct=max(abs(x - mean) for x in v) / abs(mean) * 100.0,
                         spread_pct=(max(v) - min(v)) / abs(mean) * 100.0)


def dcir_from_pulse(v0: float, i0: float, v1: float, i1: float) -> Optional[float]:
    """R_DCIR in mOhm = (V0 - V1) / (I1 - I0). Returns None when the current step is not positive."""
    di = i1 - i0
    if di <= 1e-9:
        return None
    return (v0 - v1) / di * 1000.0
