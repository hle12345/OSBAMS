"""
tests/test_suitability.py — Unit tests for suitability and lifecycle services
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "desktop"))

import unittest
from services.suitability import (
    evaluate_safety, evaluate_suitability, full_assessment,
    HealthResult, SafetyResult
)
from services.testing_profiles import (
    get_profile, get_default_profile_for_category,
    PROFILES, BATTERY_CATEGORIES
)


class TestSafetyEvaluation(unittest.TestCase):

    def test_quarantine_blocks_all(self):
        batt = {"safety_status": "Quarantine",
                "physical_notes": "Red lead cut",
                "capacity_rated_ah": 15.3}
        result = evaluate_safety(batt)
        self.assertEqual(result.status, "QUARANTINE")
        self.assertTrue(result.blocks_testing)
        self.assertFalse(result.passes)

    def test_clean_battery_passes(self):
        batt = {"safety_status": "OK",
                "physical_condition": "Good",
                "connector_condition": "XT60 intact",
                "initial_ocv_v": 41.5,
                "max_charge_voltage": 42.0}
        result = evaluate_safety(batt)
        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.passes)

    def test_ocv_above_max_triggers_hold(self):
        batt = {"safety_status": "Pending",
                "initial_ocv_v": 43.5,
                "max_charge_voltage": 42.0}
        result = evaluate_safety(batt)
        self.assertIn(result.status, ("HOLD", "QUARANTINE"))
        self.assertTrue(result.blocks_testing)

    def test_cut_lead_triggers_hold(self):
        batt = {"safety_status": "Pending",
                "physical_notes": "Red positive lead cut near XT60",
                "connector_condition": "cut"}
        result = evaluate_safety(batt)
        self.assertNotEqual(result.status, "PASS")
        self.assertTrue(result.blocks_testing)

    def test_swollen_triggers_quarantine(self):
        batt = {"safety_status": "Pending",
                "physical_condition": "pack appears swollen on one side"}
        result = evaluate_safety(batt)
        self.assertEqual(result.status, "QUARANTINE")


class TestSuitabilityEvaluation(unittest.TestCase):

    def _healthy_battery(self, soh=85.0, score=82):
        return HealthResult(
            soh_ah_pct=soh, soh_wh_pct=soh, soh_combined=soh,
            rule_score=score, consensus_score=score, grade="B")

    def _safe(self):
        return SafetyResult(status="PASS", blocks_testing=False)

    def _quarantine(self):
        return SafetyResult(status="QUARANTINE", blocks_testing=True)

    def test_quarantine_blocks_all_applications(self):
        health = self._healthy_battery()
        safety = self._quarantine()
        result = evaluate_suitability(health, safety)
        suitable = [a for a in result.applications if a.verdict == "Suitable"]
        self.assertEqual(len(suitable), 0,
                         "Quarantine must block ALL application suitability")

    def test_healthy_battery_qualifies_for_multiple(self):
        health = self._healthy_battery(soh=85.0, score=82)
        safety = self._safe()
        result = evaluate_suitability(health, safety, temp_rise_c=8.0, voltage_sag_v=2.0)
        suitable = [a.application for a in result.applications if a.verdict == "Suitable"]
        self.assertGreater(len(suitable), 2)
        self.assertIsNotNone(result.top_recommendation)

    def test_degraded_battery_not_suitable_for_high_power(self):
        health = self._healthy_battery(soh=55.0, score=48)
        safety = self._safe()
        result = evaluate_suitability(health, safety, temp_rise_c=18.0, voltage_sag_v=5.0)
        # Should not qualify for high-performance scooter
        hp = next(a for a in result.applications
                  if "high performance" in a.application)
        self.assertEqual(hp.verdict, "Not Suitable")

    def test_runtime_calculated(self):
        health = self._healthy_battery(soh=76.0, score=69)
        safety = self._safe()
        result = evaluate_suitability(health, safety,
                                       temp_rise_c=10.0, voltage_sag_v=2.8,
                                       rated_ah=15.3)
        # At least some apps should have runtime estimates
        with_runtime = [a for a in result.applications
                        if a.expected_runtime_h is not None]
        self.assertGreater(len(with_runtime), 0)

    def test_safety_always_before_health(self):
        """Safety status must be PASS before any suitability is granted."""
        health_good = self._healthy_battery(soh=95.0, score=95)
        safety_bad  = self._quarantine()
        result = evaluate_suitability(health_good, safety_bad)
        for a in result.applications:
            self.assertNotEqual(a.verdict, "Suitable",
                                f"{a.application} should NOT be Suitable when quarantined")


class TestTestingProfiles(unittest.TestCase):

    def test_all_categories_have_profiles(self):
        for cat in ["scooter", "ebike", "power_tool", "ups"]:
            p = get_default_profile_for_category(cat)
            self.assertIsNotNone(p)
            self.assertGreater(p.current_a, 0)
            self.assertGreater(p.cutoff_v, 0)

    def test_scooter_profile_reasonable(self):
        p = get_profile("scooter_standard")
        self.assertAlmostEqual(p.current_a, 3.0, places=1)
        self.assertAlmostEqual(p.cutoff_v, 30.0, places=1)
        self.assertGreaterEqual(p.max_temp_c, 45)
        self.assertGreaterEqual(p.rest_min, 15)

    def test_power_tool_higher_current_than_scooter(self):
        scooter = get_profile("scooter_standard")
        tool    = get_profile("power_tool_standard")
        self.assertGreater(tool.current_a, scooter.current_a)

    def test_ups_lower_current_long_duration(self):
        ups     = get_profile("ups_standard")
        scooter = get_profile("scooter_standard")
        self.assertLess(ups.current_a, scooter.current_a)
        self.assertGreater(ups.max_duration_h, scooter.max_duration_h)

    def test_unknown_profile_returns_custom(self):
        p = get_profile("nonexistent_profile_xyz")
        self.assertEqual(p.category, "custom")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestChemistryProfiles(unittest.TestCase):

    def test_nmc_10s_pack_voltages(self):
        from services.chemistry_profiles import get_chemistry, derive_voltages
        v = derive_voltages("NMC", 10)
        self.assertAlmostEqual(v["nominal_voltage"],    36.0, places=1)
        self.assertAlmostEqual(v["max_charge_voltage"], 42.0, places=1)
        self.assertAlmostEqual(v["cutoff_voltage"],     30.0, places=1)

    def test_lfp_different_from_nmc(self):
        from services.chemistry_profiles import get_chemistry
        nmc = get_chemistry("NMC")
        lfp = get_chemistry("LFP")
        self.assertLess(lfp.max_cell_v, nmc.max_cell_v)
        self.assertGreater(lfp.cycle_life_est, nmc.cycle_life_est)

    def test_soc_from_ocv_osb005(self):
        """OSB-005 had 30.8V OCV on 10S NMC — should be very low SOC."""
        from services.chemistry_profiles import estimate_soc_from_ocv
        soc = estimate_soc_from_ocv("NMC", 10, 30.8)
        self.assertIsNotNone(soc)
        self.assertLess(soc, 10.0, "30.8V on 10S NMC should be < 10% SOC")

    def test_unknown_chemistry_returns_defaults(self):
        from services.chemistry_profiles import get_chemistry
        unknown = get_chemistry("XYZZY")
        self.assertEqual(unknown.abbreviation, "?")
        self.assertGreater(unknown.nominal_cell_v, 0)

    def test_all_chemistries_have_soc_table(self):
        from services.chemistry_profiles import CHEMISTRIES
        for key, chem in CHEMISTRIES.items():
            if key == "unknown":
                continue
            self.assertGreater(len(chem.soc_ocv_table), 0,
                               f"{key} missing SOC-OCV table")

    def test_full_charge_is_100pct(self):
        from services.chemistry_profiles import get_chemistry
        nmc = get_chemistry("NMC")
        soc = nmc.soc_from_ocv(nmc.max_cell_v)
        self.assertEqual(soc, 100.0)
