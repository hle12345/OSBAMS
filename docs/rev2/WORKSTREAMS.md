# Parallel workstreams and dependencies

Goal chain: **Rev.2 hardware → calibration/validation layer → real battery dataset → explainable AI health assessment.**

| Stream | Scope | Can proceed now | Depends on |
|---|---|---|---|
| A Embedded/Firmware | protocol v2 (`PROTOCOL_V2_DESIGN.md`), independent ADC telemetry, timestamps/sample counters, INA228 accumulator exposure, sensor/fault status, v1 compatibility; firmware tests first | C tests against `protocol_v2_test_vectors.json` | frozen RC1.2e PCB (unchanged); bench for final checks |
| B Measurement/Validation | V/I calibration, zero offset, reference comparison, repeatability, DCIR protocol, fault injection, first-article, uncertainty / error budget (`VALIDATION_AND_CALIBRATION_PLAN.md`, `templates/`) | procedures and spreadsheets; software already host-tested | physical bench + reference instrument for real numbers |
| C Pi/Application | calibration wizard, validation dashboard, quality report, DB provenance, capacity retention, DCIR workflow, test-history comparison, report export | Settings → Calibration and Validation / Measurement Quality exist; history comparison and report export are next | protocol v2 only for the ADC / accumulator rows (shown NOT AVAILABLE until then) |
| D AI/Data | passport schema, feature extraction, dataset export, rule-based baseline, explainable ML pipeline (`ai/`) | everything, with synthetic/test CSVs | real labelled data before any model is trained for real; **no dependency on protocol v2** |

Dependencies: D→(none for infrastructure; real data for real models). C→A for ADC/accumulator display only. B→hardware. A→none for design/tests.
