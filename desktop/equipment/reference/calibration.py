"""
equipment/reference/calibration.py — OSBAMS vs reference-instrument records.

The Keysight EDU34450A is the primary independent reference. Records compare
OSBAMS vs (optionally) the 6060B readback vs the reference. No tolerance is
claimed anywhere until records exist; `asset_id` / calibration status stay
"UNKNOWN" until read off the instrument.
"""

import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional

QUANTITIES = ("voltage", "current", "power", "resistance", "continuity", "temperature")


@dataclass(frozen=True)
class ReferenceInstrument:
    model: str
    asset_id: str = "UNKNOWN"
    calibration_status: str = "UNKNOWN"      # e.g. "in-cal, due 2027-03-01"


EDU34450A = ReferenceInstrument(model="Keysight EDU34450A")          # primary reference
HP34401A = ReferenceInstrument(model="HP 34401A")                    # secondary cross-check


@dataclass
class CalibrationRecord:
    quantity: str
    reference_model: str
    reference_asset_id: str
    reference_cal_status: str
    reference_reading: float
    osbams_reading: float
    abs_error: float
    pct_error: Optional[float]
    timestamp: str
    software_commit: str
    operator: str
    channel: str = ""
    load_readback: Optional[float] = None    # 6060B reading, when practical
    load_abs_error: Optional[float] = None   # 6060B vs reference
    secondary_reference_model: str = ""      # e.g. HP 34401A
    secondary_reference_asset_id: str = ""
    secondary_reading: Optional[float] = None
    secondary_diff: Optional[float] = None   # |secondary - primary reference|
    notes: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def software_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5,
                              check=True).stdout.strip()
    except Exception:
        return "unknown"


def make_record(quantity: str, reference_reading: float, osbams_reading: float,
                operator: str, reference: ReferenceInstrument = EDU34450A,
                load_readback: Optional[float] = None, channel: str = "",
                notes: str = "", commit: Optional[str] = None,
                secondary: Optional[ReferenceInstrument] = None,
                secondary_reading: Optional[float] = None,
                timestamp: Optional[str] = None) -> CalibrationRecord:
    if quantity not in QUANTITIES:
        raise ValueError(f"quantity must be one of {QUANTITIES}")
    if not operator:
        raise ValueError("operator is required on a calibration record")
    err = osbams_reading - reference_reading
    pct = None if reference_reading == 0 else 100.0 * err / reference_reading
    return CalibrationRecord(
        quantity=quantity, reference_model=reference.model,
        reference_asset_id=reference.asset_id,
        reference_cal_status=reference.calibration_status,
        reference_reading=reference_reading, osbams_reading=osbams_reading,
        abs_error=abs(err), pct_error=None if pct is None else abs(pct),
        timestamp=timestamp or datetime.now().isoformat(timespec="seconds"),
        software_commit=commit or software_commit(), operator=operator,
        channel=channel, load_readback=load_readback,
        load_abs_error=None if load_readback is None else abs(load_readback - reference_reading),
        secondary_reference_model=secondary.model if secondary else "",
        secondary_reference_asset_id=secondary.asset_id if secondary else "",
        secondary_reading=secondary_reading,
        secondary_diff=None if secondary_reading is None else abs(secondary_reading - reference_reading),
        notes=notes)


def save_record(conn, rec: CalibrationRecord) -> int:
    """Insert into calibration_records (created by db.migrations.migrate())."""
    cur = conn.execute("""
        INSERT INTO calibration_records
          (recorded_at, quantity, channel, reference_model, reference_asset_id,
           reference_cal_status, reference_reading, osbams_reading, load_readback,
           abs_error, pct_error, software_commit, operator, notes,
           secondary_reference_model, secondary_reading, secondary_diff)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (rec.timestamp, rec.quantity, rec.channel, rec.reference_model,
         rec.reference_asset_id, rec.reference_cal_status, rec.reference_reading,
         rec.osbams_reading, rec.load_readback, rec.abs_error, rec.pct_error,
         rec.software_commit, rec.operator, rec.notes,
         rec.secondary_reference_model, rec.secondary_reading, rec.secondary_diff))
    conn.commit()
    return cur.lastrowid
