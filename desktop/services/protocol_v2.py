"""services/protocol_v2.py — OSBAMS Serial Protocol v2 (DESIGN + host reference implementation; firmware NOT changed).

Purpose: carry what the three-way capacity cross-check needs — the independent ADC voltage, the INA228's own charge/energy
accumulators, the STM32's own numerical integration, an acquisition counter and a sensor-status word — while staying
backward compatible with protocol v1 (`services/protocol.py` is untouched and still authoritative for v1).

    OSBAMS,2,<seq>,<tick_ms>,<V_mV>,<I_mA>,<P_mW>,<T_C10>,<flags>,<state>,
           <V_adc_mV>,<Q_ina_uAh>,<Q_mcu_uAh>,<E_ina_uWh>,<E_mcu_uWh>,<acq_count>,<sensor_status>,<CRC16>

18 comma-separated fields, CRLF terminated.  Fields 0..9 are IDENTICAL in meaning to v1 (only the version number differs).
Fields 10..16 are new; every numeric new field may be the literal ``NA`` when the firmware cannot provide it (never 0 as a
stand-in: 0 would be a measurement).  CRC-16/CCITT-FALSE over the text up to, not including, the comma before the CRC —
exactly as v1.

| # | Field          | Type          | Units | Meaning                                                                 |
|---|----------------|---------------|-------|-------------------------------------------------------------------------|
|10 | V_adc_mV       | int32 or NA   | mV    | independent STM32 ADC measurement of pack voltage (cross-check channel) |
|11 | Q_ina_uAh      | int64 or NA   | uAh   | INA228 CHARGE register, converted, SIGNED (follows shunt polarity) since test start |
|12 | Q_mcu_uAh      | int64 or NA   | uAh   | STM32 integration of |I| over actual timestamps since test start (magnitude) |
|13 | E_ina_uWh      | int64 or NA   | uWh   | INA228 ENERGY register, converted, since test start                      |
|14 | E_mcu_uWh      | int64 or NA   | uWh   | STM32 integration of V*I over actual timestamps since test start         |
|15 | acq_count      | uint32        | —     | measurements taken by the STM32 since test start (gaps vs `seq` = frames lost, not samples lost) |
|16 | sensor_status  | uint16        | bits  | SS_* below                                                              |

Accumulator rules (so the Pi can detect trouble instead of trusting numbers):
  * all four accumulators reset together at an explicit test-start command, never implicitly;
  * a decrease of an accumulator between frames, or SS_ACCUM_INVALID, means "reset or overflow": the Pi must flag the test
    (CAPACITY_VALIDATION_WARNING) and must not silently re-baseline;
  * the INA228 accumulators are only valid when ADCRANGE/SHUNT_CAL match the calibration profile in use (firmware sets
    SS_ACCUM_INVALID otherwise);
  * a v1 peer simply never sends fields 10..16; a v2 reader accepts v1 frames and reports those fields as unavailable.

Golden vectors shared with the future firmware tests: docs/rev2/protocol_v2_test_vectors.json (the firmware tests are to be
written FIRST against these vectors, then the encoder implemented).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from services import protocol as v1

PROTOCOL_VERSION_V2 = 2
DATA_FIELD_COUNT_V2 = 18
NA = "NA"

SS_INA_FAULT = 1 << 0
SS_ADC_FAULT = 1 << 1
SS_TEMP_FAULT = 1 << 2
SS_ACCUM_INVALID = 1 << 3
SS_TIME_JUMP = 1 << 4
SS_INTEG_GAP = 1 << 5          # STM32 integration skipped an over-long interval
SS_SAMPLE_INVALID = 1 << 6     # STM32 integration skipped an invalid sample
SS_NAMES = {SS_INA_FAULT: "INA_FAULT", SS_ADC_FAULT: "ADC_FAULT", SS_TEMP_FAULT: "TEMP_FAULT",
            SS_ACCUM_INVALID: "ACCUM_INVALID", SS_TIME_JUMP: "TIME_JUMP",
            SS_INTEG_GAP: "INTEG_GAP", SS_SAMPLE_INVALID: "SAMPLE_INVALID"}


@dataclass(frozen=True)
class OsbamsSampleV2:
    base: v1.OsbamsSample                    # fields 0..9 (protocol_version is 1 or 2)
    v_adc_mv: Optional[int] = None
    q_ina_uah: Optional[int] = None
    q_mcu_uah: Optional[int] = None
    e_ina_uwh: Optional[int] = None
    e_mcu_uwh: Optional[int] = None
    acq_count: Optional[int] = None
    sensor_status: Optional[int] = None      # None for v1 frames

    @property
    def v_adc_v(self) -> Optional[float]:
        return None if self.v_adc_mv is None else self.v_adc_mv / 1000.0

    @property
    def has_device_totals(self) -> bool:
        return self.q_ina_uah is not None and self.q_mcu_uah is not None

    @property
    def status_names(self) -> list:
        s = self.sensor_status or 0
        return [n for b, n in SS_NAMES.items() if s & b]


@dataclass(frozen=True)
class ParseResultV2:
    sample: Optional[OsbamsSampleV2] = None
    error: Optional[str] = None
    is_info: bool = False
    info_type: str = ""
    info_data: tuple = ()

    @property
    def ok(self) -> bool:
        return self.sample is not None


def _num(text: str):
    return None if text == NA else int(text)


def encode_data_frame_v2(seq: int, tick_ms: int, voltage_mv: int, current_ma: int, power_mw: int, temp_c10: int,
                         flags: int = 0, state: str = "DISCHARGING", v_adc_mv=None, q_ina_uah=None, q_mcu_uah=None,
                         e_ina_uwh=None, e_mcu_uwh=None, acq_count: int = 0, sensor_status: int = 0) -> str:
    f = lambda x: NA if x is None else str(int(x))
    body = (f"{v1.FRAME_PREFIX},{PROTOCOL_VERSION_V2},{seq},{tick_ms},{voltage_mv},{current_ma},{power_mw},{temp_c10},"
            f"{flags},{state},{f(v_adc_mv)},{f(q_ina_uah)},{f(q_mcu_uah)},{f(e_ina_uwh)},{f(e_mcu_uwh)},{acq_count},{sensor_status}")
    return f"{body},{v1.crc16(body.encode('ascii')):04X}"


def parse_any(line: str, strict_crc: bool = True) -> ParseResultV2:
    """Parse a v2 frame, or fall back to v1 (fields 10..16 reported unavailable). Never silently discards a line."""
    t = line.strip()
    parts = t.split(",")
    if len(parts) >= 2 and parts[0] == v1.FRAME_PREFIX and parts[1] == str(PROTOCOL_VERSION_V2):
        if len(parts) != DATA_FIELD_COUNT_V2:
            return ParseResultV2(error=f"field count {len(parts)}, expected {DATA_FIELD_COUNT_V2}")
        body = ",".join(parts[:-1])
        try:
            crc_rx = int(parts[-1], 16)
        except ValueError:
            return ParseResultV2(error=f"CRC field not hex: {parts[-1]!r}")
        crc_calc = v1.crc16(body.encode("ascii"))
        valid = crc_rx == crc_calc
        if strict_crc and not valid:
            return ParseResultV2(error=f"CRC mismatch: got {crc_rx:04X}, computed {crc_calc:04X}")
        if parts[9] not in v1.STATES:
            return ParseResultV2(error=f"unknown state {parts[9]!r}")
        try:
            base = v1.OsbamsSample(protocol_version=2, sequence=int(parts[2]), tick_ms=int(parts[3]), voltage_mv=int(parts[4]),
                                   current_ma=int(parts[5]), power_mw=int(parts[6]), temp_c10=int(parts[7]), flags=int(parts[8]),
                                   state=parts[9], crc_valid=valid)
            return ParseResultV2(sample=OsbamsSampleV2(base, _num(parts[10]), _num(parts[11]), _num(parts[12]),
                                                       _num(parts[13]), _num(parts[14]), int(parts[15]), int(parts[16])))
        except ValueError as e:
            return ParseResultV2(error=f"bad integer field: {e}")
    r = v1.parse_frame(line, strict_crc=strict_crc)
    if r.sample is not None:
        return ParseResultV2(sample=OsbamsSampleV2(r.sample))
    return ParseResultV2(error=r.error, is_info=r.is_info, info_type=r.info_type or "", info_data=tuple(r.info_data or ()))
