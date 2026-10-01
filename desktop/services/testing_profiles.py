"""
services/testing_profiles.py — Battery Testing Profiles

Instead of every battery using the same hardcoded scooter test,
testing profiles define per-category defaults that auto-populate
the test configuration dialog.

Each profile specifies:
  - Discharge current (A)
  - Voltage cutoff (V)
  - Max temperature (C)
  - Max duration (hours)
  - Rest period before test (minutes)
  - Notes for the operator

The Dashboard loads the correct profile automatically when
a battery category is selected.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TestingProfile:
    name:           str
    category:       str
    current_a:      float
    cutoff_v:       float
    max_temp_c:     float   = 50.0
    max_duration_h: float   = 8.0
    rest_min:       int     = 30
    load_mode:      str     = "CC"    # CC / CP / CR
    notes:          str     = ""
    # Suitability thresholds for this application
    min_soh_pct:    float   = 60.0   # below this → not suitable
    min_score:      int     = 50


# ── Profile registry ──────────────────────────────────────────────────────────

PROFILES: dict[str, TestingProfile] = {

    "scooter_standard": TestingProfile(
        name          = "Scooter — Standard Discharge",
        category      = "scooter",
        current_a     = 3.0,
        cutoff_v      = 30.0,
        max_temp_c    = 50.0,
        max_duration_h= 6.0,
        rest_min      = 30,
        notes         = "Standard 3A CC discharge for 36V/10S scooter packs. "
                        "Matches typical ~0.2C rate for 15 Ah packs.",
        min_soh_pct   = 65.0,
        min_score     = 60,
    ),

    "scooter_quick": TestingProfile(
        name          = "Scooter — Quick Screen",
        category      = "scooter",
        current_a     = 5.0,
        cutoff_v      = 30.0,
        max_temp_c    = 50.0,
        max_duration_h= 3.0,
        rest_min      = 15,
        notes         = "Higher current for faster screening. "
                        "Ah result will be slightly lower than standard test. "
                        "Use for initial sort only — follow up with standard test.",
        min_soh_pct   = 65.0,
        min_score     = 55,
    ),

    "ebike_standard": TestingProfile(
        name          = "E-Bike — Standard Discharge",
        category      = "ebike",
        current_a     = 5.0,
        cutoff_v      = 39.0,    # typical 48V / 13S pack
        max_temp_c    = 50.0,
        max_duration_h= 8.0,
        rest_min      = 45,
        notes         = "For 48V (13S) e-bike packs. "
                        "Cutoff at 3.0V/cell = 39V. Verify cell count before testing.",
        min_soh_pct   = 70.0,
        min_score     = 65,
    ),

    "power_tool_standard": TestingProfile(
        name          = "Power Tool — Standard Discharge",
        category      = "power_tool",
        current_a     = 8.0,
        cutoff_v      = 15.0,    # typical 18V / 5S pack
        max_temp_c    = 55.0,
        max_duration_h= 2.0,
        rest_min      = 20,
        notes         = "Power tools run at higher C-rates. "
                        "18V DeWalt/Milwaukee = 5S NMC cutoff ~3.0V/cell = 15V. "
                        "Monitor temperature closely at 8A.",
        min_soh_pct   = 60.0,
        min_score     = 55,
    ),

    "ups_standard": TestingProfile(
        name          = "UPS / Backup — Long Duration",
        category      = "ups",
        current_a     = 1.0,
        cutoff_v      = 30.0,
        max_temp_c    = 45.0,
        max_duration_h= 16.0,
        rest_min      = 60,
        notes         = "UPS batteries discharge slowly over many hours. "
                        "Low current gives the most accurate capacity measurement. "
                        "Allow longer rest before test for OCV stabilization.",
        min_soh_pct   = 70.0,
        min_score     = 65,
    ),

    "solar_storage": TestingProfile(
        name          = "Portable Solar Storage",
        category      = "solar_storage",
        current_a     = 2.0,
        cutoff_v      = 30.0,
        max_temp_c    = 50.0,
        max_duration_h= 10.0,
        rest_min      = 45,
        notes         = "Stationary storage — lower C-rate preferred. "
                        "2A gives accurate capacity with minimal voltage sag artifact.",
        min_soh_pct   = 55.0,
        min_score     = 50,
    ),

    "robot_standard": TestingProfile(
        name          = "Robot / Mobility Device",
        category      = "robot",
        current_a     = 4.0,
        cutoff_v      = 30.0,
        max_temp_c    = 50.0,
        max_duration_h= 5.0,
        rest_min      = 30,
        notes         = "Mid-range current for robot/mobility applications.",
        min_soh_pct   = 70.0,
        min_score     = 65,
    ),

    "custom": TestingProfile(
        name          = "Custom — Manual Configuration",
        category      = "custom",
        current_a     = 3.0,
        cutoff_v      = 30.0,
        max_temp_c    = 50.0,
        max_duration_h= 6.0,
        rest_min      = 30,
        notes         = "Set all parameters manually.",
        min_soh_pct   = 60.0,
        min_score     = 50,
    ),
}

# Battery categories with display names
BATTERY_CATEGORIES = {
    "scooter":        "Electric Scooter",
    "ebike":          "E-Bike",
    "power_tool":     "Power Tool",
    "ups":            "UPS / Backup Power",
    "solar_storage":  "Portable Solar Storage",
    "robot":          "Robot / Mobility Device",
    "custom":         "Custom / Unknown",
}

# Default profile per category
CATEGORY_DEFAULT_PROFILE = {
    "scooter":       "scooter_standard",
    "ebike":         "ebike_standard",
    "power_tool":    "power_tool_standard",
    "ups":           "ups_standard",
    "solar_storage": "solar_storage",
    "robot":         "robot_standard",
    "custom":        "custom",
}


def get_profile(profile_key: str) -> TestingProfile:
    return PROFILES.get(profile_key, PROFILES["custom"])


def get_default_profile_for_category(category: str) -> TestingProfile:
    key = CATEGORY_DEFAULT_PROFILE.get(category, "custom")
    return PROFILES[key]


def profiles_for_category(category: str) -> list[tuple[str, TestingProfile]]:
    """Return all profiles applicable to a given category."""
    return [(k, v) for k, v in PROFILES.items()
            if v.category == category or v.category == "custom"]


if __name__ == "__main__":
    print("OSBAMS Testing Profiles")
    print("=" * 50)
    for key, p in PROFILES.items():
        print(f"\n  {p.name}")
        print(f"    {p.current_a}A  cutoff={p.cutoff_v}V  "
              f"max_temp={p.max_temp_c}C  duration={p.max_duration_h}h")
        print(f"    Min SOH: {p.min_soh_pct}%  Min score: {p.min_score}")
