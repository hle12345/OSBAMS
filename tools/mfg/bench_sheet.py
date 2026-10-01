"""One-page hand-fill bench sheet (V1-V10) -> docs/rev2/pcb/BENCH_V1_V10_ONE_PAGE.pdf / .md.

V1-V10 are the audit's own list (docs/rev2/pcb/PCBWAY_REV2_CHANGE_REQUEST.md); rows are ordered by priority, not number.
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .pcb_model import REPO

OUT = os.path.join(REPO, "docs", "rev2", "pcb")

# id, priority, item, what to check (no battery connected for ANY of these), record, unlocks
ROWS = [
    ("V7", "P1", "Diode orientation D1/D2/D3",
     "Photo + cathode-band side of each installed diode relative to the net it should hold (D3 band toward the coil/relay side; D2 band to +12 V; D1 TVS band to +12 V). Power OFF; EDU34450A diode test as a cross-check.",
     "D1 band at: ______  D2 band at: ______\nD3 band at: ______  D3 Vf fwd ____ V",
     "G-01 BLOCKER: confirms/refutes the symbol-vs-footprint polarity defect"),
    ("V6", "P1", "Relay K1, ARM, E-stop block",
     "Relay: FULL marking + date code, coil resistance (expect ~90 ohm), coil current at 12 V. ARM: marking, where it sits in the coil path (before/after E-stop, or unconnected). E-stop block: NC contact count fitted, NO count.",
     "relay P/N __________  coil ____ ohm ____ mA\nARM in path: ______________  E-stop NC x __ NO x __",
     "G-02 relay keep/replace; G-05 PA0 option A (2nd NC) vs B (opto); G-14 ARM"),
    ("V1", "P1", "TC74: four discriminators (NO redesign until all four filled)",
     "(1) Package marking A-code/V-code. (2) VDD at pin 5 and idle SDA/SCL levels, U1 powered. (3) I2C1_Scan + raw TC74_Init status (NACK/TIMEOUT/BUS_ERROR/NOT_READY). (4) Scope SCL during a TC74 transaction: tLOW vs 4.7 us, tHIGH vs 4.0 us.",
     "(1) ______  (2) VDD ____ V SDA ____ SCL ____\n(3) scan 0x____  status ________\n(4) tLOW ____ us  tHIGH ____ us",
     "G-04: root cause before any TC74 interface change"),
    ("V9", "P1", "Nucleo <-> J5 wiring, power, host path",
     "Which Nucleo pins go to J5 (PC8, PC9, PA0, PA1?). How the Nucleo is powered (USB / 5V / VIN / E5V). Host link: ST-LINK USB VCP or separate UART (PA2/PA3 solder bridges).",
     "J5 pins: __________________________\nNucleo power: ______  host path: USB / UART",
     "G-05 / G-18 / G-21: Nucleo vs PCBA scope; Pi link"),
    ("V2", "P1", "VO610A feedback stage (K1 -> PC9)",
     "Photograph; record LED-side resistor values, output pull-up (value, to what rail), what the two 1N4148 do (antiparallel? series?), pack-side connection point (relay load side?).",
     "Rled ____ ohm  pull-up ____ to ____\n1N4148 role: ____________  taps relay: ______",
     "G-05: K1 feedback schematic for PC9"),
    ("V4", "P1", "Installed ADC divider (-> PA1)",
     "Resistor values and tolerances; where the tap goes (to PA1 directly? cap?); where the ground return connects; pack-side connection point. Power OFF.",
     "Rtop ____ tol __  Rbot ____ tol __\ntap -> ________  GND return -> ________",
     "G-05: protected divider; 16:1 firmware scale"),
    ("V3", "P2", "INA228 module",
     "Pin order vs J4 (3V3/GND/SCL/SDA), ALERT/A0/A1 straps, onboard shunt present/removed, how IN+ / IN- / VBUS are wired to the RSA-20-50.",
     "pin order: ____________  A0/A1: ____/____\nonboard shunt: Y/N  IN+/IN-/VBUS: ________",
     "G-12: Kelvin interface; K3 module kept"),
    ("V10", "P2", "Ground-bond point",
     "Single point where pack-negative meets logic GND? Any second path (USB shield, scope ground, Pi)? Continuity pack(-) to GND with power OFF.",
     "bond at: ______________  2nd path? Y/N\nR pack(-)-GND: ______",
     "G-13: ground bond"),
    ("V8", "P2", "R1/R2/C2/C3 + connectors",
     "Installed R1, R2, C2, C3 values and package; terminal-block and header part numbers (J1, J2, J3, J4, J5, J6) from markings/purchase records.",
     "R1 ____ R2 ____ C2 ____ C3 ____\nterminals: ______________  headers: ________",
     "G-07 / G-08: exact MPNs"),
    ("V5", "P3", "Fuse, holder, pack-bus TVS",
     "Holder marking and its datasheet DC V / A rating; installed fuse marking (expect 15 A, DC rating); any TVS across the pack bus.",
     "holder ____________ ___ VDC ___ A\nfuse ____________  pack TVS? Y/N ______",
     "G-15 / G-16"),
]


def make_pdf():
    ss = getSampleStyleSheet()
    c = lambda sz, **k: ParagraphStyle("c", parent=ss["BodyText"], fontSize=sz, leading=sz + 1.6, **k)
    story = [Paragraph("OSBAMS Rev.2 — bench verification V1–V10 (one page, fill by hand)", ParagraphStyle("t", parent=ss["Heading1"], fontSize=13, spaceAfter=1)),
             Paragraph("<b>NO BATTERY is connected for any item.</b> Power OFF unless a row says otherwise (V1 needs U1 powered, V6 coil current needs the 12 V supply). Instruments: EDU34450A (DMM), EDUX1052G (scope). "
                       "Rows ordered by priority (P1 first); IDs match the audit. Unknown = write UNKNOWN, never guess.", c(7.2)),
             Spacer(1, 2),
             Paragraph("Date ____________  Operator ____________  2nd person ____________  EDU34450A asset ID ____________  cal status ____________  Repo commit ____________", c(7.4)),
             Spacer(1, 3)]
    data = [[Paragraph(h, c(7, textColor=colors.white)) for h in ("#", "Pri", "Item", "What to check", "Record here", "Unlocks")]]
    for r in ROWS:
        data.append([Paragraph(f"<b>{r[0]}</b>", c(7.4)), Paragraph(r[1], c(7)), Paragraph(f"<b>{r[2]}</b>", c(7)),
                     Paragraph(r[3], c(6.4)), Paragraph(r[4].replace("\n", "<br/>"), c(6.4)), Paragraph(r[5], c(6.4))])
    t = Table(data, colWidths=[9 * mm, 8 * mm, 30 * mm, 100 * mm, 64 * mm, 44 * mm], rowHeights=[7 * mm] + [14.8 * mm] * len(ROWS))
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33415c")),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                           ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]
                          + [("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fff4e5")) for i, r in enumerate(ROWS, 1) if r[1] == "P1"]))
    story += [t, Spacer(1, 3),
              Paragraph("Done when every row is filled (or UNKNOWN). Then: update <b>REV1_HARDWARE_TRUTH_INVENTORY.md</b> → set <b>rev1_physical_observations_recorded</b> in RELEASE_GATES.json only with these sheets filed → revise the existing KiCad board. "
                        "P1 = blocks schematic decisions (BLOCKER-linked); P2 = HIGH, needed before release; P3 = MEDIUM.", c(7)),
              Paragraph("Signature ____________   Sheet stored at ____________________", c(7.4))]
    path = os.path.join(OUT, "BENCH_V1_V10_ONE_PAGE.pdf")
    doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=8 * mm, rightMargin=8 * mm, topMargin=7 * mm, bottomMargin=6 * mm,
                            title="OSBAMS bench V1-V10")
    doc.build(story)
    return path


def make_md():
    L = ["# Bench verification V1–V10 (one-page sheet, source of the PDF)\n",
         "Generated by `tools/mfg/bench_sheet.py`. Printable: `BENCH_V1_V10_ONE_PAGE.pdf`. **No battery is connected for any item.** "
         "IDs match the audit's V1–V10; rows ordered by priority.\n",
         "| # | Pri | Item | What to check | Unlocks |", "|---|---|---|---|---|"]
    for r in ROWS:
        L.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[5]} |")
    L.append("\nP1 = blocks schematic decisions (BLOCKER-linked); P2 = HIGH, needed before release; P3 = MEDIUM.\n")
    path = os.path.join(OUT, "BENCH_V1_V10.md")
    open(path, "w").write("\n".join(L))
    return path


if __name__ == "__main__":
    print(make_pdf(), make_md())
