"""
equipment/inventory.py — the actual OSBAMS Rev.2 equipment stack.

Only equipment that is part of the Rev.2 system or its validation workflow is
listed. Model/manufacturer are recorded; serial number, asset ID and calibration
status stay UNKNOWN until read off the instrument — never guessed.
Generates docs/rev2/SFSU_EQUIPMENT_MATRIX.md (tools/gen_rev2_docs.py).
"""

from dataclasses import dataclass

UNKNOWN = "UNKNOWN"
PRIMARY_LOAD, REFERENCE, VALIDATION_ONLY = "PRIMARY_TEST_LOAD", "REFERENCE_MEASUREMENT", "VALIDATION_ONLY"


@dataclass(frozen=True)
class Instrument:
    key: str
    manufacturer: str
    model: str
    tier: str
    role: str
    envelope: str
    uses: tuple
    limits: tuple              # explicit "do not" statements
    in_battery_test_path: bool = False
    in_automated_loop: bool = False
    interface: str = UNKNOWN
    serial_number: str = UNKNOWN       # read off the instrument; never guessed
    asset_id: str = UNKNOWN            # read off the instrument; never guessed
    calibration_status: str = UNKNOWN  # read off the instrument; never guessed


# External laboratory instruments
SFSU_EQUIPMENT = {
    "6060B": Instrument(
        "6060B", "Agilent Technologies / Keysight", "6060B electronic load", PRIMARY_LOAD,
        "primary test load — the only external load supported by Rev.2",
        "3-60 V DC, 0-60 A, 300 W max; CC / CV / CR",
        ("controlled CC / CV / CR discharge", "capacity test", "energy measurement",
         "DCIR pulse / load-step testing"),
        ("allowed current = min(battery profile, OSBAMS hardware limit, 6060B current limit, "
         "300 W / battery voltage)",
         "the 60 A rating never overrides the 300 W limit",
         "remote (GPIB) control only after the interface is confirmed AND each command is VERIFIED; "
         "CC/CV/CR/transient only as far as the official manuals document them"),
        in_battery_test_path=True, in_automated_loop=True,
        interface="GPIB — PC path NOT confirmed (BLOCKED_BY_INTERFACE_CONFIRMATION); manual panel works"),
    "EDU34450A": Instrument(
        "EDU34450A", "Keysight Technologies", "EDU34450A digital multimeter", REFERENCE,
        "reference measurement — calibration/verification reference",
        "bench DMM: DC voltage, DC current, resistance, continuity, temperature",
        ("verify OSBAMS voltage measurement", "verify current measurement",
         "validate INA228 / ADC accuracy", "calibration procedure and error analysis",
         "polarity and continuity checks"),
        ("not part of the normal automated discharge loop",
         "check its current range/fuse limits before any current measurement"),
        interface="USB/LAN (to confirm)"),
    "EDUX1052G": Instrument(
        "EDUX1052G", "Keysight Technologies", "EDUX1052G oscilloscope", VALIDATION_ONLY,
        "validation only — observation, never normal operation",
        "2-channel digital oscilloscope",
        ("relay switching", "shutdown timing", "voltage transients", "load-enable behavior"),
        ("not part of normal operation",
         "its input rating is NOT permission to probe arbitrary high-energy nodes; "
         "use rated probes and good grounding"),
    ),
}

# The OSBAMS system itself (not laboratory instruments)
SYSTEM_STACK = {
    "UI": dict(
        name="Raspberry Pi 5 + 10.1\" touchscreen", role="user interface",
        does=("standalone OSBAMS operation", "test control", "live dashboard",
              "battery database (SQLite)", "battery passport", "reports",
              "Python application and analysis engine"),
        status="software is host-tested; Pi 5 deployment not yet tested"),
    "SAFETY": dict(
        name="STM32L476RG controller", role="real-time safety controller",
        does=("sensor acquisition (INA228, independent ADC voltage, TC74)", "relay control",
              "fault handling", "watchdog", "emergency-stop monitoring"),
        status="firmware host-tested; not hardware-validated"),
    "POWER_PATH": dict(
        name="Battery interface / OSBAMS power path", role="battery connection and switching",
        does=("battery → XT60 connector → fuse → manual disconnect → relay → current shunt → 6060B",),
        status="candidate; exact parts not yet read off the hardware (HARDWARE_FREEZE_CANDIDATE.md)"),
}
PI_STM32_RULE = "The Pi requests actions. The STM32 authorizes them."

# Batteries physically available (from the OSBAMS database). Lithium-ion, ~10S.
SFSU_BATTERIES = (
    {"brand": "Ninebot/Segway", "model": "NEB1002-H",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 5.2, "wh": 187.0},
    {"brand": "Shenzhen Elite", "model": "HY-RDF-S1004UM-MH1",
     "nominal_v": 37.0, "max_v": 42.0, "ah": 12.8, "wh": 473.6},
    {"brand": "Ninebot (Fujian Eincio)", "model": "NEE1006-M",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 15.3, "wh": 551.0},
)
