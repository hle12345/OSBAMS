#!/usr/bin/env bash
# Re-export the AUTHORITATIVE fabrication files with KiCad 10 on a machine that has it.
# The package in this folder was generated WITHOUT KiCad (candidate files). Run this, diff against
# the candidates, run DRC/ERC, and upload ONLY the KiCad-exported files.
# Verify the option names with `kicad-cli pcb export gerbers --help` for your KiCad build.
set -euo pipefail
PRJ="${1:-Hardware/Schematic}"           # folder containing 'OSBAMS PCB.kicad_pcb' / .kicad_sch
OUT="${2:-manufacturing/PCBWay_OSBAMS_Rev2_PCBA/KICAD_EXPORT}"
PCB="$PRJ/OSBAMS PCB.kicad_pcb"; SCH="$PRJ/OSBAMS PCB.kicad_sch"
mkdir -p "$OUT"/{Gerber,Drill,PickAndPlace,Documentation}

# DRC / ERC first - upload nothing if either reports errors
kicad-cli pcb drc --output "$OUT/Documentation/OSBAMS_Rev2_DRC.rpt" --severity-all --exit-code-violations "$PCB"
kicad-cli sch erc --output "$OUT/Documentation/OSBAMS_Rev2_ERC.rpt" --severity-all --exit-code-violations "$SCH"

# Gerbers (2 copper layers + mask, silk, paste, edge)
kicad-cli pcb export gerbers --output "$OUT/Gerber/" \
  --layers F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  --subtract-soldermask --no-protel-ext "$PCB"
kicad-cli pcb export drill --output "$OUT/Drill/" --format excellon --excellon-separate-th \
  --drill-origin absolute --generate-map --map-format pdf "$PCB"

# Pick and place (SMT only - D1) and PDFs
kicad-cli pcb export pos --output "$OUT/PickAndPlace/OSBAMS_Rev2_CPL.csv" --format csv --units mm --side both --smd-only "$PCB"
kicad-cli sch export pdf --output "$OUT/Documentation/OSBAMS_Rev2_Schematic.pdf" "$SCH"
kicad-cli pcb export pdf --output "$OUT/Documentation/OSBAMS_Rev2_board_layers.pdf" \
  --layers F.Cu,B.Cu,F.Silkscreen,Edge.Cuts "$PCB"

( cd "$OUT/Gerber" && zip -j ../OSBAMS_Rev2_Gerber.zip *.g* ../Drill/*.drl )
echo "Done. Review DRC/ERC reports before uploading."
