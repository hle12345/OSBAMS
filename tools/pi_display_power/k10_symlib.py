#!/usr/bin/env python3
"""Extract the project symbols (lib 'OSBAMS_PiPwr') embedded in a generated schematic into <kicad>/OSBAMS_PiPwr.kicad_sym and write sym-lib-table,
so KiCad 10 ERC finds the library. usage: k10_symlib.py <schematic.kicad_sch>"""
import os, sys, re
sch = sys.argv[1]; KD = os.path.dirname(sch); L = "OSBAMS_PiPwr"
t = open(sch).read()
i = t.index("(lib_symbols"); j = i; d = 0
for j in range(i, len(t)):
    d += (t[j] == "(") - (t[j] == ")")
    if d == 0: break
blk = t[i:j + 1]; syms = []; pos = blk.index("(symbol ", 1)
while True:
    m = re.search(r'\(symbol "%s:([^"]+)"' % L, blk[pos:])
    if not m: break
    s0 = pos + m.start(); d = 0
    for k in range(s0, len(blk)):
        d += (blk[k] == "(") - (blk[k] == ")")
        if d == 0: break
    syms.append(blk[s0:k + 1].replace(f'(symbol "{L}:{m.group(1)}"', f'(symbol "{m.group(1)}"', 1)); pos = k + 1
open(os.path.join(KD, L + ".kicad_sym"), "w").write('(kicad_symbol_lib (version 20231120) (generator "osbams") (generator_version "1.0")\n' + "\n".join(syms) + "\n)\n")
open(os.path.join(KD, "sym-lib-table"), "w").write(f'(sym_lib_table\n  (version 7)\n  (lib (name "{L}")(type "KiCad")(uri "${{KIPRJMOD}}/{L}.kicad_sym")(options "")(descr "OSBAMS Pi power project symbols"))\n)\n')
print(len(syms), "symbols ->", L + ".kicad_sym")
