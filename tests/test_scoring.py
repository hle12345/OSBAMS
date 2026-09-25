"""
tests/test_scoring.py — Unit tests for OSBAMS scoring and integration
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from gui.scoring import ScoringInputs, ScoringResult, trapezoidal_integrate


class TestScoringWeights(unittest.TestCase):
    """Score components must sum to 100."""

    def test_perfect_battery(self):
        inp = ScoringInputs(
            measured_ah=15.3, rated_ah=15.3,
            measured_wh=551.0, rated_wh=551.0,
            max_temp_c=25.0, ambient_temp_c=25.0,
            initial_voltage_sag_mv=0,
            bms_cutoff_detected=False,
            physical_score=10,
            self_discharge_mv=0,
        )
        r = ScoringResult.from_inputs(inp)
        # Perfect battery: all component maxes, self-discharge neutral = 97
        self.assertEqual(r.grade, "A")
        self.assertGreaterEqual(r.total_score, 90)

    def test_dead_battery(self):
        inp = ScoringInputs(
            measured_ah=1.0, rated_ah=15.3,
            measured_wh=30.0, rated_wh=551.0,
            max_temp_c=55.0, ambient_temp_c=25.0,
            initial_voltage_sag_mv=4000,
            bms_cutoff_detected=True,
            physical_score=1,
            self_discharge_mv=800,
        )
        r = ScoringResult.from_inputs(inp)
        self.assertLess(r.total_score, 30)
        self.assertEqual(r.grade, "F")

    def test_grade_b(self):
        inp = ScoringInputs(
            measured_ah=12.4, rated_ah=15.3,
            measured_wh=446.0, rated_wh=551.0,
            max_temp_c=35.0, ambient_temp_c=25.0,
            initial_voltage_sag_mv=600,
            bms_cutoff_detected=False,
            physical_score=8,
        )
        r = ScoringResult.from_inputs(inp)
        self.assertIn(r.grade, ("A", "B", "C"))   # reasonable battery → at least C

    def test_soh_combined_formula(self):
        inp = ScoringInputs(
            measured_ah=10.0, rated_ah=15.0,
            measured_wh=360.0, rated_wh=540.0,
            max_temp_c=30.0,
        )
        r = ScoringResult.from_inputs(inp)
        # SOH_Ah = 66.7%, SOH_Wh = 66.7%, combined = 66.7%
        self.assertAlmostEqual(r.soh_ah_pct,  66.7, delta=0.5)
        self.assertAlmostEqual(r.soh_wh_pct,  66.7, delta=0.5)
        self.assertAlmostEqual(r.soh_combined, 66.7, delta=0.5)

    def test_breakdown_sum(self):
        """Breakdown values must sum to total_score."""
        inp = ScoringInputs(
            measured_ah=11.0, rated_ah=15.3,
            measured_wh=396.0, rated_wh=551.0,
            max_temp_c=40.0, ambient_temp_c=25.0,
            initial_voltage_sag_mv=1200,
            bms_cutoff_detected=False,
            physical_score=7,
        )
        r = ScoringResult.from_inputs(inp)
        self.assertEqual(sum(r.breakdown.values()), r.total_score)


class TestTrapezoidalIntegration(unittest.TestCase):

    def test_constant_current_1a_1h(self):
        """1 A for 1 hour at 36V should give ≈ 1 Ah and ≈ 36 Wh."""
        readings = [
            {"tick_ms": 0,       "current_ma": 1000, "power_mw": 36000,
             "voltage_mv": 36000, "temp_c10": 250},
            {"tick_ms": 1800000, "current_ma": 1000, "power_mw": 36000,
             "voltage_mv": 36000, "temp_c10": 250},
            {"tick_ms": 3600000, "current_ma": 1000, "power_mw": 36000,
             "voltage_mv": 36000, "temp_c10": 250},
        ]
        stats = trapezoidal_integrate(readings)
        self.assertAlmostEqual(stats["total_ah"], 1.0, delta=0.01)
        self.assertAlmostEqual(stats["total_wh"], 36.0, delta=0.5)

    def test_varying_current(self):
        """Trapezoidal vs simple: should give different results when current varies."""
        readings = [
            {"tick_ms": 0,       "current_ma": 1000, "power_mw": 36000,
             "voltage_mv": 36000, "temp_c10": 250},
            {"tick_ms": 1800000, "current_ma": 3000, "power_mw": 108000,
             "voltage_mv": 36000, "temp_c10": 250},
            {"tick_ms": 3600000, "current_ma": 1000, "power_mw": 36000,
             "voltage_mv": 36000, "temp_c10": 250},
        ]
        stats = trapezoidal_integrate(readings)
        # Average current = (1+3+1)/... trapezoidally = 2A average ≈ 2 Ah
        self.assertAlmostEqual(stats["total_ah"], 2.0, delta=0.1)

    def test_min_voltage_captured(self):
        readings = [
            {"tick_ms": 0,    "current_ma": 2000, "power_mw": 80000,
             "voltage_mv": 42000, "temp_c10": 250},
            {"tick_ms": 500,  "current_ma": 2000, "power_mw": 70000,
             "voltage_mv": 35000, "temp_c10": 300},
            {"tick_ms": 1000, "current_ma": 2000, "power_mw": 60000,
             "voltage_mv": 30000, "temp_c10": 320},
        ]
        stats = trapezoidal_integrate(readings)
        self.assertEqual(stats["min_voltage_mv"], 30000)
        self.assertEqual(stats["max_voltage_mv"], 35000)
        self.assertAlmostEqual(stats["max_temp_c"], 32.0, delta=0.1)

    def test_single_sample_returns_zeros(self):
        stats = trapezoidal_integrate([
            {"tick_ms": 0, "current_ma": 2000, "power_mw": 80000,
             "voltage_mv": 42000, "temp_c10": 250}
        ])
        self.assertEqual(stats["total_ah"], 0.0)
        self.assertEqual(stats["total_wh"], 0.0)

    def test_bms_cutoff_detection(self):
        """Sudden 3V drop at end should flag bms_cutoff_detected."""
        readings = []
        for i in range(20):
            v = 42000 - i * 100   # slow decline
            readings.append({"tick_ms": i * 500, "current_ma": 2000,
                              "power_mw": v * 2, "voltage_mv": v, "temp_c10": 250})
        # Sharp drop at end
        readings.append({"tick_ms": 10500, "current_ma": 0,
                         "power_mw": 0, "voltage_mv": 31000, "temp_c10": 250})
        readings.append({"tick_ms": 11000, "current_ma": 0,
                         "power_mw": 0, "voltage_mv": 31000, "temp_c10": 250})
        readings.append({"tick_ms": 11500, "current_ma": 0,
                         "power_mw": 0, "voltage_mv": 28000, "temp_c10": 250})
        stats = trapezoidal_integrate(readings)
        self.assertTrue(stats["bms_cutoff_detected"])


class TestValidators(unittest.TestCase):

    def test_ocv_above_max_is_error(self):
        from gui.validators import validate_battery_intake
        errs, _ = validate_battery_intake(
            osbams_id="OSB-006", safety_status="Quarantine",
            nominal_voltage=36.0, max_charge_voltage=42.0,
            initial_ocv_v=43.5,
        )
        ocv_errs = [e for e in errs if e[0] == "initial_ocv_v"]
        self.assertTrue(len(ocv_errs) > 0)

    def test_wh_inconsistency_is_warning(self):
        from gui.validators import validate_battery_intake
        _, warns = validate_battery_intake(
            osbams_id="OSB-X", safety_status="Pending",
            nominal_voltage=36.0, max_charge_voltage=42.0,
            capacity_rated_ah=15.3,
            energy_rated_wh=200.0,   # should be ~551 Wh
        )
        wh_warns = [w for w in warns if w[0] == "energy_rated_wh"]
        self.assertTrue(len(wh_warns) > 0)

    def test_quarantine_blocks_test(self):
        from gui.validators import validate_test_config
        errs, _ = validate_test_config(
            battery_safety_status="Quarantine",
            cutoff_voltage_v=30.0,
            max_temp_c=50.0,
        )
        self.assertTrue(len(errs) > 0)


class TestSerialParser(unittest.TestCase):

    def test_parse_valid_frame(self):
        """Protocol v1 sample construction and unit conversion."""
        from services.protocol import OsbamsSample
        s = OsbamsSample(
            protocol_version=1, sequence=7, tick_ms=1500,
            voltage_mv=41820, current_ma=2000, power_mw=83640,
            temp_c10=240,          # TC74 is 1 C resolution -> multiple of 10
            flags=0, state="DISCHARGING", crc_valid=True)
        self.assertAlmostEqual(s.voltage_v, 41.82, places=3)
        self.assertAlmostEqual(s.current_a,  2.0,  places=3)
        self.assertAlmostEqual(s.temp_c,    24.0,  places=1)
        self.assertTrue(s.crc_valid)
        self.assertFalse(s.has_fault)

    def test_simulator_output_parseable(self):
        """Simulator must emit valid Protocol v1 frames with correct CRC."""
        from services.electronic_load import SimulatorLoad
        from services.protocol import parse_frame
        sim   = SimulatorLoad("normal", sample_rate_ms=30000)
        lines = sim.generate_lines()
        self.assertGreater(len(lines), 0)
        for line in lines[:20]:
            r = parse_frame(line)
            self.assertIsNotNone(r.sample, f"{line!r}: {r.error}")
            self.assertTrue(r.sample.crc_valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
