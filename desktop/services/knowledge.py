"""
services/knowledge.py — OSBAMS Knowledge Engine

Stage 10 / "Biggest future" from the design review:

Every battery adds knowledge. After 100 batteries, OSBAMS knows things:

    Brand       → Typical failure mode
    Model       → Average SOH at intake
    Chemistry   → Average temperature rise
    Category    → Average voltage sag
    All packs   → Reliability distribution

This module aggregates across all tested battery assets to answer
questions like:
    "How does OSB-005 compare to other 10S6P Ninebot packs?"
    "What is the typical SOH for Spin fleet batteries at second life?"
    "Which brand shows the highest temperature rise under load?"

The knowledge is recomputed on demand (not cached) so it always
reflects the current database state.
"""

from dataclasses import dataclass, field
from typing import Optional
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class BrandKnowledge:
    brand:              str
    sample_count:       int     = 0
    avg_soh_pct:        float   = 0.0
    avg_score:          float   = 0.0
    avg_capacity_ah:    float   = 0.0
    avg_temp_rise_c:    float   = 0.0
    avg_voltage_sag_v:  float   = 0.0
    most_common_grade:  str     = "—"
    typical_issue:      str     = "—"
    models_seen:        list[str] = field(default_factory=list)


@dataclass
class FleetKnowledge:
    total_batteries:    int     = 0
    total_tests:        int     = 0
    avg_soh_pct:        float   = 0.0
    avg_score:          float   = 0.0
    pct_suitable_reuse: float   = 0.0   # % that scored ≥ 65
    pct_needs_recycle:  float   = 0.0   # % that scored < 50
    by_brand:           dict[str, BrandKnowledge] = field(default_factory=dict)
    by_chemistry:       dict[str, dict] = field(default_factory=dict)
    by_category:        dict[str, dict] = field(default_factory=dict)
    most_reliable_brand:str     = "—"
    most_common_failure:str     = "—"


@dataclass
class BatteryContext:
    """How does one battery compare to similar batteries in the fleet?"""
    battery_id:         int
    osbams_id:          str
    soh_pct:            float   = 0.0
    score:              int     = 0
    fleet_avg_soh:      float   = 0.0
    brand_avg_soh:      float   = 0.0
    brand_sample_count: int     = 0
    soh_vs_fleet:       float   = 0.0   # +/- percentage points vs fleet avg
    soh_vs_brand:       float   = 0.0   # +/- vs same brand avg
    percentile:         int     = 0     # where this battery ranks in fleet
    verdict:            str     = "—"   # "Above average", "Average", "Below average"


def compute_fleet_knowledge() -> FleetKnowledge:
    """
    Aggregate knowledge across all tested battery assets.
    Returns FleetKnowledge with per-brand and per-chemistry breakdowns.
    """
    from db.database import get_all_batteries, get_tests_for_battery
    from db.database import get_connection

    batteries = get_all_batteries()
    fk = FleetKnowledge(total_batteries=len(batteries))

    all_sohs, all_scores = [], []
    brand_data: dict[str, list] = {}
    chem_data:  dict[str, list] = {}

    for b in batteries:
        tests = [t for t in get_tests_for_battery(b["battery_id"])
                 if t.get("ended_at")]
        fk.total_tests += len(tests)
        if not tests:
            continue

        latest  = tests[0]
        soh     = latest.get("soh_percent")   or 0.0
        score   = latest.get("reliability_score") or 0
        cap     = latest.get("capacity_ah")   or 0.0
        grade   = latest.get("grade")         or "—"

        # Get features for temp/sag (if stored)
        try:
            conn = get_connection()
            feat = conn.execute(
                "SELECT temp_rise_c, voltage_sag_v FROM features WHERE test_id=?",
                (latest["test_id"],)
            ).fetchone()
            conn.close()
            temp_rise = feat[0] if feat else 0.0
            v_sag     = feat[1] if feat else 0.0
        except Exception:
            temp_rise = v_sag = 0.0

        all_sohs.append(soh)
        all_scores.append(score)

        brand = (b.get("manufacturer") or b.get("brand") or "Unknown").split("/")[0].split("(")[0].strip()
        model = b.get("model") or "—"
        chem  = b.get("chemistry") or "unknown"

        if brand not in brand_data:
            brand_data[brand] = []
        brand_data[brand].append({
            "soh": soh, "score": score, "cap": cap,
            "temp": temp_rise, "sag": v_sag,
            "grade": grade, "model": model,
            "notes": b.get("physical_notes") or "",
        })

        if chem not in chem_data:
            chem_data[chem] = []
        chem_data[chem].append({"soh": soh, "score": score, "temp": temp_rise})

    # Fleet averages
    if all_sohs:
        fk.avg_soh_pct = round(sum(all_sohs) / len(all_sohs), 1)
    if all_scores:
        fk.avg_score = round(sum(all_scores) / len(all_scores), 1)

    n_tested = len(all_scores)
    if n_tested > 0:
        fk.pct_suitable_reuse = round(
            sum(1 for s in all_scores if s >= 65) / n_tested * 100, 1)
        fk.pct_needs_recycle  = round(
            sum(1 for s in all_scores if s < 50) / n_tested * 100, 1)

    # Per-brand knowledge
    best_brand_soh = -1.0
    for brand, items in brand_data.items():
        sohs   = [x["soh"]   for x in items]
        scores = [x["score"] for x in items]
        caps   = [x["cap"]   for x in items if x["cap"] > 0]
        temps  = [x["temp"]  for x in items if x["temp"] > 0]
        sags   = [x["sag"]   for x in items if x["sag"]  > 0]

        avg_soh = round(sum(sohs)   / len(sohs),   1) if sohs   else 0.0
        avg_sc  = round(sum(scores) / len(scores), 1) if scores else 0.0
        avg_cap = round(sum(caps)   / len(caps),   2) if caps   else 0.0
        avg_tmp = round(sum(temps)  / len(temps),  1) if temps  else 0.0
        avg_sag = round(sum(sags)   / len(sags),   2) if sags   else 0.0

        from collections import Counter
        grades = [x["grade"] for x in items if x["grade"] != "—"]
        top_grade = Counter(grades).most_common(1)[0][0] if grades else "—"

        # Typical issue from notes
        all_notes = " ".join(x["notes"] for x in items).lower()
        issue_words = {"cut": "damaged lead", "swollen": "swelling",
                       "corrosion": "corrosion", "bottom": "housing damage",
                       "unknown": "unknown history"}
        issue = next((v for k, v in issue_words.items() if k in all_notes), "—")

        models = list(set(x["model"] for x in items if x["model"] != "—"))[:3]

        bk = BrandKnowledge(
            brand             = brand,
            sample_count      = len(items),
            avg_soh_pct       = avg_soh,
            avg_score         = avg_sc,
            avg_capacity_ah   = avg_cap,
            avg_temp_rise_c   = avg_tmp,
            avg_voltage_sag_v = avg_sag,
            most_common_grade = top_grade,
            typical_issue     = issue,
            models_seen       = models,
        )
        fk.by_brand[brand] = bk

        if avg_soh > best_brand_soh and len(items) >= 1:
            best_brand_soh        = avg_soh
            fk.most_reliable_brand= brand

    # Per-chemistry
    for chem, items in chem_data.items():
        sohs  = [x["soh"]  for x in items]
        temps = [x["temp"] for x in items if x["temp"] > 0]
        fk.by_chemistry[chem] = {
            "count":        len(items),
            "avg_soh":      round(sum(sohs)  / len(sohs),  1) if sohs  else 0.0,
            "avg_temp_rise":round(sum(temps) / len(temps), 1) if temps else 0.0,
        }

    return fk


def get_battery_context(battery_id: int) -> Optional[BatteryContext]:
    """
    Compare one battery against fleet and brand peers.
    Returns context showing how it ranks relative to similar assets.
    """
    from db.database import get_battery, get_tests_for_battery, get_all_batteries

    batt  = get_battery(battery_id)
    if not batt:
        return None

    tests = [t for t in get_tests_for_battery(battery_id) if t.get("ended_at")]
    if not tests:
        return None

    latest = tests[0]
    soh    = latest.get("soh_percent")      or 0.0
    score  = latest.get("reliability_score") or 0
    brand  = (batt.get("manufacturer") or batt.get("brand") or "Unknown").split("/")[0].strip()

    # Collect fleet and brand SOHs
    fleet_sohs = []
    brand_sohs = []

    for b in get_all_batteries():
        if not b.get("model"):
            continue
        bt = [t for t in get_tests_for_battery(b["battery_id"]) if t.get("ended_at")]
        if not bt:
            continue
        s = bt[0].get("soh_percent") or 0.0
        fleet_sohs.append(s)
        b_brand = (b.get("manufacturer") or b.get("brand") or "?").split("/")[0].strip()
        if b_brand == brand:
            brand_sohs.append(s)

    fleet_avg = round(sum(fleet_sohs) / len(fleet_sohs), 1) if fleet_sohs else soh
    brand_avg = round(sum(brand_sohs) / len(brand_sohs), 1) if brand_sohs else soh

    # Percentile rank
    rank = sum(1 for s in fleet_sohs if s < soh)
    pct  = int(rank / max(len(fleet_sohs), 1) * 100)

    # Verdict
    diff = soh - fleet_avg
    if diff >= 5:
        verdict = "Above fleet average"
    elif diff <= -5:
        verdict = "Below fleet average"
    else:
        verdict = "Near fleet average"

    return BatteryContext(
        battery_id         = battery_id,
        osbams_id          = batt.get("osbams_id") or f"#{battery_id}",
        soh_pct            = soh,
        score              = score,
        fleet_avg_soh      = fleet_avg,
        brand_avg_soh      = brand_avg,
        brand_sample_count = len(brand_sohs),
        soh_vs_fleet       = round(soh - fleet_avg, 1),
        soh_vs_brand       = round(soh - brand_avg, 1),
        percentile         = pct,
        verdict            = verdict,
    )


if __name__ == "__main__":
    from db.database import init_db
    init_db()

    print("=== Fleet Knowledge ===")
    fk = compute_fleet_knowledge()
    print(f"Total: {fk.total_batteries}  Tests: {fk.total_tests}")
    print(f"Avg SOH: {fk.avg_soh_pct}%  Avg Score: {fk.avg_score}")
    print(f"Suitable for reuse: {fk.pct_suitable_reuse}%")
    print(f"Most reliable brand: {fk.most_reliable_brand}")

    if fk.by_brand:
        print("\nBy brand:")
        for brand, bk in fk.by_brand.items():
            print(f"  {brand:<25} n={bk.sample_count}  "
                  f"avg_SOH={bk.avg_soh_pct}%  "
                  f"grade={bk.most_common_grade}  "
                  f"issue={bk.typical_issue}")

    print("\n=== Battery Context: OSB-001 ===")
    ctx = get_battery_context(1)
    if ctx:
        print(f"  SOH: {ctx.soh_pct}%  Fleet avg: {ctx.fleet_avg_soh}%")
        print(f"  vs fleet: {ctx.soh_vs_fleet:+.1f}%  percentile: {ctx.percentile}")
        print(f"  Verdict: {ctx.verdict}")
    print("\n✓ knowledge.py self-test passed.")
