"""services/charge_integration.py — Ah / Wh integration and the three-way cross-check.

Capacity is integrated from the measured current with the ACTUAL time between samples (never a hard-coded period):

    dAh = |I| * dt / 3600        dWh = |V * I| * dt / 3600        (trapezoidal between consecutive samples)

OSBAMS can compute capacity three independent ways during a discharge:
    A. the INA228's own charge / energy accumulators          (needs firmware to report them — protocol v2, see docs)
    B. the STM32, accumulating every measurement it takes      (same)
    C. the Raspberry Pi, integrating the saved timestamped telemetry (available today: this module)
`compare()` reports the disagreement between whatever totals are available.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Optional

DEFAULT_WARN_PCT = 1.0     # PROVISIONAL: choose the real limit after the reference validation (docs/rev2/VALIDATION_AND_CALIBRATION_PLAN.md)
WARNING = "CAPACITY_VALIDATION_WARNING"


@dataclass(frozen=True)
class Integration:
    ah: float
    wh: float
    n_samples: int
    duration_s: float
    max_gap_s: float
    long_gaps: int            # intervals longer than the gap threshold (still integrated across)


def integrate(samples: Iterable[tuple], gap_s: Optional[float] = None) -> Integration:
    """samples: iterable of (t_s, voltage_v, current_a), in time order. Integrates |I| and |V*I|."""
    ah = wh = 0.0
    prev = None
    n = 0
    maxgap = 0.0
    long_gaps = 0
    t0 = tl = None
    for t, v, i in samples:
        n += 1
        if t0 is None:
            t0 = t
        tl = t
        if prev is not None:
            dt = t - prev[0]
            if dt < 0:
                raise ValueError("samples must be in time order")
            maxgap = max(maxgap, dt)
            if gap_s is not None and dt > gap_s:
                long_gaps += 1
            ah += 0.5 * (abs(i) + abs(prev[2])) * dt / 3600.0
            wh += 0.5 * (abs(v * i) + abs(prev[1] * prev[2])) * dt / 3600.0
        prev = (t, v, i)
    return Integration(ah=ah, wh=wh, n_samples=n, duration_s=0.0 if t0 is None else tl - t0,
                       max_gap_s=maxgap, long_gaps=long_gaps)


@dataclass(frozen=True)
class Agreement:
    totals: dict
    max_disagreement_pct: Optional[float]     # (max - min) / mean * 100 over the available totals
    status: str                               # "OK" | WARNING | "INSUFFICIENT" (fewer than 2 totals)
    detail: str = ""


def compare(totals: Mapping[str, Optional[float]], warn_pct: float = DEFAULT_WARN_PCT) -> Agreement:
    """totals: e.g. {"INA228": 8.421, "STM32": 8.417, "Pi": 8.419}; None / missing entries are ignored."""
    have = {k: float(v) for k, v in totals.items() if v is not None}
    if len(have) < 2:
        return Agreement(have, None, "INSUFFICIENT", "need at least two independent totals")
    vals = list(have.values())
    mean = sum(vals) / len(vals)
    if mean <= 0:
        return Agreement(have, None, "INSUFFICIENT", "non-positive total")
    pct = (max(vals) - min(vals)) / mean * 100.0
    status = "OK" if pct <= warn_pct else WARNING
    return Agreement(have, pct, status, f"max disagreement {pct:.3f} % (limit {warn_pct} %)")
