"""PCBWay package builder for the OSBAMS Rev.2 controller PCB (no KiCad needed).

Reads the KiCad 10 .kicad_pcb / .kicad_sch directly (kicad-cli is NOT available in the
build environment and gerbonara cannot read KiCad 10 files), so every output here is a
*candidate* derived from the design files. The authoritative fabrication outputs must be
re-exported from KiCad (see export_with_kicad_cli.sh) before ordering.
"""
