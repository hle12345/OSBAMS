"""Settings → Calibration and Validation / Measurement Quality screens (offscreen Qt)."""
import os, shutil, sys, tempfile, unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from PySide6.QtWidgets import QApplication

from services import calibration as cal
from services import quality

_app = QApplication.instance() or QApplication([])


class TestSettingsTab(unittest.TestCase):
    def setUp(self):
        import db.database as dbm
        self.tmp = tempfile.mkdtemp()
        self._old = dbm.DB_PATH
        dbm.DB_PATH = os.path.join(self.tmp, "t.db")
        dbm.init_db()
        from db.migrations import migrate
        migrate()
        self.dbm = dbm

    def tearDown(self):
        self.dbm.DB_PATH = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_profile_fit_zero_and_reference_required(self):
        from gui.tabs.settings_tab import build_profile
        v = "\n".join(f"{r}, {(r - 0.02) / 1.005}" for r in (30, 34, 38, 42))
        p = build_profile(v, "", "0.002 0.001 0.003", "EDU34450A (serial per instrument)")
        self.assertAlmostEqual(p.voltage.gain, 1.005, places=6)
        self.assertEqual(p.current.n, 0)
        self.assertAlmostEqual(p.zero_current_offset_a, 0.002)
        with self.assertRaises(cal.CalibrationError):
            build_profile(v, "", "", "  ")                    # reference instrument is mandatory
        with self.assertRaises(cal.CalibrationError):
            build_profile("", "", "", "ref")                  # nothing entered

    def test_panels_save_activate_and_show_not_available(self):
        from gui.tabs.settings_tab import SettingsTab
        from services import calibration_store as store
        t = SettingsTab()
        self.assertIn("NONE", t.calibration.active.text())
        self.assertIn("NOT AVAILABLE", t.quality.head.text())      # no test yet: never a silent PASS
        t.calibration.v_pts.setPlainText("30, 29.9\n42, 41.9")
        t.calibration.ref.setText("EDU34450A")
        t.calibration.save()
        self.assertIsNotNone(store.get_active())
        self.assertIn(store.get_active().calibration_id, t.calibration.active.text())
        t.calibration.v_pts.setPlainText("30, 5\n42, 41.9")      # absurd gain is refused, not saved
        t.calibration.save()
        self.assertIn("ERROR", t.calibration.out.toPlainText())

    def test_quality_rows_unavailable_items(self):
        from gui.tabs.settings_tab import quality_rows
        q = quality.assess(None)
        rows = quality_rows(__import__("json").dumps(q.to_dict()))
        self.assertTrue(rows)
        self.assertIn("NOT AVAILABLE", [r[3] for r in rows])
        self.assertEqual(q.status, quality.REVIEW)

    def test_main_window_has_settings_tab(self):
        from gui.main_window import MainWindow
        w = MainWindow()
        self.assertIn("Settings", " ".join(w.tabs.tabText(i) for i in range(w.tabs.count())))


if __name__ == "__main__":
    unittest.main()
