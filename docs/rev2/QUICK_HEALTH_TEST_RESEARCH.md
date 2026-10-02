# Quick Health Test — research design (no PCB change, not a production feature)

**Research stage. A full controlled discharge remains the ground truth. Nothing here is a health claim.**

Sequence (per battery, low energy, inside the existing current/power limits): **OCV → small load step → larger step → recovery**.
Candidate features (`ai/features/extract.py → quick_test_features`): OCV; ΔV/ΔI between the two steps; immediate voltage sag at the large
step; recovery slope after release; dynamic resistance; temperature; response times. All use the existing 6060B manual mode and the OSBAMS
telemetry; no new hardware.

Study plan: for every battery that gets a quick test, also run the full discharge and DCIR (separate test); store both in the dataset
(`DATASET_SCHEMA.md`); only then ask whether quick features predict capacity retention, with a split by battery identity
(`ai/evaluation/split.py`) and the validation metrics recorded in the model registry. Until such data exist the quick test is
exploratory; the rule-based triage (`ai/assessment/rule_baseline.py`) does not use it.
