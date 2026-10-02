# Open dataset schema — `osbams-dataset/0.1` (experimental)

Export: `desktop/services/dataset_export.py → export_dataset(out_dir, salt)` writes `tests.csv`, `samples.csv`, `dataset.json` (manifest).
CSV and JSON, versioned by the schema id in every row. **An empty cell means "not available" — never zero.**

Battery identity is anonymized (`anon-<12 hex>` = salted SHA-256 of the OSB id); the salt stays with the contributor. Test protocol version:
`osbams-test-protocol/0.1`.

**tests.csv** (one row per test): dataset_schema, anon_battery_id, test_id, test_type, test_protocol_version, started_at, ended_at, chemistry,
nominal_voltage_v, rated_capacity_ah, cell_config, capacity_ah, energy_wh, discharge_time_s, capacity_retention_pct, retention_label,
dcir_mohm, initial_ocv_v, voltage_sag_mv, max_temp_c, ah_ina / ah_mcu / ah_pi, wh_ina / wh_mcu / wh_pi, integration_disagreement_ah_pct,
capacity_validation_status, sample_count, missing_sample_count, calibration_id, firmware_version, pcb_revision, measurement_quality, stop_reason.

**samples.csv** (one row per stored sample): dataset_schema, anon_battery_id, test_id, tick_ms, voltage_v, voltage_adc_v (independent ADC; empty
until protocol v2), current_a, power_w, temp_c, flags.

`capacity_retention_pct` is labelled "Capacity retention vs rated (not validated SOH)": measured usable capacity / rated capacity. It is not
a validated cell-level state of health. DCIR values are comparable only with their conditions (`dcir_conditions_json` in the database /
Battery Passport).

## Battery Passport (`osbams-passport/0.1`)
`services/battery_passport.py → build_passport(battery_id)`: persistent id (`OSB-000001`), manufacturer/model, chemistry, nominal voltage,
rated capacity, connector/profile, notes, every test with calibration used, capacity, energy, DCIR, temperature, measurement quality,
firmware/hardware revision, and a descriptive trend over repeated tests (not a health claim).
