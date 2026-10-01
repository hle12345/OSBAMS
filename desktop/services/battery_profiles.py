"""
services/battery_profiles.py — Rev.2 battery profiles.

A profile says what a battery is and what is SAFE for it. It does not say what
the 6060B can do: the actual test current is always
capability.compute_permitted_current(...). There is NO global minimum battery
voltage — cutoff_voltage_v is per profile. Connector type never sets current.
"""

from dataclasses import dataclass
from typing import Optional

from equipment import capability as cap

SMART_PACK_UNSUPPORTED = "SMART_PACK_UNSUPPORTED"


@dataclass(frozen=True)
class BatteryProfile:
    key: str
    manufacturer: str
    model: str
    chemistry: str
    nominal_voltage_v: float
    maximum_voltage_v: float
    cutoff_voltage_v: float
    rated_ah: float
    rated_wh: float
    recommended_test_current_a: float
    maximum_osbams_test_current_a: float      # profile ceiling; still min()'d with hardware
    connector: str
    temp_min_c: float
    temp_max_c: float
    bms_behavior: str = "unknown"             # known BMS behaviour, free text
    bms_interface: str = SMART_PACK_UNSUPPORTED

    def permitted_current(self, pack_voltage_v: Optional[float] = None) -> cap.CurrentLimit:
        """Permitted test current; defaults to the profile's maximum voltage (worst case)."""
        v = self.maximum_voltage_v if pack_voltage_v is None else pack_voltage_v
        return cap.compute_permitted_current(v, self.maximum_osbams_test_current_a)

    def validate(self) -> list:
        """Problems that make the profile untestable on Rev.2 (empty = OK)."""
        p = []
        if self.maximum_voltage_v > cap.INSTRUMENT_VOLTAGE_MAX_V:
            p.append(f"max voltage {self.maximum_voltage_v} V exceeds 6060B {cap.INSTRUMENT_VOLTAGE_MAX_V:g} V — OUT_OF_SCOPE_FOR_REV2")
        if self.cutoff_voltage_v < cap.INSTRUMENT_VOLTAGE_MIN_V:
            p.append(f"cutoff {self.cutoff_voltage_v} V below 6060B {cap.INSTRUMENT_VOLTAGE_MIN_V:g} V minimum")
        if not self.cutoff_voltage_v < self.nominal_voltage_v <= self.maximum_voltage_v:
            p.append("need cutoff < nominal <= maximum voltage")
        if self.recommended_test_current_a > self.maximum_osbams_test_current_a:
            p.append("recommended current exceeds profile maximum")
        lim = self.permitted_current()
        if not lim.blocked and self.recommended_test_current_a > lim.final_a + 1e-9:
            p.append(f"recommended {self.recommended_test_current_a} A exceeds permitted "
                     f"{lim.final_a:.2f} A at {self.maximum_voltage_v} V ({lim.limiting_factor})")
        return p


PROFILES = {
    "ninebot_neb1002": BatteryProfile(
        "ninebot_neb1002", "Ninebot/Segway", "NEB1002-H", "Li-ion NMC (10S)",
        36.0, 42.0, 30.0, 5.2, 187.0, 1.0, 5.2, "to confirm (XT60 adapter assumed)",
        0.0, 50.0, "Pack BMS; behaviour at cutoff not yet characterised"),
    "shenzhen_elite_hy_rdf": BatteryProfile(
        "shenzhen_elite_hy_rdf", "Shenzhen Elite", "HY-RDF-S1004UM-MH1", "Li-ion NMC (10S)",
        37.0, 42.0, 30.0, 12.8, 473.6, 2.5, 6.4, "to confirm",
        0.0, 50.0, "Pack BMS; behaviour at cutoff not yet characterised"),
    "ninebot_nee1006m": BatteryProfile(
        "ninebot_nee1006m", "Ninebot (Fujian Eincio)", "NEE1006-M", "Li-ion NMC (10S6P)",
        36.0, 42.0, 30.0, 15.3, 551.0, 3.0, 7.0, "XT60 / to confirm",
        0.0, 50.0, "Some units show blinking-blue BMS state; see intake notes"),
}


def get_profile(key: str) -> BatteryProfile:
    return PROFILES[key]
