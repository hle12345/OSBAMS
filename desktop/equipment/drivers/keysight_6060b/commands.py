"""
keysight_6060b/commands.py — the ONLY place SCPI strings for the 6060B live,
together with their evidence.

Official sources (the only acceptable evidence):
  [PRG] Electronic Load Family Programming Reference Manual
        (covers 6060B/6063B and related loads; Agilent/Keysight part 06060-90005)
  [OPM] 6060B/6063B Single Input Electronic Loads Operating Manual
        (Keysight part 5951-2826)

STATUS: every entry is UNVERIFIED.
  The build environment's network policy blocks www.keysight.com, so neither
  manual could be read when this table was written. The command strings below
  are CANDIDATES (they appeared in public excerpts or follow SCPI convention)
  and are NOT evidence. `section` is "NOT LOCATED" for the same reason.

RULE: a remote operation is enabled only if EVERY command it needs is VERIFIED.
  To promote a command: read it in [PRG]/[OPM], correct the string if needed,
  fill `document` and `section` (section + page), and set status VERIFIED.
  `tests/test_rev2_equipment.py` fails if a VERIFIED row has no section/page.
Status registers are returned raw; bit meanings are not decoded.
"""

from dataclasses import dataclass, replace
from typing import Optional

VERIFIED   = "VERIFIED"
UNVERIFIED = "UNVERIFIED"

PRG = "Electronic Load Family Programming Reference Manual"
OPM = "6060B/6063B Single Input Electronic Loads Operating Manual"
NOT_LOCATED = "NOT LOCATED"


@dataclass(frozen=True)
class Cmd:
    key: str
    template: str                  # candidate/verified exact command (str.format)
    document: str = PRG            # where it must be / was verified
    section: str = NOT_LOCATED     # "<section>, p.<n>" once verified
    status: str = UNVERIFIED
    query: bool = False
    note: str = ""

    def fmt(self, *args) -> str:
        return self.template.format(*args)


_C = [
    Cmd("idn",          "*IDN?", query=True),
    Cmd("mode_cc",      "MODE CURR"),
    Cmd("mode_cv",      "MODE VOLT"),
    Cmd("mode_cr",      "MODE RES"),
    Cmd("current",      "CURR {:.4f}"),
    Cmd("voltage",      "VOLT {:.4f}"),
    Cmd("resistance",   "RES {:.4f}"),
    Cmd("input_on",     "INP ON"),
    Cmd("input_off",    "INP OFF"),
    Cmd("meas_v",       "MEAS:VOLT?", query=True),
    Cmd("meas_i",       "MEAS:CURR?", query=True),
    Cmd("meas_p",       "MEAS:POW?",  query=True),
    Cmd("tran_mode",    "TRAN:MODE {}"),
    Cmd("tran_level",   "CURR:TLEV {:.4f}"),
    Cmd("tran_freq",    "TRAN:FREQ {:.4f}"),
    Cmd("tran_duty",    "TRAN:DCYC {:.2f}"),
    Cmd("tran_on",      "TRAN ON"),
    Cmd("tran_trigger", "*TRG", note="confirm trigger source semantics"),
    Cmd("stb",          "*STB?", query=True),
    Cmd("oper_cond",    "STAT:OPER:COND?", query=True),
    Cmd("ques_cond",    "STAT:QUES:COND?", query=True),
    Cmd("error",        "SYST:ERR?", query=True),
    Cmd("gpib_local",   "(GPIB go-to-local)", document=OPM,
        note="front-panel Local/lock behaviour and GTL handling — bus message, not SCPI"),
]
COMMANDS = {c.key: c for c in _C}

# operation -> every command it needs
OPERATIONS = {
    "identify":            ("idn",),
    "connect":             ("idn",),
    "set_cc":              ("mode_cc", "current"),
    "set_cv":              ("mode_cv", "voltage"),
    "set_cr":              ("mode_cr", "resistance"),
    "set_current":         ("current",),
    "set_voltage":         ("voltage",),
    "set_resistance":      ("resistance",),
    "input_on":            ("input_on",),
    "input_off":           ("input_off",),
    "measure_voltage":     ("meas_v",),
    "measure_current":     ("meas_i",),
    "measure_power":       ("meas_p",),
    "configure_transient": ("mode_cc", "current", "tran_mode", "tran_level",
                            "tran_freq", "tran_duty", "tran_on"),
    "trigger_transient":   ("tran_trigger",),
    "read_status":         ("meas_v", "meas_i", "stb", "oper_cond", "ques_cond"),
    "read_errors":         ("error",),
    "local":               ("gpib_local",),
    "remote":              ("gpib_local",),
}


def status_of(key: str, evidence: Optional[dict] = None) -> str:
    """Status of a command; `evidence` overrides are a TEST HOOK only."""
    if evidence and key in evidence:
        return evidence[key]
    return COMMANDS[key].status


def unverified_for(operation: str, evidence: Optional[dict] = None) -> list:
    return [k for k in OPERATIONS[operation] if status_of(k, evidence) != VERIFIED]


def operation_enabled(operation: str, evidence: Optional[dict] = None) -> bool:
    return not unverified_for(operation, evidence)


def evidence_rows() -> list:
    """(operation, exact command(s), official document, section/page, status)."""
    rows = []
    for op, keys in OPERATIONS.items():
        cmds = [COMMANDS[k] for k in keys]
        st = VERIFIED if all(status_of(k) == VERIFIED for k in keys) else UNVERIFIED
        rows.append((op, "; ".join(c.template for c in cmds),
                     "; ".join(sorted({c.document for c in cmds})),
                     "; ".join(sorted({c.section for c in cmds})), st))
    return rows
