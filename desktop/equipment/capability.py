"""
equipment/capability.py — 6060B power-envelope model.

The Keysight/Agilent 6060B is rated 3-60 V, 0-60 A, 300 W. Those are THREE
simultaneous limits, not a 60 A tester:

    I_load_max(V) = min(60 A, 300 W / V)

    5 V -> 60 A   10 V -> 30 A   20 V -> 15 A   30 V -> 10 A
    36 V -> 8.33 A   42 V -> 7.14 A   48 V -> 6.25 A   60 V -> 5 A

The permitted test current is the minimum of EVERYTHING in the chain:

    min(battery profile limit, OSBAMS validated hardware limit,
        connector / fuse / wiring / contactor / shunt-sensor limits,
        6060B 60 A current limit, 6060B 300 W power-derived limit)

Connector type never determines test current: an XT90 is a physical
compatibility statement, not a 90 A test.

Which voltage to pass in: the power-derived limit must use the HIGHEST
voltage the pack can present while the load is attached (see
`conservative_pack_voltage`), because 300 W / V shrinks as V rises.
"""

from dataclasses import dataclass, field
from typing import Optional, Mapping

# ── 6060B manufacturer envelope (instrument rating, NOT an OSBAMS claim) ─────
INSTRUMENT_MODEL         = "Keysight/Agilent 6060B"
INSTRUMENT_VOLTAGE_MIN_V = 3.0
INSTRUMENT_VOLTAGE_MAX_V = 60.0
INSTRUMENT_CURRENT_MAX_A = 60.0
INSTRUMENT_POWER_MAX_W   = 300.0

# Remote-control status. Do not change until an SFSU GPIB path is confirmed
# (USB<->GPIB adapter, LAN<->GPIB gateway, or GPIB-equipped PC).
REMOTE_CONTROL_STATUS = "BLOCKED_BY_INTERFACE_CONFIRMATION"

_EPS = 1e-9


class EnvelopeViolation(ValueError):
    """A load command would leave the permitted operating envelope."""


class InvariantViolation(EnvelopeViolation):
    """requested_current x conservative_pack_voltage > 300 W."""


# ── Layered limit model ─────────────────────────────────────────────────────
#   firmware hard trip   absolute protection boundary (config.FIRMWARE_HARD_TRIP_A)
#   OSBAMS ceiling       operating/test boundary       (config.SAFETY_MAX_CURRENT_A)
#   6060B @ V            min(60 A, 300 W / V)
#   battery profile      per-pack ceiling
# The commanded maximum is the minimum of the OPERATING limits. The firmware
# trip is deliberately NOT an input to that minimum: it must sit above every
# operating limit and only fires when something has already gone wrong.
def firmware_hard_trip_a() -> float:
    try:
        import config
        return float(config.FIRMWARE_HARD_TRIP_A)
    except Exception:
        return 18.5


def _default_system_current_max_a() -> float:
    """OSBAMS validated hardware current limit — single authority: config.py."""
    try:
        import config
        return float(config.SAFETY_MAX_CURRENT_A)
    except Exception:           # capability model must work stand-alone
        return 10.0


def instrument_current_limit_a(voltage_v: float) -> float:
    """min(60 A, 300 W / V) — the 6060B alone, ignoring everything else."""
    if voltage_v < INSTRUMENT_VOLTAGE_MIN_V or voltage_v > INSTRUMENT_VOLTAGE_MAX_V:
        return 0.0
    return min(INSTRUMENT_CURRENT_MAX_A, INSTRUMENT_POWER_MAX_W / voltage_v)


def conservative_pack_voltage(*voltages_v: Optional[float]) -> Optional[float]:
    """Highest known pack voltage (OCV, measured, profile max). None if none."""
    known = [v for v in voltages_v if v is not None]
    return max(known) if known else None


class ConservativeVoltage:
    """
    Monotonic non-decreasing pack-voltage estimate for the 300 W check.
    A sagging loaded reading can never lower it, so sag can never be used to
    justify more current during a test. Only a NEW test (new instance) resets it.
    """

    def __init__(self, initial_v: Optional[float] = None):
        self._v = initial_v

    @property
    def volts(self) -> Optional[float]:
        return self._v

    def update(self, measured_v: Optional[float]) -> Optional[float]:
        if measured_v is not None and (self._v is None or measured_v > self._v):
            self._v = measured_v
        return self._v


def assert_power_invariant(requested_current_a: float,
                           conservative_voltage_v: Optional[float]) -> float:
    """
    HARD INVARIANT: requested_current x conservative_pack_voltage <= 300 W.
    Returns the power; raises InvariantViolation otherwise (including unknown
    voltage, which is treated as unsafe).
    """
    if conservative_voltage_v is None:
        raise InvariantViolation("conservative pack voltage unknown")
    p = float(requested_current_a) * float(conservative_voltage_v)
    if p > INSTRUMENT_POWER_MAX_W + _EPS:
        raise InvariantViolation(
            f"{requested_current_a:.3f} A x {conservative_voltage_v:.2f} V = "
            f"{p:.1f} W > {INSTRUMENT_POWER_MAX_W:g} W")
    return p


@dataclass(frozen=True)
class PowerPathLimits:
    """
    Current ratings of the OSBAMS power path. None = NOT SPECIFIED/VERIFIED.
    An unspecified component does not silently pass: it is listed in
    `CurrentLimit.unspecified` and the OSBAMS validated limit still caps
    the result. See docs/rev2/LV_POWER_PATH_CAPABILITY.md.
    """
    connector_a: Optional[float] = None
    fuse_a:      Optional[float] = None
    wiring_a:    Optional[float] = None
    contactor_a: Optional[float] = None   # relay / contactor
    disconnect_a: Optional[float] = None  # manual disconnect (continuous carrying)
    shunt_a:     Optional[float] = None   # shunt / current-sensor range
    max_voltage_v: Optional[float] = None # lowest DC voltage rating in the path

    def as_dict(self) -> dict:   # current ratings only
        return {"connector": self.connector_a, "fuse": self.fuse_a,
                "wiring": self.wiring_a, "relay/contactor": self.contactor_a,
                "disconnect": self.disconnect_a, "shunt/sensor": self.shunt_a}


# Rev.2 power path (docs/rev2/HARDWARE_FREEZE_CANDIDATE.md). Known numbers only:
#   shunt   RSA-20-50, 20 A class (repo)
#   fuse    15 A TARGET (part number not yet confirmed)
#   disconnect Blue Sea 6006: 48 V DC max, 25 A switching (manufacturer listing)
# Contactor (Durakool DG57CM: ratings are VARIANT-dependent), connector and wiring
# stay unspecified until the exact parts are read off the hardware.
# The OSBAMS validated limits (config) cap everything regardless.
REV2_POWER_PATH = PowerPathLimits(fuse_a=15.0, shunt_a=20.0, disconnect_a=300.0,
                                  max_voltage_v=48.0)

# Where each number comes from. NONE of these is read off the physical unit yet,
# so nothing here is "verified OSBAMS hardware"; the 10 A ceiling covers the gap.
POWER_PATH_STATUS = {
    "fuse":            "TARGET 15 A — part/holder not confirmed",
    "disconnect":      "Blue Sea 6006 listing: 48 V DC, 300 A continuous, 25 A switching — not read from the unit",
    "relay/contactor": "Durakool DG57CM — variant-dependent ratings, suffix not read — UNSPECIFIED",
    "shunt/sensor":    "RSA-20-50, 20 A class (repo) — installed part not confirmed",
    "connector":       "XT60 (XT30/XT90 adapters) — UNSPECIFIED; a plug never sets test current",
    "wiring":          "UNSPECIFIED",
}
REV1_POWER_PATH = REV2_POWER_PATH      # backward-compatible alias


@dataclass
class CurrentLimit:
    """Full breakdown — exactly what the UI must display."""
    battery_voltage_v:    Optional[float]
    profile_limit_a:      Optional[float]
    osbams_limit_a:       float
    instrument_limit_a:   float      # 6060B 60 A
    power_limit_a:        Optional[float]   # 300 W / V
    component_limits_a:   dict = field(default_factory=dict)
    unspecified:          list = field(default_factory=list)
    final_a:              float = 0.0
    limiting_factor:      str = ""
    blocked_reason:       str = ""
    system_voltage_max_v: float = 0.0

    @property
    def blocked(self) -> bool:
        return bool(self.blocked_reason)

    def rows(self) -> list:
        """(label, value) rows for the UI limit panel (live limiting factor included)."""
        def a(x, nd=2): return "n/a" if x is None else f"{x:.{nd}f} A"
        v = "unknown" if self.battery_voltage_v is None else f"{self.battery_voltage_v:.1f} V"
        parts = [f"{a(self.instrument_limit_a, 0)} (6060B)"]
        if self.power_limit_a is not None:
            parts.append(f"{self.power_limit_a:.2f} A (300 W/V)")
        parts.append(f"{a(self.osbams_limit_a, 0)} (OSBAMS)")
        if self.profile_limit_a is not None:
            parts.append(f"{self.profile_limit_a:.2f} A (profile)")
        final = a(self.final_a) if not self.blocked else f"BLOCKED — {self.blocked_reason}"
        return [
            ("Pack voltage (conservative)",     v),
            ("6060B current rating",            a(self.instrument_limit_a, 0)),
            ("6060B power-derived limit",       a(self.power_limit_a)),
            ("OSBAMS validated limit",          a(self.osbams_limit_a, 0)),
            ("OSBAMS validated voltage ceiling", f"{self.system_voltage_max_v:g} V"),
            ("Battery-profile limit",           a(self.profile_limit_a)),
            ("FINAL PERMITTED",                 final),
            ("Limiting factor",                 self.limiting_factor or "—"),
            ("min(...)",                        "min(" + ", ".join(parts) + ")"),
            ("Firmware hard trip (protection only, not an operating limit)",
             a(firmware_hard_trip_a(), 1)),
        ]


def _default_system_voltage_max_v() -> float:
    try:
        import config
        return float(config.OSBAMS_VALIDATED_MAX_VOLTAGE_V)
    except Exception:
        return 44.0


def compute_permitted_current(
        pack_voltage_v: Optional[float],
        profile_current_limit_a: Optional[float] = None,
        system_current_max_a: Optional[float] = None,
        power_path: PowerPathLimits = REV2_POWER_PATH,
        system_voltage_max_v: Optional[float] = None) -> CurrentLimit:
    """
    The one function that decides how much current may be requested.
    Fail-safe: unknown/out-of-range voltage -> 0 A with a blocked_reason.
    """
    osbams = _default_system_current_max_a() if system_current_max_a is None \
        else float(system_current_max_a)
    vmax = _default_system_voltage_max_v() if system_voltage_max_v is None \
        else float(system_voltage_max_v)
    if power_path.max_voltage_v is not None:
        vmax = min(vmax, power_path.max_voltage_v)
    vmax = min(vmax, INSTRUMENT_VOLTAGE_MAX_V)
    comps  = {k: v for k, v in power_path.as_dict().items() if v is not None}
    unspec = [k for k, v in power_path.as_dict().items() if v is None]
    res = CurrentLimit(
        battery_voltage_v=pack_voltage_v, profile_limit_a=profile_current_limit_a,
        system_voltage_max_v=vmax,
        osbams_limit_a=osbams, instrument_limit_a=INSTRUMENT_CURRENT_MAX_A,
        power_limit_a=None, component_limits_a=comps, unspecified=unspec)

    if pack_voltage_v is None:
        res.blocked_reason = "pack voltage unknown"
        res.limiting_factor = "voltage unknown"
        return res
    if pack_voltage_v < INSTRUMENT_VOLTAGE_MIN_V - _EPS:
        res.blocked_reason = (f"pack voltage {pack_voltage_v:.2f} V below the "
                              f"6060B {INSTRUMENT_VOLTAGE_MIN_V:g} V minimum")
        res.limiting_factor = "6060B min voltage"
        return res
    if pack_voltage_v > INSTRUMENT_VOLTAGE_MAX_V + _EPS:
        res.blocked_reason = (f"pack voltage {pack_voltage_v:.2f} V above the "
                              f"6060B {INSTRUMENT_VOLTAGE_MAX_V:g} V maximum")
        res.limiting_factor = "6060B max voltage"
        return res
    if pack_voltage_v > vmax + _EPS:
        res.blocked_reason = (f"pack voltage {pack_voltage_v:.2f} V above the OSBAMS "
                              f"validated system ceiling {vmax:g} V (provisional)")
        res.limiting_factor = "OSBAMS voltage ceiling"
        return res

    res.power_limit_a = INSTRUMENT_POWER_MAX_W / pack_voltage_v
    candidates = {
        "6060B 60 A":              INSTRUMENT_CURRENT_MAX_A,
        "6060B 300 W / V":         res.power_limit_a,
        "OSBAMS hardware limit":   osbams,
    }
    if profile_current_limit_a is not None:
        candidates["battery profile"] = float(profile_current_limit_a)
    for k, v in comps.items():
        candidates[k + " rating"] = float(v)
    name, val = min(candidates.items(), key=lambda kv: kv[1])
    res.final_a = max(0.0, val)
    res.limiting_factor = name
    return res


def check_load_command(requested_voltage_v: float, requested_current_a: float,
                       requested_power_w: Optional[float] = None,
                       profile_current_limit_a: Optional[float] = None,
                       system_current_max_a: Optional[float] = None,
                       power_path: PowerPathLimits = REV2_POWER_PATH,
                       system_voltage_max_v: Optional[float] = None) -> CurrentLimit:
    """
    Gate for EVERY load command. Raises EnvelopeViolation unless
        V <= 60, 3 <= V, I <= 60, V*I <= 300
    and all OSBAMS / profile / component limits hold. Returns the breakdown.
    """
    v, i = float(requested_voltage_v), float(requested_current_a)
    p = v * i if requested_power_w is None else float(requested_power_w)
    if i < 0:
        raise EnvelopeViolation(f"negative current request {i} A")
    lim = compute_permitted_current(v, profile_current_limit_a,
                                    system_current_max_a, power_path,
                                    system_voltage_max_v)
    if lim.blocked:
        raise EnvelopeViolation(lim.blocked_reason)
    if i > INSTRUMENT_CURRENT_MAX_A + _EPS:
        raise EnvelopeViolation(f"{i:.3f} A exceeds the 6060B {INSTRUMENT_CURRENT_MAX_A:g} A limit")
    if p > INSTRUMENT_POWER_MAX_W + _EPS:
        raise EnvelopeViolation(
            f"{v:.2f} V x {i:.3f} A = {p:.1f} W exceeds the 6060B "
            f"{INSTRUMENT_POWER_MAX_W:g} W limit (max {lim.power_limit_a:.2f} A at this voltage)")
    if i > lim.final_a + _EPS:
        raise EnvelopeViolation(
            f"{i:.3f} A exceeds the permitted {lim.final_a:.3f} A at {v:.2f} V "
            f"(limited by {lim.limiting_factor})")
    return lim


def envelope_table(voltages=(5, 10, 12, 20, 24, 30, 36, 42, 48, 60),
                   profile_current_limit_a=None) -> list:
    """Rows for docs/Learning Mode: (V, 6060B-only A, final permitted A)."""
    return [(v, instrument_current_limit_a(v),
             compute_permitted_current(v, profile_current_limit_a).final_a)
            for v in voltages]
