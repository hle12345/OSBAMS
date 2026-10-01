"""
services/electronic_load.py — Electronic Load Abstraction Layer

Architecture from ChatGPT screenshot:
    class ElectronicLoad:
        connect(), set_mode(), set_current(), set_power(),
        input_on(), input_off(), read_status()

Implementations:
    ManualLoad     — operator controls load manually; software only measures
    OwonLoad       — OWON OEL1515 via USB-CDC SCPI
    SimulatorLoad  — synthetic discharge curve for development

Keeps software independent of one specific instrument.
"""

import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LoadStatus:
    connected:   bool  = False
    input_on:    bool  = False
    mode:        str   = "CC"          # CC / CV / CR / CP
    voltage_v:   float = 0.0
    current_a:   float = 0.0
    power_w:     float = 0.0
    error:       str   = ""


class ElectronicLoad(ABC):
    """Base class — all load implementations share this interface."""

    @abstractmethod
    def connect(self) -> bool:
        """Open connection. Returns True on success."""
        ...

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        ...

    @abstractmethod
    def set_mode(self, mode: str):
        """Set operating mode: 'CC', 'CV', 'CR', 'CP'."""
        ...

    @abstractmethod
    def set_current(self, amps: float):
        """Set constant-current setpoint."""
        ...

    @abstractmethod
    def set_power(self, watts: float):
        """Set constant-power setpoint."""
        ...

    @abstractmethod
    def input_on(self) -> bool:
        """Enable load input. Returns True on success."""
        ...

    @abstractmethod
    def input_off(self) -> bool:
        """Disable load input. Returns True on success."""
        ...

    @abstractmethod
    def read_status(self) -> LoadStatus:
        """Read current load state."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def is_controllable(self) -> bool:
        """False for ManualLoad — operator controls hardware directly."""
        ...

    def lock_front_panel(self, locked: bool = True) -> bool:
        """
        Lock the instrument front panel during an automated test.

        Without this, an operator can turn a knob mid-test and change the
        discharge current with the software none the wiser — the recorded
        setpoint and the actual current diverge silently.

        Pattern adopted from mbA2D/Test_Equipment_Control (Eload_BK8600).
        Default returns False: no action taken. Remote instruments override
        this with SYST:REM / SYST:LOC.
        """
        return False


# ── ManualLoad ────────────────────────────────────────────────────────────────

class ManualLoad(ElectronicLoad):
    """
    Operator controls the physical load manually.
    Software only measures and logs; cannot command the load.
    Used with OWON OEL1515 in manual mode (v1 OSBAMS).
    """

    def __init__(self):
        self._connected = False

    @property
    def name(self) -> str: return "Manual Load (operator controlled)"

    @property
    def is_controllable(self) -> bool: return False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def set_mode(self, mode: str):
        print(f"[ManualLoad] Set mode to {mode} manually on the load panel.")

    def set_current(self, amps: float):
        print(f"[ManualLoad] Set {amps:.2f} A manually on the load panel.")

    def set_power(self, watts: float):
        print(f"[ManualLoad] Set {watts:.1f} W manually on the load panel.")

    def input_on(self) -> bool:
        """
        Cannot enable a manual load from software.
        Returns False because no action was performed.
        """
        print("[ManualLoad] ACTION REQUIRED: enable load input on the panel.")
        return False

    def input_off(self) -> bool:
        """
        SAFETY CRITICAL — cannot disable a manual load from software.

        Returns False because no hardware action occurred. The caller must
        treat this as "load state unknown" and alert the operator. Returning
        True here would make software safety detection a warning that looks
        like protection.

        Verify load-off by one of:
          - operator confirmation at the panel
          - measured current below threshold (confirm_off_by_current)
          - STM32 load-enable line, if the load has a remote inhibit input
        """
        print("[ManualLoad] *** ACTION REQUIRED: DISABLE LOAD INPUT NOW ***")
        return False

    def confirm_off_by_current(self, measured_current_a: float,
                                threshold_a: float = 0.1) -> bool:
        """
        Infer that the load stopped from measured current.
        This is the only verification available for a manual load.
        """
        return abs(measured_current_a) <= threshold_a

    def read_status(self) -> LoadStatus:
        return LoadStatus(connected=self._connected,
                          mode="CC",
                          error="Manual mode — software cannot verify load state")


# ── OwonLoad ──────────────────────────────────────────────────────────────────

class OwonLoad(ElectronicLoad):
    """
    OWON OEL1515 / OEL300 via USB-CDC.
    Uses SCPI-like commands over serial.
    Requires: pip install pyserial
    """

    def __init__(self, port: str, baud: int = 115200):
        self._port = port
        self._baud = baud
        self._ser  = None

    @property
    def name(self) -> str: return f"OWON Electronic Load ({self._port})"

    @property
    def is_controllable(self) -> bool: return True

    def connect(self) -> bool:
        try:
            import serial
            self._ser = serial.Serial(self._port, self._baud, timeout=2)
            time.sleep(0.5)
            resp = self._cmd("*IDN?")
            return "OWON" in resp.upper() or len(resp) > 0
        except Exception as e:
            print(f"[OwonLoad] connect error: {e}")
            return False

    def disconnect(self):
        if self._ser:
            try:    self.input_off()
            except: pass
            self._ser.close()
            self._ser = None

    def _cmd(self, cmd: str) -> str:
        if not self._ser:
            return ""
        self._ser.write((cmd + "\n").encode())
        time.sleep(0.05)
        return self._ser.readline().decode("ascii", errors="ignore").strip()

    def set_mode(self, mode: str):
        modes = {"CC": "CURR", "CV": "VOLT", "CR": "RES", "CP": "POW"}
        self._cmd(f":FUNC {modes.get(mode, 'CURR')}")

    def set_current(self, amps: float):
        self._cmd(f":CURR:STAT:L1 {amps:.3f}")

    def set_power(self, watts: float):
        self._cmd(f":POW:STAT:L1 {watts:.2f}")

    def lock_front_panel(self, locked: bool = True) -> bool:
        """SCPI remote mode locks the panel; local mode releases it."""
        self._cmd("SYST:REM" if locked else "SYST:LOC")
        return True

    def input_on(self) -> bool:
        self._cmd(":INP ON")
        return True

    def input_off(self) -> bool:
        self._cmd(":INP OFF")
        return True

    def read_status(self) -> LoadStatus:
        try:
            v = float(self._cmd(":MEAS:VOLT?") or 0)
            i = float(self._cmd(":MEAS:CURR?") or 0)
            return LoadStatus(connected=True, input_on=True,
                              voltage_v=v, current_a=i, power_w=round(v*i, 3))
        except Exception as e:
            return LoadStatus(connected=False, error=str(e))


# ── SimulatorLoad ─────────────────────────────────────────────────────────────

class SimulatorLoad(ElectronicLoad):
    """
    Generates synthetic discharge data for development and testing.
    Emits data through a serial-compatible queue so the existing
    SerialReader thread works unchanged.

    Profiles:
        normal     — healthy battery (15.3 Ah rated, ~13 Ah actual)
        degraded   — 65% SOH, moderate sag, early BMS cutoff
        hot        — overheating during discharge
        weak       — low capacity, high sag
        fail       — sensor loss partway through

    Usage:
        sim = SimulatorLoad(profile="normal")
        sim.connect()
        lines = sim.get_lines(n=100)   # list of OSBAMS CSV strings
    """

    PROFILES = {
        "normal": {
            "rated_ah": 15.3, "soh": 0.88, "start_v": 42.0,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 25.0, "temp_rise": 10.0, "sag_v": 1.2,
        },
        "degraded": {
            "rated_ah": 15.3, "soh": 0.65, "start_v": 41.5,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 25.0, "temp_rise": 16.0, "sag_v": 2.8,
        },
        "hot": {
            "rated_ah": 15.3, "soh": 0.80, "start_v": 41.8,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 26.0, "temp_rise": 28.0, "sag_v": 1.5,
        },
        "weak": {
            "rated_ah": 15.3, "soh": 0.45, "start_v": 40.0,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 25.0, "temp_rise": 12.0, "sag_v": 5.0,
        },
        "cold": {
            "rated_ah": 15.3, "soh": 0.70, "start_v": 40.5,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 5.0, "temp_rise": 6.0, "sag_v": 3.5,
        },
        "high_resistance": {
            "rated_ah": 15.3, "soh": 0.72, "start_v": 41.0,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 26.0, "temp_rise": 22.0, "sag_v": 7.5,
        },
        "cell_imbalance": {
            "rated_ah": 15.3, "soh": 0.60, "start_v": 41.8,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 25.0, "temp_rise": 14.0, "sag_v": 4.0,
        },
        "overtemp": {
            "rated_ah": 15.3, "soh": 0.82, "start_v": 41.9,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 30.0, "temp_rise": 32.0, "sag_v": 1.8,
        },
        "fail": {
            "rated_ah": 15.3, "soh": 0.75, "start_v": 41.9,
            "cutoff_v": 31.0, "current_a": 3.0,
            "temp_start": 25.0, "temp_rise": 8.0, "sag_v": 1.8,
        },
    }

    def __init__(self, profile: str = "normal", sample_rate_ms: int = 500):
        self._profile_name = profile
        self._p            = self.PROFILES.get(profile, self.PROFILES["normal"])
        self._sample_ms    = sample_rate_ms
        self._connected    = False

    @property
    def name(self) -> str: return f"Simulator ({self._profile_name})"

    @property
    def is_controllable(self) -> bool: return True

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def set_mode(self, mode: str): pass
    def set_current(self, amps: float): self._p["current_a"] = amps
    def set_power(self, watts: float): pass

    def input_on(self) -> bool:
        return True

    def input_off(self) -> bool:
        return True

    def read_status(self) -> LoadStatus:
        return LoadStatus(connected=self._connected, input_on=True, mode="CC",
                          current_a=self._p["current_a"])

    def generate_lines(self) -> list[str]:
        """
        Generate the full discharge as OSBAMS CSV lines.
        Returns a list of strings ready to feed into the serial parser.
        """
        import math
        p = self._p
        actual_ah  = p["rated_ah"] * p["soh"]
        current_a  = p["current_a"]
        dur_h      = actual_ah / current_a
        dur_ms     = int(dur_h * 3600 * 1000)
        steps      = dur_ms // self._sample_ms
        fail_at    = int(steps * 0.7) if self._profile_name == "fail" else -1

        lines = []
        seq   = 0

        for i in range(steps):
            t_ms = i * self._sample_ms
            progress = i / steps

            # Voltage: starts high, falls with slight S-curve
            v_range = p["start_v"] - p["cutoff_v"]
            v_drop  = v_range * (progress ** 0.8)
            voltage = p["start_v"] - v_drop
            if i == 1:   # initial sag when load applied
                voltage -= p["sag_v"]

            # Current (slight variation)
            current = current_a * (1.0 + 0.02 * math.sin(progress * 6))

            # Power
            power = voltage * current

            # Temperature: rises then plateaus
            temp = p["temp_start"] + p["temp_rise"] * (1 - math.exp(-progress * 3))

            # Status flag
            status = 0
            if temp > 50:   status |= 4    # overtemp
            if voltage < 30: status |= 8   # undervoltage

            # Simulate sensor failure
            if i == fail_at and self._profile_name == "fail":
                from services.protocol import encode_data_frame, FLAG_SENSOR_ERR
                lines.append(encode_data_frame(
                    seq=seq, tick_ms=t_ms,
                    voltage_mv=int(voltage*1000),
                    current_ma=int(current*1000),
                    power_mw=int(power*1000),
                    temp_c10=int(temp)*10,
                    flags=status | FLAG_SENSOR_ERR,
                    state="DISCHARGING"))
                # Gap — a few missing samples
                seq += 1
                continue

            # Protocol v1 frame with CRC — uses the shared encoder so the
            # simulator can never drift from the real firmware format.
            from services.protocol import encode_data_frame
            state = "DISCHARGE" if progress < 0.98 else "CUTOFF"
            state = "DISCHARGING" if state == "DISCHARGE" else state
            lines.append(encode_data_frame(
                seq=seq, tick_ms=t_ms,
                voltage_mv=int(voltage*1000),
                current_ma=int(current*1000),
                power_mw=int(power*1000),
                temp_c10=int(temp)*10,      # TC74 is 1 C resolution
                flags=status, state=state))
            seq += 1

        return lines


# ── Stubs for future instruments ──────────────────────────────────────────────

class Agilent6060BLoad(ElectronicLoad):
    """Placeholder — Agilent 6060B via GPIB/RS-232."""
    @property
    def name(self): return "Agilent 6060B (not implemented)"
    @property
    def is_controllable(self): return False
    def connect(self): return False
    def disconnect(self): pass
    def set_mode(self, m): pass
    def set_current(self, a): pass
    def set_power(self, w): pass
    def input_on(self): return False
    def input_off(self): return False
    def read_status(self): return LoadStatus(error="Not implemented")


class RigolLoad(ElectronicLoad):
    """Placeholder — Rigol DL3000 series."""
    @property
    def name(self): return "Rigol DL3000 (not implemented)"
    @property
    def is_controllable(self): return False
    def connect(self): return False
    def disconnect(self): pass
    def set_mode(self, m): pass
    def set_current(self, a): pass
    def set_power(self, w): pass
    def input_on(self): return False
    def input_off(self): return False
    def read_status(self): return LoadStatus(error="Not implemented")


# ── Factory ───────────────────────────────────────────────────────────────────

def create_load(load_type: str, **kwargs) -> ElectronicLoad:
    """
    Factory function.
    load_type: "manual" | "owon" | "simulator" | "agilent" | "rigol"
    """
    types = {
        "manual":    ManualLoad,
        "owon":      OwonLoad,
        "simulator": SimulatorLoad,
        "agilent":   Agilent6060BLoad,
        "rigol":     RigolLoad,
    }
    cls = types.get(load_type.lower(), ManualLoad)
    return cls(**kwargs)


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Simulator self-test ===")
    for profile in ["normal", "degraded", "hot", "weak"]:
        sim   = SimulatorLoad(profile=profile, sample_rate_ms=5000)
        lines = sim.generate_lines()
        print(f"  {profile:<10}  {len(lines):>5} samples  first: {lines[0][:60]}...")
    print("✓ electronic_load.py self-test passed")
