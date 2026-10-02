"""services/run_persistence.py — store orchestrator Results in the `tests` row."""

import json

from db.database import get_connection


def save_run_results(test_id: int, res, operator: str = "operator", calibration_id=None, quality=None,
                     rated_capacity_ah=None, firmware_version=None, pcb_revision=None,
                     total_frames: int = 0, missing_frames: int = 0, integration=None) -> None:
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
        # traceability / validation layer (columns added by db.migrations.migrate())
        conn.execute("""UPDATE tests SET calibration_id=?, rated_capacity_ah=?, capacity_retention_pct=?,
                measurement_quality=?, quality_json=?, firmware_version=?, pcb_revision=?, sample_count=?,
                missing_sample_count=?, dcir_conditions_json=?, integration_json=? WHERE test_id=?""",
            (calibration_id, rated_capacity_ah, getattr(res, "capacity_retention_pct", None),
             None if quality is None else quality.status, None if quality is None else json.dumps(quality.to_dict()),
             firmware_version, pcb_revision, res.n_samples, missing_frames if total_frames else None,
             json.dumps(res.dcir_conditions) if getattr(res, "dcir_conditions", None) else None,
             None if integration is None else json.dumps(integration), test_id))
        conn.commit()
    finally:
        conn.close()


def save_capacity_validation(test_id: int, cv) -> None:
    """Store the three-way cross-check (services.capacity_validation.CapacityValidation) on the test row."""
    conn = get_connection()
    try:
        conn.execute("""UPDATE tests SET ah_ina=?, ah_mcu=?, ah_pi=?, wh_ina=?, wh_mcu=?, wh_pi=?,
                integration_disagreement_ah_pct=?, integration_disagreement_wh_pct=?, capacity_validation_status=?,
                sample_count=?, missing_sample_count=?, calibration_id=COALESCE(?, calibration_id),
                firmware_version=COALESCE(?, firmware_version), pcb_revision=COALESCE(?, pcb_revision),
                integration_json=? WHERE test_id=?""",
            (cv.ah.get("INA228"), cv.ah.get("STM32"), cv.ah.get("Pi"), cv.wh.get("INA228"), cv.wh.get("STM32"),
             cv.wh.get("Pi"), cv.disagreement_ah_pct, cv.disagreement_wh_pct, cv.status, cv.sample_count,
             cv.missing_sample_count, cv.calibration_id, cv.firmware_version, cv.pcb_revision, cv.to_json(), test_id))
        conn.commit()
    finally:
        conn.close()
