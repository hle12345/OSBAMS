"""
scoring.py — OSBAMS Reliability Score Engine (v3)

Score components (total = 100):
    Energy retention        25 pts   measured_Wh / rated_Wh
    Capacity retention      20 pts   measured_Ah / rated_Ah
    Thermal behavior        15 pts   temperature rise above ambient
    Voltage sag             15 pts   initial voltage sag under load
    BMS / cutoff behavior   10 pts   did BMS cut off early? clean shutoff?
    Physical condition      10 pts   0-10 score from intake
    Self-discharge           5 pts   optional OCV drop over rest period

Grade bands (from ChatGPT screenshot):
    90-100  A   Strong reuse candidate
    80-89   B   Reuse with normal monitoring
    65-79   C   Limited or lower-power reuse
    50-64   D   Restricted experimental use
    0-49    F   Recycle or engineering review

SOH (from screenshot):
    SOH_Ah       = measured_Ah / rated_Ah * 100
    SOH_Wh       = measured_Wh / rated_Wh * 100
    SOH_combined = 0.4 * SOH_Ah + 0.6 * SOH_Wh   (Wh weighted more)
"""

from dataclasses import dataclass, field
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import SCORE_WEIGHTS, GRADE_BANDS, SOH_AH_WEIGHT, SOH_WH_WEIGHT


# ── Input data class ──────────────────────────────────────────────────────────

@dataclass
class ScoringInputs:
    # Measured (from test)
    measured_ah:           float = 0.0
    measured_wh:           float = 0.0
    max_temp_c:            float = 25.0
    ambient_temp_c:        float = 25.0
    initial_voltage_sag_mv:int   = 0     # mV drop from OCV when load first applied
    bms_cutoff_detected:   bool  = False  # did BMS cut before our voltage limit?
    voltage_cutoff_v:      float = 30.0  # configured cutoff for this test

    # From battery record
    rated_ah:              float = 0.0
    rated_wh:              float = 0.0
    physical_score:        int   = 8     # 0-10 from intake

    # Optional
    self_discharge_mv:     int   = 0     # OCV drop over rest period (0 = not measured)


@dataclass
class ScoringResult:
    # Component scores
    energy_retention_pts:   int = 0
    capacity_retention_pts: int = 0
    thermal_pts:            int = 0
    voltage_sag_pts:        int = 0
    bms_pts:                int = 0
    physical_pts:           int = 0
    self_discharge_pts:     int = 0

    # Totals
    total_score: int = 0
    grade:       str = "—"
    recommendation: str = "—"

    # SOH
    soh_ah_pct:  float = 0.0
    soh_wh_pct:  float = 0.0
    soh_combined:float = 0.0

    breakdown: dict = field(default_factory=dict)

    @classmethod
    def from_inputs(cls, inp: ScoringInputs) -> "ScoringResult":
        r = cls()
        w = SCORE_WEIGHTS

        # ── SOH ──────────────────────────────────────────────────────
        if inp.rated_ah > 0:
            r.soh_ah_pct = round((inp.measured_ah / inp.rated_ah) * 100, 1)
        if inp.rated_wh > 0:
            r.soh_wh_pct = round((inp.measured_wh / inp.rated_wh) * 100, 1)
        r.soh_combined = round(
            SOH_AH_WEIGHT * r.soh_ah_pct + SOH_WH_WEIGHT * r.soh_wh_pct, 1)

        # ── Energy retention (25 pts) ─────────────────────────────────
        eng_ratio = (inp.measured_wh / inp.rated_wh) if inp.rated_wh > 0 else 0.0
        r.energy_retention_pts = min(w["energy_retention"],
                                     int(w["energy_retention"] * min(eng_ratio, 1.0)))

        # ── Capacity retention (20 pts) ───────────────────────────────
        cap_ratio = (inp.measured_ah / inp.rated_ah) if inp.rated_ah > 0 else 0.0
        r.capacity_retention_pts = min(w["capacity_retention"],
                                       int(w["capacity_retention"] * min(cap_ratio, 1.0)))

        # ── Thermal behavior (15 pts) ─────────────────────────────────
        # 0°C rise = 15, 30°C rise = 0 (linear)
        rise = max(0.0, inp.max_temp_c - inp.ambient_temp_c)
        r.thermal_pts = max(0, int(w["thermal_behavior"] * (1.0 - rise / 30.0)))

        # ── Voltage sag (15 pts) ──────────────────────────────────────
        # < 200 mV sag = full 15; > 3000 mV = 0 (linear)
        sag = inp.initial_voltage_sag_mv
        r.voltage_sag_pts = max(0, int(w["voltage_sag"] * (1.0 - sag / 3000.0)))
        r.voltage_sag_pts = min(r.voltage_sag_pts, w["voltage_sag"])

        # ── BMS / cutoff behavior (10 pts) ────────────────────────────
        if inp.bms_cutoff_detected:
            # BMS cut before our voltage limit — partial credit
            r.bms_pts = w["bms_cutoff"] // 2
        else:
            r.bms_pts = w["bms_cutoff"]

        # ── Physical condition (10 pts) ───────────────────────────────
        r.physical_pts = int(w["physical_condition"] * inp.physical_score / 10.0)

        # ── Self-discharge (5 pts) ────────────────────────────────────
        if inp.self_discharge_mv > 0:
            # < 100 mV/day = full; > 1000 mV/day = 0
            r.self_discharge_pts = max(0, int(
                w["self_discharge"] * (1.0 - inp.self_discharge_mv / 1000.0)))
        else:
            r.self_discharge_pts = w["self_discharge"] // 2  # not measured: neutral

        # ── Total ─────────────────────────────────────────────────────
        r.total_score = (r.energy_retention_pts + r.capacity_retention_pts +
                         r.thermal_pts + r.voltage_sag_pts + r.bms_pts +
                         r.physical_pts + r.self_discharge_pts)
        r.total_score = max(0, min(100, r.total_score))

        # ── Grade ─────────────────────────────────────────────────────
        for threshold, grade, rec in GRADE_BANDS:
            if r.total_score >= threshold:
                r.grade = grade
                r.recommendation = rec
                break

        r.breakdown = {
            "Energy retention (25)":   r.energy_retention_pts,
            "Capacity retention (20)": r.capacity_retention_pts,
            "Thermal behavior (15)":   r.thermal_pts,
            "Voltage sag (15)":        r.voltage_sag_pts,
            "BMS / cutoff (10)":       r.bms_pts,
            "Physical condition (10)": r.physical_pts,
            "Self-discharge (5)":      r.self_discharge_pts,
        }
        return r


# ── Trapezoidal integrator ────────────────────────────────────────────────────

def trapezoidal_integrate(readings: list[dict]) -> dict:
    """
    Integrate Ah and Wh from raw readings using trapezoidal rule.

    For every adjacent pair of samples:
        Δt = current_tick_ms - previous_tick_ms   (in seconds)
        average_current = (I_previous + I_current) / 2
        average_power   = (P_previous + P_current) / 2
        Ah += average_current × Δt_hours
        Wh += average_power   × Δt_hours

    Returns dict with:
        total_ah, total_wh, min_voltage_mv, max_voltage_mv,
        max_temp_c, initial_voltage_sag_mv, discharge_time_s,
        average_current_a, average_power_w, sample_count,
        bms_cutoff_detected
    """
    if len(readings) < 2:
        return {
            "total_ah": 0.0, "total_wh": 0.0,
            "min_voltage_mv": 0, "max_voltage_mv": 0,
            "max_temp_c": 0.0, "initial_voltage_sag_mv": 0,
            "discharge_time_s": 0.0,
            "average_current_a": 0.0, "average_power_w": 0.0,
            "sample_count": len(readings),
            "bms_cutoff_detected": False,
        }

    total_ah = 0.0
    total_wh = 0.0
    voltages = []
    temps    = []
    currents = []
    powers   = []

    for i in range(1, len(readings)):
        prev = readings[i - 1]
        curr = readings[i]

        dt_ms  = curr["tick_ms"] - prev["tick_ms"]
        dt_s   = dt_ms / 1000.0
        dt_h   = dt_s  / 3600.0

        if dt_h <= 0:
            continue

        # Trapezoidal averages
        avg_i_ma = (abs(prev["current_ma"]) + abs(curr["current_ma"])) / 2.0
        avg_p_mw = (abs(prev["power_mw"])   + abs(curr["power_mw"]))   / 2.0

        total_ah += (avg_i_ma / 1000.0) * dt_h   # mA → A
        total_wh += (avg_p_mw / 1000.0) * dt_h   # mW → W

        voltages.append(curr["voltage_mv"])
        temps.append(curr["temp_c10"] / 10.0)
        currents.append(abs(curr["current_ma"]) / 1000.0)
        powers.append(abs(curr["power_mw"]) / 1000.0)

    first_v  = readings[0]["voltage_mv"]
    second_v = readings[1]["voltage_mv"] if len(readings) > 1 else first_v
    initial_sag = max(0, first_v - second_v)   # mV drop when load applied

    min_v = min(voltages) if voltages else 0
    max_v = max(voltages) if voltages else 0
    max_t = max(temps)    if temps    else 0.0

    t_start = readings[0]["tick_ms"]
    t_end   = readings[-1]["tick_ms"]
    dur_s   = (t_end - t_start) / 1000.0

    avg_i = sum(currents) / len(currents) if currents else 0.0
    avg_p = sum(powers)   / len(powers)   if powers   else 0.0

    # BMS cutoff detection: voltage dropped sharply at the end
    bms_cutoff = False
    if len(voltages) >= 3:
        last_v   = voltages[-1]
        prev_v   = voltages[-3]
        if (prev_v - last_v) > 2000:   # > 2V sudden drop in last 2 samples
            bms_cutoff = True

    return {
        "total_ah":              round(total_ah, 4),
        "total_wh":              round(total_wh, 4),
        "min_voltage_mv":        min_v,
        "max_voltage_mv":        max_v,
        "max_temp_c":            round(max_t, 1),
        "initial_voltage_sag_mv":initial_sag,
        "discharge_time_s":      round(dur_s, 1),
        "average_current_a":     round(avg_i, 4),
        "average_power_w":       round(avg_p, 4),
        "sample_count":          len(readings),
        "bms_cutoff_detected":   bms_cutoff,
    }


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test scoring
    inp = ScoringInputs(
        measured_ah=12.4, measured_wh=446.0,
        rated_ah=15.3, rated_wh=551.0,
        max_temp_c=38.0, ambient_temp_c=25.0,
        initial_voltage_sag_mv=800,
        bms_cutoff_detected=False,
        physical_score=7,
    )
    r = ScoringResult.from_inputs(inp)
    print(f"Score: {r.total_score}  Grade: {r.grade}  Rec: {r.recommendation}")
    print(f"SOH Ah={r.soh_ah_pct:.1f}%  Wh={r.soh_wh_pct:.1f}%  Combined={r.soh_combined:.1f}%")
    print("Breakdown:")
    for k, v in r.breakdown.items():
        print(f"  {k:<30} {v:>3}")

    # Test trapezoidal integration
    fake_readings = [
        {"tick_ms": 0,     "current_ma": 2000, "power_mw": 84000,
         "voltage_mv": 42000, "temp_c10": 250},
        {"tick_ms": 1800000, "current_ma": 2000, "power_mw": 80000,
         "voltage_mv": 40000, "temp_c10": 280},
        {"tick_ms": 3600000, "current_ma": 2000, "power_mw": 76000,
         "voltage_mv": 38000, "temp_c10": 310},
    ]
    stats = trapezoidal_integrate(fake_readings)
    print(f"\nTrapezoidal: Ah={stats['total_ah']:.3f}  Wh={stats['total_wh']:.3f}")
    print(f"  min_v={stats['min_voltage_mv']}  max_t={stats['max_temp_c']}°C")
    print("✓ scoring.py self-test passed")
