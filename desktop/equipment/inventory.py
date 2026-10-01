"""
equipment/inventory.py — SFSU laboratory equipment inventory (Rev.2).

Rev.2 is designed ONLY around this equipment. `envelope` strings record
manufacturer ratings as supplied by the project owner; `asset_id` and
`calibration_status` are unknown until read off the instruments and are
recorded as such — never guessed.
"""

from dataclasses import dataclass

UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Instrument:
    key: str
    model: str
    role: str
    envelope: str
    uses: tuple
    limits: tuple              # explicit "do not" statements
    manufacturer: str = UNKNOWN
    serial_number: str = UNKNOWN      # read off the instrument; never guessed
    asset_id: str = UNKNOWN           # read off the instrument; never guessed
    calibration_status: str = UNKNOWN # read off the instrument; never guessed
    interface: str = UNKNOWN


SFSU_EQUIPMENT = {
    "6060B": Instrument(
        key="6060B", manufacturer="Agilent Technologies / Keysight", model="Agilent/Keysight 6060B",
        role="PRIMARY electronic load",
        envelope="3-60 V DC input, 60 A max, 300 W max; CC/CV/CR; transient; GPIB",
        uses=("constant-current discharge", "DCIR current step",
              "voltage-sag steps", "transient characterization"),
        limits=("I_max(V) = min(60 A, 300 W / V) — 60 A is NOT available at all voltages",
                "never commanded outside V<=60, I<=60, V*I<=300"),
        interface="GPIB — path to PC NOT confirmed (BLOCKED_BY_INTERFACE_CONFIRMATION)"),
    "EDU34450A": Instrument(
        key="EDU34450A", manufacturer="Keysight Technologies", model="Keysight EDU34450A 5.5-digit DMM",
        role="PRIMARY independent reference measurement instrument",
        envelope="bench DMM (DCV/DCI/resistance/continuity/temperature)",
        uses=("OSBAMS voltage calibration", "current verification",
              "power verification", "resistance", "continuity",
              "temperature verification"),
        limits=("verify its range/fuse limits before any current measurement",),
        interface="USB/LAN (to confirm)"),
    "EDU36311A": Instrument(
        key="EDU36311A", manufacturer="Keysight Technologies", model="Keysight EDU36311A triple-output supply",
        role="low-energy commissioning source",
        envelope="CH1 0-6 V / 5 A; CH2 0-30 V / 1 A; CH3 0-30 V / 1 A; "
                 "series operation of independent outputs per manufacturer docs",
        uses=("sensor validation", "ADC calibration", "state-machine tests",
              "contactor logic", "fault injection", "voltage-threshold tests",
              "6060B/OSBAMS comms testing"),
        limits=("NOT a substitute for a 42 V high-current battery",),
        interface="USB/LAN (to confirm)"),
    "EDUX1052G": Instrument(
        key="EDUX1052G", manufacturer="Keysight Technologies", model="Keysight EDUX1052G oscilloscope",
        role="dynamic validation",
        envelope="2-channel scope",
        uses=("contactor timing", "load switching", "precharge transient",
              "voltage sag", "current-step response", "UART/I2C/PWM",
              "E-stop response timing", "supply startup", "fault shutdown timing"),
        limits=("analog input rating is NOT permission to probe arbitrary "
                "high-energy nodes; use proper probes and grounding",)),
    "EDU33212A": Instrument(
        key="EDU33212A", manufacturer="Keysight Technologies", model="Keysight EDU33212A waveform generator",
        role="signal simulation / injection",
        envelope="2-channel function generator",
        uses=("sensor signal simulation", "ADC input tests", "frequency response",
              "fault injection", "filter characterization"),
        limits=("never a battery power source",)),
    "AD2": Instrument(
        key="AD2", manufacturer="Digilent", model="Digilent Analog Discovery 2",
        role="low-energy instrumentation / protocol development",
        envelope="low-voltage analog + digital",
        uses=("UART", "SPI", "I2C", "digital logic", "PWM",
              "BMS communication research", "impedance experiments"),
        limits=("never a high-energy battery measurement instrument",)),
    "HANDHELD_DMM": Instrument(
        key="HANDHELD_DMM", manufacturer="UNKNOWN", model="Handheld multimeter",
        role="secondary / manual verification",
        envelope="basic DMM",
        uses=("continuity", "polarity", "supply rails", "basic voltage", "wiring checks"),
        limits=("bench Keysight DMM remains the preferred quantitative reference",)),
}

# Batteries physically available (from the OSBAMS database).
SFSU_BATTERIES = (
    {"brand": "Ninebot/Segway", "model": "NEB1002-H",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 5.2, "wh": 187.0},
    {"brand": "Shenzhen Elite", "model": "HY-RDF-S1004UM-MH1",
     "nominal_v": 37.0, "max_v": 42.0, "ah": 12.8, "wh": 473.6},
    {"brand": "Ninebot (Fujian Eincio)", "model": "NEE1006-M",
     "nominal_v": 36.0, "max_v": 42.0, "ah": 15.3, "wh": 551.0},
)

# Capabilities Rev.2 explicitly does NOT have.
OUT_OF_SCOPE_FOR_REV2 = (
    "packs above 60 V (Dat Bike ~72 V class, 100 V, 150 V, 500 V)",
    "EV modules above 60 V and full automotive EV packs",
    "regenerative cyclers / Bitrode / Arbin / Chroma / Digatron drivers",
    "'90 A' testing (XT90 is a connector, not a test current)",
    "the Rev.1 USB-SCPI electronic load (removed; archived under legacy/rev1/)",
)
