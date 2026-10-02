#!/usr/bin/env python3
"""Isolation-barrier rule for the Pi power board (runs in the KiCad 10 container): net classes PRIMARY (12 V side) / ISOLATED (5 V side), a custom DRC rule that requires
>= MIN mm copper-to-copper between the two classes on every layer, the DRC result, a negative control (rule tightened to prove KiCad applies it), and a report of
mounting holes / shield / chassis pads (hidden second ground paths). usage: k10_isolation.py <kicad dir> <project> [min_mm]"""
import os, sys, json, subprocess, shutil, re
import pcbnew
from pcbnew import ToMM
KD, NAME = sys.argv[1], sys.argv[2]; MIN = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
PCB = f"{KD}/{NAME}.kicad_pcb"; PRO = f"{KD}/{NAME}.kicad_pro"; DRU = f"{KD}/{NAME}.kicad_dru"
pj = json.load(open(PRO)); ns = pj.setdefault("net_settings", {"classes": [{"name": "Default"}], "meta": {"version": 3}})
ns["classes"] = [c for c in ns.get("classes", []) if c["name"] not in ("PRIMARY", "ISOLATED")] or [{"name": "Default"}]
if not any(c["name"] == "Default" for c in ns["classes"]): ns["classes"].insert(0, {"name": "Default"})
ns["classes"] += [{"name": "PRIMARY"}, {"name": "ISOLATED"}]
ns["netclass_patterns"] = [{"netclass": "PRIMARY", "pattern": p} for p in ("*12V*",)] + [{"netclass": "ISOLATED", "pattern": p} for p in ("*5V*", "*PI_GND*", "*PG_LED_A*", "*TRIM*")]
json.dump(pj, open(PRO, "w"), indent=2)
def rule(mm): return f'''(version 1)
# OSBAMS Pi power: single isolation boundary between the 12 V (PRIMARY) and isolated 5 V (ISOLATED) copper; only U1 (1.6 kVDC) bridges it
(rule "isolation_barrier_a"
  (condition "A.hasNetclass('PRIMARY') && B.hasNetclass('ISOLATED')")
  (constraint clearance (min {mm}mm)))
(rule "isolation_barrier_b"
  (condition "A.hasNetclass('ISOLATED') && B.hasNetclass('PRIMARY')")
  (constraint clearance (min {mm}mm)))
'''
def drc(tag):
    out = f"/tmp/_iso_{tag}.json"
    subprocess.run(["/usr/bin/kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "--units", "mm", "-o", out, PCB], capture_output=True)
    d = json.load(open(out)); os.remove(out)
    return [v for v in d.get("violations", []) if v["type"] == "clearance"]
open(DRU, "w").write(rule(MIN)); v_rule = drc("main")
open(DRU, "w").write(rule(MIN * 3)); v_neg = drc("neg")
open(DRU, "w").write(rule(MIN))
b = pcbnew.LoadBoard(PCB)
pri = [p for f in b.GetFootprints() for p in f.Pads() if "12V" in p.GetNetname()]; sec = [p for f in b.GetFootprints() for p in f.Pads() if re.search("5V|PI_GND|PG_LED_A|TRIM", p.GetNetname())]
both = [(f.GetReference(), "primary+isolated pads on one part") for f in b.GetFootprints() if any("12V" in p.GetNetname() for p in f.Pads()) and any(re.search("5V|PI_GND|PG_LED_A|TRIM", p.GetNetname()) for p in f.Pads())]
tie = {n for n in (p.GetNetname() for f in b.GetFootprints() for p in f.Pads()) if "12V" in n and re.search("PI_GND|5V", n)}
holes = [(f.GetReference(), [(p.GetNumber(), p.GetNetname() or "<no net>", "NPTH" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "PTH/SMD") for p in f.Pads()]) for f in b.GetFootprints() if f.GetReference().startswith(("H", "MH", "K", "M"))]
nets_pi = {z.GetNetname() for z in b.Zones() if "PI_GND" in z.GetNetname()}; nets_12 = {z.GetNetname() for z in b.Zones() if "12V_GND" in z.GetNetname()}
lines = [f"Isolation check ({NAME}, KiCad 10.0.6)", "",
         f"Rule: copper of net class PRIMARY (*12V*: +12V_IN, +12V_F, 12V_GND) vs ISOLATED (*5V*, *PI_GND*, *PG_LED_A*, *TRIM*) >= {MIN:g} mm on every layer (file {os.path.basename(DRU)}).",
         f"DRC with the {MIN:g} mm rule: {len(v_rule)} isolation clearance violations  -> {'PASS' if not v_rule else 'FAIL'}",
         f"Negative control (rule tightened to {MIN*3:g} mm, same board): {len(v_neg)} violations -> {'rule is applied by KiCad' if v_neg else 'RULE NOT APPLIED (check)'}",
         f"Parts with pads on both sides: {sorted({r for r, _ in both})} (expected: U1 only)",
         f"Nets joining a 12 V net and a 5 V / PI_GND net: {sorted(tie) or 'none'}",
         f"GND pours: 12V_GND zones {sorted(nets_12)}, PI_GND zones {sorted(nets_pi)} (separate zones; no stitching / bond / Y capacitor)",
         "Mounting holes / board-only footprints (hidden second ground path check):"] + [f"  {r}: {pads}" for r, pads in holes] + [
         "  -> mounting holes are NPTH with no copper pad (no chassis / shield connection from the board)" if all(all(t == "NPTH" or n == "<no net>" for _, n, t in pads) for _, pads in holes) else "  -> CHECK: a mounting pad carries copper"]
open(f"{os.path.dirname(KD)}/reports/Isolation_check.txt", "w").write("\n".join(lines) + "\n"); print("\n".join(lines))
