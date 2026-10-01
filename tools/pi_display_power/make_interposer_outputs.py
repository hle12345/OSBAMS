#!/usr/bin/env python3
import sys, os, glob, subprocess, zipfile
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
D = sys.argv[1]; NAME = "OSBAMS_Pi_Power_Interposer_RevA"; K = f"{D}/kicad/{NAME}.kicad_pcb"
for f in glob.glob(f"{D}/gerbers/*") + glob.glob(f"{D}/drill/*"): os.remove(f)
subprocess.run(["kicad-cli","pcb","export","gerbers","-o",f"{D}/gerbers/","-l","F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts","--subtract-soldermask",K],capture_output=True)
subprocess.run(["kicad-cli","pcb","export","drill","-o",f"{D}/drill/","--format","excellon","--excellon-units","mm","--generate-map","--map-format","gerberx2",K],capture_output=True)
with zipfile.ZipFile(f"{D}/gerbers/{NAME}_RC1_gerbers_drill.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob(f"{D}/gerbers/*") + glob.glob(f"{D}/drill/*")):
        if not f.endswith(".zip"): z.write(f, os.path.basename(f))
wb = Workbook(); ws = wb.active; ws.title = "BOM"
ws.append(["Designator", "Qty", "Description", "Manufacturer", "MPN", "Footprint", "Status"])
rows = [
 ["J1", 1, "Micro-Fit 3.0 header, right-angle, dual row, 4 circuits (keyed)", "Molex", "430450400", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal", "Locked part; library footprint (pegs included); not cross-checked vs Molex PDF"],
 ["J2", 1, "Samtec SSW-120-01-S-D: 2x20, 2.54 mm, through-hole vertical receptacle, 30 uin gold / tin tails, body 8.51 mm, tail 2.64 mm, 4.7 A (one pin powered per row). Mounted from the UNDERSIDE, soldered from the top.", "Samtec", "SSW-120-01-S-D", "OSBAMS_PiPwr:SSW-120-01-S-D_RPi_TopView (pad pattern by Pi pin number, 1.0 mm drill - confirm vs Samtec footprint)", "Owner-selected; ordering code/dimensions to re-check vs the SSW-120 product page. Do NOT use SSW-120-04-G-D (14.83 mm tail, no stock)"],
 ["K1, K2", 2, "M2.5 female-female hex standoff, 20 mm (key posts, outward side) + M2.5 screws - length from check_stack_height.py", "generic", "M2.5 x 20 mm standoff", "NPTH 2.7 mm", "Length computed: socket face stays 11.5 mm above the Pi PCB when reversed (pin tips ~9 mm)"],
 ["M1, M2", 2, "M2.5 female-female hex standoff, 11 mm (= 8.51 mm socket body + ~2.5 mm Pi header plastic) + M2.5 screws, to the Pi header-end mounting holes", "generic", "M2.5 x 11 mm standoff", "NPTH 2.7 mm", "Standard HAT spacer length; confirm on a physical Pi 5"],
 ["Harness", 1, "Micro-Fit receptacle housing 43025-0400 at both ends (candidate), 4x 16 AWG, <=150 mm, crimped, 43030-family terminals", "Molex", "43025-0400 + 43030 (candidate)", "", "OPEN - confirm terminal for 16 AWG; strain relief (cable tie / clip)"],
]
for r in rows: ws.append(r)
for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
for col, w in zip("ABCDEFG", (12, 5, 70, 14, 26, 70, 70)): ws.column_dimensions[col].width = w
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical="top")
wb.save(f"{D}/bom/{NAME}_RC1_BOM.xlsx"); print("interposer outputs done")
