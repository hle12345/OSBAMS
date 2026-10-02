#!/usr/bin/env python3
import sys, os, glob, subprocess, zipfile
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
D = sys.argv[1]; NAME = "OSBAMS_Pi_Power_Interposer_RevA"; K = f"{D}/kicad/{NAME}.kicad_pcb"
REL = os.environ.get("REL", "RC1")
# assembly drawings (top / bottom) via kicad-cli 10
from kenv import kicli
import cairosvg, shutil
S = f"{D}/docs/_svg"; os.makedirs(S, exist_ok=True)
for tag, layers in (("top", "F.Cu,F.SilkS,F.Fab,Edge.Cuts"), ("bottom", "B.Cu,B.SilkS,Edge.Cuts")):
    kicli("pcb", "export", "svg", "--exclude-drawing-sheet", "--page-size-mode", "2", "-l", layers, *(["--mirror"] if tag == "bottom" else []), "-o", f"{S}/{tag}.svg", K)
    cairosvg.svg2pdf(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.pdf")
    cairosvg.svg2png(url=f"{S}/{tag}.svg", write_to=f"{D}/docs/Assembly_drawing_{tag}.png", output_width=1800, background_color="white")
shutil.rmtree(S, ignore_errors=True)
wb = Workbook(); ws = wb.active; ws.title = "BOM"
ws.append(["Designator", "Qty", "Description", "Manufacturer", "MPN", "Footprint", "Status"])
rows = [
 ["J1", 1, "Micro-Fit 3.0 header, right-angle, dual row, 4 circuits (keyed)", "Molex", "430450400", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal", "Locked part (ratings owner-cited); KiCad 10 library footprint (pegs included); not cross-checked vs the Molex PDF"],
 ["J2", 1, "Samtec SSW-120-01-S-D: 2x20, 2.54 mm, through-hole vertical receptacle, 30 uin gold / tin tails, body 8.51 mm, tail 2.64 mm, 4.7 A (one pin powered per row). Mounted from the UNDERSIDE, soldered from the top.", "Samtec", "SSW-120-01-S-D", "OSBAMS_PiPwr:SSW-120-01-S-D_RPi_TopView (pad pattern by Pi pin number, 1.0 mm drill - confirm vs Samtec footprint)", "Dimensions CONFIRMED by Samtec catalog F-226 (8.51 mm body, lead style -01 = 2.64 mm tail). PLATING LETTER OPEN: catalog plating codes are -F/-L (10 uin Au)/-G (20 uin Au)/-T; -S is a row option there. Confirm the orderable code (owner: SSW-120-01-S-D) with the distributor, or order SSW-120-01-L-D / -G-D. Do NOT use SSW-120-04-G-D (14.83 mm tail, no stock)"],
 ["K1, K2", 2, "M2.5 female-female hex standoff, 20 mm (key posts, outward side) + M2.5 screws - length from check_stack_height.py", "generic", "M2.5 x 20 mm standoff", "NPTH 2.7 mm", "Length computed: socket face stays 11.5 mm above the Pi PCB when reversed (pin tips ~9 mm)"],
 ["M1, M2", 2, "M2.5 female-female hex standoff, 11 mm (= 8.51 mm socket body + ~2.5 mm Pi header plastic) + M2.5 screws, to the Pi header-end mounting holes", "generic", "M2.5 x 11 mm standoff", "NPTH 2.7 mm", "Standard HAT spacer length; confirm on a physical Pi 5"],
 ["Harness", 1, "Micro-Fit receptacle housing 43025-0400 at both ends, 4 x 16 AWG <= 150 mm, crimped (off-board; see the power-board BOM/Harness.md)", "Molex", "43025-0400 + 43030-family terminals (owner selects exact MPN)", "", "Terminals and wire NOT verified (no Molex 43030 drawing in the project); strain relief required"],
]
for r in rows: ws.append(r)
for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
for col, w in zip("ABCDEFG", (12, 5, 70, 14, 26, 70, 70)): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save(f"{D}/bom/{NAME}_{REL}_BOM.xlsx"); print("interposer outputs done")
