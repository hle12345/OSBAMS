"""
pdf_report.py — OSBAMS Battery Assessment PDF Report Generator

Generates a professional single-page PDF report for each completed test.
Output matches the ChatGPT example:

    Battery: OSB-0007
    Measured Capacity: 12.4 Ah
    Measured Energy:   446 Wh
    SOH:               81%
    Grade:             B
    Recommendation:    Reuse with monitoring

    Second-Life Uses:
      ✓ Campus / low-speed scooter
      ✓ Portable solar storage
      ✗ High-power scooter ...

    Why: [AI explanation bullets]

Uses reportlab — pure Python, no LaTeX, no external tools.
"""

import os
import io
from datetime import datetime
from typing import Optional

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ── Colors ────────────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1F3864")
BLUE   = colors.HexColor("#2E75B6")
GREEN  = colors.HexColor("#16a34a")
AMBER  = colors.HexColor("#d97706")
RED    = colors.HexColor("#dc2626")
GREY   = colors.HexColor("#6b7280")
LGREY  = colors.HexColor("#f3f4f6")
WHITE  = colors.white
BLACK  = colors.black

GRADE_COLORS = {
    "A": GREEN, "B": BLUE, "C": AMBER, "F": RED, "—": GREY
}


def _grade_color(grade: str):
    return GRADE_COLORS.get(grade, GREY)


def generate_pdf(battery_id: int,
                 test_id: int,
                 output_path: Optional[str] = None) -> Optional[str]:
    """
    Generate a PDF report for a completed test.

    Args:
        battery_id:  ID in batteries table
        test_id:     ID in tests table
        output_path: where to save the PDF (default: db/reports/OSB-XXXX_testN.pdf)

    Returns:
        Path to the saved PDF, or None if generation failed.
    """
    if not REPORTLAB_AVAILABLE:
        print("ERROR: reportlab not installed. Run: pip install reportlab")
        return None

    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_battery, get_tests_for_battery, get_readings

    batt  = get_battery(battery_id)
    if not batt:
        return None

    tests = get_tests_for_battery(battery_id)
    test  = next((t for t in tests if t["test_id"] == test_id), None)
    if not test:
        return None

    # AI result (if available)
    try:
        from gui.ai_model import OSBAMSModel
        model = OSBAMSModel()
        ai    = model.predict(battery_id, test_id)
    except Exception:
        ai = None

    # Output path
    if output_path is None:
        reports_dir = os.path.join(os.path.dirname(__file__), "..", "db", "reports")
        os.makedirs(reports_dir, exist_ok=True)
        oid  = batt.get("osbams_id") or f"B{battery_id:04d}"
        output_path = os.path.join(reports_dir,
                                   f"{oid}_test{test_id}.pdf")

    # ── Build PDF ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize  = LETTER,
        leftMargin  = 0.75 * inch,
        rightMargin = 0.75 * inch,
        topMargin   = 0.75 * inch,
        bottomMargin= 0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story  = []

    def h1(text, color=NAVY):
        return Paragraph(
            f'<font color="{color.hexval()}" size="16"><b>{text}</b></font>',
            styles["Normal"])

    def h2(text, color=BLUE):
        return Paragraph(
            f'<font color="{color.hexval()}" size="12"><b>{text}</b></font>',
            styles["Normal"])

    def body(text):
        return Paragraph(f'<font size="10">{text}</font>', styles["Normal"])

    def small(text, color=GREY):
        return Paragraph(
            f'<font color="{color.hexval()}" size="8">{text}</font>',
            styles["Normal"])

    def sp(h=8):
        return Spacer(1, h)

    def hr():
        return HRFlowable(width="100%", thickness=1,
                          color=colors.HexColor("#e5e7eb"), spaceAfter=6)

    # ── Header ────────────────────────────────────────────────────────
    oid   = batt.get("osbams_id") or f"#{battery_id}"
    brand = batt.get("manufacturer") or batt.get("brand") or "Unknown"
    model_name = batt.get("model") or "—"

    header_data = [[
        Paragraph(f'<font color="#1F3864" size="18"><b>OSBAMS</b></font>', styles["Normal"]),
        Paragraph(
            f'<font color="#6b7280" size="9">Battery Assessment Report<br/>'
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</font>',
            styles["Normal"]),
    ]]
    header_table = Table(header_data, colWidths=[3*inch, 4*inch])
    header_table.setStyle(TableStyle([
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (1,0), (1,0),   "RIGHT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(header_table)
    story.append(hr())

    # ── Battery identity ──────────────────────────────────────────────
    story.append(h1(f"🔋  {oid}  —  {brand} {model_name}"))
    story.append(sp(4))

    ident_rows = [
        ["Serial #",      batt.get("serial_number") or "Unknown",
         "Chemistry",     batt.get("chemistry") or "?"],
        ["Nominal V",     f"{batt.get('nominal_voltage','?')} V",
         "Cell config",   batt.get("cell_config") or "?"],
        ["Rated Ah",      f"{batt.get('capacity_rated_ah','?')} Ah",
         "Rated Wh",      f"{batt.get('energy_rated_wh','?')} Wh"],
        ["Source",        batt.get("source_type") or "?",
         "Intake date",   (batt.get("intake_date") or "?")[:10]],
    ]
    ident_table = Table(
        [[Paragraph(f'<font size="9" color="#6b7280"><b>{r[0]}</b></font>', styles["Normal"]),
          Paragraph(f'<font size="9">{r[1]}</font>', styles["Normal"]),
          Paragraph(f'<font size="9" color="#6b7280"><b>{r[2]}</b></font>', styles["Normal"]),
          Paragraph(f'<font size="9">{r[3]}</font>', styles["Normal"])]
         for r in ident_rows],
        colWidths=[1.2*inch, 2.0*inch, 1.2*inch, 2.3*inch],
    )
    ident_table.setStyle(TableStyle([
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0,0), (0,-1),  LGREY),
        ("BACKGROUND", (2,0), (2,-1),  LGREY),
        ("PADDING",    (0,0), (-1,-1), 5),
    ]))
    story.append(ident_table)
    story.append(sp(12))

    # ── Test results ──────────────────────────────────────────────────
    story.append(h2("Test Results"))
    story.append(sp(4))

    grade      = test.get("grade") or "—"
    gc         = _grade_color(grade)
    soh        = test.get("soh_percent")
    cap_ah     = test.get("capacity_ah")
    eng_wh     = test.get("energy_wh")
    rec        = test.get("recommendation") or "—"
    score      = test.get("reliability_score") or 0
    dur_s      = test.get("discharge_time_s") or 0
    dur_str    = f"{int(dur_s // 3600)}h {int((dur_s % 3600) // 60)}m" if dur_s else "—"
    max_temp   = test.get("max_temp_c")

    safety_status = batt.get("safety_status") or "Unknown"
    uncertainty   = "±5%" if (ai and ai.ml_active) else "±8% (rule-based)"

    results_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Safety Status",      safety_status,
         "Test Date",          (test.get("started_at") or "?")[:10]],
        ["Measured Capacity",  f"{cap_ah:.2f} Ah" if cap_ah else "—",
         "Measured Energy",    f"{eng_wh:.1f} Wh" if eng_wh else "—"],
        ["Estimated SOH",      f"{soh:.0f}%  ({uncertainty})" if soh else "—",
         "Reliability Score",  f"{score} / 100"],
        ["Grade",              grade,
         "Recommendation",     rec],
        ["Discharge Time",     dur_str,
         "Peak Temperature",   f"{max_temp:.1f}°C" if max_temp else "—"],
        ["Test ID",            f"#{test_id}",
         "Load Mode",          test.get("load_mode") or "Manual"],
    ]

    def rval(val, bold=False, color=BLACK):
        w = "<b>" if bold else ""
        e = "</b>" if bold else ""
        return Paragraph(
            f'<font size="10" color="{color.hexval()}">{w}{val}{e}</font>',
            styles["Normal"])

    rt = Table(
        [[rval(r[0], bold=True, color=GREY),
          rval(r[1], bold=(i > 0 and r[0] == "Grade"),
               color=gc if r[0] == "Grade" else BLACK),
          rval(r[2], bold=True, color=GREY),
          rval(r[3])]
         for i, r in enumerate(results_data)],
        colWidths=[1.5*inch, 1.9*inch, 1.5*inch, 1.8*inch],
    )
    rt.setStyle(TableStyle([
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
        ("BACKGROUND", (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",  (0,0), (-1,0),  WHITE),
        ("BACKGROUND", (0,1), (0,-1),  LGREY),
        ("BACKGROUND", (2,1), (2,-1),  LGREY),
        ("PADDING",    (0,0), (-1,-1), 5),
    ]))
    story.append(rt)
    story.append(sp(12))

    # ── Second-life recommendation ─────────────────────────────────────
    if ai and ai.second_life:
        story.append(h2("Second-Life Recommendation"))
        story.append(sp(4))

        sl_rows = []
        for u in ai.second_life:
            mark  = "✓" if u.approved else "✗"
            mcolor = GREEN if u.approved else RED
            sl_rows.append([
                Paragraph(f'<font color="{mcolor.hexval()}" size="11"><b>{mark}</b></font>',
                          styles["Normal"]),
                Paragraph(f'<font size="9"><b>{u.label}</b></font>', styles["Normal"]),
                Paragraph(f'<font size="8" color="#6b7280">{u.reason}</font>',
                          styles["Normal"]),
            ])

        sl_table = Table(sl_rows, colWidths=[0.3*inch, 1.8*inch, 4.6*inch])
        sl_table.setStyle(TableStyle([
            ("GRID",    (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("PADDING", (0,0), (-1,-1), 4),
            ("VALIGN",  (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(sl_table)
        story.append(sp(12))

    # ── AI analysis ───────────────────────────────────────────────────
    if ai:
        story.append(h2("Health Estimation & Decision Support"))
        story.append(sp(4))

        ai_data = [
            [body(f"Rule score: <b>{ai.rule_score}</b>"),
             body(f"ML assist:  <b>{ai.ai_score}</b>"),
             body(f"Consensus:  <b>{ai.final_score}</b>"),
             body(f"Confidence: <b>{ai.confidence:.0%}</b>"),
             body(f"ML active:  <b>{'Yes' if ai.ml_active else 'No (rule-based)'}</b>")],
        ]
        ai_table = Table(ai_data, colWidths=[1.3*inch]*5)
        ai_table.setStyle(TableStyle([
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
            ("BACKGROUND", (0,0), (-1,-1), LGREY),
            ("PADDING",    (0,0), (-1,-1), 5),
        ]))
        story.append(ai_table)
        story.append(sp(6))

        story.append(body("<b>Why:</b>"))
        for reason in ai.reasons:
            story.append(body(f"&nbsp;&nbsp;• {reason}"))
        story.append(sp(12))

    # ── Physical notes ────────────────────────────────────────────────
    phys_notes = batt.get("physical_notes")
    if phys_notes:
        story.append(h2("Inspection Notes"))
        story.append(sp(4))
        story.append(body(phys_notes))
        story.append(sp(8))

    # ── Footer ────────────────────────────────────────────────────────
    story.append(hr())
    # Reproducibility block — every version that produced this report
    from config import (APP_VERSION, FIRMWARE_VERSION, PROTOCOL_VERSION,
                        SCHEMA_VERSION, RULE_ENGINE_VERSION)
    ai_mode = "ML-assisted" if (ai and ai.ml_active) else "Rule-only"
    ml_n    = getattr(ai, "trained_on", 0) if ai else 0
    repro_line = (
        f"App {APP_VERSION}  ·  Firmware {FIRMWARE_VERSION}  ·  "
        f"Protocol {PROTOCOL_VERSION}  ·  DB schema {SCHEMA_VERSION}  ·  "
        f"Rule engine {RULE_ENGINE_VERSION}  ·  "
        f"Health estimation: {ai_mode} ({ml_n} batteries)  ·  "
        f"Generated {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ·  "
        f"Report {oid}-T{test_id}"
    )
    story.append(small(repro_line))
    story.append(small(
        "This assessment is based on external pack-level measurements. "
        "It does not certify the internal condition of individual cells "
        "or guarantee future safety. ENGR 696/697GW Senior Capstone, SFSU."
    ))

    doc.build(story)
    return output_path


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import init_db, create_battery, start_test, end_test

    init_db()
    import os
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "osbams.db")

    # Use existing battery 7 if present, else create a test one
    from db.database import get_battery
    batt = get_battery(7)
    if not batt:
        bid, oid = create_battery("fleet", brand="Ninebot", model="NEE1006-M",
                                   nominal_voltage=36.0, capacity_rated_ah=15.3,
                                   energy_rated_wh=551.0, chemistry="Li-Ion NMC",
                                   cell_config="10S6P")
        tid = start_test(bid, "discharge")
        end_test(tid, 12.4, 446.0, 3600.0, 38.0, 81.0, 78, "B",
                 "Reuse with monitoring")
    else:
        bid = 7
        from db.database import get_tests_for_battery
        tests = get_tests_for_battery(bid)
        if tests:
            tid = tests[0]["test_id"]
        else:
            tid = start_test(bid, "discharge")
            end_test(tid, 12.4, 446.0, 3600.0, 38.0, 81.0, 78, "B",
                     "Reuse with monitoring")

    out = generate_pdf(bid, tid)
    print(f"PDF generated: {out}")
