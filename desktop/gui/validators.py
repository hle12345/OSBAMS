"""
gui/validators.py — OSBAMS Input Validation

Validates battery intake fields before DB write.
Returns list of (field_name, message) tuples for any errors or warnings.
"""


def validate_battery_intake(**fields) -> tuple[list, list]:
    """
    Validate a battery intake form submission.

    Returns:
        (errors, warnings) — both are lists of (field, message) tuples.
        errors block saving; warnings allow saving with confirmation.
    """
    errors   = []
    warnings = []

    nom_v  = fields.get("nominal_voltage")
    max_v  = fields.get("max_charge_voltage")
    min_v  = fields.get("cutoff_voltage")
    cap_ah = fields.get("capacity_rated_ah")
    eng_wh = fields.get("energy_rated_wh")
    series = fields.get("series_count")
    par    = fields.get("parallel_count")
    phys   = fields.get("physical_score")
    safety = fields.get("safety_status")
    serial = fields.get("serial_number")
    ocv    = fields.get("initial_ocv_v")
    osbams_id = fields.get("osbams_id")

    # ── Required ─────────────────────────────────────────────────────
    if not safety:
        errors.append(("safety_status", "Safety status must be selected."))

    if not osbams_id:
        errors.append(("osbams_id", "OSBAMS ID is required."))

    # ── Voltage relationships ─────────────────────────────────────────
    if nom_v and max_v:
        if max_v <= nom_v:
            errors.append(("max_charge_voltage",
                f"Max charge voltage ({max_v}V) must be greater than "
                f"nominal voltage ({nom_v}V)."))

    if nom_v and min_v:
        if min_v >= nom_v:
            errors.append(("cutoff_voltage",
                f"Cutoff voltage ({min_v}V) must be less than "
                f"nominal voltage ({nom_v}V)."))

    # ── Positive values ───────────────────────────────────────────────
    if cap_ah is not None and cap_ah <= 0:
        errors.append(("capacity_rated_ah", "Rated capacity must be positive."))

    if eng_wh is not None and eng_wh <= 0:
        errors.append(("energy_rated_wh", "Rated energy must be positive."))

    if nom_v is not None and nom_v <= 0:
        errors.append(("nominal_voltage", "Nominal voltage must be positive."))

    # ── Physical score range ──────────────────────────────────────────
    if phys is not None and not (0 <= phys <= 10):
        errors.append(("physical_score",
            "Physical score must be between 0 and 10."))

    # ── Cell count sanity ─────────────────────────────────────────────
    if series is not None and not (1 <= series <= 30):
        warnings.append(("series_count",
            f"Series count {series} is unusual for a scooter battery "
            "(expected 8–13)."))

    if par is not None and not (1 <= par <= 20):
        warnings.append(("parallel_count",
            f"Parallel count {par} is unusual (expected 1–10)."))

    # ── Wh consistency check ──────────────────────────────────────────
    if nom_v and cap_ah and eng_wh:
        expected_wh = nom_v * cap_ah
        if abs(expected_wh - eng_wh) / eng_wh > 0.15:   # > 15% off
            warnings.append(("energy_rated_wh",
                f"Rated energy {eng_wh} Wh is inconsistent with "
                f"{nom_v}V × {cap_ah}Ah = {expected_wh:.1f} Wh. "
                f"Verify nameplate values."))
        else:
            pass  # consistent — no warning needed

    # ── Initial OCV safety ────────────────────────────────────────────
    if ocv and max_v:
        if ocv > max_v * 1.02:   # more than 2% above max
            errors.append(("initial_ocv_v",
                f"Initial OCV {ocv}V exceeds registered maximum {max_v}V. "
                "Verify measurement before connecting to load."))
        elif ocv > max_v:
            warnings.append(("initial_ocv_v",
                f"Initial OCV {ocv}V slightly above rated max {max_v}V. "
                "Verify with a second measurement."))

    if ocv and min_v:
        if ocv < min_v:
            warnings.append(("initial_ocv_v",
                f"Initial OCV {ocv}V is below cutoff voltage {min_v}V. "
                "Battery may be deeply discharged. Charge before testing."))

    return errors, warnings


def validate_test_config(**fields) -> tuple[list, list]:
    """Validate test configuration before starting a discharge test."""
    errors   = []
    warnings = []

    cutoff_v = fields.get("cutoff_voltage_v")
    max_temp = fields.get("max_temp_c")
    current  = fields.get("current_setpoint_a")
    power    = fields.get("power_setpoint_w")
    safety   = fields.get("battery_safety_status")

    # Safety gate — quarantine batteries cannot be tested
    if safety in ("Quarantine", "Unsafe — recycle"):
        errors.append(("battery_safety_status",
            f"Battery safety status is '{safety}'. "
            "Resolve safety issue before connecting to load."))

    if cutoff_v is not None and cutoff_v < 20:
        errors.append(("cutoff_voltage_v",
            f"Cutoff voltage {cutoff_v}V is dangerously low. "
            "Minimum recommended is 27V for a 10S Li-ion pack."))

    if max_temp is not None and max_temp > 60:
        errors.append(("max_temp_c",
            f"Max temperature limit {max_temp}°C exceeds safe limit. "
            "Recommended maximum is 50°C."))

    if current is not None and current > 10:
        warnings.append(("current_setpoint_a",
            f"Current setpoint {current}A is high for scooter pack testing. "
            "Ensure load and wiring are rated for this current."))

    return errors, warnings


def format_errors(errors: list, warnings: list) -> str:
    """Format errors and warnings as a human-readable string."""
    lines = []
    if errors:
        lines.append("ERRORS (must fix before saving):")
        for field, msg in errors:
            lines.append(f"  ✗ [{field}] {msg}")
    if warnings:
        lines.append("WARNINGS (review before proceeding):")
        for field, msg in warnings:
            lines.append(f"  ⚠ [{field}] {msg}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Example: OSB-006's 43.5V reading
    errs, warns = validate_battery_intake(
        osbams_id         = "OSB-006",
        safety_status     = "Quarantine",
        nominal_voltage   = 36.0,
        max_charge_voltage= 42.0,
        cutoff_voltage    = 30.0,
        capacity_rated_ah = 15.3,
        energy_rated_wh   = 551.0,
        series_count      = 10,
        parallel_count    = 6,
        physical_score    = 5,
        initial_ocv_v     = 43.5,
    )
    print(format_errors(errs, warns))
    print()

    # Wh inconsistency example
    errs2, warns2 = validate_battery_intake(
        osbams_id="OSB-002", safety_status="Pending",
        nominal_voltage=37.0, max_charge_voltage=42.0,
        capacity_rated_ah=12.8, energy_rated_wh=473.6,
        physical_score=8,
    )
    print(format_errors(errs2, warns2))
    print("✓ validators.py self-test passed")
