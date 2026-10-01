"""
equipment/drivers/base.py — ElectronicLoad interface for the 6060B family.

Every concrete load routes EVERY setpoint through `_guard_current()` /
`_guard_resistance()` / `_guard_cv()`, which call capability.check_load_command
before anything reaches hardware (or the simulated hardware).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from equipment import capability as cap


class InterfaceBlocked(RuntimeError):
    """Remote control requested but no confirmed SFSU interface exists."""


class CommandNotVerified(RuntimeError):
    """Command not yet verified against the official 6060B programming manual."""


@dataclass
class LoadStatus:
    connected:  bool  = False
    input_on:   bool  = False
    mode:       str   = "CC"            # CC / CV / CR
    voltage_v:  float = 0.0
    current_a:  float = 0.0
    power_w:    float = 0.0
    setpoint:   float = 0.0             # amps (CC), volts (CV) or ohms (CR)
    flags:      list  = field(default_factory=list)   # e.g. ["OVERPOWER"]
    error:      str   = ""


class ElectronicLoad(ABC):
    """Common interface. Concrete classes: Keysight6060B, Manual6060B, Simulator6060B."""

    def __init__(self, profile_current_limit_a: Optional[float] = None,
                 system_current_max_a: Optional[float] = None,
                 power_path: cap.PowerPathLimits = cap.REV2_POWER_PATH,
                 system_voltage_max_v: Optional[float] = None):
        self.system_voltage_max_v = system_voltage_max_v
        self.profile_current_limit_a = profile_current_limit_a
        self.system_current_max_a = system_current_max_a
        self.power_path = power_path
        self._pack_voltage_v: Optional[float] = None

    # ── envelope guard ──────────────────────────────────────────────────
    def set_pack_voltage(self, volts: Optional[float]) -> None:
        """Highest voltage the pack can present (see conservative_pack_voltage)."""
        self._pack_voltage_v = volts

    def _pack_voltage_for_limit(self) -> Optional[float]:
        """Hook: remote/simulated loads refresh from the instrument."""
        return self._pack_voltage_v

    def permitted_current(self) -> cap.CurrentLimit:
        return cap.compute_permitted_current(
            self._pack_voltage_for_limit(), self.profile_current_limit_a,
            self.system_current_max_a, self.power_path, self.system_voltage_max_v)

    def _guard_current(self, amps: float) -> cap.CurrentLimit:
        v = self._pack_voltage_for_limit()
        if v is None:
            raise cap.EnvelopeViolation("pack voltage unknown — measure OCV first")
        return cap.check_load_command(v, amps, None, self.profile_current_limit_a,
                                      self.system_current_max_a, self.power_path,
                                      self.system_voltage_max_v)

    def _guard_resistance(self, ohms: float) -> cap.CurrentLimit:
        if ohms <= 0:
            raise cap.EnvelopeViolation("resistance must be > 0")
        v = self._pack_voltage_for_limit()
        if v is None:
            raise cap.EnvelopeViolation("pack voltage unknown — measure OCV first")
        # CR draws I = V / R at the HIGHEST pack voltage.
        return cap.check_load_command(v, v / ohms, None, self.profile_current_limit_a,
                                      self.system_current_max_a, self.power_path,
                                      self.system_voltage_max_v)

    def _guard_cv(self, volts: float, max_expected_current_a: Optional[float]) -> cap.CurrentLimit:
        """
        CV mode sinks whatever current holds the voltage, which cannot be
        bounded from the setpoint alone. The caller must state the maximum
        current it expects (pack V - setpoint over total series resistance)
        and that figure is checked against the envelope.
        """
        if max_expected_current_a is None:
            raise cap.EnvelopeViolation(
                "CV mode needs max_expected_current_a — current is not bounded by the setpoint")
        v = self._pack_voltage_for_limit()
        if v is None:
            raise cap.EnvelopeViolation("pack voltage unknown — measure OCV first")
        if not (cap.INSTRUMENT_VOLTAGE_MIN_V <= volts <= cap.INSTRUMENT_VOLTAGE_MAX_V):
            raise cap.EnvelopeViolation(
                f"CV setpoint {volts:.2f} V outside 6060B {cap.INSTRUMENT_VOLTAGE_MIN_V:g}-"
                f"{cap.INSTRUMENT_VOLTAGE_MAX_V:g} V")
        return cap.check_load_command(v, max_expected_current_a, None,
                                      self.profile_current_limit_a,
                                      self.system_current_max_a, self.power_path,
                                      self.system_voltage_max_v)

    # ── interface ───────────────────────────────────────────────────────
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def is_controllable(self) -> bool:
        """False for Manual6060B — the operator controls the hardware."""

    @abstractmethod
    def connect(self) -> bool: ...
    @abstractmethod
    def disconnect(self) -> None: ...
    @abstractmethod
    def identify(self) -> str: ...

    @abstractmethod
    def set_cc(self, amps: float) -> bool: ...
    @abstractmethod
    def set_cv(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool: ...
    @abstractmethod
    def set_cr(self, ohms: float) -> bool: ...

    @abstractmethod
    def set_current(self, amps: float) -> bool: ...
    @abstractmethod
    def set_voltage(self, volts: float, max_expected_current_a: Optional[float] = None) -> bool: ...
    @abstractmethod
    def set_resistance(self, ohms: float) -> bool: ...

    @abstractmethod
    def input_on(self) -> bool: ...
    @abstractmethod
    def input_off(self) -> bool:
        """True ONLY if the input is known to be off."""

    @abstractmethod
    def measure_voltage(self) -> float: ...
    @abstractmethod
    def measure_current(self) -> float: ...
    @abstractmethod
    def measure_power(self) -> float: ...

    @abstractmethod
    def configure_transient(self, low_a: float, high_a: float, freq_hz: float,
                            duty_pct: float = 50.0, mode: str = "CONT") -> bool: ...
    @abstractmethod
    def trigger_transient(self) -> bool: ...

    @abstractmethod
    def read_status(self) -> LoadStatus: ...
    @abstractmethod
    def read_errors(self) -> list: ...

    @abstractmethod
    def local(self) -> bool: ...
    @abstractmethod
    def remote(self) -> bool: ...
