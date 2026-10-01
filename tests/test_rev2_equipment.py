"""Rev.2 equipment layer: capability model, 6060B drivers, simulator, profiles."""
import os, re, sqlite3, sys, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from equipment import capability as cap
from equipment.drivers import (Keysight6060B, Manual6060B, Simulator6060B,
                               InterfaceBlocked, CommandNotVerified, create_load)
from equipment.drivers.keysight_6060b import ScriptedTransport


class TestCapability(unittest.TestCase):
    EXPECTED = {5: 60.0, 10: 30.0, 20: 15.0, 30: 10.0, 36: 8.33, 42: 7.14, 48: 6.25, 60: 5.0}

    def test_instrument_only_examples(self):
        for v, a in self.EXPECTED.items():
            self.assertAlmostEqual(cap.instrument_current_limit_a(v), a, places=2, msg=f"{v} V")

    def test_final_is_min_of_everything(self):
        lim = cap.compute_permitted_current(42.0, profile_current_limit_a=5.0)
        self.assertAlmostEqual(lim.final_a, 5.0)
        self.assertEqual(lim.limiting_factor, "battery profile")
        lim = cap.compute_permitted_current(42.0, profile_current_limit_a=50.0)
        self.assertAlmostEqual(lim.final_a, 300 / 42, places=6)
        lim = cap.compute_permitted_current(5.0, 50.0, system_current_max_a=60.0,
                                            power_path=cap.PowerPathLimits())
        self.assertAlmostEqual(lim.final_a, 50.0)

    def test_osbams_limit_not_silently_60(self):
        import config
        self.assertLess(config.SAFETY_MAX_CURRENT_A, 60.0)
        self.assertLessEqual(cap.compute_permitted_current(5.0).final_a,
                             config.SAFETY_MAX_CURRENT_A)

    def test_component_limit_caps(self):
        pp = cap.PowerPathLimits(fuse_a=4.0)
        lim = cap.compute_permitted_current(12.0, power_path=pp)
        self.assertAlmostEqual(lim.final_a, 4.0)
        self.assertIn("connector", lim.unspecified)

    def test_voltage_bounds_block(self):
        for v in (None, 0.0, 2.9, 60.01, 72.0, 100.0, 150.0, 500.0):
            self.assertTrue(cap.compute_permitted_current(v).blocked, v)
            self.assertEqual(cap.compute_permitted_current(v).final_a, 0.0)
        for v in (3.0, 60.0):
            self.assertFalse(cap.compute_permitted_current(v).blocked)

    def test_check_rejects_power_current_voltage(self):
        with self.assertRaises(cap.EnvelopeViolation):
            cap.check_load_command(42.0, 8.0)            # 336 W
        with self.assertRaises(cap.EnvelopeViolation):
            cap.check_load_command(61.0, 1.0)
        with self.assertRaises(cap.EnvelopeViolation):
            cap.check_load_command(5.0, 61.0, system_current_max_a=100.0)
        with self.assertRaises(cap.EnvelopeViolation):
            cap.check_load_command(12.0, -1.0)
        cap.check_load_command(42.0, 7.14)               # ok
        cap.check_load_command(60.0, 5.0)                # exactly 300 W

    def test_xt90_is_not_90a(self):
        # Connector never appears in the model; 42 V is 7.14 A at best.
        self.assertLess(cap.compute_permitted_current(42.0).final_a, 7.15)

    def test_ui_rows(self):
        labels = [k for k, _ in cap.compute_permitted_current(42.0, 5.0).rows()]
        self.assertEqual(labels, [
            "Battery voltage", "Battery profile current limit",
            "OSBAMS hardware current limit", "6060B current limit",
            "6060B power-derived limit (300 W / V)", "FINAL PERMITTED CURRENT"])

    def test_remote_control_blocked_constant(self):
        self.assertEqual(cap.REMOTE_CONTROL_STATUS, "BLOCKED_BY_INTERFACE_CONFIRMATION")


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.s = Simulator6060B("36v_15p3ah_healthy")
        self.s.connect()
        self.s.set_pack_voltage(42.0)

    def test_enforces_300w(self):
        with self.assertRaises(cap.EnvelopeViolation):
            self.s.set_cc(8.0)
        self.assertTrue(self.s.set_cc(7.0))

    def test_cr_and_cv_guarded(self):
        with self.assertRaises(cap.EnvelopeViolation):
            self.s.set_cr(2.0)                        # 21 A at 42 V
        with self.assertRaises(cap.EnvelopeViolation):
            self.s.set_cv(35.0)                       # unbounded current
        self.assertTrue(self.s.set_cr(10.0))

    def test_unknown_voltage_refuses(self):
        s = Simulator6060B("normal"); s.connect()
        self.assertTrue(s.set_cc(3.0))                # sim knows its own OCV
        k = Manual6060B()
        with self.assertRaises(cap.EnvelopeViolation):
            k.set_cc(1.0)                             # manual: pack voltage unknown

    def test_discharge_integrates_ah(self):
        s = Simulator6060B("normal"); s.connect(); s.set_cc(3.0); s.input_on()
        ah = 0.0
        for _ in range(200_000):
            st = s.step(1.0)
            ah += st.current_a / 3600
            if "BATTERY_EMPTY" in st.flags or not st.input_on:
                break
        self.assertAlmostEqual(ah, s.capacity_ah, delta=0.05)

    def test_hardware_trip_if_voltage_rises_past_envelope(self):
        s = Simulator6060B("48v_healthy"); s.connect()
        s.set_pack_voltage(54.6); s.set_cc(5.0); s.input_on()
        s._setpoint = 6.0                             # bypass guard = fault injection
        st = s.step(1.0)
        self.assertFalse(st.input_on)
        self.assertIn("OVERPOWER", st.flags)

    def test_transient_levels_checked(self):
        with self.assertRaises(cap.EnvelopeViolation):
            self.s.configure_transient(1.0, 9.0, 10.0)
        self.assertTrue(self.s.configure_transient(1.0, 6.0, 10.0))

    def test_scenarios_all_within_envelope_and_below_60v(self):
        for name, p in Simulator6060B.SCENARIOS.items():
            self.assertLessEqual(p["start_v"], 60.0, name)
            cap.check_load_command(p["start_v"], p["current_a"])
        self.assertTrue(all(k in Simulator6060B.SCENARIOS for k in (
            "12v_healthy", "24v_healthy", "36v_5p2ah_healthy", "36v_15p3ah_healthy",
            "42v_full_healthy", "48v_healthy", "60v_boundary_healthy",
            "36v_15p3ah_degraded", "36v_15p3ah_high_resistance",
            "36v_15p3ah_cell_bms_fault", "36v_15p3ah_overtemp", "36v_15p3ah_comm_loss")))
        self.assertFalse(any(("400" in k or "ev_" in k) for k in Simulator6060B.SCENARIOS))


class TestManual(unittest.TestCase):
    def test_cannot_confirm_off(self):
        m = Manual6060B(); m.connect()
        self.assertFalse(m.input_off())
        self.assertFalse(m.input_on())
        self.assertFalse(m.is_controllable)

    def test_instructions_are_validated(self):
        m = Manual6060B(); m.set_pack_voltage(42.0)
        with self.assertRaises(cap.EnvelopeViolation):
            m.set_cc(9.0)
        self.assertTrue(m.set_cc(5.0))
        m.record_front_panel(41.0, 8.0)
        self.assertIsNotNone(m.check_readback())


class TestKeysight(unittest.TestCase):
    IDN = "HEWLETT-PACKARD,6060B,0,A.00.00"

    def make(self, **kw):
        t = ScriptedTransport({"*IDN?": self.IDN, "MEAS:VOLT?": "42.0",
                               "MEAS:CURR?": "0.0", "MEAS:POW?": "0.0",
                               "SYST:ERR?": "0,No error"})
        d = Keysight6060B(transport=t, interface_confirmed=True, **kw)
        return d, t

    def test_blocked_until_interface_confirmed(self):
        with self.assertRaises(InterfaceBlocked):
            Keysight6060B(resource="GPIB0::5::INSTR").connect()

    def test_connect_identifies(self):
        d, _ = self.make()
        self.assertTrue(d.connect())
        self.assertIn("6060B", d.identify())

    def test_rejects_wrong_instrument(self):
        t = ScriptedTransport({"*IDN?": "OWON,OEL1515,0,1"})
        self.assertFalse(Keysight6060B(transport=t, interface_confirmed=True).connect())

    def test_envelope_checked_before_any_write(self):
        d, t = self.make(); d.connect()
        n = len(t.writes)
        with self.assertRaises(cap.EnvelopeViolation):
            d.set_cc(8.0)                             # 42 V live -> 7.14 A max
        self.assertEqual(len(t.writes), n)
        d.set_cc(7.0)
        self.assertEqual(t.writes[-2:], ["MODE CURR", "CURR 7.0000"])

    def test_loaded_reading_cannot_relax_limit(self):
        d, t = self.make(); d.connect()
        d.set_pack_voltage(42.0)                      # OCV known
        t.replies["MEAS:VOLT?"] = "36.0"              # sagged
        with self.assertRaises(cap.EnvelopeViolation):
            d.set_cc(8.0)                             # OK at 36 V (8.33 A) but not at OCV

    def test_unverified_commands_blocked_by_default(self):
        d, t = self.make(); d.connect()
        with self.assertRaises(CommandNotVerified):
            d.set_cr(10.0)
        with self.assertRaises(CommandNotVerified):
            d.set_cv(40.0, 1.0)
        self.assertFalse(any(w.startswith(("RES", "VOLT", "MODE RES", "MODE VOLT")) for w in t.writes))

    def test_unverified_allowed_when_opted_in(self):
        d, t = self.make(allow_unverified=True); d.connect()
        d.set_cr(10.0)
        self.assertIn("MODE RES", t.writes)

    def test_input_on_off_and_measure(self):
        d, t = self.make(); d.connect()
        d.set_cc(5.0); d.input_on(); d.input_off()
        self.assertEqual(t.writes[-2:], ["INP ON", "INP OFF"])
        self.assertEqual(d.measure_voltage(), 42.0)

    def test_transient_checks_both_levels(self):
        d, t = self.make(allow_unverified=True); d.connect()
        with self.assertRaises(cap.EnvelopeViolation):
            d.configure_transient(1.0, 9.0, 100.0)
        d.configure_transient(1.0, 5.0, 100.0)
        self.assertIn("CURR:TLEV 5.0000", t.writes)

    def test_read_errors_drains(self):
        d, t = self.make(); d.connect()
        self.assertEqual(d.read_errors(), [])

    def test_disconnect_turns_input_off_and_local(self):
        d, t = self.make(); d.connect(); d.disconnect()
        self.assertIn("INP OFF", t.writes); self.assertTrue(t.local_called)

    def test_every_command_has_status(self):
        from equipment.drivers.keysight_6060b.commands import COMMANDS, TRUSTED, UNVERIFIED
        for k, c in COMMANDS.items():
            self.assertTrue(c.status in TRUSTED or c.status == UNVERIFIED, k)

    def test_factory_has_only_rev2_loads(self):
        self.assertIsInstance(create_load("manual"), Manual6060B)
        self.assertIsInstance(create_load("simulator"), Simulator6060B)
        for bad in ("owon", "itech", "bitrode", "arbin", "chroma", "digatron"):
            with self.assertRaises(ValueError):
                create_load(bad)


class TestProfilesAndRecords(unittest.TestCase):
    def test_profiles_valid_and_in_envelope(self):
        from services.battery_profiles import PROFILES
        self.assertEqual(len(PROFILES), 3)
        for k, p in PROFILES.items():
            self.assertEqual(p.validate(), [], k)
            self.assertLessEqual(p.permitted_current().final_a, 7.15)

    def test_over_60v_profile_flagged(self):
        from services.battery_profiles import BatteryProfile
        p = BatteryProfile("x", "Dat", "72V", "NMC", 72, 84, 60, 20, 1440, 3, 5, "XT90", 0, 50)
        self.assertTrue(any("OUT_OF_SCOPE_FOR_REV2" in m for m in p.validate()))

    def test_no_global_min_voltage(self):
        import config
        self.assertFalse(hasattr(config, "SAFETY_MIN_VOLTAGE_MV"))
        self.assertFalse(hasattr(config, "DEFAULT_CUTOFF_V"))

    def test_calibration_record(self):
        from equipment.reference import make_record
        r = make_record("voltage", 40.000, 40.200, operator="jl", load_readback=40.1, commit="abc123")
        self.assertAlmostEqual(r.abs_error, 0.2); self.assertAlmostEqual(r.pct_error, 0.5)
        self.assertEqual(r.reference_model, "Keysight EDU34450A")
        self.assertEqual(r.reference_asset_id, "UNKNOWN")
        self.assertAlmostEqual(r.load_abs_error, 0.1)
        with self.assertRaises(ValueError):
            make_record("voltage", 1, 1, operator="")

    def test_calibration_persisted(self):
        from equipment.reference.calibration import make_record, save_record
        import db.migrations as m
        # run the CREATE TABLE statement text against an in-memory DB
        src = open(m.__file__).read()
        ddl = re.search(r'CREATE TABLE IF NOT EXISTS calibration_records \(.*?\n        \)', src, re.S).group(0)
        conn = sqlite3.connect(":memory:"); conn.execute(ddl)
        rid = save_record(conn, make_record("current", 2.0, 2.01, operator="jl", commit="x"))
        self.assertEqual(rid, 1)

    def test_validators_use_envelope(self):
        from gui.validators import validate_test_config
        e, _ = validate_test_config(current_setpoint_a=8.0, pack_voltage_v=42.0)
        self.assertTrue(e)
        e, _ = validate_test_config(current_setpoint_a=3.0, pack_voltage_v=42.0, cutoff_voltage_v=9.0)
        self.assertFalse(e)                          # 9 V cutoff fine for a 3S pack
        e, _ = validate_test_config(cutoff_voltage_v=2.0)
        self.assertTrue(e)

    def test_learning_mode_live_lesson(self):
        from services.learning_mode import power_limit_lesson, LESSONS
        txt = power_limit_lesson(42.0)
        self.assertIn("300 / 42 = 7.14 A", txt)
        self.assertIn("FINAL PERMITTED CURRENT", txt)
        self.assertTrue(any("60 A" in t for t, _ in LESSONS))


class TestNoLegacyDependencies(unittest.TestCase):
    """OWON and out-of-scope hardware must not appear in active Rev.2 code."""

    def _active_files(self):
        for base in ("desktop", "tools", "Firmware"):
            for root, _d, files in os.walk(os.path.join(ROOT, base)):
                for f in files:
                    if f.endswith((".py", ".c", ".h")):
                        yield os.path.join(root, f)

    def test_no_owon_in_active_code(self):
        bad = [p for p in self._active_files()
               if re.search(r"owon|oel1515", open(p, errors="replace").read(), re.I)]
        self.assertEqual(bad, [])

    def test_no_legacy_imports(self):
        bad = [p for p in self._active_files()
               if p.endswith(".py") and re.search(r"^\s*(from|import)\s+legacy", open(p).read(), re.M)]
        self.assertEqual(bad, [])

    def test_no_out_of_scope_drivers(self):
        names = ("owon", "itech", "bitrode", "arbin", "chroma", "digatron")
        drv = os.path.join(ROOT, "desktop", "equipment", "drivers")
        found = [f for f in os.listdir(drv) if any(n in f.lower() for n in names)]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
