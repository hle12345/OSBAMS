"""
services/protocol.py — OSBAMS Serial Protocol v1

SINGLE AUTHORITATIVE DEFINITION. Firmware, parser, simulator, tests, and
documentation all derive from this file. If the frame changes, it changes
here first and everything else follows.

────────────────────────────────────────────────────────────────────────────
PROTOCOL v1 FRAME
────────────────────────────────────────────────────────────────────────────

    OSBAMS,<ver>,<seq>,<tick_ms>,<V_mV>,<I_mA>,<P_mW>,<T_C10>,<flags>,<state>,<CRC16>

Example:

    OSBAMS,1,42,1500,41820,3000,125460,250,0,DISCHARGING,4A8F

11 fields, comma-separated, terminated with CRLF.

| # | Field   | Type   | Units  | Notes                                        |
|---|---------|--------|--------|----------------------------------------------|
| 0 | OSBAMS  | literal| —      | frame synchronisation                        |
| 1 | ver     | uint8  | —      | protocol version, currently 1                |
| 2 | seq     | uint32 | —      | increments per frame; gaps indicate loss     |
| 3 | tick_ms | uint32 | ms     | controller uptime                            |
| 4 | V_mV    | int32  | mV     | bus voltage                                  |
| 5 | I_mA    | int32  | mA     | positive = discharge                         |
| 6 | P_mW    | int32  | mW     | power                                        |
| 7 | T_C10   | int16  | 0.1 °C | ALWAYS a multiple of 10 (TC74 is 1 °C)       |
| 8 | flags   | uint16 | bits   | see FLAG_* below                             |
| 9 | state   | string | —      | controller state machine state               |
|10 | CRC16   | hex4   | —      | CRC-16/CCITT-FALSE over fields 0..9 inclusive|

CRC is computed over the frame text from 'O' up to but NOT including the
comma that precedes the CRC field.

────────────────────────────────────────────────────────────────────────────
NON-DATA FRAMES
────────────────────────────────────────────────────────────────────────────

    OSBAMS,BOOT,<fw_version>,<protocol_version>
    OSBAMS,SENSOR,<channel>,<health>
    OSBAMS,STATE,<state>
    OSBAMS,FAULT,<reason>

These are informational and are not CRC-protected.
"""

from dataclasses import dataclass
from typing import Optional

# ── Protocol identity ────────────────────────────────────────────────────────
PROTOCOL_VERSION = 1
FRAME_PREFIX     = "OSBAMS"
DATA_FIELD_COUNT = 11          # including prefix and CRC
LEGACY_FIELD_COUNT = 6         # firmware v0.1: OSBAMS,tick,V,I,P,T

# ── Status flags (bit field, field 8) ────────────────────────────────────────
FLAG_SENSOR_ERR   = 1 << 0
FLAG_TEMP_ERR     = 1 << 1
FLAG_OVERTEMP     = 1 << 2
FLAG_UNDERVOLT    = 1 << 3
FLAG_OVERCURRENT  = 1 << 4
FLAG_REVERSE_CURR = 1 << 5
FLAG_LOAD_FAULT   = 1 << 6

FLAG_NAMES = {
    FLAG_SENSOR_ERR:   "SENSOR_ERR",
    FLAG_TEMP_ERR:     "TEMP_ERR",
    FLAG_OVERTEMP:     "OVERTEMP",
    FLAG_UNDERVOLT:    "UNDERVOLT",
    FLAG_OVERCURRENT:  "OVERCURRENT",
    FLAG_REVERSE_CURR: "REVERSE_CURRENT",
    FLAG_LOAD_FAULT:   "LOAD_FAULT",
}

# ── Controller states (field 9) ──────────────────────────────────────────────
STATES = [
    "BOOT", "SELF_TEST", "IDLE", "PACK_DETECTED", "PRECHECK", "READY",
    "RESTING", "DISCHARGING", "PAUSED", "CUTOFF", "RECOVERY",
    "COMPLETE", "FAULT",
]


# ── CRC-16/CCITT-FALSE ───────────────────────────────────────────────────────
# Must match Protocol_Crc16() in firmware/Middleware/Src/protocol.c exactly:
#   init 0xFFFF, poly 0x1021, no reflection, no final XOR.

def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


# ── Sample ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OsbamsSample:
    protocol_version: int
    sequence:         int
    tick_ms:          int
    voltage_mv:       int
    current_ma:       int
    power_mw:         int
    temp_c10:         int
    flags:            int
    state:            str
    crc_valid:        bool

    # ── Convenience conversions ──────────────────────────────────────────
    @property
    def time_s(self) -> float: return self.tick_ms / 1000.0
    @property
    def voltage_v(self) -> float: return self.voltage_mv / 1000.0
    @property
    def current_a(self) -> float: return self.current_ma / 1000.0
    @property
    def power_w(self)   -> float: return self.power_mw   / 1000.0
    @property
    def temp_c(self)    -> float: return self.temp_c10   / 10.0

    @property
    def active_flags(self) -> list[str]:
        return [name for bit, name in FLAG_NAMES.items() if self.flags & bit]

    @property
    def has_fault(self) -> bool:
        critical = (FLAG_OVERTEMP | FLAG_UNDERVOLT |
                    FLAG_OVERCURRENT | FLAG_REVERSE_CURR | FLAG_LOAD_FAULT)
        return bool(self.flags & critical)


# ── Parse result ─────────────────────────────────────────────────────────────

@dataclass
class ParseResult:
    sample:  Optional[OsbamsSample] = None
    error:   Optional[str]          = None
    is_info: bool                   = False   # BOOT/SENSOR/STATE/FAULT frame
    info_type: Optional[str]        = None
    info_data: Optional[list]       = None

    @property
    def ok(self) -> bool:
        return self.sample is not None or self.is_info


# ── Encoder (used by the simulator and by tests) ─────────────────────────────

def encode_data_frame(seq: int, tick_ms: int, voltage_mv: int,
                      current_ma: int, power_mw: int, temp_c10: int,
                      flags: int = 0, state: str = "DISCHARGING") -> str:
    """Build a complete Protocol v1 DATA frame including CRC."""
    body = (f"{FRAME_PREFIX},{PROTOCOL_VERSION},{seq},{tick_ms},"
            f"{voltage_mv},{current_ma},{power_mw},{temp_c10},"
            f"{flags},{state}")
    crc = crc16(body.encode("ascii"))
    return f"{body},{crc:04X}"


# ── Parser ───────────────────────────────────────────────────────────────────

def parse_frame(line: str, strict_crc: bool = True,
                allow_legacy: bool = False) -> ParseResult:
    """
    Parse one line into a ParseResult.

    Never silently discards a malformed line: every failure path returns
    an error string so the caller can count and report it.

    strict_crc   — reject frames whose CRC does not match
    allow_legacy — also accept the 6-field firmware v0.1 format
    """
    line = line.strip()
    if not line:
        return ParseResult(error="empty line")

    if line.startswith("#"):
        return ParseResult(is_info=True, info_type="COMMENT", info_data=[line])

    if not line.startswith(FRAME_PREFIX + ","):
        return ParseResult(error=f"missing {FRAME_PREFIX} prefix")

    parts = line.split(",")

    # ── Informational frames ──────────────────────────────────────────
    if len(parts) >= 2 and parts[1] in ("BOOT", "SENSOR", "STATE", "FAULT",
                                         "SELFTEST", "SIM_END"):
        return ParseResult(is_info=True, info_type=parts[1],
                           info_data=parts[2:])

    # ── Legacy v0.1 format ────────────────────────────────────────────
    if len(parts) == LEGACY_FIELD_COUNT:
        if not allow_legacy:
            return ParseResult(
                error=f"legacy 6-field frame rejected (protocol v1 requires "
                      f"{DATA_FIELD_COUNT} fields); pass allow_legacy=True to accept")
        try:
            return ParseResult(sample=OsbamsSample(
                protocol_version=0, sequence=0,
                tick_ms=int(parts[1]), voltage_mv=int(parts[2]),
                current_ma=int(parts[3]), power_mw=int(parts[4]),
                temp_c10=int(parts[5]), flags=0, state="UNKNOWN",
                crc_valid=False))
        except ValueError as e:
            return ParseResult(error=f"legacy frame bad integer: {e}")

    # ── Protocol v1 DATA frame ────────────────────────────────────────
    if len(parts) != DATA_FIELD_COUNT:
        return ParseResult(
            error=f"field count {len(parts)}, expected {DATA_FIELD_COUNT}")

    try:
        ver = int(parts[1])
    except ValueError:
        return ParseResult(error=f"bad protocol version field: {parts[1]!r}")

    if ver != PROTOCOL_VERSION:
        return ParseResult(
            error=f"protocol version {ver}, expected {PROTOCOL_VERSION}")

    # CRC over everything before the final comma
    body     = ",".join(parts[:-1])
    crc_text = parts[-1]
    try:
        crc_rx = int(crc_text, 16)
    except ValueError:
        return ParseResult(error=f"CRC field not hex: {crc_text!r}")

    crc_calc  = crc16(body.encode("ascii"))
    crc_valid = (crc_rx == crc_calc)

    if strict_crc and not crc_valid:
        return ParseResult(
            error=f"CRC mismatch: got {crc_rx:04X}, computed {crc_calc:04X}")

    try:
        state = parts[9]
        if state not in STATES:
            return ParseResult(error=f"unknown state {state!r}")
        return ParseResult(sample=OsbamsSample(
            protocol_version = ver,
            sequence         = int(parts[2]),
            tick_ms          = int(parts[3]),
            voltage_mv       = int(parts[4]),
            current_ma       = int(parts[5]),
            power_mw         = int(parts[6]),
            temp_c10         = int(parts[7]),
            flags            = int(parts[8]),
            state            = state,
            crc_valid        = crc_valid,
        ))
    except ValueError as e:
        return ParseResult(error=f"bad integer field: {e}")


# ── Stream statistics ────────────────────────────────────────────────────────

@dataclass
class StreamStats:
    """Tracks frame health across a session. Nothing is silently dropped."""
    frames_ok:        int = 0
    frames_malformed: int = 0
    frames_crc_bad:   int = 0
    frames_info:      int = 0
    sequence_gaps:    int = 0
    samples_lost:     int = 0
    time_reversals:   int = 0
    last_sequence:    Optional[int] = None
    last_tick_ms:     Optional[int] = None
    last_error:       Optional[str] = None

    def record(self, result: ParseResult) -> None:
        if result.error:
            self.frames_malformed += 1
            self.last_error = result.error
            if "CRC" in result.error:
                self.frames_crc_bad += 1
            return

        if result.is_info:
            self.frames_info += 1
            return

        s = result.sample
        self.frames_ok += 1

        # Sequence gap detection
        if self.last_sequence is not None:
            expected = self.last_sequence + 1
            if s.sequence > expected:
                self.sequence_gaps += 1
                self.samples_lost += s.sequence - expected
            elif s.sequence < self.last_sequence:
                # counter reset or out-of-order
                self.sequence_gaps += 1
        self.last_sequence = s.sequence

        # Timestamp monotonicity
        if self.last_tick_ms is not None and s.tick_ms < self.last_tick_ms:
            self.time_reversals += 1
        self.last_tick_ms = s.tick_ms

    @property
    def total_frames(self) -> int:
        return self.frames_ok + self.frames_malformed + self.frames_info

    @property
    def loss_percent(self) -> float:
        expected = self.frames_ok + self.samples_lost
        return (self.samples_lost / expected * 100.0) if expected else 0.0

    def summary(self) -> str:
        return (f"{self.frames_ok} ok · {self.frames_malformed} malformed "
                f"({self.frames_crc_bad} CRC) · {self.sequence_gaps} gaps · "
                f"{self.samples_lost} lost ({self.loss_percent:.2f}%) · "
                f"{self.time_reversals} time reversals")


if __name__ == "__main__":
    print("OSBAMS Protocol v1 — self-test\n")

    frame = encode_data_frame(42, 1500, 41820, 3000, 125460, 250, 0, "DISCHARGING")
    print(f"Encoded: {frame}")

    r = parse_frame(frame)
    assert r.ok and r.sample, r.error
    s = r.sample
    print(f"Parsed : seq={s.sequence} {s.voltage_v}V {s.current_a}A "
          f"{s.power_w}W {s.temp_c}C state={s.state} crc_valid={s.crc_valid}")

    # Corrupt the CRC
    bad = frame[:-1] + ("0" if frame[-1] != "0" else "1")
    r2 = parse_frame(bad)
    print(f"Bad CRC: rejected = {r2.sample is None}  ({r2.error})")

    # Wrong field count
    r3 = parse_frame("OSBAMS,1,42,1500")
    print(f"Short  : rejected = {r3.sample is None}  ({r3.error})")

    # Legacy
    r4 = parse_frame("OSBAMS,1500,41820,0,0,240", allow_legacy=True)
    print(f"Legacy : accepted = {r4.sample is not None}")

    # Stats with a gap
    stats = StreamStats()
    for seq in [1, 2, 5, 6]:
        stats.record(parse_frame(encode_data_frame(seq, seq*500, 40000, 3000,
                                                    120000, 250, 0, "DISCHARGING")))
    print(f"Stats  : {stats.summary()}")

    print("\nSelf-test passed.")
