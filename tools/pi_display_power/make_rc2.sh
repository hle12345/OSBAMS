#!/bin/sh
# Creates OSBAMS_Pi_Display_Power_RevA_RC2 and OSBAMS_Pi_Power_Interposer_RevA_RC2 ONLY if the RC2 gate is clear.
# Before running: run KiCad 10 ERC on both schematics, save the reports into each project's reports/ folder, then set
# "erc_clean_kicad10" to {"value": true, "status": "verified"} in datasheet_inputs.json.
set -e
cd "$(dirname "$0")"
python3 rc2_gate.py || { echo "RC2 gate OPEN - not creating RC2"; exit 1; }
R=../..
mkdir -p $R/OSBAMS_Pi_Display_Power_RevA_RC2/{kicad,gerbers,drill,bom,cpl,docs,reports,generator} $R/OSBAMS_Pi_Power_Interposer_RevA_RC2
cp -r $R/OSBAMS_Pi_Display_Power_RevA_RC1/generator/* $R/OSBAMS_Pi_Display_Power_RevA_RC2/generator/
PWR_DIR=$R/OSBAMS_Pi_Display_Power_RevA_RC2 IP_DIR=$R/OSBAMS_Pi_Power_Interposer_RevA_RC2 REL=RC2 ./build_all.sh
echo "RC2 created (copy your ERC reports into each reports/ folder and update the README status)."
