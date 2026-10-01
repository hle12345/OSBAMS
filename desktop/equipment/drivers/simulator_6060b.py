"""
equipment/drivers/simulator_6060b.py — simulated 6060B + simulated battery.

Enforces the SAME 60 V / 60 A / 300 W envelope as the real instrument (same
capability model), and models what a real load would do if the envelope were
exceeded mid-discharge (input trips off, flag raised).

Scenarios = pack (12/24/36/42/48/60 V class) x condition (healthy, degraded,
high_resistance, cell_bms_fault, overtemp, comm_loss), plus the Rev.1-era
short names (normal, degraded, hot, ...) kept for the demo-data tooling.
No pack above 60 V exists in this simulator by construction.
"""

import math
from typing import Optional

from equipment import capability as cap
from equipment.drivers.base import ElectronicLoad, LoadStatus

# ── Packs (all inside the 3-60 V envelope) ───────────────────────────────────
PACKS = {
    "12v":          dict(label="12 V (3S NMC)",         start_v=12.6, cutoff_v=9.0,  rated_ah=5.0,  current_a=2.0),
    "24v":          dict(label="24 V (6S NMC)",         start_v=25.2, cutoff_v=18.0, rated_ah=10.0, current_a=3.0),
    "36v_5p2ah":    dict(label="36 V 5.2 Ah (Ninebot NEB1002)", start_v=42.0, cutoff_v=30.0, rated_ah=5.2,  current_a=1.0),
    "36v_15p3ah":   dict(label="36 V 15.3 Ah (Ninebot NEE1006-M)", start_v=42.0, cutoff_v=31.0, rated_ah=15.3, current_a=3.0),
    "42v_full":     dict(label="42 V fully charged (12.8 Ah)", start_v=42.0, cutoff_v=30.0, rated_ah=12.8, current_a=2.5),
    "48v":          dict(label="48 V (13S NMC)",        start_v=54.6, cutoff_v=39.0, rated_ah=10.0, current_a=4.0),
    "60v_boundary": dict(label="60 V boundary case",    start_v=60.0, cutoff_v=42.0, rated_ah=5.0,  current_a=4.0),
}

# soh, per-cell R (mohm), temp rise, fault
HEALTH = {
    "healthy":         dict(soh=0.92, r_cell_mohm=25,  temp_rise=8.0,  fault=None),
    "degraded":        dict(soh=0.65, r_cell_mohm=55,  temp_rise=16.0, fault=None),
    "high_resistance": dict(soh=0.72, r_cell_mohm=150, temp_rise=22.0, fault=None),
    "cell_bms_fault":  dict(soh=0.60, r_cell_mohm=70,  temp_rise=14.0, fault="bms"),
    "overtemp":        dict(soh=0.82, r_cell_mohm=40,  temp_rise=32.0, fault=None),
    "comm_loss":       dict(soh=0.75, r_cell_mohm=40,  temp_rise=8.0,  fault="comm"),
}


def _series_cells(start_v: float) -> int:
    return max(1, round(start_v / 4.2))


def _build_matrix() -> dict:
    out = {}
    for pk, p in PACKS.items():
        for hk, h in HEALTH.items():
            r_pack = (_series_cells(p["start_v"]) * h["r_cell_mohm"] / 1000.0) * (10.0 / p["rated_ah"])
            out[f"{pk}_{hk}"] = dict(
                rated_ah=p["rated_ah"], soh=h["soh"], start_v=p["start_v"],
                cutoff_v=p["cutoff_v"], current_a=p["current_a"],
                temp_start=25.0, temp_rise=h["temp_rise"],
                sag_v=round(r_pack * p["current_a"], 3), fault=h["fault"],
                label=f"{p['label']} — {hk}")
    return out


def _legacy(**kw):
    kw.setdefault("fault", None)
    kw.setdefault("label", "36 V 15.3 Ah (legacy scenario)")
    return kw


# Rev.1-era short names, all 36 V / 15.3 Ah at 3 A (7.14 A is the 42 V limit).
LEGACY_SCENARIOS = {
    "normal":          _legacy(rated_ah=15.3, soh=0.88, start_v=42.0, cutoff_v=31.0, current_a=3.0, temp_start=25.0, temp_rise=10.0, sag_v=1.2),
    "degraded":        _legacy(rated_ah=15.3, soh=0.65, start_v=41.5, cutoff_v=31.0, current_a=3.0, temp_start=25.0, temp_rise=16.0, sag_v=2.8),
    "hot":             _legacy(rated_ah=15.3, soh=0.80, start_v=41.8, cutoff_v=31.0, current_a=3.0, temp_start=26.0, temp_rise=28.0, sag_v=1.5),
    "weak":            _legacy(rated_ah=15.3, soh=0.45, start_v=40.0, cutoff_v=31.0, current_a=3.0, temp_start=25.0, temp_rise=12.0, sag_v=5.0),
    "cold":            _legacy(rated_ah=15.3, soh=0.70, start_v=40.5, cutoff_v=31.0, current_a=3.0, temp_start=5.0,  temp_rise=6.0,  sag_v=3.5),
    "high_resistance": _legacy(rated_ah=15.3, soh=0.72, start_v=41.0, cutoff_v=31.0, current_a=3.0, temp_start=26.0, temp_rise=22.0, sag_v=7.5),
    "cell_imbalance":  _legacy(rated_ah=15.3, soh=0.60, start_v=41.8, cutoff_v=31.0, current_a=3.0, temp_start=25.0, temp_rise=14.0, sag_v=4.0, fault="bms"),
    "overtemp":        _legacy(rated_ah=15.3, soh=0.82, start_v=41.9, cutoff_v=31.0, current_a=3.0, temp_start=30.0, temp_rise=32.0, sag_v=1.8),
    "fail":            _legacy(rated_ah=15.3, soh=0.75, start_v=41.9, cutoff_v=31.0, current_a=3.0, temp_start=25.0, temp_rise=8.0,  sag_v=1.8, fault="comm"),
}

SCENARIOS = {**LEGACY_SCENARIOS, **_build_matrix()}


class Simulator6060B(ElectronicLoad):
    """
    Simulated load + battery. Two uses:
      * live: connect(), set_cc(), input_on(), step(dt) ... measure_*()
      * batch: generate_lines() -> Protocol v1 frames for the serial parser
    """

    SCENARIOS = SCENARIOS
    PROFILES = SCENARIOS            # name kept for demo/serial tooling

    def __init__(self, profile: str = "normal", sample_rate_ms: int = 500, **limits):
        super().__init__(**limits)
        if profile not in SCENARIOS:
            raise ValueError(f"unknown scenario {profile!r}")
        self._profile_name = profile
        self._p = dict(SCENARIOS[profile])
        self._sample_ms = sample_rate_ms
        self._connected = False
        self._input_on = False
        self._mode = "CC"
        self._setpoint = 0.0
        self._soc = 1.0
        self._pol = 0.0            # slow (polarization) part of the voltage drop
        self._t_s = 0.0
        self._flags: list = []
        self._errors: list = []
        self._tran: Optional[dict] = None
        self._tran_active = False
        self._remote = False
        # an out-of-envelope scenario is a bug in the scenario table
        cap.check_load_command(self._p["start_v"], self._p["current_a"], None,
                               self.profile_current_limit_a, self.system_current_max_a,
                               self.power_path)

    # ── battery model ───────────────────────────────────────────────────
    @property
    def capacity_ah(self) -> float:
        return self._p["rated_ah"] * self._p["soh"]

    @property
    def r_pack_ohm(self) -> float:
        return self._p["sag_v"] / self._p["current_a"]

    def ocv(self) -> float:
        rng = self._p["start_v"] - self._p["cutoff_v"]
        return self._p["start_v"] - rng * (1.0 - self._soc) ** 0.8

    def temperature_c(self) -> float:
        return self._p["temp_start"] + self._p["temp_rise"] * (1 - math.exp(-3 * (1 - self._soc)))

    def _load_current(self, v_ocv: float) -> float:
        if not self._input_on or self._soc <= 0:
            return 0.0
        if self._tran_active and self._tran:
            t = self._tran
            return t["high"] if (self._t_s * t["freq"]) % 1.0 < t["duty"] / 100.0 else t["low"]
        if self._mode == "CC":
            return self._setpoint
        if self._mode == "CR":
            return v_ocv / (self._setpoint + self.r_pack_ohm)
        return max(0.0, (v_ocv - self._setpoint) / self.r_pack_ohm)      # CV

    # Pack resistance = instantaneous half + polarization half (tau 30 s):
    # a current step shows R_inst at once and approaches R_total slowly, and the
    # voltage recovers gradually after the load is removed.
    POL_FRACTION = 0.5
    POL_TAU_S = 30.0

    def _state(self):
        v_ocv = self.ocv()
        i = self._load_current(v_ocv)
        r_inst = self.r_pack_ohm * (1 - self.POL_FRACTION)
        v = v_ocv - i * r_inst - self._pol if self._soc > 0 else self._p["cutoff_v"] * 0.5
        return v, i, v * i

    def step(self, dt_s: float) -> LoadStatus:
        """Advance simulated time; trips the input if the envelope is exceeded."""
        v, i, p = self._state()
        trips = []
        if i > cap.INSTRUMENT_CURRENT_MAX_A + 1e-9: trips.append("OVERCURRENT")
        if p > cap.INSTRUMENT_POWER_MAX_W + 1e-9:   trips.append("OVERPOWER")
        if trips and self._input_on:
            self._input_on = False
            for t in trips:
                if t not in self._flags: self._flags.append(t)
            self._errors.append("SIM: input tripped — " + ",".join(trips))
            return self.read_status()
        target = i * self.r_pack_ohm * self.POL_FRACTION
        self._pol += (target - self._pol) * (1 - math.exp(-dt_s / self.POL_TAU_S))
        self._soc = max(0.0, self._soc - i * dt_s / 3600.0 / self.capacity_ah)
        self._t_s += dt_s
        if self._soc <= 0 and "BATTERY_EMPTY" not in self._flags:
            self._flags.append("BATTERY_EMPTY")
        return self.read_status()

    # ── ElectronicLoad ──────────────────────────────────────────────────
    @property
    def name(self) -> str: return f"Simulator6060B ({self._profile_name})"
    @property
    def is_controllable(self) -> bool: return True

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._input_on = False
        self._connected = False

    def identify(self) -> str:
        return "SIMULATED,6060B,0,sim-1.0"

    def _pack_voltage_for_limit(self) -> Optional[float]:
        return cap.conservative_pack_voltage(self._pack_voltage_v, self.ocv())

    def set_cc(self, amps: float) -> bool:
        self._guard_current(amps)
        self._mode, self._setpoint = "CC", amps
        return True

    def set_cv(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool:
        self._guard_cv(volts, max_expected_current_a)
        self._mode, self._setpoint = "CV", volts
        return True

    def set_cr(self, ohms: float) -> bool:
        self._guard_resistance(ohms)
        self._mode, self._setpoint = "CR", ohms
        return True

    def set_current(self, amps: float) -> bool:    return self.set_cc(amps)
    def set_voltage(self, volts, max_expected_current_a=None) -> bool:
        return self.set_cv(volts, max_expected_current_a)
    def set_resistance(self, ohms: float) -> bool: return self.set_cr(ohms)

    def input_on(self) -> bool:
        if not self._connected:
            raise ConnectionError("simulator not connected")
        if self._mode == "CC": self._guard_current(self._setpoint)
        if self._mode == "CR": self._guard_resistance(self._setpoint)
        self._input_on = True
        return True

    def input_off(self) -> bool:
        self._input_on = False
        return True

    def measure_voltage(self) -> float: return self._state()[0]
    def measure_current(self) -> float: return self._state()[1]
    def measure_power(self) -> float:   return self._state()[2]

    def configure_transient(self, low_a, high_a, freq_hz, duty_pct=50.0, mode="CONT") -> bool:
        for a in (low_a, high_a):
            self._guard_current(a)
        if freq_hz <= 0 or not (0 < duty_pct < 100):
            raise ValueError("invalid transient frequency/duty")
        self._mode, self._setpoint = "CC", low_a
        self._tran = dict(low=low_a, high=high_a, freq=freq_hz, duty=duty_pct, mode=mode)
        self._tran_active = False
        return True

    def trigger_transient(self) -> bool:
        if not self._tran:
            return False
        self._tran_active = True
        return True

    def read_status(self) -> LoadStatus:
        v, i, p = self._state()
        return LoadStatus(connected=self._connected, input_on=self._input_on,
                          mode=self._mode, voltage_v=v, current_a=i, power_w=p,
                          setpoint=self._setpoint, flags=list(self._flags))

    def read_errors(self) -> list:
        e, self._errors = self._errors, []
        return e

    def local(self) -> bool:
        self._remote = False
        return True

    def remote(self) -> bool:
        self._remote = True
        return True

    # ── batch mode: Protocol v1 frames ──────────────────────────────────
    def generate_lines(self) -> list:
        """Whole constant-current discharge as OSBAMS Protocol v1 frames."""
        from services.protocol import encode_data_frame, FLAG_SENSOR_ERR
        p = self._p
        current_a = p["current_a"]
        steps = int(self.capacity_ah / current_a * 3600 * 1000) // self._sample_ms
        fail_at = int(steps * 0.7) if p["fault"] == "comm" else -1
        bms_at = int(steps * 0.85) if p["fault"] == "bms" else steps + 1
        v_range = p["start_v"] - p["cutoff_v"]
        lines, seq = [], 0
        for i in range(steps):
            progress = i / steps
            voltage = p["start_v"] - v_range * (progress ** 0.8)
            if i == 1:
                voltage -= p["sag_v"]
            if i >= bms_at:                       # weak cell collapses -> BMS-style cliff
                voltage -= v_range * 0.25 * ((i - bms_at) / max(1, steps - bms_at)) * 4
            current = current_a * (1.0 + 0.02 * math.sin(progress * 6))
            power = voltage * current
            temp = p["temp_start"] + p["temp_rise"] * (1 - math.exp(-progress * 3))
            status = 0
            if temp > 50: status |= 4
            if voltage < p["cutoff_v"] - 1.0: status |= 8
            t_ms = i * self._sample_ms
            if i == fail_at:
                status |= FLAG_SENSOR_ERR
                state = "DISCHARGING"
            elif i >= bms_at:
                state = "DISCHARGING"
            else:
                state = "DISCHARGING" if progress < 0.98 else "CUTOFF"
            lines.append(encode_data_frame(
                seq=seq, tick_ms=t_ms, voltage_mv=int(voltage * 1000),
                current_ma=int(current * 1000), power_mw=int(power * 1000),
                temp_c10=int(temp) * 10, flags=status, state=state))
            seq += 1
            if i == fail_at:
                seq += 3                          # communication gap
        return lines
