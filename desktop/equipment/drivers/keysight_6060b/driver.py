"""
keysight_6060b/driver.py — Keysight/Agilent 6060B over GPIB/SCPI.

Safety properties:
  * connect() refuses unless the operator asserts `interface_confirmed=True`
    (REMOTE_CONTROL_STATUS == BLOCKED_BY_INTERFACE_CONFIRMATION until then).
  * every setpoint passes capability.check_load_command BEFORE any write.
  * the pack voltage used for the 300 W check is max(caller-supplied OCV,
    live reading) so a loaded (sagged) reading can never relax the limit.
  * an operation runs only if EVERY command it needs is VERIFIED against the
    official manuals (commands.py). Today none are, so every remote
    operation is blocked (CommandNotVerified).
"""

from typing import Optional

from equipment import capability as cap
from equipment.drivers.base import (ElectronicLoad, LoadStatus,
                                    InterfaceBlocked, CommandNotVerified)
from .commands import COMMANDS, OPERATIONS, Cmd, unverified_for
from .transport import Transport, PyVisaTransport


class Keysight6060B(ElectronicLoad):

    def __init__(self, resource: Optional[str] = None,
                 transport: Optional[Transport] = None,
                 interface_confirmed: bool = False,
                 evidence: Optional[dict] = None, **limits):
        """`evidence` overrides command status — a TEST HOOK, never for production."""
        super().__init__(**limits)
        self._resource = resource
        self._t: Optional[Transport] = transport
        self._interface_confirmed = interface_confirmed
        self._evidence = evidence
        self._connected = False
        self._input_on = False
        self._mode = "CC"
        self._setpoint = 0.0
        self._idn = ""
        self._last_error = ""

    # ── low level ───────────────────────────────────────────────────────
    def _require(self, operation: str) -> None:
        bad = unverified_for(operation, self._evidence)
        if bad:
            raise CommandNotVerified(
                f"operation '{operation}' blocked: command(s) {bad} not VERIFIED "
                f"against the official 6060B manuals (see 6060B_COMMAND_EVIDENCE.md)")

    def _cmd(self, key: str) -> Cmd:
        return COMMANDS[key]

    def _send(self, key: str, *args) -> None:
        if not self._connected:
            raise ConnectionError("6060B not connected")
        self._t.write(self._cmd(key).fmt(*args))

    def _ask(self, key: str) -> str:
        if not self._connected:
            raise ConnectionError("6060B not connected")
        return self._t.query(self._cmd(key).fmt())

    # ── ElectronicLoad ──────────────────────────────────────────────────
    @property
    def name(self) -> str:
        return f"Keysight/Agilent 6060B ({self._resource or 'transport'})"

    @property
    def is_controllable(self) -> bool:
        return True

    def connect(self) -> bool:
        if not self._interface_confirmed:
            raise InterfaceBlocked(
                f"6060B remote control = {cap.REMOTE_CONTROL_STATUS}. Confirm a "
                f"USB-GPIB adapter, LAN-GPIB gateway or GPIB PC, then pass "
                f"interface_confirmed=True. Use Manual6060B meanwhile.")
        self._require("connect")
        try:
            if self._t is None:
                if not self._resource:
                    raise InterfaceBlocked("no VISA resource or transport supplied")
                self._t = PyVisaTransport(self._resource)
            self._connected = True
            self._idn = self.identify()
            ok = "6060" in self._idn
            if not ok:
                self._last_error = f"unexpected instrument: {self._idn!r}"
                self._connected = False
            return ok
        except InterfaceBlocked:
            raise
        except Exception as e:
            self._last_error = str(e)
            self._connected = False
            return False

    def disconnect(self) -> None:
        if self._connected:
            try:
                self.input_off()
                self.local()
            except CommandNotVerified as e:
                self._last_error = str(e)
            finally:
                self._connected = False
                if self._t:
                    self._t.close()

    def identify(self) -> str:
        self._require("identify")
        return self._ask("idn")

    def _pack_voltage_for_limit(self) -> Optional[float]:
        live = None
        if self._connected:
            try:
                live = self.measure_voltage()
            except Exception:
                live = None
        return cap.conservative_pack_voltage(self._pack_voltage_v, live)

    def _enter_mode(self, key: str, mode: str) -> None:
        if self._mode != mode and self._input_on:
            self.input_off()            # never change mode with input live
        self._send(key)
        self._mode = mode

    def set_cc(self, amps: float) -> bool:
        self._require("set_cc")
        self._guard_current(amps)
        self._enter_mode("mode_cc", "CC")
        return self.set_current(amps)

    def set_cv(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool:
        self._require("set_cv")
        self._guard_cv(volts, max_expected_current_a)
        self._enter_mode("mode_cv", "CV")
        return self.set_voltage(volts, max_expected_current_a)

    def set_cr(self, ohms: float) -> bool:
        self._require("set_cr")
        self._guard_resistance(ohms)
        self._enter_mode("mode_cr", "CR")
        return self.set_resistance(ohms)

    def set_current(self, amps: float) -> bool:
        self._require("set_current")
        self._guard_current(amps)
        self._send("current", amps)
        self._setpoint = amps
        return True

    def set_voltage(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool:
        self._require("set_voltage")
        self._guard_cv(volts, max_expected_current_a)
        self._send("voltage", volts)
        self._setpoint = volts
        return True

    def set_resistance(self, ohms: float) -> bool:
        self._require("set_resistance")
        self._guard_resistance(ohms)
        self._send("resistance", ohms)
        self._setpoint = ohms
        return True

    def input_on(self) -> bool:
        self._require("input_on")
        if self._mode == "CC":
            self._guard_current(self._setpoint)         # re-check at enable time
        elif self._mode == "CR":
            self._guard_resistance(self._setpoint)
        self._send("input_on")
        self._input_on = True
        return True

    def input_off(self) -> bool:
        self._require("input_off")
        self._send("input_off")             # always allowed — it is the safe state
        self._input_on = False
        return True

    def _meas(self, key: str) -> float:
        return float(self._ask(key))

    def measure_voltage(self) -> float:
        self._require("measure_voltage"); return self._meas("meas_v")

    def measure_current(self) -> float:
        self._require("measure_current"); return self._meas("meas_i")

    def measure_power(self) -> float:
        self._require("measure_power"); return self._meas("meas_p")

    def configure_transient(self, low_a: float, high_a: float, freq_hz: float,
                            duty_pct: float = 50.0, mode: str = "CONT") -> bool:
        """
        Both levels are checked; the HIGHER one is what must fit the envelope.
        `low_a` is the normal CURR level, `high_a` the transient level.
        """
        self._require("configure_transient")
        mode = mode.upper()
        if mode not in ("CONT", "PULS", "TOGG"):
            raise ValueError("transient mode must be CONT, PULS or TOGG")
        if not (0 < duty_pct < 100) or freq_hz <= 0:
            raise ValueError("invalid transient frequency/duty")
        for a in (low_a, high_a):
            self._guard_current(a)
        self._enter_mode("mode_cc", "CC")
        self.set_current(low_a)
        self._send("tran_mode", mode)
        self._send("tran_level", high_a)
        self._send("tran_freq", freq_hz)
        self._send("tran_duty", duty_pct)
        self._send("tran_on")
        return True

    def trigger_transient(self) -> bool:
        self._require("trigger_transient")
        self._send("tran_trigger")
        return True

    def read_status(self) -> LoadStatus:
        """Raw registers only — bit meanings are not decoded until verified."""
        self._require("read_status")
        try:
            v, i = self.measure_voltage(), self.measure_current()
            st = LoadStatus(connected=True, input_on=self._input_on, mode=self._mode,
                            voltage_v=v, current_a=i, power_w=round(v * i, 3),
                            setpoint=self._setpoint)
            st.flags = [f"STB={self._ask('stb').strip()}",
                        f"OPER_COND={self._ask('oper_cond').strip()}",
                        f"QUES_COND={self._ask('ques_cond').strip()}"]
            return st
        except Exception as e:
            return LoadStatus(connected=self._connected, error=str(e))

    def read_errors(self) -> list:
        """Drain SYST:ERR? until '0,...' (max 20 reads)."""
        self._require("read_errors")
        errs = []
        for _ in range(20):
            r = self._ask("error").strip()
            if r.startswith("0") or r.startswith("+0"):
                break
            errs.append(r)
        return errs

    def local(self) -> bool:
        self._require("local")
        go = getattr(self._t, "go_to_local", None)
        return bool(go()) if go else False

    def remote(self) -> bool:
        self._require("remote")
        # GPIB remote state is entered by addressing the instrument (REN);
        # any query/write does so. No SCPI string is assumed.
        return self._connected
