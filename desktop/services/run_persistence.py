"""services/run_persistence.py — store orchestrator Results in the `tests` row."""

from db.database import get_connection


def save_run_results(test_id: int, res, operator: str = "operator") -> None:
    """Write the Rev.2 result fields (columns added by db.migrations.migrate())."""
    rec30 = res.recovery_v.get(30.0)
    rec_final = res.recovery_v[max(res.recovery_v)] if res.recovery_v else None
    sag_mv = None if res.initial_sag_v is None else int(round(res.initial_sag_v * 1000))
    ir = res.dcir_mohm
    notes = f"{res.kind} run: {res.phase}; {res.stop_reason}".strip()
    conn = get_connection()
    try:
        conn.execute("""
            UPDATE tests SET operator=?, load_mode='CC', current_setpoint_a=?,
                initial_ocv_v=?, resting_voltage_after_v=?, stop_reason=?,
                average_current_a=?, average_power_w=?, voltage_sag_mv=?,
                internal_resistance_mohm=?, power_setpoint_w=?
            WHERE test_id=?""",
            (operator, res.commanded_current_a, res.ocv_v,
             rec_final if rec_final is not None else rec30, res.stop_reason,
             res.avg_current_a, res.avg_power_w, sag_mv, ir,
             None if res.commanded_current_a is None or res.conservative_voltage_v is None
             else res.commanded_current_a * res.conservative_voltage_v, test_id))
        conn.execute("UPDATE tests SET notes=COALESCE(notes||' | ','')||? WHERE test_id=?",
                     (notes, test_id))
        conn.commit()
    finally:
        conn.close()
