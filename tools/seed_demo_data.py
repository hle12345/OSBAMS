#!/usr/bin/env python3
"""
tools/seed_demo_data.py — Populate OSBAMS with realistic demo data

Creates synthetic but realistic test histories for your 7 existing packs
so the presentation can show:
  1. What battery is this?           → Registry / Battery Details
  2. Is it safe?                     → Safety status, quarantine flags
  3. How much capacity/energy?       → Test results, SOH
  4. How does it compare?            → Comparison tab, SOH trend
  5. What should be done next?       → AI recommendation, second-life uses

Usage:
    python tools/seed_demo_data.py           # add test history to OSB-001..007
    python tools/seed_demo_data.py --reset   # wipe tests then re-seed
    python tools/seed_demo_data.py --dry-run # show what would be created

Safe to run multiple times with --reset.
"""

import sys
import os
import json
import argparse
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "desktop"))
from db.database import (
    get_connection, get_all_batteries, start_test, end_test,
    insert_reading, get_tests_for_battery, init_db
)
from db.migrations import migrate, save_prediction, log_event
from gui.scoring import ScoringInputs, ScoringResult, trapezoidal_integrate
from equipment.drivers import Simulator6060B
from gui.ai_model import OSBAMSModel, extract_features, second_life_recommendation

# ── Demo scenarios per battery ────────────────────────────────────────────────
# Maps OSB ID → list of test scenarios (oldest → newest)
DEMO_SCENARIOS = {
    "OSB-001": [
        # Small 5.2 Ah Ninebot pack — decent for its size
        {"profile": "normal",   "soh_override": 0.87, "days_ago": 45,
         "notes": "First test — pack appears functional"},
        {"profile": "normal",   "soh_override": 0.85, "days_ago": 10,
         "notes": "Second test — capacity stable"},
    ],
    "OSB-002": [
        # 12.8 Ah Shenzhen Elite — unknown history
        {"profile": "degraded", "soh_override": 0.72, "days_ago": 30,
         "notes": "Capacity below expectation — moderate degradation"},
    ],
    "OSB-003": [
        # Another small Ninebot — no serial, slightly worse
        {"profile": "degraded", "soh_override": 0.68, "days_ago": 20,
         "notes": "Lower capacity, moderate voltage sag observed"},
        {"profile": "degraded", "soh_override": 0.66, "days_ago": 5,
         "notes": "Second test confirms degradation — grade C"},
    ],
    "OSB-004": [
        # 12.8 Ah Shenzhen Elite v2 — better than OSB-002
        {"profile": "normal",   "soh_override": 0.81, "days_ago": 25,
         "notes": "Solid performance — reuse candidate"},
    ],
    "OSB-005": [
        # 15.3 Ah NEE1006-M — bottom open, was depleted at 30.8V
        # Had to charge first, then test. Came back reasonably well.
        {"profile": "normal",   "soh_override": 0.76, "days_ago": 14,
         "notes": "Bottom cover open — charged overnight first. "
                  "OCV recovered to 41.2V after charge. "
                  "Capacity acceptable for light reuse."},
        {"profile": "normal",   "soh_override": 0.74, "days_ago": 2,
         "notes": "Repeat test — capacity consistent. Grade C."},
    ],
    "OSB-006": [
        # Quarantine — 43.5V anomaly — NO test data (safety hold)
        # Intentionally empty so UI shows quarantine state correctly
    ],
    "OSB-007": [
        # Cut red lead — also quarantine — NO test data
    ],
}


def _sim_readings(profile: str, rated_ah: float,
                  soh_override: float, base_tick: int = 0) -> list[dict]:
    """Generate simulated readings scaled to the battery's rated capacity."""
    sim = Simulator6060B(profile=profile, sample_rate_ms=500)
    p   = sim._p.copy()
    p["rated_ah"] = rated_ah
    p["soh"]      = soh_override

    actual_ah = rated_ah * soh_override
    current_a = p["current_a"]
    dur_ms    = int((actual_ah / current_a) * 3600 * 1000)
    # Use 30-second samples for demo seeding (accurate Ah/Wh, manageable row count)
    # 15.3 Ah / 3A = 5.1h = 612 steps at 30s — fast and accurate
    seed_rate_ms = 30_000
    steps        = dur_ms // seed_rate_ms

    import math
    readings = []
    for i in range(steps):
        progress = i / max(steps, 1)
        v_range = p["start_v"] - p["cutoff_v"]
        voltage = p["start_v"] - v_range * (progress ** 0.8)
        if i == 1:
            voltage -= p["sag_v"]
        current = current_a * (1.0 + 0.02 * math.sin(progress * 6))
        power   = voltage * current
        temp    = p["temp_start"] + p["temp_rise"] * (1 - math.exp(-progress * 3))
        readings.append({
            "tick_ms":    base_tick + i * seed_rate_ms,
            "voltage_mv": int(voltage * 1000),
            "current_ma": int(current * 1000),
            "power_mw":   int(power * 1000),
            "temp_c10":   int(temp * 10),
        })
    return readings


def seed(dry_run: bool = False):
    init_db()
    migrate()

    batteries = {b["osbams_id"]: b for b in get_all_batteries() if b.get("osbams_id")}
    model     = OSBAMSModel()
    created   = []

    for osbams_id, scenarios in DEMO_SCENARIOS.items():
        batt = batteries.get(osbams_id)
        if not batt:
            print(f"  SKIP {osbams_id} — not in database")
            continue

        if not scenarios:
            print(f"  {osbams_id} — quarantine, no test data (correct)")
            continue

        existing = get_tests_for_battery(batt["battery_id"])
        completed = [t for t in existing if t.get("ended_at")]
        if completed and not dry_run:
            print(f"  {osbams_id} — already has {len(completed)} test(s), skipping")
            continue

        rated_ah = batt.get("capacity_rated_ah") or 10.0
        rated_wh = batt.get("energy_rated_wh")   or rated_ah * 36.0

        for scenario in scenarios:
            test_date = datetime.now() - timedelta(days=scenario["days_ago"])
            profile   = scenario["profile"]
            soh_ov    = scenario["soh_override"]
            notes_txt = scenario["notes"]

            if dry_run:
                print(f"  [DRY RUN] {osbams_id}  profile={profile}  "
                      f"soh={soh_ov:.0%}  date={test_date.date()}")
                continue

            # Insert test session
            tid = start_test(batt["battery_id"], "discharge")

            # Generate and store readings
            readings = _sim_readings(profile, rated_ah, soh_ov)
            for r in readings:
                insert_reading(tid, r["tick_ms"], r["voltage_mv"],
                               r["current_ma"], r["power_mw"], r["temp_c10"])

            # Calculate results via trapezoidal integration
            stats = trapezoidal_integrate(readings)

            # Scoring
            inp = ScoringInputs(
                measured_ah            = stats["total_ah"],
                measured_wh            = stats["total_wh"],
                max_temp_c             = stats["max_temp_c"],
                ambient_temp_c         = 25.0,
                initial_voltage_sag_mv = stats["initial_voltage_sag_mv"],
                bms_cutoff_detected    = stats["bms_cutoff_detected"],
                rated_ah               = rated_ah,
                rated_wh               = rated_wh,
                physical_score         = batt.get("physical_score") or 8,
            )
            score_result = ScoringResult.from_inputs(inp)

            # Close test with full results
            conn = get_connection()
            conn.execute("""
                UPDATE tests SET
                    started_at=?, ended_at=?,
                    notes=?,
                    capacity_ah=?, energy_wh=?,
                    discharge_time_s=?,
                    min_voltage_mv=?, max_temp_c=?,
                    soh_percent=?,
                    reliability_score=?, grade=?, recommendation=?,
                    average_current_a=?, average_power_w=?,
                    voltage_sag_mv=?,
                    ambient_temp_c=?, cutoff_voltage_v=?,
                    current_setpoint_a=?, load_mode=?,
                    stop_reason=?
                WHERE test_id=?
            """, (
                test_date.isoformat(),
                (test_date + timedelta(seconds=stats["discharge_time_s"])).isoformat(),
                notes_txt,
                round(stats["total_ah"], 3),
                round(stats["total_wh"], 3),
                round(stats["discharge_time_s"], 1),
                stats["min_voltage_mv"],
                round(stats["max_temp_c"], 1),
                round(score_result.soh_combined, 1),
                score_result.total_score,
                score_result.grade,
                score_result.recommendation,
                round(stats["average_current_a"], 3),
                round(stats["average_power_w"], 3),
                stats["initial_voltage_sag_mv"],
                25.0, 30.0, 3.0, "CC",
                "voltage_cutoff",
                tid,
            ))
            conn.commit()
            conn.close()

            # AI prediction
            ai_result = model.predict(batt["battery_id"], tid)
            try:
                save_prediction(tid, batt["battery_id"], ai_result)
            except Exception:
                pass   # predictions table migration may differ — non-fatal

            # Audit log
            log_event("test_complete",
                      f"Demo seed: {osbams_id} test#{tid} "
                      f"Ah={stats['total_ah']:.2f} grade={score_result.grade}",
                      battery_id=batt["battery_id"], test_id=tid)

            created.append({
                "osbams_id": osbams_id,
                "test_id":   tid,
                "profile":   profile,
                "ah":        round(stats["total_ah"], 2),
                "wh":        round(stats["total_wh"], 1),
                "soh":       round(score_result.soh_combined, 1),
                "score":     score_result.total_score,
                "grade":     score_result.grade,
                "ai_label":  ai_result.label,
                "date":      test_date.date(),
            })

    return created


def reset_tests():
    """Remove all test sessions and readings (batteries preserved)."""
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute("DELETE FROM readings")
    conn.execute("DELETE FROM features")
    try:
        conn.execute("DELETE FROM predictions")
    except Exception:
        pass
    conn.execute("DELETE FROM tests")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    conn.close()
    print("All test data cleared (batteries preserved).")


def print_summary(created: list):
    if not created:
        print("\nNo new test sessions created.")
        return
    print(f"\nCreated {len(created)} test session(s):\n")
    print(f"  {'ID':<10} {'Profile':<12} {'Ah':>6} {'Wh':>7} "
          f"{'SOH':>6} {'Score':>6} {'Grade':>6} {'AI Label':<15} {'Date'}")
    print("  " + "─" * 85)
    for r in created:
        print(f"  {r['osbams_id']:<10} {r['profile']:<12} "
              f"{r['ah']:>6.2f} {r['wh']:>7.1f} "
              f"{r['soh']:>5.1f}% {r['score']:>6} {r['grade']:>6}   "
              f"{r['ai_label']:<15} {r['date']}")
    print()
    print("Registry now shows:")
    print("  OSB-001  Grade B  — healthy small pack")
    print("  OSB-002  Grade C  — moderate degradation")
    print("  OSB-003  Grade C  — consistent degradation (2 tests)")
    print("  OSB-004  Grade B  — reuse candidate")
    print("  OSB-005  Grade C  — light use only (2 tests, SOH trend visible)")
    print("  OSB-006  Quarantine — no tests (43.5V anomaly)")
    print("  OSB-007  Quarantine — no tests (cut lead)")
    print()
    print("Run: python main.py  — then open the Registry and AI tabs.")


def main():
    parser = argparse.ArgumentParser(description="OSBAMS demo data seeder")
    parser.add_argument("--reset",   action="store_true",
                        help="Delete all test data before seeding")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be created without writing")
    args = parser.parse_args()

    if args.reset and not args.dry_run:
        reset_tests()

    print("Seeding demo test data...")
    created = seed(dry_run=args.dry_run)
    print_summary(created)


if __name__ == "__main__":
    main()
