# Validation and calibration layer (Rev.2)

**Status: software and procedures only. Nothing here has been run on hardware; no limit below is a validated specification.**
This layer sits *around* the frozen Rev.2 hardware (STM32L476RG, INA228, independent ADC channel, TC74, relay/E-stop/ARM chain,
Pi 5, SQLite). It changes no PCB. It follows the literature takeaways in `Documentation`: calibrated direct measurement first,
documented limitations for low-cost instruments, staged low-energy validation, and accurate current integration.

Related existing documents (this plan adds the software/data layer, it does not replace them): `INSTRUMENT_CALIBRATION_PLAN.md`, `LV_HARDWARE_VALIDATION_PLAN.md`, `BENCH_CHECKLIST.md`, `FIRST_BATTERY_TEST_PROCEDURE.md`, `CALIBRATION_RECORD_TEMPLATE.md`.

## 0. Where the strategy comes from (literature review — methods informed, not validated by)
The additions in this plan are derived from a literature review of battery-testing and low-cost-instrument papers. **The papers do not
validate OSBAMS**; their methods shaped the strategy: (1) calibrated direct measurement comes before any advanced SOH estimation; (2) low-cost
instruments must be validated against a reference instrument and their limits documented; (3) Raspberry-Pi/open-source testers are validated
against reference equipment; (4) testing is staged — low-energy and fault-injection first; (5) current integration needs accurate current and
accurate timing. Every limit in this plan is PROVISIONAL until OSBAMS' own reference data exist. Related: `PROTOCOL_V2_DESIGN.md`,
`DATASET_SCHEMA.md`, `QUICK_HEALTH_TEST_RESEARCH.md`, `WORKSTREAMS.md`, `ai/README.md`.

Workflow: **calibrate → validate against a reference → fault-inject → characterize packs → (later) learn from the data.**

## 1. What exists in the repo now

| Item | Where | Notes |
|---|---|---|
| Linear calibration fit, residual table, zero offset, profile + id | `desktop/services/calibration.py` | `corrected = gain*raw + offset`, separately for V and I; gain outside 0.90–1.10 is refused (wrong reference / wiring) |
| Calibration persistence, one active profile | `desktop/services/calibration_store.py`, table `calibrations` | applied to live samples in the dashboard; no profile → results flagged REVIEW REQUIRED |
| Ah/Wh integration with the actual sample spacing + agreement check | `desktop/services/charge_integration.py` | warns `CAPACITY_VALIDATION_WARNING` above the (provisional) limit |
| Measurement-quality report | `desktop/services/quality.py` | PASS / REVIEW REQUIRED; unavailable items are listed as not available, never silently passed |
| Capacity retention, repeatability, DCIR pulse maths | `desktop/services/metrics.py` | retention carries a "not a validated cell-level SOH" note |
| Provenance columns on `tests`, ADC/flags columns on `readings` | `desktop/db/migrations.py` | additive and idempotent |
| DCIR result records its conditions | `DcirTest.results().dcir_conditions` | OCV, step currents, pulse length, max temperature |
| Tests | `tests/test_validation_layer.py` | host-only |

**Not done (needs firmware / protocol work — separate, deliberate change):** the INA228 charge/energy accumulators, an STM32-side
accumulator and the independent ADC voltage are not in the v1 serial frame (`desktop/services/protocol.py`), so the three-way
integration currently has only the Pi total and the quality report lists the ADC cross-check as *not available*. Proposed protocol v2
adds `V_adc_mV`, `charge_uAh_ina`, `charge_uAh_mcu` (and the energy equivalents) with the same CRC scheme; it changes the frozen
safety-controller interface, so it needs its own review, firmware tests (`make -C Firmware/Tests run`) and a version bump. Also not
done: the Pi calibration/validation **screens** (`Settings → Calibration / Validation`); the service layer above is ready for them.

## 2. Calibration procedure (outside any battery test)
Use a reference instrument alongside OSBAMS (the EDU34450A is the reference in this project). Record instrument, operator, ambient temperature.

| Channel | Reference points | Record at each point |
|---|---|---|
| Voltage | 30, 34, 38, 42, 44 V (current-limited source, no battery) | reference V, INA228 V, ADC V (when available) |
| Current | 0 A first (zero offset), then 1, 2, 5, 8, 10 A | reference I, INA228 I |

Fit with `fit_linear`, store with `save_calibration` (id `CAL-YYYY-MM-DD-NN`), keep the residual table with the lab record
(`templates/calibration_points.csv`, `CALIBRATION_RECORD_TEMPLATE.md`). Re-calibrate when the shunt, INA228, cabling or board changes,
and after the limit on calibration age (provisional 90 days).

## 3. Reference-instrument validation (a lab procedure, not an OSBAMS feature)
After calibrating, check **different** points than were used for the fit and tabulate error against the reference
(`templates/reference_validation.csv`): reference, OSBAMS, error, error %. Set the quality limits (`QualityLimits`) from these results; until
then they are placeholders. Also run one full discharge with the EDU34450A integrating Ah in parallel and compare totals.

## 4. Three-way capacity integration
A. INA228 accumulators, B. STM32 accumulation of every measurement, C. Pi integration of the saved timestamped telemetry. Use the **measured**
time between samples. Report all three and the maximum disagreement; above the limit raise `CAPACITY_VALIDATION_WARNING`. Today only C is
available on hardware (§1). The host side of the full comparison exists (`services/capacity_validation.py`, protocol v2 reference parser,
golden vectors; design in `PROTOCOL_V2_DESIGN.md`); the firmware does not send v2 yet. The comparison stores Ah and Wh per method, % disagreement,
sample and missing-sample counts, calibration id, firmware version and PCB revision. The agreement threshold is provisional (default 1 %).
Pi reconstruction for the agreement uses raw samples (like-for-like with the device); the calibrated Pi result is reported separately.

## 5. DCIR (separate test)
`Start Test → Internal Resistance`: R = (V0 − V1) / (I1 − I0) with a fixed pulse length; always store state of charge/OCV, temperature,
current, pulse duration (done: `dcir_conditions`). A DCIR value without its conditions is not comparable between runs.

## 6. Capacity retention, not SOH
Show **capacity retention vs rated** (measured usable capacity / rated capacity from the profile) and the note that it is an
experimental pack-level assessment. Pack-terminal tests cannot see individual cell imbalance — state this limitation in every report.

## 7. Repeatability
Run the same pack three times under identical conditions; report mean, standard deviation, CV % and the maximum deviation %
(`metrics.repeatability`). Define "±x %" as the maximum deviation from the mean and say so.

## 8. Fault-injection suite (before any real pack; current-limited source, resistive load)
Record PASS/FAIL, date, operator, firmware version in `templates/fault_injection.csv`.

| # | Fault | Expected response | Result |
|---|---|---|---|
| 1 | E-stop pressed | relay drops immediately; load current falls to ~0 | |
| 2 | ARM off | load cannot energize | |
| 3 | INA228 absent / I²C fault | fault, load off | |
| 4 | TC74 absent | temperature fault, test refuses to start | |
| 5 | ADC vs INA228 disagreement | sensor fault (needs protocol v2) | |
| 6 | Pi disconnected / UART silent | STM32 stays safe (load off after the comm-loss timeout) | |
| 7 | UART corrupted (bad CRC) | frames rejected, no unsafe command | |
| 8 | Relay feedback wrong | latched relay fault | |
| 9 | Kelvin lead open | out-of-range shunt reading → sensor fault, load off | |
| 10 | Hot-plug of sense harness at 42–44 V | pins stay below limits; no calibration shift (controller audit F4) | |

The hardware first-article tests F1–F8 in `Hardware/Rev2_Controller/CONTROLLER_PROTECTION_AND_CONNECTOR_AUDIT.md` are part of this suite.

## 9. Database traceability
`tests` now also stores: calibration id, rated capacity, capacity retention %, measurement-quality status and JSON, firmware version, PCB
revision, sample/missing-sample counts, DCIR conditions, integration totals. `calibrations` stores every profile with its residuals.
`readings` has nullable `voltage_adc_mv` and `flags` columns, filled once the protocol carries them.

## 9b. User interface and data products
`Settings → Calibration` (voltage/current points, zero-current offset, reference instrument, active profile, fit and residuals) and
`Validation / Measurement Quality` (profile, gains/offsets, zero offset, ADC-vs-INA228 and integration agreement, missing samples,
PASS / REVIEW REQUIRED; unavailable items show NOT AVAILABLE) are in `desktop/gui/tabs/settings_tab.py`. Battery Passport and the open dataset
export: `DATASET_SCHEMA.md`.

## 10. Machine learning comes last
Collect labeled data first (capacity retention, DCIR with conditions, temperature, discharge-curve shape, voltage sag, pack type, repeated
tests over time). Do not present a trained model as validated until it has real labels and cross-validation; for the capstone, ML is future work. The `ai/` area holds only the infrastructure (rule-based baseline, feature definitions, group-by-battery
evaluation, explainable model zoo, registry); it refuses to train on too little validated data and is exercised with clearly-labelled synthetic data only.
