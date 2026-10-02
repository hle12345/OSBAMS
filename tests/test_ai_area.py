"""AI/data area: features, rule baseline, group split, trainer gating, registry (synthetic/test CSVs only)."""
import csv, os, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from ai.assessment import rule_baseline as rb
from ai.datasets import synthetic
from ai.evaluation.split import group_split, regression_metrics
from ai.features import extract
from ai.model_registry import registry
from ai.models import zoo
from ai.training.train import train, InsufficientData


class TestFeatures(unittest.TestCase):
    def test_missing_is_none_not_zero(self):
        f = extract.from_test_row({"capacity_retention_pct": "85", "dcir_mohm": ""})
        self.assertEqual(f["capacity_retention_pct"], 85.0)
        self.assertIsNone(f["dcir_mohm"])
        self.assertIsNone(extract.to_vector(f, ["capacity_retention_pct", "dcir_mohm"]))

    def test_quick_test_features(self):
        f = extract.quick_test_features(40.0, {"i_a": 1.0, "v_loaded_v": 39.9}, {"i_a": 5.0, "v_loaded_v": 39.5, "v_immediate_v": 39.4,
                                        "t_response_ms": 12}, [(0, 39.6), (10, 39.9)], 24.0)
        self.assertAlmostEqual(f["dv_di_mohm"], 100.0)
        self.assertAlmostEqual(f["immediate_sag_mv"], 600.0)
        self.assertAlmostEqual(f["dynamic_resistance_mohm"], 100.0)
        self.assertAlmostEqual(f["recovery_slope_mv_per_s"], 30.0)
        self.assertIsNone(extract.quick_test_features(None, None, None)["dv_di_mohm"])

    def test_load_from_exported_csv(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "tests.csv")
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["anon_battery_id", "test_id", "chemistry", "measurement_quality", "capacity_retention_pct", "dcir_mohm"])
            w.writerow(["a1", "1", "NMC", "PASS", "88", "120"])
        r = extract.load_test_features(p)
        self.assertEqual(r[0]["features"]["dcir_mohm"], 120.0)
        self.assertEqual(r[0]["measurement_quality"], "PASS")


class TestRuleBaseline(unittest.TestCase):
    good = dict(capacity_retention_pct=90, dcir_mohm=100, voltage_sag_mv=1500, temp_rise_c=8, delivered_wh=170, discharge_duration_s=5000)

    def test_outcomes(self):
        self.assertEqual(rb.assess(self.good, "PASS").outcome, rb.REUSE)
        self.assertEqual(rb.assess(dict(self.good, capacity_retention_pct=70), "PASS").outcome, rb.MONITOR)
        a = rb.assess(dict(self.good, capacity_retention_pct=40), "PASS")
        self.assertEqual((a.outcome, a.reasons), (rb.RECYCLE, ["RETENTION_VERY_LOW"]))

    def test_quality_and_missing_inputs_never_favourable(self):
        self.assertEqual(rb.assess(self.good, "REVIEW REQUIRED").outcome, rb.RETEST)
        self.assertEqual(rb.assess(self.good, None).reasons, ["MEASUREMENT_QUALITY_UNKNOWN"])
        a = rb.assess(dict(self.good, dcir_mohm=None), "PASS")
        self.assertEqual((a.outcome, a.reasons), (rb.RETEST, ["MISSING_DCIR_MOHM"]))
        self.assertEqual(rb.assess(dict(self.good, discharge_duration_s=100), "PASS").outcome, rb.RETEST)

    def test_thresholds_configurable_and_provisional(self):
        th = rb.Thresholds(reuse_min_retention_pct=95.0)
        self.assertEqual(rb.assess(self.good, "PASS", th).outcome, rb.MONITOR)
        self.assertEqual(rb.assess(self.good, "PASS").thresholds_status, "PROVISIONAL")


class TestTrainingGates(unittest.TestCase):
    def test_group_split_has_no_leakage(self):
        g = [f"b{i // 2}" for i in range(40)]
        tr, te = group_split(g, 0.3, seed=1)
        self.assertFalse({g[i] for i in tr} & {g[i] for i in te})
        self.assertEqual(len(tr) + len(te), 40)
        with self.assertRaises(ValueError):
            group_split(["x", "x"])

    def test_refuses_real_data_without_enough_validated_batteries(self):
        recs = synthetic.generate(10)
        for r in recs:
            r["measurement_quality"] = "PASS"
        with self.assertRaises(InsufficientData):
            train(recs, ["dcir_mohm"], min_batteries=30)

    def test_refuses_unvalidated_quality_rows(self):
        recs = synthetic.generate(40)              # quality SYNTHETIC, declared as real -> filtered out -> too few
        with self.assertRaises(InsufficientData):
            train(recs, ["dcir_mohm"])

    def test_synthetic_requires_explicit_opt_in_and_is_marked(self):
        recs = synthetic.generate(40)
        with self.assertRaises(InsufficientData):
            train(recs, ["dcir_mohm"], synthetic=True)
        path = os.path.join(tempfile.mkdtemp(), "reg.jsonl")
        for mt in ("linear", "random_forest", "gradient_boosting", "gaussian_process"):
            model, e = train(recs, ["dcir_mohm", "voltage_sag_mv"], model_type=mt, dataset_version=synthetic.SYNTHETIC_DATASET_VERSION,
                             test_protocol="synthetic", synthetic=True, allow_synthetic=True, registry_path=path)
            self.assertTrue(e["synthetic"])
            self.assertLess(e["validation_metrics"]["mae"], 10.0)
            self.assertIn("SYNTHETIC", " ".join(e["limitations"]))
            self.assertEqual(e["training_battery_count"] + e["test_battery_count"], 40)
        self.assertEqual(len(registry.load(path)), 4)

    def test_registry_requires_fields_and_zoo_has_no_deep_nets(self):
        with self.assertRaises(ValueError):
            registry.record({"model_id": "x"}, os.path.join(tempfile.mkdtemp(), "r.jsonl"))
        self.assertNotIn("mlp", " ".join(zoo.MODEL_TYPES))
        with self.assertRaises(ValueError):
            zoo.make("neural_net")

    def test_metrics(self):
        m = regression_metrics([1, 2, 3], [1, 2, 4])
        self.assertAlmostEqual(m["mae"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
