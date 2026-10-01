#!/usr/bin/env python3
"""
import_spreadsheet.py — One-time import of OSBAMS_Battery_Database.xlsx
                         into the SQLite database.

Usage:
    python import_spreadsheet.py                          # looks for xlsx next to this file
    python import_spreadsheet.py path/to/file.xlsx       # explicit path

The script:
  1. Reads "Battery Inventory" sheet, skipping the two header rows.
  2. Maps every column to the correct DB field.
  3. Preserves the OSB-001...OSB-007 IDs exactly.
  4. Skips rows where OSBAMS ID is blank (empty intake slots).
  5. Is SAFE to re-run — it checks for existing OSB IDs and skips
     duplicates rather than inserting twice.
  6. Prints a clear summary of what was inserted / skipped.
"""

import sys
import os
import sqlite3

# ── Locate files ──────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_XLSX = os.path.join(SCRIPT_DIR, "..", "OSBAMS_Battery_Database.xlsx")
XLSX_PATH   = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_XLSX

if not os.path.exists(XLSX_PATH):
    print(f"ERROR: Cannot find spreadsheet at: {XLSX_PATH}")
    print("Usage: python import_spreadsheet.py [path/to/OSBAMS_Battery_Database.xlsx]")
    sys.exit(1)

sys.path.insert(0, SCRIPT_DIR)
from db.database import init_db, create_battery, get_connection

# ── Helpers ───────────────────────────────────────────────────────────

def clean(val):
    """Return None for empty/NaN/placeholder values, else stripped string."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "nan", "NaN", "None", "Unknown", "unknown",
             "Not measured", "—", "-", "N/A", "n/a"):
        return None
    return s


def to_float(val):
    """Parse a float from a cell, ignoring text like '43.5 — VERIFY'."""
    s = clean(val)
    if s is None:
        return None
    # Take only the numeric prefix before any space/dash
    import re
    m = re.match(r"^-?\d+(\.\d+)?", s)
    return float(m.group()) if m else None


def to_int(val):
    f = to_float(val)
    return int(f) if f is not None else None


def parse_source(ocv_str, physical_str, bms_str, connector_str, notes_str):
    """Infer source_type from available text clues."""
    combined = " ".join(filter(None, [physical_str, bms_str, notes_str, connector_str])).lower()
    if any(w in combined for w in ["spin", "lime", "bird", "fleet"]):
        return "fleet"
    if any(w in combined for w in ["walmart", "gotrax", "hiboy", "razor", "retail"]):
        return "consumer_retail"
    return "fleet"   # Ninebot scooter packs are fleet by default


def parse_safety(notes_str, ocv_str):
    """Derive safety_status from notes and OCV fields."""
    n = (notes_str or "").lower()
    o = str(ocv_str or "").lower()
    if "quarantine" in n or "do not connect" in n or "cut" in n:
        return "Quarantine"
    if "verify" in n or "verify" in o or "recheck" in n:
        return "Hold - Verify"
    if "bottom" in n or "open" in n or "inspect" in n:
        return "Pending - Inspect"
    if "ok" in n or "intact" in n:
        return "OK"
    return "Pending"


# ── Read spreadsheet ──────────────────────────────────────────────────
try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl not installed. Run: pip install openpyxl")
    sys.exit(1)

print(f"\nOSBAMS Spreadsheet → SQLite Importer")
print(f"Source : {XLSX_PATH}")
print(f"Target : {os.path.join(SCRIPT_DIR, 'db', 'osbams.db')}")
print("-" * 60)

wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)

if "Battery Inventory" not in wb.sheetnames:
    print("ERROR: Sheet 'Battery Inventory' not found in workbook.")
    print(f"Available sheets: {wb.sheetnames}")
    sys.exit(1)

ws = wb["Battery Inventory"]

# Column mapping — row 3 is the header row (rows 1-2 are group labels)
# A=OSBAMS ID, B=OEM Serial, C=Model, D=Manufacturer, E=Chemistry,
# F=Nominal V, G=Max Charge V, H=Rated Ah, I=Rated Wh,
# J=Cell Config, K=Series, L=Parallel,
# M=Initial OCV, N=OCV Date, O=Physical Condition,
# P=BMS/LED Status, Q=Connector/Wiring, R=Safety/Notes

COL = {
    "osbams_id":           1,   # A
    "serial_number":       2,   # B
    "model":               3,   # C
    "manufacturer":        4,   # D
    "chemistry":           5,   # E
    "nominal_voltage":     6,   # F
    "max_charge_voltage":  7,   # G
    "capacity_rated_ah":   8,   # H
    "energy_rated_wh":     9,   # I
    "cell_config":        10,   # J
    "series_count":       11,   # K
    "parallel_count":     12,   # L
    "initial_ocv_v":      13,   # M
    "ocv_date":           14,   # N
    "physical_condition": 15,   # O
    "bms_led_status":     16,   # P
    "connector_condition":17,   # Q
    "physical_notes":     18,   # R
}

def cell(row, col_num):
    return row[col_num - 1]  # openpyxl row is 0-indexed tuple

# ── Init DB ───────────────────────────────────────────────────────────
init_db()
conn = get_connection()
existing_ids = {r[0] for r in
                conn.execute("SELECT osbams_id FROM batteries").fetchall()}
conn.close()

# ── Process rows (data starts at row 4, rows 1-3 are headers) ─────────
inserted = []
skipped  = []
errors   = []

for row_num, row in enumerate(ws.iter_rows(min_row=4, values_only=True), start=4):
    osbams_id = clean(row[COL["osbams_id"] - 1])
    if not osbams_id or not osbams_id.startswith("OSB-"):
        continue   # blank intake slot or non-data row

    if osbams_id in existing_ids:
        skipped.append(f"  SKIP  {osbams_id} — already in database")
        continue

    # Extract raw values
    serial    = clean(row[COL["serial_number"] - 1])
    model     = clean(row[COL["model"] - 1])
    mfr       = clean(row[COL["manufacturer"] - 1])
    chem      = clean(row[COL["chemistry"] - 1])
    nom_v     = to_float(row[COL["nominal_voltage"] - 1])
    max_v     = to_float(row[COL["max_charge_voltage"] - 1])
    rated_ah  = to_float(row[COL["capacity_rated_ah"] - 1])
    rated_wh  = to_float(row[COL["energy_rated_wh"] - 1])
    cell_cfg  = clean(row[COL["cell_config"] - 1])
    # Strip ? from cell config (10S6P? → 10S6P)
    if cell_cfg and cell_cfg.endswith("?"):
        cell_cfg = cell_cfg[:-1]
    series    = to_int(row[COL["series_count"] - 1])
    parallel_raw = clean(row[COL["parallel_count"] - 1])
    parallel  = to_int(parallel_raw) if parallel_raw and parallel_raw != "?" else None

    ocv_raw   = row[COL["initial_ocv_v"] - 1]
    ocv_v     = to_float(ocv_raw)     # None if "43.5 — VERIFY" or "Not measured"
    ocv_date  = clean(row[COL["ocv_date"] - 1])

    phys_cond = clean(row[COL["physical_condition"] - 1])
    bms       = clean(row[COL["bms_led_status"] - 1])
    connector = clean(row[COL["connector_condition"] - 1])
    notes     = clean(row[COL["physical_notes"] - 1])

    # Infer fields not directly in spreadsheet
    source    = parse_source(str(ocv_raw), phys_cond, bms, connector, notes)
    safety    = parse_safety(notes, ocv_raw)

    # Brand is first word of manufacturer
    brand = mfr.split("/")[0].split("(")[0].strip() if mfr else None

    # Physical score: default 8, lower if safety issue
    phys_score = 5 if safety in ("Quarantine", "Hold - Verify") else 8
    if phys_cond and "open" in phys_cond.lower():
        phys_score = 6

    try:
        battery_id, assigned_id = create_battery(
            osbams_id_override   = osbams_id,
            source_type          = source,
            brand                = brand,
            manufacturer         = mfr,
            model                = model,
            serial_number        = serial,
            chemistry            = chem,
            nominal_voltage      = nom_v,
            max_charge_voltage   = max_v,
            capacity_rated_ah    = rated_ah,
            energy_rated_wh      = rated_wh,
            cell_config          = cell_cfg,
            series_count         = series,
            parallel_count       = parallel,
            initial_ocv_v        = ocv_v,
            ocv_date             = ocv_date,
            physical_score       = phys_score,
            physical_condition   = phys_cond,
            bms_led_status       = bms,
            connector_condition  = connector,
            safety_status        = safety,
            physical_notes       = notes,
        )
        inserted.append(
            f"  ✓ {assigned_id}  {(model or '?'):20s}  "
            f"OCV={ocv_v or '?':>6}V  Safety={safety}"
        )
        existing_ids.add(osbams_id)
    except Exception as e:
        errors.append(f"  ERROR row {row_num} ({osbams_id}): {e}")

# ── Summary ───────────────────────────────────────────────────────────
print(f"\nInserted ({len(inserted)}):")
for line in inserted: print(line)

if skipped:
    print(f"\nSkipped — already in DB ({len(skipped)}):")
    for line in skipped: print(line)

if errors:
    print(f"\nErrors ({len(errors)}):")
    for line in errors: print(line)

print("\n" + "=" * 60)
conn = get_connection()
total = conn.execute("SELECT COUNT(*) FROM batteries").fetchone()[0]
conn.close()
print(f"Database now contains {total} battery record(s).")
print(f"DB path: {os.path.join(SCRIPT_DIR, 'db', 'osbams.db')}")
print()
print("Next steps:")
print("  1. Run  python main.py  — all 7 packs appear in Registry tab")
print("  2. OSB-006 and OSB-007 show Safety=Quarantine/Hold in the GUI")
print("  3. Add new batteries via the Battery Registration tab (they get OSB-008+)")
print("  4. Use spreadsheet as intake paper form only — SQLite is now the source of truth")
