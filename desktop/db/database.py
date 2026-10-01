"""
database.py — OSBAMS SQLite schema v3

batteries table now includes all fields from the Excel intake spreadsheet:
  manufacturer, max_charge_voltage, series_count, parallel_count,
  initial_ocv_v, ocv_date, bms_led_status, connector_condition,
  safety_status — so the DB is the full source of truth.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "osbams.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _next_osbams_id(conn) -> str:
    row = conn.execute("SELECT MAX(battery_id) FROM batteries").fetchone()
    return f"OSB-{(row[0] or 0) + 1:04d}"


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS batteries (
            -- Internal
            battery_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            osbams_id           TEXT    UNIQUE NOT NULL,
            created_at          TEXT    NOT NULL DEFAULT (datetime('now')),

            -- Source
            intake_date         TEXT    NOT NULL,
            source_type         TEXT    NOT NULL DEFAULT 'unknown'
                                    CHECK(source_type IN
                                    ('fleet','consumer_retail','unknown')),

            -- Identity
            brand               TEXT,
            manufacturer        TEXT,       -- full mfr name / factory
            model               TEXT,
            serial_number       TEXT,
            fleet_id            TEXT,
            barcode             TEXT,
            photo_path          TEXT,

            -- Nameplate electrical specs
            chemistry           TEXT,
            nominal_voltage     REAL,       -- V  e.g. 36.0
            max_charge_voltage  REAL,       -- V  e.g. 42.0
            cutoff_voltage      REAL,       -- V  e.g. 30.0 (optional)
            capacity_rated_ah   REAL,       -- Ah
            energy_rated_wh     REAL,       -- Wh
            cell_config         TEXT,       -- e.g. "10S6P"
            series_count        INTEGER,    -- S
            parallel_count      INTEGER,    -- P

            -- Initial inspection (filled at intake, before any test)
            initial_ocv_v       REAL,       -- measured OCV at intake
            ocv_date            TEXT,       -- YYYY-MM-DD
            physical_score      INTEGER DEFAULT 8,  -- 0-10
            physical_condition  TEXT,       -- housing / shell notes
            bms_led_status      TEXT,       -- LED behavior at rest
            connector_condition TEXT,       -- connector + wiring condition
            safety_status       TEXT        -- OK / Quarantine / Hold / Pending
                                    DEFAULT 'Pending',
            physical_notes      TEXT        -- freeform general notes
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            test_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            battery_id          INTEGER NOT NULL
                                    REFERENCES batteries(battery_id),
            started_at          TEXT    NOT NULL,
            ended_at            TEXT,
            test_type           TEXT    DEFAULT 'discharge',
            notes               TEXT,
            -- Results (filled when test ends)
            capacity_ah         REAL,
            energy_wh           REAL,
            discharge_time_s    REAL,
            min_voltage_mv      INTEGER,
            max_temp_c          REAL,
            soh_percent         REAL,
            reliability_score   INTEGER,
            grade               TEXT,
            recommendation      TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            reading_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id     INTEGER NOT NULL REFERENCES tests(test_id),
            tick_ms     INTEGER NOT NULL,
            voltage_mv  INTEGER NOT NULL,
            current_ma  INTEGER NOT NULL,
            power_mw    INTEGER NOT NULL,
            temp_c10    INTEGER NOT NULL,
            sampled_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── Migration: add new columns to existing DB without wiping data ──
    existing_cols = {r[1] for r in
                     c.execute("PRAGMA table_info(batteries)").fetchall()}
    migrations = [
        ("manufacturer",        "TEXT"),
        ("max_charge_voltage",  "REAL"),
        ("cutoff_voltage",      "REAL"),
        ("cell_config",         "TEXT"),
        ("series_count",        "INTEGER"),
        ("parallel_count",      "INTEGER"),
        ("initial_ocv_v",       "REAL"),
        ("ocv_date",            "TEXT"),
        ("physical_condition",  "TEXT"),
        ("bms_led_status",      "TEXT"),
        ("connector_condition", "TEXT"),
        ("safety_status",       "TEXT DEFAULT 'Pending'"),
    ]
    for col, defn in migrations:
        if col not in existing_cols:
            c.execute(f"ALTER TABLE batteries ADD COLUMN {col} {defn}")

    conn.commit()
    conn.close()
    set_schema_version()
    # Auto-backup on startup (non-blocking, skips if DB is fresh/empty)
    try:
        from db.migrations import backup_db
        import sqlite3 as _sq
        c2 = get_connection()
        n = c2.execute("SELECT COUNT(*) FROM batteries").fetchone()[0]
        c2.close()
        if n > 0:
            backup_db()
    except Exception:
        pass   # backup failure should never block startup


# ── Battery CRUD ──────────────────────────────────────────────────────────────

def create_battery(
    source_type="unknown",
    brand=None, manufacturer=None, model=None,
    serial_number=None, fleet_id=None, barcode=None, photo_path=None,
    chemistry=None,
    nominal_voltage=None, max_charge_voltage=None, cutoff_voltage=None,
    capacity_rated_ah=None, energy_rated_wh=None,
    cell_config=None, series_count=None, parallel_count=None,
    initial_ocv_v=None, ocv_date=None,
    physical_score=8, physical_condition=None,
    bms_led_status=None, connector_condition=None,
    safety_status="Pending", physical_notes=None,
    osbams_id_override=None,          # pass OSB-00X to preserve existing IDs
) -> tuple[int, str]:
    """Insert battery. Returns (battery_id, osbams_id)."""
    conn = get_connection()
    osbams_id = osbams_id_override or _next_osbams_id(conn)
    c = conn.cursor()
    c.execute("""
        INSERT INTO batteries (
            osbams_id, intake_date, source_type,
            brand, manufacturer, model,
            serial_number, fleet_id, barcode, photo_path,
            chemistry, nominal_voltage, max_charge_voltage, cutoff_voltage,
            capacity_rated_ah, energy_rated_wh,
            cell_config, series_count, parallel_count,
            initial_ocv_v, ocv_date,
            physical_score, physical_condition,
            bms_led_status, connector_condition,
            safety_status, physical_notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        osbams_id, datetime.now().isoformat(), source_type,
        brand, manufacturer, model,
        serial_number, fleet_id, barcode, photo_path,
        chemistry, nominal_voltage, max_charge_voltage, cutoff_voltage,
        capacity_rated_ah, energy_rated_wh,
        cell_config, series_count, parallel_count,
        initial_ocv_v, ocv_date,
        physical_score, physical_condition,
        bms_led_status, connector_condition,
        safety_status, physical_notes,
    ))
    battery_id = c.lastrowid
    conn.commit()
    conn.close()
    return battery_id, osbams_id


def update_battery(battery_id: int, **kwargs):
    """Update any battery columns by keyword."""
    if not kwargs:
        return
    conn = get_connection()
    cols = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [battery_id]
    conn.execute(f"UPDATE batteries SET {cols} WHERE battery_id=?", vals)
    conn.commit()
    conn.close()


def update_battery_photo(battery_id: int, photo_path: str):
    update_battery(battery_id, photo_path=photo_path)


def get_all_batteries() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM batteries ORDER BY battery_id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_battery(battery_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM batteries WHERE battery_id=?", (battery_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Test CRUD ─────────────────────────────────────────────────────────────────

def start_test(battery_id: int, test_type: str = "discharge") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO tests (battery_id, started_at, test_type) VALUES (?,?,?)",
        (battery_id, datetime.now().isoformat(), test_type)
    )
    test_id = c.lastrowid
    conn.commit()
    conn.close()
    return test_id


def end_test(test_id, capacity_ah, energy_wh, discharge_time_s,
             max_temp_c, soh_percent, reliability_score,
             grade, recommendation, notes=None, min_voltage_mv=None):
    conn = get_connection()
    conn.execute("""
        UPDATE tests SET
            ended_at=?, capacity_ah=?, energy_wh=?,
            discharge_time_s=?, min_voltage_mv=?, max_temp_c=?,
            soh_percent=?, reliability_score=?,
            grade=?, recommendation=?, notes=?
        WHERE test_id=?
    """, (datetime.now().isoformat(), capacity_ah, energy_wh,
          discharge_time_s, min_voltage_mv, max_temp_c,
          soh_percent, reliability_score,
          grade, recommendation, notes, test_id))
    conn.commit()
    conn.close()


def get_tests_for_battery(battery_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tests WHERE battery_id=? ORDER BY test_id DESC",
        (battery_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Readings ──────────────────────────────────────────────────────────────────

def insert_reading(test_id, tick_ms, voltage_mv, current_ma, power_mw, temp_c10):
    conn = get_connection()
    conn.execute("""
        INSERT INTO readings
            (test_id, tick_ms, voltage_mv, current_ma, power_mw, temp_c10)
        VALUES (?,?,?,?,?,?)
    """, (test_id, tick_ms, voltage_mv, current_ma, power_mw, temp_c10))
    conn.commit()
    conn.close()


def get_readings(test_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM readings WHERE test_id=? ORDER BY tick_ms ASC",
        (test_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print("DB initialized:", DB_PATH)


# ── Features table (added v4) ─────────────────────────────────────────────────
# Computed once per completed test, stored for fast AI training.

def ensure_features_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS features (
            feature_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            test_id             INTEGER NOT NULL UNIQUE
                                    REFERENCES tests(test_id),
            battery_id          INTEGER NOT NULL
                                    REFERENCES batteries(battery_id),
            computed_at         TEXT NOT NULL DEFAULT (datetime('now')),
            -- 8 model features
            capacity_ratio      REAL,
            energy_ratio        REAL,
            temp_rise_c         REAL,
            voltage_sag_v       REAL,
            voltage_spread_v    REAL,
            discharge_rate_c    REAL,
            energy_efficiency   REAL,
            physical_score      REAL,
            -- derived outputs (cached)
            rule_score          INTEGER,
            ai_score            INTEGER,
            consensus_score     INTEGER,
            ai_label            TEXT,
            ai_confidence       REAL,
            recommendation      TEXT,
            second_life_uses    TEXT   -- JSON list
        )
    """)
    conn.commit()
    conn.close()


def upsert_features(test_id: int, battery_id: int, **kwargs):
    """Insert or replace a feature row for a test."""
    ensure_features_table()
    conn = get_connection()
    cols = ["test_id", "battery_id"] + list(kwargs.keys())
    vals = [test_id, battery_id]     + list(kwargs.values())
    placeholders = ",".join("?" * len(cols))
    col_str = ",".join(cols)
    conn.execute(
        f"INSERT OR REPLACE INTO features ({col_str}) VALUES ({placeholders})",
        vals
    )
    conn.commit()
    conn.close()


def get_features_for_test(test_id: int) -> dict | None:
    ensure_features_table()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM features WHERE test_id=?", (test_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_features() -> list:
    """Return all feature rows — used for ML training."""
    ensure_features_table()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM features ORDER BY feature_id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Schema versioning ─────────────────────────────────────────────────────────

SCHEMA_VERSION = "1.2.0"   # increment when schema changes

def get_schema_version() -> dict:
    """Return stored schema/db/migration versions, or defaults if not set."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_info (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        rows = dict(conn.execute("SELECT key, value FROM schema_info").fetchall())
    except Exception:
        rows = {}
    finally:
        conn.close()
    return {
        "schema_version":    rows.get("schema_version",    SCHEMA_VERSION),
        "database_version":  rows.get("database_version",  "1.0"),
        "migration_version": rows.get("migration_version", "1"),
    }


def set_schema_version(schema: str = SCHEMA_VERSION,
                       database: str = "1.0",
                       migration: str = "1"):
    """Write version info into the DB itself."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_info (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    for key, val in [("schema_version", schema),
                     ("database_version", database),
                     ("migration_version", migration)]:
        conn.execute("""
            INSERT INTO schema_info (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                                           updated_at=excluded.updated_at
        """, (key, val))
    conn.commit()
    conn.close()
