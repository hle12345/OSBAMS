#!/usr/bin/env python3
"""Fab/assembly outputs: gerbers, drill, BOM xlsx, CPL csv, drawings. Run after build_pcb.py."""
import os, sys, subprocess, csv, zipfile, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import *
D = sys.argv[1]; K = f"{D}/kicad/{NAME}.kicad_pcb"
def sh(*a): r = subprocess.run(a, capture_output=True, text=True); print(" ".join(a[:4]), "->", (r.stdout + r.stderr).strip().splitlines()[-1:]); return r

# --- Gerbers + drill
for f in glob.glob(f"{D}/gerbers/*") + glob.glob(f"{D}/drill/*"): os.remove(f)
sh("kicad-cli","pcb","export","gerbers","-o",f"{D}/gerbers/","-l","F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts","--subtract-soldermask",K)
sh("kicad-cli","pcb","export","drill","-o",f"{D}/drill/","--format","excellon","--excellon-units","mm","--generate-map","--map-format","gerberx2",K)
with zipfile.ZipFile(f"{D}/gerbers/{NAME}_RC1_gerbers_drill.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob(f"{D}/gerbers/*") + glob.glob(f"{D}/drill/*")):
        if not f.endswith(".zip"): z.write(f, os.path.basename(f))

# --- Assembly drawing (top silk + copper + fab refs) and bottom
S = "/tmp/claude-0/-home-user-OSBAMS/44f9f13a-662c-51f9-9d22-4a46c7c73bb2/scratchpad"
import cairosvg
for tag, layers in (("top", "F.Cu,F.SilkS,F.Fab,Edge.Cuts"), ("bottom", "B.Cu,B.SilkS,Edge.Cuts")):
    sh("kicad-cli","pcb","export","svg","--exclude-drawing-sheet","--page-size-mode","2","-l",layers,*(["--mirror"] if tag=="bottom" else []),"-o",f"{S}/{tag}.svg",K)
    cairosvg.svg2pdf(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.pdf")
    cairosvg.svg2png(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.png", output_width=1800, background_color="white")

# --- CPL (positions from the PCB; Y shown bottom-left origin, +Y up)
import pcbnew
b = pcbnew.LoadBoard(K); rows = []
mt = {p[0]: p[6] for p in PARTS}
for fp in b.GetFootprints():
    r = fp.GetReference()
    if r not in mt: continue
    if r in ("R2","R3"): continue
    rows.append([r, f"{fp.GetPosition().x/1e6:.3f}", f"{BOARD_H - fp.GetPosition().y/1e6:.3f}", "Top", f"{fp.GetOrientationDegrees():.0f}", mt[r]])
rows.sort(key=lambda x: x[0])
with open(f"{D}/cpl/{NAME}_RC1_CPL.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation", "Mount"]); w.writerows(rows)

# --- BOM XLSX
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
wb = Workbook(); ws = wb.active; ws.title = "BOM"
hdr = ["Designator", "Qty", "Value", "Description", "Manufacturer", "MPN", "Footprint (KiCad)", "Mount", "Sourcing / notes", "Verification status"]
ws.append(hdr)
special = {"U1": "Verify PCBWay stock; if not sourceable mark CONSIGNED / customer-supplied (do not substitute without approval)",
           "F1": "Active; DigiKey-stocked per design brief", "F2": "Active; DigiKey-stocked per design brief"}
LIBNOTE = "Footprint: official KiCad library (generated from manufacturer datasheet); NOT cross-checked against the manufacturer PDF"
status = {"U1": "Footprint from Mean Well RSDW40/RDDW40 spec drawing (2022-05-24); verify mirror/rotation in KiCad", "F1": LIBNOTE, "F2": LIBNOTE, "TVS1": LIBNOTE,
          "J_IN": LIBNOTE + "; mating parts unverified", "J_OUT": LIBNOTE + " (pegs + drills included); mating parts unverified",
          "C2": LIBNOTE + "; verify body D8/pitch 3.5 vs EEU-FM1H101", "C4": LIBNOTE + "; verify body D10/pitch 5.0 vs EEU-FR1C681",
          "R2": "DNP - do not fit", "R3": "DNP - do not fit"}
import re
groups = {}
for p in PARTS: groups.setdefault(p[4] + "|" + p[1] if p[0].startswith("TP") or p[4] in ("GRM188R71H104KA93D",) else p[0], []).append(p)
for k, g in groups.items():
    p = g[0]; refs = ", ".join(x[0] for x in g)
    ws.append([refs, len(g), p[1], p[2], p[3], p[4], p[5], p[6], (special.get(p[0], "") + " " + p[7]).strip() or "Confirm stock/lifecycle at order", status.get(p[0], "MPN from design brief/selection; stock + land pattern not verified offline")])
ws.append([]); ws.append(["MATING HARNESS PARTS (not on PCB) - all candidates, verify against Molex 43025/43030 and 214755 families"])
ws.append(["J_OUT mate", 1, "", "Micro-Fit 3.0 receptacle housing, 4 circuits, dual row", "Molex", "43025-0400", "", "Harness", "Keyed; mates J_OUT 430450400", "Verify"])
ws.append(["J_IN mate", 1, "", "Micro-Fit 3.0 receptacle housing, 2 circuits", "Molex", "43025-0200", "", "Harness", "Keyed; mates J_IN 430450200", "Verify"])
ws.append(["Terminals", 6, "", "Micro-Fit 3.0 crimp terminals (43030 family) - 4 out + 2 in, wire 18 AWG", "Molex", "43030-0007 (candidate)", "", "Harness", "Select exact terminal for 18 AWG insulation OD; confirm current rating", "Verify - candidate only"])
ws.append(["Pi-side housing", 1, "", "Harwin M20 2x5 cable housing, populate cavities 2,4,6,9 only (UNPOLARISED - needs anti-reversal key)", "Harwin", "M20-1070500", "", "Harness", "Owner-cited; confirm layout on Harwin drawing", "Owner-cited"])
ws.append(["Pi-side contacts", 4, "", "Harwin M20 gold crimp contact, 22-30 AWG, 3 A, 20 mOhm max", "Harwin", "M20-1160042", "", "Harness", "22 AWG branch leads; 2x +5V, 2x GND", "Owner-cited"])
ws.append(["Anti-reversal key / interposer", 1, "", "Mechanical key or keyed interposer for Pi end", "TBD", "TBD", "", "Harness", "Reversed housing swaps +5V and GND - decision required", "OPEN"])
ws.append(["Wire", 1, "", "16 AWG trunk (<=150 mm) + 22 AWG branch leads (~50 mm), red/black", "TBD", "TBD", "", "Harness", "", "OPEN"])
for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
for i, wd in enumerate([16, 6, 14, 52, 18, 24, 26, 8, 52, 46], 1): ws.column_dimensions[get_column_letter(i)].width = wd
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
ws.freeze_panes = "A2"
ws2 = wb.create_sheet("Notes")
for l in ["OSBAMS_Pi_Display_Power_RevA RC1 BOM - release candidate, NOT final fabrication authorization.",
          "MPNs in the brief (U1, F1, F2, TVS1, J_OUT) are locked. Others were selected offline; distributor stock/lifecycle NOT checked from the build container.",
          "Fiducials (FID1-3) and mounting holes (H1-H4) are board features: no BOM line.",
          "If PCBWay cannot source RSDW40F-05: consigned/customer-supplied. No substitution without approval."]: ws2.append([l])
ws2.column_dimensions["A"].width = 140
wb.save(f"{D}/bom/{NAME}_RC1_BOM.xlsx")
print("outputs done")
