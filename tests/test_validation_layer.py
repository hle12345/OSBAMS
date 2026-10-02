"""Calibration / integration / quality / repeatability layer (host-only; no hardware)."""
import json, os, shutil, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from services import calibration as cal
from services import charge_integration as ci
from services import metrics, quality


class TestCalibration(unittest.TestCase):
    def test_fit_recovers_known_gain_and_offset(self):
        # channel reads 0.5 % low with +0.02 V offset:  raw = (ref - 0.02) / 1.005  ->  corrected = 1.005*raw + 0.02
        pts = [cal.CalPoint(r, (r - 0.02) / 1.005) for r in cal.VOLTAGE_POINTS_V]
        f = cal.fit_linear(pts)
        self.assertAlmostEqual(f.gain, 1.005, places=9)
        self.assertAlmostEqual(f.offset, 0.02, places=9)
        self.assertLess(f.max_abs_residual, 1e-9)
        self.assertAlmostEqual(f.apply(pts[2].raw), pts[2].reference, places=9)

    def test_residuals_reported_for_noisy_data(self):
        pts = [cal.CalPoint(1.0, 1.01), cal.CalPoint(5.0, 5.00), cal.CalPoint(10.0, 9.98)]
        f = cal.fit_linear(pts)
        rows = cal.residual_table(pts, f)
        self.assertEqual(len(rows), 3)
        self.assertGreater(f.rmse, 0.0)
        self.assertAlmostEqual(max(abs(r["error"]) for r in rows), f.max_abs_residual)

    def test_bad_inputs_refused(self):
        with self.assertRaises(cal.CalibrationError):
            cal.fit_linear([cal.CalPoint(30, 30)])                           # one point
        with self.assertRaises(cal.CalibrationError):
            cal.fit_linear([cal.CalPoint(30, 5), cal.CalPoint(30, 5)])       # no spread
        with self.assertRaises(cal.CalibrationError):                          # wrong reference value -> absurd gain
            cal.fit_linear([cal.CalPoint(30, 15), cal.CalPoint(44, 22)])

    def test_zero_offset(self):
        m, sd = cal.zero_offset([0.0018, 0.0020, 0.0016, 0.0019])
        self.assertAlmostEqual(m, 0.001825, places=6)
        self.assertGreater(sd, 0)
        with self.assertRaises(cal.CalibrationError):
            cal.zero_offset([0.0])

    def test_profile_round_trip_and_identity(self):
        v = cal.fit_linear([cal.CalPoint(30, 30.02), cal.CalPoint(44, 44.05)])
        p = cal.CalibrationProfile("CAL-2026-10-15-01", voltage=v, current=cal.IDENTITY, zero_current_offset_a=0.0018,
                                   reference_instrument="EDU34450A", operator="joe", temperature_c=24.0)
        q = cal.CalibrationProfile.from_json(p.to_json())
        self.assertEqual(q, p)
        self.assertEqual(cal.CalibrationProfile("x").apply_voltage(41.0), 41.0)   # identity leaves values alone
        self.assertEqual(cal.make_calibration_id(__import__("datetime").date(2026, 10, 15), 1), "CAL-2026-10-15-01")


class TestIntegration(unittest.TestCase):
    def test_constant_current_exact_even_with_irregular_dt(self):
        ts = [0.0, 0.7, 2.0, 2.4, 10.0]                      # irregular sampling, not a fixed 10 ms
        r = ci.integrate((t, 40.0, 3.0) for t in ts)
        self.assertAlmostEqual(r.ah, 3.0 * 10.0 / 3600.0, places=12)
        self.assertAlmostEqual(r.wh, 120.0 * 10.0 / 3600.0, places=12)
        self.assertEqual(r.n_samples, 5)
        self.assertAlmostEqual(r.max_gap_s, 7.6)

    def test_ramp_is_trapezoidal_and_gaps_counted(self):
        r = ci.integrate([(0.0, 40.0, 0.0), (10.0, 40.0, 10.0)], gap_s=5.0)
        self.assertAlmostEqual(r.ah, 0.5 * 10.0 * 10.0 / 3600.0)
        self.assertEqual(r.long_gaps, 1)
        with self.assertRaises(ValueError):
            ci.integrate([(1.0, 40, 1), (0.5, 40, 1)])

    def test_three_way_agreement(self):
        ok = ci.compare({"INA228": 8.421, "STM32": 8.417, "Pi": 8.419})
        self.assertEqual(ok.status, "OK")
        self.assertAlmostEqual(ok.max_disagreement_pct, 0.0475, places=3)
        bad = ci.compare({"INA228": 8.421, "STM32": 8.30, "Pi": 8.419})
        self.assertEqual(bad.status, ci.WARNING)
        self.assertEqual(ci.compare({"Pi": 8.4, "INA228": None}).status, "INSUFFICIENT")


class TestMetrics(unittest.TestCase):
    def test_retention_and_note(self):
        self.assertAlmostEqual(metrics.capacity_retention_pct(8.42, 10.0), 84.2)
        self.assertIsNone(metrics.capacity_retention_pct(8.42, None))
        self.assertIn("not equivalent to a validated cell-level", metrics.RETENTION_NOTE)

    def test_repeatability(self):
        r = metrics.repeatability([8.42, 8.39, 8.44])
        self.assertAlmostEqual(r.mean, 8.416667, places=5)
        self.assertAlmostEqual(r.spread_pct, 0.05 / 8.416667 * 100, places=4)
        self.assertGreater(r.cv_pct, 0)
        self.assertLess(r.max_dev_pct, 0.4)
        with self.assertRaises(ValueError):
            metrics.repeatability([8.4])

    def test_dcir_pulse_example(self):
        self.assertAlmostEqual(metrics.dcir_from_pulse(40.82, 0.0, 40.16, 5.0), 132.0, places=6)
        self.assertIsNone(metrics.dcir_from_pulse(40.0, 5.0, 39.9, 5.0))


class TestQuality(unittest.TestCase):
    def _cal(self, zero=0.0018, resid=0.1):
        fit = cal.CalFit(1.0, 0.0, 5, 0.01, 0.02, resid)
        return cal.CalibrationProfile("CAL-T", voltage=fit, current=fit, zero_current_offset_a=zero)

    def test_pass_with_calibration_and_agreement(self):
        q = quality.assess(self._cal(), {"INA228": 8.421, "STM32": 8.417, "Pi": 8.419}, 0.16, 42815, 0)
        self.assertEqual(q.status, quality.PASS, q.reasons)
        self.assertEqual(q.calibration_id, "CAL-T")
        self.assertTrue(any("Zero-current offset" in l for l in q.lines()))

    def test_no_calibration_requires_review(self):
        q = quality.assess(None)
        self.assertEqual(q.status, quality.REVIEW)
        self.assertIn("no calibration profile applied", q.reasons)

    def test_each_failure_is_named(self):
        q = quality.assess(self._cal(zero=0.05), {"A": 8.4, "B": 8.0}, 2.0, 1000, 50)
        self.assertEqual(q.status, quality.REVIEW)
        text = " | ".join(q.reasons)
        for what in ("Zero-current offset", "ADC vs INA228", "Missing samples", ci.WARNING):
            self.assertIn(what, text)

    def test_unavailable_adc_channel_is_not_silently_passed(self):
        q = quality.assess(self._cal(), None, None, 100, 0)
        item = next(i for i in q.items if i.name.startswith("ADC"))
        self.assertIsNone(item.ok)
        self.assertIn("not reported", item.note)
        q2 = quality.assess(self._cal(), None, None, 100, 0, limits=quality.QualityLimits(require_adc_crosscheck=True))
        self.assertEqual(q2.status, quality.REVIEW)


class TestPersistenceAndOrchestrator(unittest.TestCase):
    def setUp(self):
        import db.database as dbm
        self.tmp = tempfile.mkdtemp()
        self._old = dbm.DB_PATH
        dbm.DB_PATH = os.path.join(self.tmp, "t.db")
        dbm.init_db()
        from db.migrations import migrate
        migrate(); migrate()                                  # idempotent
        self.dbm = dbm

    def tearDown(self):
        self.dbm.DB_PATH = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_calibration_store_one_active(self):
        from services import calibration_store as cs
        a = cal.CalibrationProfile("CAL-A", voltage=cal.CalFit(1.001, 0.0, 3, 0, 0, 0.1))
        b = cal.CalibrationProfile("CAL-B")
        cs.save_calibration(a); self.assertEqual(cs.get_active().calibration_id, "CAL-A")
        cs.save_calibration(b); self.assertEqual(cs.get_active().calibration_id, "CAL-B")
        self.assertEqual(cs.get_calibration("CAL-A").voltage.gain, 1.001)
        self.assertIsNone(cs.get_calibration("nope"))

    def test_run_results_carry_provenance(self):
        sys.path.insert(0, os.path.join(ROOT, "tests"))
        from equipment.drivers import Simulator6060B
        from services.battery_profiles import PROFILES
        from services.test_orchestrator import CapacityTest, RunConfig, run_simulated
        from services.run_persistence import save_run_results
        sim = Simulator6060B("36v_5p2ah_healthy")
        run = CapacityTest(PROFILES["ninebot_neb1002"], sim, RunConfig())
        res = run_simulated(run, sim, dt_s=2.0)
        self.assertEqual(res.phase, "COMPLETE", res.stop_reason)
        rated = PROFILES["ninebot_neb1002"].rated_ah
        self.assertAlmostEqual(res.capacity_retention_pct, res.capacity_ah / rated * 100)
        self.assertIn("not equivalent", res.retention_note)
        bid, _ = self.dbm.create_battery(source_type="fleet", brand="Ninebot", model="NEB1002-H", chemistry="NMC",
                                         nominal_voltage=36.0, max_charge_voltage=42.0, cutoff_voltage=30.0,
                                         capacity_rated_ah=5.2, energy_rated_wh=187.0)
        tid = self.dbm.start_test(bid)
        q = quality.assess(None)
        save_run_results(tid, res, calibration_id=None, quality=q, rated_capacity_ah=rated,
                         firmware_version="test", pcb_revision="RC1.2e")
        row = dict(self.dbm.get_connection().execute("SELECT * FROM tests WHERE test_id=?", (tid,)).fetchone())
        self.assertEqual(row["measurement_quality"], quality.REVIEW)
        self.assertEqual(row["pcb_revision"], "RC1.2e")
        self.assertAlmostEqual(row["capacity_retention_pct"], res.capacity_retention_pct)
        self.assertEqual(json.loads(row["quality_json"])["status"], quality.REVIEW)

    def test_dcir_result_records_its_conditions(self):
        from equipment.drivers import Simulator6060B
        from services.battery_profiles import PROFILES
        from services.test_orchestrator import DcirTest, RunConfig, run_simulated
        sim = Simulator6060B("36v_5p2ah_healthy")
        res = run_simulated(DcirTest(PROFILES["ninebot_neb1002"], sim, RunConfig()), sim, dt_s=0.5)
        c = res.dcir_conditions
        self.assertEqual(res.phase, "COMPLETE", res.stop_reason)
        self.assertEqual(c["step_currents_a"], [0.5, 1.0])
        self.assertEqual(c["pulse_s"], 10.0)
        self.assertIsNotNone(c["ocv_v"])


if __name__ == "__main__":
    unittest.main()
