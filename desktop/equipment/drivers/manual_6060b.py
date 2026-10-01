"""
equipment/drivers/manual_6060b.py — operator drives the 6060B front panel.

Software cannot command or verify the load. Every "set" is still validated
against the full envelope and answered with the maximum permitted setting, so
the operator is never told to dial in something the instrument/OSBAMS can't
take. This is the ONLY 6060B mode available until the SFSU GPIB path is
confirmed (6060B_REMOTE_CONTROL = BLOCKED_BY_INTERFACE_CONFIRMATION).
"""

from typing import Optional

from equipment import capability as cap
from equipment.drivers.base import ElectronicLoad, LoadStatus


class Manual6060B(ElectronicLoad):

    def __init__(self, **limits):
        super().__init__(**limits)
        self._connected = False
        self._last = (0.0, 0.0)          # operator-entered / OSBAMS-read (V, A)
        self.instructions: list = []     # what the operator was told to do

    def _say(self, msg: str) -> bool:
        self.instructions.append(msg)
        print(f"[Manual6060B] {msg}")
        return True

    @property
    def name(self) -> str: return "Manual 6060B (operator front panel)"
    @property
    def is_controllable(self) -> bool: return False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def identify(self) -> str:
        return "Agilent/Keysight 6060B (manual — identity not machine-verified)"

    def _ok(self, lim: cap.CurrentLimit, what: str) -> bool:
        return self._say(f"{what} on the panel. Permitted max here: "
                         f"{lim.final_a:.2f} A ({lim.limiting_factor}).")

    def set_cc(self, amps: float) -> bool:
        return self._ok(self._guard_current(amps), f"Select CC mode and set {amps:.3f} A")

    def set_cv(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool:
        return self._ok(self._guard_cv(volts, max_expected_current_a),
                        f"Select CV mode and set {volts:.2f} V")

    def set_cr(self, ohms: float) -> bool:
        return self._ok(self._guard_resistance(ohms), f"Select CR mode and set {ohms:.3f} ohm")

    def set_current(self, amps: float) -> bool: return self.set_cc(amps)
    def set_voltage(self, volts, max_expected_current_a=None) -> bool:
        return self.set_cv(volts, max_expected_current_a)
    def set_resistance(self, ohms: float) -> bool: return self.set_cr(ohms)

    def input_on(self) -> bool:
        self._say("ACTION REQUIRED: enable the load input on the panel.")
        return False                      # nothing was done by software

    def input_off(self) -> bool:
        self._say("*** ACTION REQUIRED: DISABLE LOAD INPUT NOW ***")
        return False                      # state unknown -> caller must alert operator

    def confirm_off_by_current(self, measured_current_a: float,
                               threshold_a: float = 0.1) -> bool:
        """Only verification available for a manual load: measured current ~ 0."""
        return abs(measured_current_a) <= threshold_a

    def record_front_panel(self, volts: float, amps: float) -> None:
        """Operator (or OSBAMS INA228) readings; used for envelope monitoring."""
        self._last = (volts, amps)
        self._pack_voltage_v = max(self._pack_voltage_v or 0.0, volts)

    def check_readback(self) -> Optional[str]:
        """Return a warning string if the last reading broke the envelope."""
        v, i = self._last
        try:
            cap.check_load_command(max(v, self._pack_voltage_v or 0.0), i, None,
                                   self.profile_current_limit_a,
                                   self.system_current_max_a, self.power_path,
                                   self.system_voltage_max_v)
        except cap.EnvelopeViolation as e:
            return str(e)
        return None

    def measure_voltage(self) -> float: return self._last[0]
    def measure_current(self) -> float: return self._last[1]
    def measure_power(self) -> float:   return self._last[0] * self._last[1]

    def configure_transient(self, low_a, high_a, freq_hz, duty_pct=50.0, mode="CONT") -> bool:
        for a in (low_a, high_a):
            self._guard_current(a)
        return self._say(f"Configure transient on the panel: {low_a:.3f}/{high_a:.3f} A, "
                         f"{freq_hz:g} Hz, {duty_pct:g}% ({mode}).")

    def trigger_transient(self) -> bool:
        return self._say("Press the front-panel trigger/transient key.") and False

    def read_status(self) -> LoadStatus:
        return LoadStatus(connected=self._connected, voltage_v=self._last[0],
                          current_a=self._last[1], power_w=self.measure_power(),
                          error="Manual mode — software cannot verify load state")

    def read_errors(self) -> list: return []
    def local(self) -> bool:  return True      # panel is always local
    def remote(self) -> bool: return False
