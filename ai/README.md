# OSBAMS `ai/` — experimental health-assessment area

**Experimental / research stage.** Nothing here is a validated battery state-of-health or a safety certification. Thresholds are
provisional until reference-instrument validation and real labelled data exist. Capacity retention (measured usable ÷ rated) is not
a validated cell-level SOH.

Layout: `features/` (feature definitions, quick-test features) · `assessment/` (non-ML rule baseline: REUSE_CANDIDATE / MONITOR /
RETEST_REQUIRED / RECYCLE_CANDIDATE with reason codes; missing inputs or non-PASS quality can only give RETEST_REQUIRED) · `models/`
(small explainable zoo: linear/logistic, random forest, gradient boosting, Gaussian process — no deep networks) · `training/` (refuses to
train without enough validated, labelled batteries; synthetic data only with explicit opt-in) · `evaluation/` (split by battery identity,
metrics) · `datasets/` (clearly labelled SYNTHETIC generator and sample) · `model_registry/` (append-only record of dataset version, feature
version, model type, battery count, chemistry coverage, protocol, metrics, limitations).

The AI work uses the exported dataset (`docs/rev2/DATASET_SCHEMA.md`) or synthetic/test CSVs; it does not depend on protocol v2.
Quick Health Test: `docs/rev2/QUICK_HEALTH_TEST_RESEARCH.md`.
