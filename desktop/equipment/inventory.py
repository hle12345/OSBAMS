"""
equipment/inventory.py — SFSU laboratory equipment (Rev.2 active roles).

Rev.2 is designed ONLY around this equipment and the lithium-ion packs in the
OSBAMS database. Model/manufacturer are recorded now; serial number, asset ID
and calibration status stay UNKNOWN until read off each instrument — never
guessed. Envelope strings are manufacturer-class figures to be confirmed on the
unit. Generates docs/rev2/SFSU_EQUIPMENT_MATRIX.md (tools/gen_rev2_docs.py).
"""

from dataclasses import dataclass

UNKNOWN = "UNKNOWN"
PRIMARY, SECONDARY, SEPARATE = "PRIMARY", "SECONDARY", "SEPARATE_LAB_EQUIPMENT"


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
    interface: str = UNKNOWN
    serial_number: str = UNKNOWN       # read off the instrument; never guessed
    asset_id: str = UNKNOWN            # read off the instrument; never guessed
    calibration_status: str = UNKNOWN  # read off the instrument; never guessed


SFSU_EQUIPMENT = {
    "6060B": Instrument(
        "6060B", "Agilent Technologies / Keysight", "6060B", PRIMARY,
        "primary programmable battery load",
        "3-60 V DC input, 0-60 A, 300 W max; CC/CV/CR; transient; GPIB",
        ("constant-current discharge", "DCIR current step", "voltage-sag steps",
         "transient only where officially documented"),
        ("I_max(V) = min(60 A, 300 W / V): 60 A is NOT available at all voltages",
         "the 60 A front-panel rating never overrides the 300 W limit",
         "never commanded outside V<=60, I<=60, V*I<=300 and the OSBAMS limits",
         "remote (GPIB) control only after the interface is confirmed AND each command is VERIFIED"),
        in_battery_test_path=True,
        interface="GPIB — PC path NOT confirmed (BLOCKED_BY_INTERFACE_CONFIRMATION); manual panel works"),
    "EDU34450A": Instrument(
        "EDU34450A", "Keysight Technologies", "EDU34450A 5.5-digit DMM", PRIMARY,
        "primary reference DMM",
        "bench DMM: DCV, DCI, resistance, continuity, temperature",
        ("OSBAMS voltage calibration", "current verification",
         "resistance / continuity checks", "reference measurements"),
        ("check its current range/fuse limits before any current measurement",),
        interface="USB/LAN (to confirm)"),
    "HP34401A": Instrument(
        "HP34401A", "Hewlett-Packard (Agilent)", "34401A 6.5-digit DMM", SECONDARY,
        "secondary reference DMM — independent cross-check of the EDU34450A",
        "bench DMM: DCV, DCI, resistance (confirm ranges on the unit)",
        ("cross-check against EDU34450A", "independent validation"),
        ("not the primary reference; check its calibration sticker before relying on it",),
        interface="GPIB/RS-232 (to confirm)"),
    "EDU36311A": Instrument(
        "EDU36311A", "Keysight Technologies", "EDU36311A triple-output supply", PRIMARY,
        "programmable commissioning source (NOT a battery load)",
        "CH1 0-6 V / 5 A; CH2 0-30 V / 1 A; CH3 0-30 V / 1 A; series operation of "
        "independent outputs per manufacturer docs",
        ("low-energy sensor validation", "state-machine tests", "ADC calibration",
         "fault-threshold testing"),
        ("not a battery and cannot sink current — it does not reproduce a 42 V high-current pack",),
        interface="USB/LAN (to confirm)"),
    "HPE3630A": Instrument(
        "HPE3630A", "Hewlett-Packard (Agilent)", "E3630A triple-output bench supply", SECONDARY,
        "secondary bench source — low-energy / manual commissioning",
        "triple output, low-voltage class (confirm ranges on the unit)",
        ("logic and sensor testing", "manual commissioning"),
        ("not a battery load; manual only",)),
    "EDUX1052G": Instrument(
        "EDUX1052G", "Keysight Technologies", "EDUX1052G oscilloscope", PRIMARY,
        "primary oscilloscope",
        "2-channel digital oscilloscope",
        ("contactor timing", "shutdown timing", "UART/I2C observation",
         "switching / transient observation"),
        ("the input rating is NOT permission to probe arbitrary high-energy nodes; "
         "use rated probes and good grounding",)),
    "HP54601B": Instrument(
        "HP54601B", "Hewlett-Packard (Agilent)", "54601B oscilloscope", SECONDARY,
        "secondary oscilloscope — optional cross-check / extra channels",
        "multi-channel digital oscilloscope (confirm channels/bandwidth on the unit)",
        ("cross-check timing captured on the EDUX1052G", "extra channels"),
        ("same probing rules as the primary scope",)),
    "EDU33212A": Instrument(
        "EDU33212A", "Keysight Technologies", "EDU33212A waveform generator", PRIMARY,
        "waveform / signal injection",
        "2-channel function generator",
        ("sensor simulation", "signal-conditioning and filter tests", "ADC input tests"),
        ("never a battery power source",)),
    "HP33120A": Instrument(
        "HP33120A", "Hewlett-Packard (Agilent)", "33120A function/arbitrary generator", SECONDARY,
        "secondary waveform generator — same role where useful",
        "function/arbitrary waveform generator",
        ("signal injection", "sensor simulation"),
        ("never a battery power source",)),
    "AD2": Instrument(
        "AD2", "Digilent", "Analog Discovery 2", PRIMARY,
        "low-voltage digital/protocol debugging",
        "low-voltage analog + digital I/O",
        ("UART / SPI / I2C", "logic analysis", "low-voltage signal injection"),
        ("not a high-energy battery measurement instrument",)),
    "HANDHELD_DMM": Instrument(
        "HANDHELD_DMM", UNKNOWN, "Handheld multimeter", SECONDARY,
        "polarity, continuity, basic rail verification",
        "basic handheld DMM",
        ("polarity", "continuity", "basic rail verification"),
        ("never the quantitative reference — the bench DMMs are",)),
    "OPTIMATE": Instrument(
        "OPTIMATE", "OptiMate (exact models UNKNOWN)", "12.8 V LiFePO4 battery chargers", SEPARATE,
        "separate lab equipment for compatible 12.8 V LFP batteries — documented only",
        "12.8 V LiFePO4 chargers",
        ("charging compatible 12.8 V LFP batteries, outside OSBAMS",),
        ("NOT part of the OSBAMS battery-test path and not integrated in software",
         "NEVER use on the 36-42 V lithium-ion packs")),
}

# Batteries physically available (from the OSBAMS database). Lithium-ion, ~10S.
SFSU_BATTERIES = (
    {"brand": "Ninebot/Segway", "model": "NEB1002-H",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 5.2, "wh": 187.0},
    {"brand": "Shenzhen Elite", "model": "HY-RDF-S1004UM-MH1",
     "nominal_v": 37.0, "max_v": 42.0, "ah": 12.8, "wh": 473.6},
    {"brand": "Ninebot (Fujian Eincio)", "model": "NEE1006-M",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 15.3, "wh": 551.0},
)
