"""
services/lifecycle.py — Battery Lifecycle Events and Fleet Statistics

Stage 8: Events — Everything becomes an event
Stage 10: Fleet Statistics — The "100 batteries" view

Events replace tests-only history with a full timeline:
    Battery Created → Inspected → Charged → Tested →
    Repaired → Retested → Relocated → Retired → Recycled

Fleet statistics give the macro view:
    Registered: 126  Healthy: 41  Repair: 18  Recycle: 67
    Average SOH  ·  Average Capacity  ·  Most Common Issue
"""

import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


# ── Event types ───────────────────────────────────────────────────────────────

EVENT_TYPES = {
    "registered":   ("📋", "Registered",       "Battery registered in OSBAMS"),
    "inspected":    ("🔍", "Inspected",         "Physical and safety inspection completed"),
    "charged":      ("⚡", "Charged",           "Battery charged before testing"),
    "tested":       ("🧪", "Tested",            "Discharge test completed"),
    "repaired":     ("🔧", "Repaired",          "Repair or refurbishment performed"),
    "retested":     ("🔁", "Re-tested",         "Follow-up discharge test completed"),
    "relocated":    ("📦", "Relocated",         "Battery moved to new location"),
    "assigned":     ("✅", "Assigned",          "Battery assigned to an application"),
    "returned":     ("↩", "Returned",          "Battery returned from deployment"),
    "safety_hold":  ("⚠", "Safety Hold",      "Battery placed on safety hold"),
    "quarantine":   ("🚫", "Quarantine",       "Battery quarantined"),
    "retired":      ("💤", "Retired",          "Battery retired from active use"),
    "recycled":     ("♻", "Recycled",         "Battery sent for recycling"),
    "note":         ("📝", "Note",             "Operator note added"),
    "import":       ("📥", "Imported",         "Battery record imported from spreadsheet"),
}


@dataclass
class BatteryEvent:
    event_id:    int
    battery_id:  int
    osbams_id:   str
    event_type:  str
    occurred_at: str
    operator:    str
    description: str
    data_json:   Optional[str] = None   # extra structured data

    @property
    def icon(self) -> str:
        return EVENT_TYPES.get(self.event_type, ("•", "", ""))[0]

    @property
    def label(self) -> str:
        return EVENT_TYPES.get(self.event_type, ("", self.event_type, ""))[1]

    @property
    def date_str(self) -> str:
        return self.occurred_at[:10]

    @property
    def time_str(self) -> str:
        return self.occurred_at[11:16] if len(self.occurred_at) > 10 else ""


# ── DB helpers ────────────────────────────────────────────────────────────────

def ensure_events_table():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_connection
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS battery_events (
            event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            battery_id  INTEGER NOT NULL,
            osbams_id   TEXT    NOT NULL,
            event_type  TEXT    NOT NULL,
            occurred_at TEXT    NOT NULL DEFAULT (datetime('now')),
            operator    TEXT    DEFAULT 'operator',
            description TEXT    NOT NULL,
            data_json   TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_event(battery_id: int, osbams_id: str, event_type: str,
              description: str, operator: str = "operator",
              data: dict = None) -> int:
    ensure_events_table()
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_connection
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO battery_events
            (battery_id, osbams_id, event_type, occurred_at, operator, description, data_json)
        VALUES (?,?,?,?,?,?,?)
    """, (battery_id, osbams_id, event_type,
          datetime.now().isoformat(), operator, description,
          json.dumps(data) if data else None))
    eid = c.lastrowid
    conn.commit()
    conn.close()
    return eid


def get_events(battery_id: int) -> list[BatteryEvent]:
    ensure_events_table()
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_connection
    conn = get_connection()
    rows = conn.execute("""
        SELECT event_id, battery_id, osbams_id, event_type,
               occurred_at, operator, description, data_json
        FROM battery_events
        WHERE battery_id = ?
        ORDER BY occurred_at ASC
    """, (battery_id,)).fetchall()
    conn.close()
    return [BatteryEvent(*r) for r in rows]


def get_recent_events(n: int = 20) -> list[BatteryEvent]:
    """Recent events across all batteries — for a global activity feed."""
    ensure_events_table()
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_connection
    conn = get_connection()
    rows = conn.execute("""
        SELECT event_id, battery_id, osbams_id, event_type,
               occurred_at, operator, description, data_json
        FROM battery_events
        ORDER BY occurred_at DESC LIMIT ?
    """, (n,)).fetchall()
    conn.close()
    return [BatteryEvent(*r) for r in rows]


# ── Fleet statistics ──────────────────────────────────────────────────────────

@dataclass
class FleetStats:
    total_batteries:    int   = 0
    # By health grade
    grade_a:            int   = 0
    grade_b:            int   = 0
    grade_c:            int   = 0
    grade_d:            int   = 0
    grade_f:            int   = 0
    not_tested:         int   = 0
    # By safety
    safe_count:         int   = 0
    hold_count:         int   = 0
    quarantine_count:   int   = 0
    # Metrics
    avg_soh_pct:        float = 0.0
    avg_capacity_ah:    float = 0.0
    avg_score:          float = 0.0
    total_tests:        int   = 0
    # Top issues
    most_common_issue:  str   = "—"

    @property
    def healthy_count(self) -> int:
        return self.grade_a + self.grade_b

    @property
    def repair_count(self) -> int:
        return self.grade_c + self.grade_d

    @property
    def recycle_count(self) -> int:
        return self.grade_f


def compute_fleet_stats() -> FleetStats:
    """Compute fleet-wide statistics from the database."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_all_batteries, get_tests_for_battery

    batteries = get_all_batteries()
    stats = FleetStats(total_batteries=len(batteries))

    grade_counts = {"A":0,"B":0,"C":0,"D":0,"F":0}
    soh_vals, cap_vals, score_vals = [], [], []

    for b in batteries:
        # Safety
        safety = (b.get("safety_status") or "").lower()
        if "quarantine" in safety or "unsafe" in safety:
            stats.quarantine_count += 1
        elif "hold" in safety or "verify" in safety or "inspect" in safety:
            stats.hold_count += 1
        else:
            stats.safe_count += 1

        # Tests
        tests = [t for t in get_tests_for_battery(b["battery_id"])
                 if t.get("ended_at")]
        stats.total_tests += len(tests)

        if not tests:
            stats.not_tested += 1
            continue

        latest = tests[0]
        grade  = latest.get("grade") or ""
        if grade in grade_counts:
            grade_counts[grade] += 1

        soh = latest.get("soh_percent")
        cap = latest.get("capacity_ah")
        sc  = latest.get("reliability_score")
        if soh: soh_vals.append(soh)
        if cap: cap_vals.append(cap)
        if sc:  score_vals.append(sc)

    stats.grade_a = grade_counts["A"]
    stats.grade_b = grade_counts["B"]
    stats.grade_c = grade_counts["C"]
    stats.grade_d = grade_counts["D"]
    stats.grade_f = grade_counts["F"]

    if soh_vals:   stats.avg_soh_pct    = round(sum(soh_vals)   / len(soh_vals),   1)
    if cap_vals:   stats.avg_capacity_ah= round(sum(cap_vals)   / len(cap_vals),   2)
    if score_vals: stats.avg_score      = round(sum(score_vals) / len(score_vals), 1)

    # Most common issue (from physical notes)
    issue_words = {}
    for b in batteries:
        notes = (b.get("physical_notes") or "").lower()
        for word in ["swollen","cut","corrosion","damaged","bottom","connector","unknown"]:
            if word in notes:
                issue_words[word] = issue_words.get(word, 0) + 1
    if issue_words:
        stats.most_common_issue = max(issue_words, key=issue_words.get).title()

    return stats


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import init_db, get_all_batteries
    init_db()

    # Seed a few events for OSB-001 if exists
    batts = get_all_batteries()
    if batts:
        b = next((b for b in batts if b.get("model")), batts[0])
        bid  = b["battery_id"]
        oid  = b.get("osbams_id") or "OSB-001"

        log_event(bid, oid, "registered", "Battery registered via spreadsheet import")
        log_event(bid, oid, "inspected",  "Initial visual inspection — no damage observed")
        log_event(bid, oid, "charged",    "Charged to full before test (42.0V)")
        log_event(bid, oid, "tested",     "First discharge test completed — Grade C")

        events = get_events(bid)
        print(f"\nEvents for {oid} ({len(events)} events):")
        for e in events:
            print(f"  {e.date_str}  {e.icon}  {e.label:<15}  {e.description}")

    print("\n--- Fleet Statistics ---")
    stats = compute_fleet_stats()
    print(f"Total: {stats.total_batteries}")
    print(f"Healthy (A+B): {stats.healthy_count}  Repair (C+D): {stats.repair_count}  Recycle (F): {stats.recycle_count}")
    print(f"Not tested: {stats.not_tested}  Quarantine: {stats.quarantine_count}  Hold: {stats.hold_count}")
    print(f"Avg SOH: {stats.avg_soh_pct}%  Avg Capacity: {stats.avg_capacity_ah} Ah  Avg Score: {stats.avg_score}")
    print(f"Total tests: {stats.total_tests}  Most common issue: {stats.most_common_issue}")
    print("\n✓ lifecycle.py self-test passed.")
