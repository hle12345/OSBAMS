"""
keysight_6060b/commands.py — the ONLY place SCPI strings for the 6060B live.

Source of truth is the official Agilent/Keysight documentation:
    Agilent 6060B/6063B Operating Manual and
    Electronic Load Family Programming Reference Guide (part no. 06060-90005).

HONEST STATUS OF THIS TABLE
---------------------------
The official PDFs could not be downloaded from the build environment (egress
blocked), so every entry carries a verification status instead of pretending:

  PUBLIC_EXCERPT  keyword seen in public excerpts of the Agilent manuals
                  (e.g. "MODE CURR" / "CURR 6" in the service-manual test
                  procedure; INP/OUTP alias, MEAS:CURR?, CURR:TLEV,
                  TRAN:MODE CONT in the programming material).
  SCPI_STANDARD   IEEE-488.2 common command or standard SCPI query keyword;
                  the 6060B is documented as SCPI-compliant. Read-only.
  UNVERIFIED      NOT confirmed against 06060-90005. Blocked by default.

The driver refuses UNVERIFIED commands unless constructed with
`allow_unverified=True`. To promote an entry: read the programming guide on the
physical manual/CD, fix the syntax if needed, change its status to
`MANUAL_CONFIRMED`, and record the page in `source`. Status registers are
returned RAW; bit meanings are deliberately not decoded until confirmed.
"""

from dataclasses import dataclass

PUBLIC_EXCERPT   = "PUBLIC_EXCERPT"
SCPI_STANDARD    = "SCPI_STANDARD"
MANUAL_CONFIRMED = "MANUAL_CONFIRMED"
UNVERIFIED       = "UNVERIFIED"

TRUSTED = frozenset({PUBLIC_EXCERPT, SCPI_STANDARD, MANUAL_CONFIRMED})


@dataclass(frozen=True)
class Cmd:
    template: str
    status: str
    source: str = ""
    query: bool = False

    def fmt(self, *args) -> str:
        return self.template.format(*args)


COMMANDS = {
    # identification / housekeeping
    "idn":          Cmd("*IDN?", SCPI_STANDARD, "IEEE-488.2 mandatory", True),
    "cls":          Cmd("*CLS",  SCPI_STANDARD, "IEEE-488.2 mandatory"),
    "stb":          Cmd("*STB?", SCPI_STANDARD, "IEEE-488.2 mandatory", True),
    "esr":          Cmd("*ESR?", SCPI_STANDARD, "IEEE-488.2 mandatory", True),
    "error":        Cmd("SYST:ERR?", SCPI_STANDARD, "SCPI standard query", True),
    # modes
    "mode_cc":      Cmd("MODE CURR", PUBLIC_EXCERPT, "6060B service manual GPIB test example"),
    "mode_cv":      Cmd("MODE VOLT", UNVERIFIED, "check 06060-90005 MODE command"),
    "mode_cr":      Cmd("MODE RES",  UNVERIFIED, "check 06060-90005 MODE command"),
    # setpoints
    "current":      Cmd("CURR {:.4f}", PUBLIC_EXCERPT, "service manual example 'CURR 6'"),
    "voltage":      Cmd("VOLT {:.4f}", UNVERIFIED),
    "resistance":   Cmd("RES {:.4f}",  UNVERIFIED),
    # input
    "input_on":     Cmd("INP ON",  PUBLIC_EXCERPT, "INPut command (OUTPut alias)"),
    "input_off":    Cmd("INP OFF", PUBLIC_EXCERPT, "INPut command (OUTPut alias)"),
    # measurement
    "meas_i":       Cmd("MEAS:CURR?", PUBLIC_EXCERPT, "MEAS:CURR? documented", True),
    "meas_v":       Cmd("MEAS:VOLT?", SCPI_STANDARD, "MEASure family documented for V/I/P", True),
    "meas_p":       Cmd("MEAS:POW?",  SCPI_STANDARD, "MEASure family documented for V/I/P", True),
    # transient
    "tran_mode":    Cmd("TRAN:MODE {}", PUBLIC_EXCERPT, "TRAN:MODE CONT seen; PULS/TOGG unverified"),
    "tran_level":   Cmd("CURR:TLEV {:.4f}", PUBLIC_EXCERPT, "transient (higher) level"),
    "tran_freq":    Cmd("TRAN:FREQ {:.4f}", UNVERIFIED),
    "tran_duty":    Cmd("TRAN:DCYC {:.2f}", UNVERIFIED),
    "tran_on":      Cmd("TRAN ON",  UNVERIFIED),
    "tran_off":     Cmd("TRAN OFF", UNVERIFIED),
    "tran_trigger": Cmd("*TRG",     UNVERIFIED, "confirm trigger source semantics"),
    # status (raw only)
    "oper_cond":    Cmd("STAT:OPER:COND?", SCPI_STANDARD, "SCPI; bit meanings NOT decoded", True),
    "ques_cond":    Cmd("STAT:QUES:COND?", SCPI_STANDARD, "SCPI; bit meanings NOT decoded", True),
    # remote/local — GPIB REN/GTL are transport-level; no SCPI string assumed
}
