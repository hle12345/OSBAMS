#!/usr/bin/env python3
"""Fab/assembly outputs: gerbers, drill, BOM xlsx, CPL csv, drawings. Run after build_pcb.py."""
import os, sys, subprocess, csv, zipfile, glob, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts import *
from kenv import kicli
D = sys.argv[1]; K = f"{D}/kicad/{NAME}.kicad_pcb"
def sh(*a):
    a = a[1:] if a[0] == "kicad-cli" else a
    r = kicli(*a); print(" ".join(map(str, a[:4])), "->", (r.stdout + r.stderr).strip().splitlines()[-1:]); return r
REL = os.environ.get("REL", "RC1")

# --- Gerbers + drill: only when GERBERS=1 (RC2 ships NO Gerbers - the owner exports them from the final board in KiCad 10)
if os.environ.get("GERBERS") == "1":
    for f in glob.glob(f"{D}/gerbers/*") + glob.glob(f"{D}/drill/*"): os.remove(f)
    sh("kicad-cli","pcb","export","gerbers","-o",f"{D}/gerbers/","-l","F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts","--subtract-soldermask",K)
    sh("kicad-cli","pcb","export","drill","-o",f"{D}/drill/","--format","excellon","--excellon-units","mm","--generate-map","--map-format","gerberx2",K)

# --- Assembly drawing (top silk + copper + fab refs) and bottom
S = f"{D}/docs/_svg"; os.makedirs(S, exist_ok=True)
import cairosvg
for tag, layers in (("top", "F.Cu,F.SilkS,F.Fab,Edge.Cuts"), ("bottom", "B.Cu,B.SilkS,Edge.Cuts")):
    sh("kicad-cli","pcb","export","svg","--exclude-drawing-sheet","--page-size-mode","2","-l",layers,*(["--mirror"] if tag=="bottom" else []),"-o",f"{S}/{tag}.svg",K)
    cairosvg.svg2pdf(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.pdf")
    cairosvg.svg2png(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.png", output_width=1800, background_color="white")

# --- CPL (kicad-cli pos export: board top-left is the page origin, Y negative downwards -> Y from the bottom-left = BOARD_H + PosY)
sh("kicad-cli","pcb","export","pos","--format","csv","--units","mm","--side","front","-o",f"{S}/pos.csv",K)
rows = []; mt = {p[0]: p[6] for p in PARTS}
for r_ in csv.DictReader(open(f"{S}/pos.csv")):
    r = r_["Ref"]
    if r not in mt or r in ("R2", "R3"): continue
    rows.append([r, f"{float(r_['PosX']):.3f}", f"{BOARD_H + float(r_['PosY']):.3f}", "Top", f"{float(r_['Rot']):.0f}", mt[r]])
rows.sort(key=lambda x: x[0])
with open(f"{D}/cpl/{NAME}_{REL}_CPL.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation", "Mount"]); w.writerows(rows)
shutil.rmtree(S, ignore_errors=True)

# --- BOM XLSX
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
wb = Workbook(); ws = wb.active; ws.title = "BOM"
hdr = ["Designator", "Qty", "Value", "Description", "Manufacturer", "MPN", "Footprint (KiCad)", "Mount", "Sourcing / notes", "Verification status"]
ws.append(hdr)
special = {"U1": "Verify PCBWay stock; if not sourceable mark CONSIGNED / customer-supplied (do not substitute without approval)",
           "F1": "Confirm PCBWay/DigiKey stock for 0407008.WR (reel 3000; ask for cut tape/qty)", "F2": "Active; DigiKey-stocked per design brief"}
LIBNOTE = "Footprint: official KiCad library (generated from manufacturer datasheet); NOT cross-checked against the manufacturer PDF"
status = {"U1": "Footprint from Mean Well RSDW40/RDDW40 spec drawing (2022-05-24); verify mirror/rotation in KiCad", "F1": "Datasheet-verified (Littelfuse 407, rev 09/14/20): 8 A time-lag, 24 V, 60 A@24VDC, 9 mOhm, I2t 24.12; land pattern = datasheet recommended pads", "F2": "Datasheet-verified (451/453 rev): 8 A very fast-acting, 125 V, 7.7 mOhm cold, I2t 20.23; pads 1.96x3.15, span 6.86 match the library footprint", "TVS1": "Electrical data USER-RELAYED from the Littelfuse SMBJ15A row (VRWM 15 V, VBR 16.7-18.5 V @ 1 mA, VC 24.4 V @ 24.6 A, IR 1 uA); footprint = KiCad library D_SMB (DO-214AA, cathode pad 1), not PDF-verified",
          "J_IN": LIBNOTE + "; mating parts unverified", "J_OUT": LIBNOTE + " (pegs + drills included); mating parts unverified",
          "C2": LIBNOTE + "; verify body D8/pitch 3.5 vs EEU-FM1H101", "C4": LIBNOTE + "; verify body D10/pitch 5.0 vs EEU-FR1C681",
          "J_DISP": LIBNOTE + "; mating parts unverified", "R2": "DNP - footprint only, no part purchased", "R3": "Not fitted at assembly; fit the select-on-test value (kit 61.9k/71.5k/84.5k) at calibration"}
import re
groups = {}
for p in PARTS: groups.setdefault(p[4] + "|" + p[1] if p[0].startswith("TP") or p[4] in ("GRM188R71H104KA93D",) else p[0], []).append(p)
for k, g in groups.items():
    p = g[0]; refs = ", ".join(x[0] for x in g)
    ws.append([refs, len(g), p[1], p[2], p[3], p[4], p[5], p[6], (special.get(p[0], "") + " " + p[7]).strip() or "Confirm stock/lifecycle at order", status.get(p[0], "MPN from design brief/selection; stock + land pattern not verified offline")])
ws.append([]); ws.append([]); ws.append(["OFF-BOARD HARNESS / MATING PARTS (not on the PCB). Housings are the Molex mating parts of the 430450x00 headers; the crimp terminal and wire MPNs are NOT verified (no Molex terminal drawing in the project files) - owner to confirm before ordering the harness"])
ws.append(["J_IN mate", 1, "", "Micro-Fit 3.0 receptacle housing, 2 circuits, dual-row family", "Molex", "43025-0200", "", "Harness", "Mates J_IN 430450200 (keyed)", "Mate of the 43045 header per Molex family naming; mating drawing not in project files"])
ws.append(["J_OUT mate", 1, "", "Micro-Fit 3.0 receptacle housing, 4 circuits", "Molex", "43025-0400", "", "Harness", "Mates J_OUT 430450400 (keyed)", "As above"])
ws.append(["J_DISP mate", 1, "", "Micro-Fit 3.0 receptacle housing, 2 circuits (display feed)", "Molex", "43025-0200", "", "Harness", "Mates J_DISP 430450200 (keyed)", "As above; display end: MX1.25 2-pin per the Waveshare package cables (user-relayed) - confirm the housing"])
ws.append(["Terminals", 12, "", "Micro-Fit 3.0 female crimp terminals, 18 AWG / 0.75 mm2, tin: 2 (J_IN) + 4 (J_OUT) + 2 (J_DISP) + 4 (interposer J1) = 12 (+ spares)", "Molex", "43030-0038", "", "Harness", "Crimp per Molex ATS-638280200: conductor crimp 1.00-1.10 mm, strip 2.54-2.92 mm, pull >= 89 N; hand tool 63828-0200, locator 63828-0275; (-0039/-0040 = selective gold variants)", "VERIFIED for 18 AWG (Molex ATS-638280200, uploaded); no 16 AWG 43030 terminal exists; current rating with 18 AWG not in that file (first-article temperature check)"])
ws.append(["Pi-end interposer", 1, "", "OSBAMS_Pi_Power_Interposer_RevA (keyed Micro-Fit to Pi GPIO) - see its own BOM", "OSBAMS", "Interposer RevA RC2", "", "Harness", "Replaces the Harwin M20 housing", "Designed; ERC/DRC clean in KiCad 10; key check PASS (plan view + height)"])
ws.append(["Wire", 1, "", "18 AWG UL1061-type, insulation OD <= 1.85 mm, <= 150 mm, 4 wires (Pi branch, red/black, 1:1 to the interposer); display feed 2 wires 18 AWG (or 20 AWG + 43030-0007), <= 200 mm", "owner", "18 AWG UL1061-type (supplier by owner)", "", "Harness", "Insulation OD must be <= 1.85 mm to fit the terminal insulation crimp", "Specified; supplier open"])
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
wb.save(f"{D}/bom/{NAME}_{REL}_BOM.xlsx")
print("outputs done")
