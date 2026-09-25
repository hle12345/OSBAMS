"""
serial_reader.py — Background thread that reads OSBAMS Protocol v1 frames
and emits parsed measurements as Qt signals.

The frame format is defined authoritatively in services/protocol.py.
This module does not redefine it — it imports the parser.

Malformed frames are never silently discarded. Every parse failure is
counted in StreamStats and surfaced through the frame_error signal so the
operator can see link quality during a test.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal

from services.protocol import (
    parse_frame, StreamStats, OsbamsSample,
    PROTOCOL_VERSION, FRAME_PREFIX,
)
from config import SERIAL_BAUD, SERIAL_TIMEOUT_S


def list_serial_ports() -> list[str]:
    """Return available serial port device names."""
    return [p.device for p in serial.tools.list_ports.comports()]

def list_serial_ports() -> list[str]:
    """Return available serial port device names."""
    return [p.device for p in serial.tools.list_ports.comports()]

# Alias for callers expecting this name (e.g. gui/tabs/dashboard_tab.py)
list_ports = list_serial_ports

class SerialReader(QThread):
    """
    Reads Protocol v1 frames from a serial port.

    Signals:
        sample_received(OsbamsSample) — a valid, CRC-checked DATA frame
        info_received(str, list)      — BOOT / SENSOR / STATE / FAULT frame
        frame_error(str)              — a malformed frame, with reason
        stats_updated(StreamStats)    — periodic link-quality report
        connection_lost(str)          — port closed or read failure
    """

    sample_received = Signal(object)
    info_received   = Signal(str, list)
    frame_error     = Signal(str)
    stats_updated   = Signal(object)
    connection_lost = Signal(str)

    STATS_EVERY_N_FRAMES = 20

    def __init__(self, port: str,
                 baud: int = SERIAL_BAUD,
                 strict_crc: bool = True,
                 allow_legacy: bool = False):
        super().__init__()
        self._port         = port
        self._baud         = baud
        self._strict_crc   = strict_crc
        self._allow_legacy = allow_legacy
        self._running      = False
        self.stats         = StreamStats()

    # ── Thread body ──────────────────────────────────────────────────

    def run(self):
        self._running = True
        ser = None
        try:
            ser = serial.Serial(self._port, self._baud,
                                timeout=SERIAL_TIMEOUT_S)
        except Exception as e:
            self.connection_lost.emit(f"Could not open {self._port}: {e}")
            return

        frame_count = 0
        try:
            while self._running:
                try:
                    raw = ser.readline()
                except Exception as e:
                    self.connection_lost.emit(f"Read failed: {e}")
                    break

                if not raw:
                    continue   # timeout, not an error

                try:
                    line = raw.decode("ascii", errors="replace").strip()
                except Exception:
                    self.stats.frames_malformed += 1
                    self.frame_error.emit("undecodable bytes")
                    continue

                if not line:
                    continue

                result = parse_frame(line,
                                     strict_crc=self._strict_crc,
                                     allow_legacy=self._allow_legacy)
                self.stats.record(result)

                if result.error:
                    self.frame_error.emit(result.error)
                elif result.is_info:
                    self.info_received.emit(result.info_type or "",
                                            result.info_data or [])
                elif result.sample:
                    self.sample_received.emit(result.sample)

                frame_count += 1
                if frame_count % self.STATS_EVERY_N_FRAMES == 0:
                    self.stats_updated.emit(self.stats)
        finally:
            if ser and ser.is_open:
                ser.close()
            self.stats_updated.emit(self.stats)

    def stop(self):
        self._running = False
        self.wait(2000)
