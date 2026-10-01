#!/usr/bin/env python3
"""RC2 gate: refuses unless every required datasheet input is verified."""
import json, os, sys
I = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasheet_inputs.json")))
need = ["j_out_contact_max_mohm", "pi_end_contact_max_mohm", "f2_resistance_max_mohm", "rsdw_tolerance_pct", "rsdw_footprint_drawing", "erc_clean_kicad10"]
bad = [k for k in need if not I[k]["verified"]]
trim_ok = I["rsdw_trim_allowed"]["verified"]
print("RC2 gate:", "OPEN" if bad or not trim_ok else "CLEAR")
for k in bad: print("  unverified:", k, "-", I[k]["source"])
if not trim_ok: print("  unverified: rsdw_trim_allowed (trim range/formula) - R2/R3 stay DNP")
sys.exit(1 if bad or not trim_ok else 0)
