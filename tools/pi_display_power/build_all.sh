#!/bin/sh
# Regenerates OSBAMS_Pi_Display_Power_RevA_RC1 (needs KiCad 7+ with python3 pcbnew, openpyxl, cairosvg, matplotlib)
set -e
cd "$(dirname "$0")"; D=../../OSBAMS_Pi_Display_Power_RevA_RC1; N=OSBAMS_Pi_Display_Power_RevA
/usr/bin/python3 build_pcb.py $D/kicad/$N.kicad_pcb
python3 build_sch.py $D/kicad/$N.kicad_sch
/usr/bin/python3 $D/generator/run_drc.py $D/kicad/$N.kicad_pcb $D/reports/DRC_report.rpt
/usr/bin/python3 check_design.py $D
/usr/bin/python3 make_outputs.py $D
/usr/bin/python3 make_figs.py $D
python3 voltage_budget.py $D
I=../../OSBAMS_Pi_Power_Interposer_RevA_RC1
/usr/bin/python3 build_interposer.py $I
/usr/bin/python3 make_interposer_outputs.py $I
python3 check_pi5_keying.py $I || true
python3 rc2_gate.py || true
