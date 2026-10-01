"""Rev.2 orchestrator, invariants, dashboard wiring (offscreen Qt)."""
import os, shutil, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "desktop"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from equipment import capability as cap
from equipment.drivers import Simulator6060B, Manual6060B
from services.battery_profiles import PROFILES, profile_from_battery
from services.test_orchestrator import (CapacityTest, DcirTest, Phase, RunConfig,
                                        Sample, run_simulated)

NEB = PROFILES["ninebot_neb1002"]


def sim_run(kind=CapacityTest, scenario="36v_5p2ah_healthy", dt=2.0, cfg=None, **kw):
    sim = Simulator6060B(scenario)
    run = kind(NEB, sim, cfg or RunConfig(), **kw)
    return run, sim, run_simulated(run, sim, dt_s=dt)


class TestInvariant(unittest.TestCase):
    def test_hard_invariant(self):
        self.assertAlmostEqual(cap.assert_power_invariant(7.14, 42.0), 299.88)
        with self.assertRaises(cap.InvariantViolation):
            cap.assert_power_invariant(7.2, 42.0)
        with self.assertRaises(cap.InvariantViolation):
            cap.assert_power_invariant(1.0, None)

    def test_conservative_voltage_is_monotone(self):
        c = cap.ConservativeVoltage(42.0)
        for v in (40.0, 36.0, 30.0):                 # sag
            c.update(v)
        self.assertEqual(c.volts, 42.0)
        c.update(42.5)
        self.assertEqual(c.volts, 42.5)

    def test_sag_cannot_buy_more_current(self):
        c = cap.ConservativeVoltage(42.0); c.update(34.0)
        with self.assertRaises(cap.InvariantViolation):
            cap.assert_power_invariant(8.0, c.volts)   # fine at 34 V (272 W), not at 42 V

    def test_layered_limits(self):
        import config
        self.assertLess(config.SAFETY_MAX_CURRENT_A, config.FIRMWARE_HARD_TRIP_A)
        self.assertLessEqual(config.FIRMWARE_HARD_TRIP_A, cap.REV1_POWER_PATH.shunt_a)
        # firmware trip is NOT an input to the commanded maximum
        lim = cap.compute_permitted_current(42.0, 5.0)
        self.assertEqual(lim.final_a, 5.0)
        self.assertNotIn("firmware", " ".join(lim.component_limits_a))

    def test_panel_rows_show_limiting_factor(self):
        rows = dict(cap.compute_permitted_current(42.0, 5.0).rows())
        self.assertEqual(rows["Battery"], "42.0 V")
        self.assertEqual(rows["6060B current rating"], "60 A")
        self.assertEqual(rows["6060B power-derived limit"], "7.14 A")
        self.assertEqual(rows["OSBAMS validated limit"], "10 A")
        self.assertEqual(rows["Battery-profile limit"], "5.00 A")
        self.assertEqual(rows["FINAL PERMITTED"], "5.00 A")
        self.assertEqual(rows["Limiting factor"], "battery profile")
        self.assertTrue(rows["min(...)"].startswith("min("))


class TestCapacityRun(unittest.TestCase):
    def test_full_flow_complete(self):
        run, sim, r = sim_run()
        self.assertEqual(r.phase, "COMPLETE", r.stop_reason)
        self.assertIn("cutoff", r.stop_reason)
        phases = [e[1] for e in r.events]
        for p in ("OCV", "READY", "DISCHARGE", "LOAD_OFF", "RECOVERY"):
            self.assertIn(p, phases)
        self.assertAlmostEqual(r.ocv_v, 42.0, delta=0.05)
        self.assertEqual(r.commanded_current_a, 1.0)
        self.assertGreater(r.capacity_ah, 0.5 * sim.capacity_ah)
        self.assertLessEqual(r.capacity_ah, sim.capacity_ah * 1.01)
        self.assertAlmostEqual(r.soh_capacity, r.capacity_ah / NEB.rated_ah)
        self.assertGreater(r.energy_wh, 30.0 * r.capacity_ah * 0.9)   # V between 30 and 42
        self.assertLess(r.v_min, NEB.cutoff_voltage_v + 0.5)
        self.assertIn(300.0, r.recovery_v)
        self.assertGreater(r.recovery_v[300.0], r.v_end)               # voltage recovers
        self.assertGreater(r.max_temp_c, 25.0)

    def test_ah_matches_independent_integration(self):
        run, sim, r = sim_run(dt=1.0)
        samples = [x for x in run.samples if x[4] == "DISCHARGE"]
        ah = sum(0.5 * (abs(a[2]) + abs(b[2])) * (b[0] - a[0]) / 3600
                 for a, b in zip(samples, samples[1:]))
        self.assertAlmostEqual(r.capacity_ah, ah, delta=0.02)

    def test_current_never_rises_and_power_stays_under_300(self):
        run, sim, r = sim_run()
        loaded = [x for x in run.samples if x[4] == "DISCHARGE"]
        self.assertLessEqual(max(abs(x[2]) for x in loaded), r.commanded_current_a * 1.15 + 0.1)
        self.assertLessEqual(max(x[1] * abs(x[2]) for x in loaded), 300.0)
        self.assertLessEqual(r.commanded_current_a * r.conservative_voltage_v, 300.0)

    def test_explicit_request_over_permitted_refused(self):
        run, sim, r = sim_run(requested_current_a=7.0)   # 7 A x 42 V = 294 W, but profile max 5.2 A
        self.assertEqual(r.phase, "FAULT")
        self.assertIn("refused by envelope", r.stop_reason)
        self.assertFalse(sim.read_status().input_on)

    def test_request_over_300w_refused(self):
        big = PROFILES["ninebot_nee1006m"]
        sim = Simulator6060B("36v_15p3ah_healthy")
        run = CapacityTest(big, sim, requested_current_a=8.0)
        r = run_simulated(run, sim)
        self.assertEqual(r.phase, "FAULT")
        self.assertIn("W", r.stop_reason)

    def test_dead_pack_rejected(self):
        sim = Simulator6060B("36v_5p2ah_healthy")
        sim._soc = 0.0                                    # at cutoff OCV
        run = CapacityTest(NEB, sim)
        r = run_simulated(run, sim, max_steps=400)
        self.assertEqual(r.phase, "FAULT"); self.assertIn("cutoff", r.stop_reason)

    def test_overtemp_aborts_with_verified_off(self):
        run, sim, r = sim_run(scenario="36v_5p2ah_overtemp")
        self.assertEqual(r.phase, "FAULT"); self.assertIn("over-temperature", r.stop_reason)
        self.assertFalse(sim.read_status().input_on)
        self.assertIn("load OFF confirmed", " ".join(e[2] for e in r.events))

    def test_comm_loss_detected(self):
        sim = Simulator6060B("36v_5p2ah_healthy"); sim.connect()
        run = CapacityTest(NEB, sim); run.start()
        t = 0.0
        while run.phase is not Phase.DISCHARGE and t < 200:
            t += 1; st = sim.step(1.0)
            run.on_sample(Sample(t, st.voltage_v, st.current_a, 25.0))
            if run.phase is Phase.READY: run.confirm()
        self.assertIs(run.phase, Phase.DISCHARGE)
        run.tick(t + 60)
        self.assertIn(run.phase, (Phase.LOAD_OFF, Phase.FAULT))
        self.assertIn("communication loss", run.stop_reason)

    def test_sensor_fault_flag_aborts(self):
        sim = Simulator6060B("36v_5p2ah_healthy"); sim.connect()
        run = CapacityTest(NEB, sim); run.start()
        run.on_sample(Sample(1, 42.0, 0.0, 25.0, fault=True))
        self.assertEqual(run.phase, Phase.FAULT)

    def test_voltage_rise_beyond_conservative_trips_invariant(self):
        # commanded current is fixed; if the pack voltage later reads HIGHER the
        # 300 W invariant is re-evaluated and can fault the run.
        sim = Simulator6060B("36v_5p2ah_healthy")
        run = CapacityTest(PROFILES["ninebot_nee1006m"], sim, requested_current_a=7.0)
        r0 = run_simulated(run, sim, max_steps=200)       # reaches DISCHARGE
        self.assertIn(run.phase, (Phase.DISCHARGE,))
        run.on_sample(Sample(run._last_t + 1, 43.0, 7.0, 25.0))   # 301 W
        self.assertIn(run.phase, (Phase.LOAD_OFF, Phase.FAULT))
        self.assertIn("invariant", run.stop_reason)


class TestManualLoad(unittest.TestCase):
    def test_manual_requires_operator_and_verifies_off(self):
        prompts = []
        manual = Manual6060B()
        sim = Simulator6060B("36v_5p2ah_healthy")          # stands in for the bench battery + INA228
        run = CapacityTest(NEB, manual, prompt=prompts.append)
        run.start(); sim.connect(); t = 0.0; enabled = False
        for _ in range(100_000):
            if run.done: break
            t += 2.0
            st = sim.step(2.0)
            run.on_sample(Sample(t, st.voltage_v, st.current_a, sim.temperature_c()))
            if run.phase is Phase.READY: run.confirm()
            if run.phase is Phase.DISCHARGE and not enabled:
                sim.set_pack_voltage(42.0); sim.set_cc(run.commanded_a); sim.input_on(); enabled = True
            if run.phase is Phase.LOAD_OFF and sim.read_status().input_on:
                sim.input_off()                            # operator obeys the prompt
        r = run.results()
        self.assertEqual(r.phase, "COMPLETE", r.stop_reason)
        self.assertTrue(any("DISABLE" in p for p in prompts))
        self.assertTrue(any("Enable the load" in p for p in prompts))

    def test_manual_off_not_obeyed_is_fault(self):
        manual = Manual6060B(); sim = Simulator6060B("36v_5p2ah_healthy")
        run = CapacityTest(NEB, manual); run.start(); sim.connect(); t = 0.0; on = False
        for _ in range(100_000):
            if run.done: break
            t += 2.0; st = sim.step(2.0)
            run.on_sample(Sample(t, st.voltage_v, st.current_a, 25.0))
            if run.phase is Phase.READY: run.confirm()
            if run.phase is Phase.DISCHARGE and not on:
                sim.set_pack_voltage(42.0); sim.set_cc(run.commanded_a); sim.input_on(); on = True
            if run.phase is Phase.DISCHARGE and t > 100:
                run.abort("test")                          # operator ignores the prompt afterwards
        self.assertEqual(run.phase, Phase.FAULT)
        self.assertIn("LOAD-OFF NOT CONFIRMED", run.stop_reason)


class TestDcir(unittest.TestCase):
    def test_dcir_steps(self):
        run, sim, r = sim_run(DcirTest, dt=0.5)
        self.assertEqual(r.phase, "COMPLETE", r.stop_reason)
        self.assertEqual(len(r.dcir_steps), 2)
        self.assertEqual([round(s["current_a"], 1) for s in r.dcir_steps], [0.5, 1.0])
        self.assertTrue(all(s["d_voltage_v"] > 0 for s in r.dcir_steps))
        # instantaneous part is half of the simulated pack resistance; 10 s holds see part of the rest
        r_inst = sim.r_pack_ohm * 1000 * (1 - sim.POL_FRACTION)
        self.assertGreater(r.dcir_mohm, r_inst * 0.9)
        self.assertLess(r.dcir_mohm, sim.r_pack_ohm * 1000 * 1.05)
        self.assertEqual(r.commanded_current_a, 1.0)       # peak step
        self.assertIn(300.0, r.recovery_v)

    def test_higher_resistance_gives_higher_dcir(self):
        a = sim_run(DcirTest, "36v_5p2ah_healthy", 0.5)[2].dcir_mohm
        b = sim_run(DcirTest, "36v_5p2ah_high_resistance", 0.5)[2].dcir_mohm
        self.assertGreater(b, 2 * a)

    def test_step_over_permitted_refused(self):
        cfg = RunConfig(dcir_steps_a=(1.0, 6.0))
        run, sim, r = sim_run(DcirTest, cfg=cfg)
        self.assertEqual(r.phase, "FAULT")
        self.assertEqual(r.dcir_steps, [])

    def test_steps_must_increase(self):
        run, sim, r = sim_run(DcirTest, cfg=RunConfig(dcir_steps_a=(1.0, 0.5)))
        self.assertEqual(r.phase, "FAULT")


class TestProfileResolver(unittest.TestCase):
    def test_known_model_and_derived(self):
        self.assertIs(profile_from_battery({"model": "NEE1006-M"}), PROFILES["ninebot_nee1006m"])
        p = profile_from_battery(dict(model="X", nominal_voltage=24, max_charge_voltage=25.2,
                                      cutoff_voltage=18, capacity_rated_ah=10, osbams_id="OSB-9"))
        self.assertEqual((p.recommended_test_current_a, p.maximum_osbams_test_current_a), (2.0, 5.0))
        self.assertEqual(p.validate(), [])

    def test_missing_cutoff_refused(self):
        with self.assertRaises(ValueError):
            profile_from_battery(dict(model="X", nominal_voltage=24, max_charge_voltage=25.2,
                                      capacity_rated_ah=10))


try:
    from PySide6.QtWidgets import QApplication
    _app = QApplication.instance() or QApplication([])
    HAVE_QT = True
except Exception:                                    # pragma: no cover
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "Qt not available")
class TestDashboardWiring(unittest.TestCase):
    def setUp(self):
        import db.database as dbm
        self.tmp = tempfile.mkdtemp()
        self._old = dbm.DB_PATH
        dbm.DB_PATH = os.path.join(self.tmp, "t.db")
        dbm.init_db()
        from db.migrations import migrate
        migrate()
        self.dbm = dbm
        self.bid, _ = dbm.create_battery(
            source_type="fleet", brand="Ninebot", model="NEB1002-H", chemistry="NMC",
            nominal_voltage=36.0, max_charge_voltage=42.0, cutoff_voltage=30.0,
            capacity_rated_ah=5.2, energy_rated_wh=187.0)

    def tearDown(self):
        self.dbm.DB_PATH = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _sample(self, t, st, temp):
        from services.protocol import OsbamsSample
        return OsbamsSample(1, int(t), int(t * 1000), int(st.voltage_v * 1000),
                            int(st.current_a * 1000), int(st.power_w * 1000),
                            int(temp * 10) // 10 * 10, 0, "DISCHARGING", True)

    def test_panel_shows_live_limit_and_full_run_persists(self):
        import gui.tabs.dashboard_tab as dt

        class FakeSig:
            def connect(self, f): pass
        class FakeReader:
            sample_received = error_occurred = FakeSig()
            def __init__(self, port): pass
            def start(self): pass
            def stop(self): pass
            def wait(self): pass
        dt.SerialReader = FakeReader
        # coarse 10 s simulated sampling for test speed (real stream is 0.5 s)
        dt.RunConfig = lambda: RunConfig(sample_gap_s=60, ocv_min_samples=2,
                                         recovery_s=60, recovery_marks_s=(30.0,))
        tab = dt.DashboardTab()
        tab.set_battery(self.bid, "OSB test")
        rows = dict(tab.limit_panel._labels)
        self.assertEqual(rows["Battery"].text(), "42.0 V")            # worst case before OCV
        self.assertEqual(rows["6060B power-derived limit"].text(), "7.14 A")
        tab.port_combo.clear(); tab.port_combo.addItem("FAKE")
        tab._start_test()
        self.assertIs(tab._orch.phase, Phase.OCV)

        sim = Simulator6060B("36v_5p2ah_healthy"); sim.connect(); sim.set_pack_voltage(42.0)
        t, enabled = 0.0, False
        for _ in range(20000):
            t += 10.0
            st = sim.step(10.0)
            tab._on_sample(self._sample(t, st, sim.temperature_c()))
            _app.processEvents()
            if tab._orch is None:
                break
            ph = tab._orch.phase
            if ph is Phase.READY:
                self.assertTrue(tab.confirm_btn.isEnabled())
                self.assertEqual(rows["FINAL PERMITTED"].text(), "5.20 A")   # profile limit < 7.14 A
                self.assertEqual(rows["Limiting factor"].text(), "battery profile")
                self.assertEqual(rows["Battery"].text(), "42.0 V")
                tab.confirm_btn.click()
            if ph is Phase.DISCHARGE and not enabled:
                sim.set_cc(tab._orch.commanded_a); sim.input_on(); enabled = True
            if ph is Phase.LOAD_OFF and sim.read_status().input_on:
                sim.input_off()
        self.assertIsNone(tab._orch)                                    # finished and torn down
        tests = self.dbm.get_tests_for_battery(self.bid)
        self.assertEqual(len(tests), 1)
        row = tests[0]
        self.assertGreater(row["capacity_ah"], 1.0)
        self.assertAlmostEqual(row["initial_ocv_v"], 42.0, delta=0.1)
        self.assertEqual(row["current_setpoint_a"], 1.0)
        self.assertIn("cutoff", row["stop_reason"])
        self.assertTrue(tab.csv_btn.isEnabled())

    def test_dashboard_refuses_battery_without_cutoff(self):
        import gui.tabs.dashboard_tab as dt
        bid, _ = self.dbm.create_battery(source_type="fleet", model="Z",
                nominal_voltage=36, max_charge_voltage=42, capacity_rated_ah=5)
        tab = dt.DashboardTab(); tab.set_battery(bid, "no cutoff")
        self.assertIsNone(tab._profile)
        self.assertIn("cutoff", tab.prompt_lbl.text().lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
