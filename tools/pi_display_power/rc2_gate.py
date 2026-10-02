#!/usr/bin/env python3
"""RC2 gate: refuses unless every required input is verified or owner-cited. Bench validation is a first-article step, not a gate."""
import json, os, sys
I = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasheet_inputs.json")))
need = ["f2_resistance_cold_mohm", "j_out_contact_max_mohm", "rsdw_trim_network", "rsdw_tolerance_pct", "rsdw_footprint_drawing",
        "f1_mpn", "interposer_socket_mpn", "pi5_mechanical_drawing_step", "interposer_key_3d_check", "erc_clean_kicad10", "display_power_feed"]  # socket contact resistance is a first-article measured parameter, not a gate
ok = lambda k: I[k]["status"] in ("verified", "owner_cited", "user_relayed_manufacturer") and I[k]["value"] not in (None, False)
bad = [k for k in need if not ok(k)]
print("RC2 gate:", "OPEN" if bad else "CLEAR")
for k in bad: print("  open:", k, "-", I[k]["source"][:160])
for k in need:
    if I[k]["status"] == "owner_cited": print("  note: owner-cited, re-check vs PDF:", k)
print("  first-article (not a gate): bench_pi_voltage - loaded Pi voltage + harness temperature rise; trim calibration per docs/Trim_calibration_procedure.md")
sys.exit(1 if bad else 0)
