"""
config.py — OSBAMS Central Configuration

SINGLE SOURCE OF TRUTH for all tunable constants on the Python side.

Cross-language note: firmware constants live in firmware/Core/Inc/app_config.h.
The two files must agree, but C cannot import Python. Agreement is enforced by
tests/test_config_sync.py, which parses both files and fails the build if a
shared constant diverges. "Defined once" means one authority per value with a
verified mirror, not one physical file for both languages.

Version scheme (see VERSIONS below):
    System / Desktop / Firmware : 0.9.0-dev1  (Engineering Prototype)
    Hardware validation pending — see docs/known_limitations.md
    Serial protocol     : 1
    Database schema     : 6

Do NOT call the complete product 1.0 until hardware validation is finished.
"""

import os

# ══════════════════════════════════════════════════════════════════════════════
# VERSIONS — one scheme, used everywhere
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_VERSION      = "0.9.0-dev1"    # whole-system version
BUILD_DESCRIPTOR    = "Engineering Prototype — Hardware verification and calibration pending"
APP_VERSION         = "0.9.0-dev1"    # desktop application
FIRMWARE_VERSION    = "0.9.0-dev1"    # STM32 embedded controller
PROTOCOL_VERSION    = 1               # serial frame format
SCHEMA_VERSION      = 6               # SQLite database schema
RULE_ENGINE_VERSION = "1.0"           # 7-component scoring
ML_MODEL_ID         = "RF-001"        # RandomForest, GroupKFold-validated
HARDWARE_REV        = "Engineering Prototype"  # not frozen; contactor/E-stop/sensor still in flux

VERSIONS = {
    "system":      SYSTEM_VERSION,
    "application": APP_VERSION,
    "firmware":    FIRMWARE_VERSION,
    "protocol":    PROTOCOL_VERSION,
    "schema":      SCHEMA_VERSION,
    "rule_engine": RULE_ENGINE_VERSION,
    "ml_model":    ML_MODEL_ID,
    "hardware":    HARDWARE_REV,
}

APP_NAME   = "OSBAMS"
APP_FULL   = "Open Second-Life Battery Assessment & Management System"
APP_AUTHOR = "Joe Le"
APP_SCHOOL = "San Francisco State University"
APP_COURSE = "ENGR 696 / 697GW"


# ══════════════════════════════════════════════════════════════════════════════
# PATHS
# ══════════════════════════════════════════════════════════════════════════════

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "db", "osbams.db")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
REPORTS_DIR = os.path.join(EXPORTS_DIR, "reports")
CSV_DIR     = os.path.join(EXPORTS_DIR, "csv")
MODELS_DIR  = os.path.join(EXPORTS_DIR, "models")
PHOTOS_DIR  = os.path.join(BASE_DIR, "db", "photos")
BACKUPS_DIR = os.path.join(BASE_DIR, "db", "backups")

_REQUIRED_DIRS = [EXPORTS_DIR, REPORTS_DIR, CSV_DIR,
                  MODELS_DIR, PHOTOS_DIR, BACKUPS_DIR]


def ensure_directories() -> None:
    """
    Create the runtime directory tree.

    Called explicitly from main.py at startup, NOT at import time.
    Importing a configuration module should never touch the filesystem —
    it makes the module untestable and surprises anyone who imports it
    for a single constant.
    """
    for d in _REQUIRED_DIRS:
        os.makedirs(d, exist_ok=True)


# ══════════════════════════════════════════════════════════════════════════════
# SERIAL PROTOCOL
# ══════════════════════════════════════════════════════════════════════════════

SERIAL_BAUD         = 115200
SERIAL_TIMEOUT_S    = 1.0
SERIAL_FRAME_PREFIX = "OSBAMS"

# Frame: OSBAMS,<seq>,<tick_ms>,<V_mV>,<I_mA>,<P_mW>,<T_C10>,<flags>,<status>
#
# T_C10 NOTE: this field carries tenths of a degree for protocol uniformity,
# but the TC74 sensor has 1 °C resolution. Values are therefore always
# multiples of 10 (240 = 24 °C, 250 = 25 °C). Sub-degree precision does
# not exist in the hardware.

STATUS_OK           = 0
STATUS_INA228_ERR   = 1
STATUS_TC74_ERR     = 2
STATUS_OVERTEMP     = 4
STATUS_UNDERVOLTAGE = 8
STATUS_OVERCURRENT  = 16


# ══════════════════════════════════════════════════════════════════════════════
# SAFETY LIMITS — hard stops enforced by BOTH firmware and desktop software
# These are the ONLY safety constants. There is no second set.
# ══════════════════════════════════════════════════════════════════════════════

SAFETY_MAX_TEMP_C      = 50.0     # °C  — auto-stop above this
SAFETY_MIN_VOLTAGE_MV  = 28_000   # mV  — absolute floor, never go below
SAFETY_MAX_VOLTAGE_MV  = 44_000   # mV  — flag if pack exceeds this at intake
SAFETY_MAX_CURRENT_A   = 10.0     # A   — stop if exceeded
SAFETY_RECOVERY_REST_S = 30       # s   — rest after discharge before OCV read


# ══════════════════════════════════════════════════════════════════════════════
# TEST DEFAULTS — starting values, overridable per test profile
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_CUTOFF_V       = 30.0    # V  — for 10S NMC; other chemistries differ
DEFAULT_CURRENT_A      = 3.0     # A
DEFAULT_SAMPLE_RATE_MS = 500     # ms — defined ONCE
DEFAULT_MAX_DURATION_H = 8.0     # h


# ══════════════════════════════════════════════════════════════════════════════
# SCORING — 7 components, must sum to 100
# ══════════════════════════════════════════════════════════════════════════════

SCORE_WEIGHTS = {
    "energy_retention":   25,
    "capacity_retention": 20,
    "thermal_behavior":   15,
    "voltage_sag":        15,
    "bms_cutoff":         10,
    "physical_condition": 10,
    "self_discharge":      5,
}
assert sum(SCORE_WEIGHTS.values()) == 100, "Score weights must sum to 100"

GRADE_BANDS = [
    (90, "A", "Strong reuse candidate"),
    (80, "B", "Reuse with normal monitoring"),
    (65, "C", "Limited or lower-power reuse"),
    (50, "D", "Restricted experimental use"),
    (0,  "F", "Recycle or engineering review"),
]

# SOH = 0.4 x SOH_Ah + 0.6 x SOH_Wh  (energy weighted higher)
SOH_AH_WEIGHT = 0.40
SOH_WH_WEIGHT = 0.60


# ══════════════════════════════════════════════════════════════════════════════
# ML PHASES — one consistent scheme
#
# The rule engine ALWAYS carries at least 50% weight. ML never outweighs
# the deterministic engineering scoring, regardless of dataset size.
# ══════════════════════════════════════════════════════════════════════════════

# Phase boundaries. Ranges are: < 10, 10-29, >= 30 (no overlap, no gap).
ML_PHASE_RULE_ONLY_MAX    = 10   # n <  10        -> rule only
ML_PHASE_EXPERIMENTAL_MAX = 30   # 10 <= n < 30   -> experimental assistance
                                 # n >= 30        -> ML assisted (max 50%)

# Weights per phase. rule + ml = 1.0 in every row.
# ML is CAPPED at 0.50 — it assists, it does not decide.
ML_PHASE_WEIGHTS = {
    "rule_only":    {"rule": 1.00, "ml": 0.00},   # n < 10
    "experimental": {"rule": 0.80, "ml": 0.20},   # 10 <= n < 30
    "assisted":     {"rule": 0.50, "ml": 0.50},   # n >= 30  (ML capped here)
}


def ml_phase_for(n_batteries: int) -> str:
    """Return the phase name for a given number of independent batteries."""
    if n_batteries < ML_PHASE_RULE_ONLY_MAX:
        return "rule_only"
    if n_batteries < ML_PHASE_EXPERIMENTAL_MAX:
        return "experimental"
    return "assisted"


def ml_weights_for(n_batteries: int) -> tuple:
    """Return (rule_weight, ml_weight) for a given dataset size."""
    w = ML_PHASE_WEIGHTS[ml_phase_for(n_batteries)]
    return w["rule"], w["ml"]


# ══════════════════════════════════════════════════════════════════════════════
# CALIBRATION
# ══════════════════════════════════════════════════════════════════════════════

CALIBRATION_INTERVAL_DAYS = 90
INA228_ACCURACY_PCT       = 0.5   # +/-0.5% typical, per datasheet
TC74_ACCURACY_C           = 2.0   # +/-2 C per datasheet
TC74_RESOLUTION_C         = 1.0   # whole degrees only — not 0.1 C


# ══════════════════════════════════════════════════════════════════════════════
# HARDWARE SCOPE — what is validated vs what is architectural
# ══════════════════════════════════════════════════════════════════════════════

# INA228 measures the pack directly. Its 85 V bus range covers a fully
# charged 10S NMC pack (42 V) with margin, so it is the production voltage,
# current, and power sensor — not a development-only part.
INA228_MAX_BUS_VOLTAGE_V = 85.0
INA228_SHUNT_MILLIOHM    = 2.0    # external shunt, Rev A starting value
INA228_IMAX_A            = 10.0   # expected full-scale current
INA228_SCOPE = (
    "INA228 with an external shunt measures bus voltage, shunt voltage, "
    "current, power, energy, and charge. Its 85 V bus rating covers the "
    "42 V maximum of a fully charged 10S NMC pack."
)

PRIMARY_DEVELOPMENT_TARGET = "10S NMC scooter battery packs"
CHEMISTRY_SCOPE = (
    "Architecture supports multiple battery categories and chemistries. "
    "Primary development target: 10S NMC scooter battery packs. "
    "No chemistry or category has been validated against hardware."
)

ELECTRONIC_LOAD_SCOPE = (
    "OSBAMS v1 uses a manually configured, appropriately rated DC electronic "
    "load. The specific instrument is selected at build time; the "
    "ElectronicLoad abstraction supports remote control when a programmable "
    "load is available."
)


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT VISION AND FRAMING
# ══════════════════════════════════════════════════════════════════════════════

VISION = (
    "Develop an open, modular engineering platform that standardizes the "
    "assessment, lifecycle tracking, and engineering decision support of "
    "second-life lithium battery assets across research, education, repair, "
    "and reuse."
)

THREE_QUESTIONS = {
    "Health":      "How much capacity and energy remain?",
    "Safety":      "Is this battery safe to handle and test?",
    "Suitability": "What applications is this battery suited for?",
}

FIVE_QUESTIONS = [
    "What battery asset is this?",
    "Is it safe?",
    "How healthy is it?",
    "How has it changed over time?",
    "What should we do with it next?",
]

ASSET_ATTRIBUTES = [
    "Identity", "Specifications", "Inspections", "Measurements",
    "Events", "History", "Recommendations", "Lifecycle",
]

PLATFORM_MODULES = [
    "Registration", "Inspection", "Measurement", "History",
    "Analytics", "Decision Support", "Lifecycle", "Reporting", "Knowledge",
]


# ══════════════════════════════════════════════════════════════════════════════
# STATUS — honest current state, used in README and About dialog
# ══════════════════════════════════════════════════════════════════════════════

PROJECT_STATUS = {
    "desktop_software":      "Feature-complete candidate",
    "firmware_architecture": "Advanced architecture partially implemented",
    "hardware_integration":  "Pending",
    "end_to_end_validation": "Pending",
}

STATUS_SUMMARY = (
    "OSBAMS has a mature desktop-software architecture and an expanded "
    "embedded-controller code structure. The original sensor-acquisition "
    "prototype exists and is verified in simulation. RTOS, USB CDC, CAN, "
    "ADC-DMA, watchdog, storage, calibration, and full hardware safety still "
    "require implementation and verification."
)
