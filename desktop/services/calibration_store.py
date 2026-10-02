"""services/calibration_store.py — persist calibration profiles in SQLite and keep exactly one active."""
from typing import Optional

from db.database import get_connection
from db import migrations
from services.calibration import CalibrationProfile


def _ensure():
    migrations.migrate()


def save_calibration(profile: CalibrationProfile, activate: bool = True) -> None:
    _ensure()
    conn = get_connection()
    try:
        conn.execute("""INSERT OR REPLACE INTO calibrations
            (calibration_id, created_at, voltage_gain, voltage_offset, current_gain, current_offset,
             zero_current_offset_a, reference_instrument, operator, temperature_c, profile_json, is_active, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,0,?)""",
            (profile.calibration_id, profile.created, profile.voltage.gain, profile.voltage.offset,
             profile.current.gain, profile.current.offset, profile.zero_current_offset_a,
             profile.reference_instrument, profile.operator, profile.temperature_c, profile.to_json(), profile.notes))
        if activate:
            conn.execute("UPDATE calibrations SET is_active=CASE WHEN calibration_id=? THEN 1 ELSE 0 END",
                         (profile.calibration_id,))
        conn.commit()
    finally:
        conn.close()


def get_calibration(calibration_id: str) -> Optional[CalibrationProfile]:
    _ensure()
    conn = get_connection()
    try:
        row = conn.execute("SELECT profile_json FROM calibrations WHERE calibration_id=?", (calibration_id,)).fetchone()
    finally:
        conn.close()
    return None if row is None else CalibrationProfile.from_json(row[0])


def get_active() -> Optional[CalibrationProfile]:
    _ensure()
    conn = get_connection()
    try:
        row = conn.execute("SELECT profile_json FROM calibrations WHERE is_active=1").fetchone()
    finally:
        conn.close()
    return None if row is None else CalibrationProfile.from_json(row[0])
