"""Protocol v2 (host reference), three-way capacity validation, passport, dataset export (host-only; no hardware)."""
import csv, json, os, shutil, sys, tempfile, unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from services import calibration as cal
from services import capacity_validation as cv
from services import protocol_v2 as p2


def _frames(n=60, drop=(), q_scale=1.0, reset_at=None, na=False):
    """Constant 3 A discharge at 40 V, 1 s frames; device accumulators consistent with the readings (scaled by q_scale)."""
    out = []
    for i in range(n):
        if i in drop:
            continue
        t = i * 1000
        q = int(3.0 * i / 3600 * 1e6 * q_scale)
        e = int(120.0 * i / 3600 * 1e6 * q_scale)
        if reset_at is not None and i >= reset_at:
            q, e = q - int(3.0 * reset_at / 3600 * 1e6), e - int(120.0 * reset_at / 3600 * 1e6)
        line = p2.encode_data_frame_v2(i, t, 40000, 3000, 120000, 250, v_adc_mv=None if na else 40010,
                                       q_ina_uah=None if na else q, q_mcu_uah=None if na else q,
                                       e_ina_uwh=None if na else e, e_mcu_uwh=None if na else e, acq_count=i, sensor_status=0)
        out.append(p2.parse_any(line).sample)
    return out


class TestProtocolV2(unittest.TestCase):
    def test_golden_vectors(self):
        with open(os.path.join(ROOT, "docs", "rev2", "protocol_v2_test_vectors.json")) as f:
            vec = json.load(f)
        for v in vec["vectors"]:
            r = p2.parse_any(v["line"])
            e = v["expect"]
            self.assertEqual(r.ok, e["ok"], v["name"])
            if not e["ok"]:
                self.assertIn(e["error_contains"], r.error, v["name"])
                continue
            s = r.sample
            for k, val in e.items():
                if k == "ok":
                    continue
                got = s.base.voltage_mv if k == "voltage_mv" else getattr(s, k)
                self.assertEqual(got, val, f"{v['name']}.{k}")

    def test_round_trip_and_na_is_not_zero(self):
        line = p2.encode_data_frame_v2(1, 2, 3, 4, 5, 6, v_adc_mv=None, q_ina_uah=0, acq_count=7, sensor_status=p2.SS_ADC_FAULT)
        s = p2.parse_any(line).sample
        self.assertIsNone(s.v_adc_mv)
        self.assertEqual(s.q_ina_uah, 0)
        self.assertEqual(s.status_names, ["ADC_FAULT"])

    def test_corrupted_frame_rejected(self):
        line = p2.encode_data_frame_v2(1, 2, 3, 4, 5, 6)
        bad = line.replace(",3,4,", ",9,4,")
        self.assertFalse(p2.parse_any(bad).ok)


class TestCapacityValidation(unittest.TestCase):
    def _run(self, frames, calibration=None):
        t = cv.AccumulatorTracker(calibration)
        for s in frames:
            t.add(s)
        return cv.validate(t.summary(gap_s=5.0), calibration_id="CAL-X", firmware_version="fw", pcb_revision="RC1.2e")

    def test_three_methods_agree(self):
        r = self._run(_frames())
        self.assertEqual(r.status, "OK", r.notes)
        self.assertEqual(set(r.ah), {"INA228", "STM32", "Pi"})
        self.assertLess(r.disagreement_ah_pct, 1.0)
        self.assertEqual((r.calibration_id, r.pcb_revision), ("CAL-X", "RC1.2e"))

    def test_disagreement_raises_warning(self):
        r = self._run(_frames(q_scale=1.05))
        self.assertEqual(r.status, cv.WARNING)

    def test_na_accumulators_never_agree_silently(self):
        r = self._run(_frames(na=True))
        self.assertEqual(r.status, "INSUFFICIENT")
        self.assertIsNone(r.ah["INA228"])

    def test_missing_frames_counted(self):
        r = self._run(_frames(drop=(10, 11, 30)))
        self.assertEqual(r.missing_sample_count, 3)

    def test_accumulator_reset_is_flagged_not_rebaselined(self):
        r = self._run(_frames(reset_at=30))
        self.assertEqual(r.status, cv.WARNING)

    def test_like_for_like_raw_vs_calibrated(self):
        c = cal.CalibrationProfile("CAL-G", current=cal.CalFit(1.02, 0.0, 3, 0, 0, 0.1))
        r = self._run(_frames(), c)
        self.assertEqual(r.status, "OK")                        # agreement uses RAW Pi samples
        self.assertAlmostEqual(r.calibrated_pi_ah / r.ah["Pi"], 1.02, places=3)


class TestPassportAndDataset(unittest.TestCase):
    def setUp(self):
        import db.database as dbm
        self.tmp = tempfile.mkdtemp()
        self._old = dbm.DB_PATH
        dbm.DB_PATH = os.path.join(self.tmp, "t.db")
        dbm.init_db()
        from db.migrations import migrate
        migrate()
        self.dbm = dbm
        self.bid, self.oid = dbm.create_battery(source_type="fleet", brand="B", model="M", chemistry="NMC", nominal_voltage=36.0,
                                                max_charge_voltage=42.0, cutoff_voltage=30.0, capacity_rated_ah=5.0,
                                                energy_rated_wh=180.0)
        for cap, r in ((4.5, 80.0), (4.2, 90.0)):
            tid = dbm.start_test(self.bid)
            conn = dbm.get_connection()
            conn.execute("UPDATE tests SET capacity_ah=?, internal_resistance_mohm=?, capacity_retention_pct=?, "
                         "calibration_id='CAL-X', pcb_revision='RC1.2e' WHERE test_id=?", (cap, r, cap / 5.0 * 100, tid))
            conn.commit(); conn.close()
            dbm.insert_reading(tid, 0, 40000, 3000, 120000, 250)

    def tearDown(self):
        self.dbm.DB_PATH = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_persistent_id_format(self):
        self.assertRegex(self.oid, r"^OSB-\d{6}$")

    def test_passport_contents_and_trend(self):
        from services.battery_passport import build_passport, PASSPORT_SCHEMA
        p = build_passport(self.bid)
        self.assertEqual(p["schema"], PASSPORT_SCHEMA)
        self.assertEqual(len(p["tests"]), 2)
        self.assertEqual(p["tests"][0]["calibration_id"], "CAL-X")
        self.assertAlmostEqual(p["trend"]["capacity_change_pct"], (4.2 - 4.5) / 4.5 * 100)
        self.assertIn("not a validated", p["disclaimer"])
        self.assertIsNone(build_passport(9999))

    def test_dataset_export_anonymized_and_na_empty(self):
        from services.dataset_export import export_dataset, anonymize, TEST_COLUMNS, SAMPLE_COLUMNS
        out = os.path.join(self.tmp, "ds")
        n = export_dataset(out, salt="s3cret")
        self.assertEqual((n["tests"], n["samples"], n["batteries"]), (2, 2, 1))
        rows = list(csv.DictReader(open(os.path.join(out, "tests.csv"))))
        self.assertEqual(list(rows[0].keys()), TEST_COLUMNS)
        self.assertEqual(rows[0]["anon_battery_id"], anonymize(self.oid, "s3cret"))
        self.assertNotIn(self.oid, open(os.path.join(out, "tests.csv")).read())
        self.assertEqual(rows[0]["ah_ina"], "")                     # unavailable = empty, never 0
        self.assertIn("not validated SOH", rows[0]["retention_label"])
        srows = list(csv.DictReader(open(os.path.join(out, "samples.csv"))))
        self.assertEqual(list(srows[0].keys()), SAMPLE_COLUMNS)
        self.assertEqual(srows[0]["voltage_adc_v"], "")
        with self.assertRaises(ValueError):
            anonymize(self.oid, "")

    def test_capacity_validation_persisted(self):
        from services.run_persistence import save_capacity_validation
        t = cv.AccumulatorTracker()
        for s in _frames():
            t.add(s)
        res = cv.validate(t.summary(5.0), calibration_id="CAL-X", firmware_version="fw", pcb_revision="RC1.2e")
        tid = self.dbm.get_tests_for_battery(self.bid)[0]["test_id"]
        save_capacity_validation(tid, res)
        row = dict(self.dbm.get_connection().execute("SELECT * FROM tests WHERE test_id=?", (tid,)).fetchone())
        self.assertEqual(row["capacity_validation_status"], "OK")
        self.assertIsNotNone(row["ah_ina"])
        self.assertEqual(row["sample_count"], 60)


if __name__ == "__main__":
    unittest.main()
