"""
db/migrations.py — OSBAMS database schema migrations

Run this once to upgrade an existing osbams.db to the full v6 schema.
Safe to re-run: uses ADD COLUMN IF NOT EXISTS pattern.

New columns added to `tests` (from recommendation screenshot):
  operator, ambient_temp_c, load_mode, current_setpoint_a,
  power_setpoint_w, cutoff_voltage_v, stop_reason,
  initial_ocv_v, resting_voltage_after_v,
  average_current_a, average_power_w, max_current_a,
  voltage_sag_mv, internal_resistance_mohm

New tables:
  predictions  — stores every AI prediction (not overwritten)
  model_versions — tracks ML model history
  audit_log    — records significant events
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db.database import get_connection
from datetime import datetime


def _add_col(c, table: str, col: str, defn: str):
    """Add column if it doesn't already exist."""
    existing = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
    if col not in existing:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
        return True
    return False


def migrate():
    conn = get_connection()
    c    = conn.cursor()
    added = []

    # ── Expand tests table ────────────────────────────────────────────
    test_additions = [
        ("operator",                "TEXT"),
        ("ambient_temp_c",          "REAL"),
        ("load_mode",               "TEXT DEFAULT 'CC'"),
        ("current_setpoint_a",      "REAL"),
        ("power_setpoint_w",        "REAL"),
        ("cutoff_voltage_v",        "REAL"),
        ("stop_reason",             "TEXT"),   # cutoff / safety / manual / timeout
        ("initial_ocv_v",           "REAL"),   # OCV before test started
        ("resting_voltage_after_v", "REAL"),   # OCV after rest post-discharge
        ("average_current_a",       "REAL"),
        ("average_power_w",         "REAL"),
        ("max_current_a",           "REAL"),
        ("voltage_sag_mv",          "INTEGER"),
        ("internal_resistance_mohm","REAL"),   # estimated from V sag / I
    ]
    for col, defn in test_additions:
        if _add_col(c, "tests", col, defn):
            added.append(f"tests.{col}")

    # ── Expand batteries table ────────────────────────────────────────
    batt_additions = [
        ("archived",         "INTEGER DEFAULT 0"),   # 0=active, 1=archived
        ("cutoff_voltage",   "REAL"),
        ("acquisition_date", "TEXT"),
        ("acquisition_location", "TEXT"),
        ("pack_mass_kg",     "REAL"),
        ("manufacture_date", "TEXT"),
    ]
    for col, defn in batt_additions:
        if _add_col(c, "batteries", col, defn):
            added.append(f"batteries.{col}")

    # ── predictions table (stores every AI result permanently) ────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id             INTEGER NOT NULL REFERENCES tests(test_id),
            battery_id          INTEGER NOT NULL REFERENCES batteries(battery_id),
            created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            model_version       TEXT    DEFAULT 'rule-v1',
            health_label        TEXT,
            confidence          REAL,
            predicted_soh_pct   REAL,
            predicted_capacity_ah REAL,
            predicted_energy_wh   REAL,
            rule_score          INTEGER,
            ml_score            INTEGER,
            final_score         INTEGER,
            grade               TEXT,
            recommendation      TEXT,
            second_life_json    TEXT,   -- JSON list of {label, approved}
            reasons_json        TEXT,   -- JSON list of reason strings
            importances_json    TEXT    -- JSON dict of feature importances
        )
    """)

    # ── model_versions table ──────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS model_versions (
            version_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            version_name        TEXT    NOT NULL,   -- e.g. rf_v001
            trained_at          TEXT    NOT NULL DEFAULT (datetime('now')),
            n_batteries         INTEGER,
            n_tests             INTEGER,
            n_features          INTEGER,
            feature_list        TEXT,   -- JSON list
            hyperparams         TEXT,   -- JSON dict
            cv_accuracy         REAL,
            model_file_path     TEXT,
            notes               TEXT
        )
    """)

    # ── audit_log table ───────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at   TEXT    NOT NULL DEFAULT (datetime('now')),
            event_type  TEXT    NOT NULL,
            battery_id  INTEGER,
            test_id     INTEGER,
            user        TEXT    DEFAULT 'operator',
            description TEXT    NOT NULL,
            old_value   TEXT,
            new_value   TEXT
        )
    """)

    # ── Log migration itself ──────────────────────────────────────────
    if added:
        c.execute("""
            INSERT INTO audit_log (event_type, description)
            VALUES ('migration', ?)
        """, (f"Added columns: {', '.join(added)}",))

    conn.commit()
    conn.close()
    return added


def log_event(event_type: str, description: str,
              battery_id: int = None, test_id: int = None,
              old_value: str = None, new_value: str = None):
    """Write one audit log entry."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO audit_log
            (event_type, battery_id, test_id, description, old_value, new_value)
        VALUES (?,?,?,?,?,?)
    """, (event_type, battery_id, test_id, description, old_value, new_value))
    conn.commit()
    conn.close()


def save_prediction(test_id: int, battery_id: int, result,
                    model_version: str = "rule-v1"):
    """Persist an AI prediction to the predictions table."""
    import json
    conn = get_connection()
    conn.execute("""
        INSERT INTO predictions
            (test_id, battery_id, model_version,
             health_label, confidence,
             predicted_soh_pct, predicted_capacity_ah, predicted_energy_wh,
             rule_score, ml_score, final_score, grade, recommendation,
             second_life_json, reasons_json, importances_json)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        test_id, battery_id, model_version,
        result.label, result.confidence,
        None, None, None,
        result.rule_score, result.ai_score, result.final_score,
        result.grade, result.label,
        json.dumps([{"label": u.label, "approved": u.approved}
                    for u in result.second_life]),
        json.dumps(result.reasons),
        json.dumps(result.importances),
    ))
    conn.commit()
    conn.close()


def save_model_version(version_name: str, n_batteries: int, n_tests: int,
                       cv_accuracy: float, model_file_path: str,
                       feature_list: list, hyperparams: dict):
    """Record a trained model version."""
    import json
    conn = get_connection()
    conn.execute("""
        INSERT INTO model_versions
            (version_name, n_batteries, n_tests, n_features,
             feature_list, hyperparams, cv_accuracy, model_file_path)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        version_name, n_batteries, n_tests, len(feature_list),
        json.dumps(feature_list), json.dumps(hyperparams),
        cv_accuracy, model_file_path,
    ))
    conn.commit()
    conn.close()


def backup_db():
    """Copy osbams.db to db/backups/osbams_backup_DATETIME.db"""
    import shutil
    from config import DB_PATH, BACKUPS_DIR
    ts   = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = os.path.join(BACKUPS_DIR, f"osbams_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    log_event("backup", f"Database backed up to {dest}")
    return dest


if __name__ == "__main__":
    print("Running OSBAMS database migration...")
    added = migrate()
    if added:
        print(f"Added {len(added)} column(s):")
        for col in added:
            print(f"  + {col}")
    else:
        print("Schema already up to date.")

    print("\nBacking up database...")
    dest = backup_db()
    print(f"Backup: {dest}")
    print("Migration complete.")
