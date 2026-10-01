#!/usr/bin/env python3
"""RC2 gate: refuses unless every required input is verified or owner-cited."""
import json, os, sys
I = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasheet_inputs.json")))
need = ["f2_resistance_cold_mohm", "j_out_contact_max_mohm", "rsdw_trim_network", "rsdw_tolerance_pct", "pi_end_connector_mpn", "pi_end_contact_max_mohm", "rsdw_footprint_drawing", "rsdw_input_fuse_recommendation_resolved", "pi_end_pin_map_confirmed", "erc_clean_kicad10", "bench_pi_voltage"]
ok = lambda k: I[k]["status"] in ("verified", "owner_cited") and I[k]["value"] not in (None, False)
bad = [k for k in need if not ok(k)]
print("RC2 gate:", "OPEN" if bad else "CLEAR")
for k in bad: print("  open:", k, "-", I[k]["source"])
for k in need:
    if I[k]["status"] == "owner_cited": print("  note: owner-cited, re-check vs PDF:", k)
sys.exit(1 if bad else 0)
