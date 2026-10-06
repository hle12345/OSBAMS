# RevC routing (executed inside build_carrier_pcb.py; positions derived from the placed pads). Layout-only change of RevB: same nets, same netclasses, same 10 mm isolation rule.
pp = padpos
# ---------------- primary (+12 V): J_IN top right, F1, TVS1 in the right column, C1/C2 under the module's primary end ----------------
j1 = pp("J_IN", 1); f1a, f1b = pp("F1", 1), pp("F1", 2); u1p1 = pp("U1", 1)
trk("+12V_IN", [j1, (60.8, j1[1]), (60.8, 16.0), (f1a[0], 16.0), f1a], 2.0)
tp1 = pp("TP1", 1); trk("+12V_IN", [(60.8, tp1[1]), tp1], 0.8)
TX = 52.9                                                       # +12V_F trunk x (module end 51.9, F1 pad edge 54.6)
trk("+12V_F", [f1b, (TX, f1b[1]), (TX, u1p1[1]), u1p1], 2.5)
t1 = pp("TVS1", 1); trk("+12V_F", [f1b, t1], 1.5)
trk("+12V_F", [(TX, f1b[1]), (TX, 33.0), (pp("C2", 1)[0], 33.0), pp("C2", 1)], 1.5)
c1a, c1b = pp("C1", 1), pp("C1", 2); trk("+12V_F", [c1a, (c1a[0], 33.0)], 0.8)
trk("12V_GND", [c1b, (c1b[0], c1b[1] - 1.6)], 0.8); via("12V_GND", c1b[0], c1b[1] - 1.6)
t2 = pp("TVS1", 2); trk("12V_GND", [t2, (t2[0] + 3.0, t2[1])], 1.5); via("12V_GND", t2[0] + 3.0, t2[1])
tp2 = pp("TP2", 1); trk("12V_GND", [tp2, (tp2[0], tp2[1] + 2.0)], 0.8); via("12V_GND", tp2[0], tp2[1] + 2.0)
# ---------------- secondary (isolated 5 V) ----------------
u4 = pp("U1", 4); f2a, f2b = pp("F2", 1), pp("F2", 2)
# 5V_ISO_RAW: one F.Cu pour from module pin 4 (top left) down under the module to F2 pad 1 (about 5.7 mm wide: left edge clear of the PI_GND pad 5, no track neck)
zone("5V_ISO_RAW", pcbnew.F_Cu, [(2.6, 2.9), (10.9, 2.9), (10.9, 28.3), (6.62, 28.3), (6.62, 30.2), (4.9, 30.2), (4.9, 6.2), (2.6, 6.2)], 1)
# 5V_PI: F.Cu pour from F2 pad 2 over J_DISP pad 1, C4/C5/C6, R1, TP4 down to Pi header pins 2 and 4
x2, x4 = pin_xy(2)[0], pin_xy(4)[0]
zone("5V_PI", pcbnew.F_Cu, [(9.0, 29.2), (33.0, 29.2), (33.0, 43.3), (x4 + 1.2, 43.3), (x4 + 1.2, 45.95), (x2 - 1.3, 45.95), (x2 - 1.3, 43.3), (9.0, 43.3)], 1)
for ref in ("C5", "C6"):
    g_ = pp(ref, 2); trk("PI_GND", [g_, (g_[0], g_[1] - 1.6)], 0.5); via("PI_GND", g_[0], g_[1] - 1.6)
r1b, d1a, d1k = pp("R1", 2), pp("D1", 2), pp("D1", 1)
trk("PG_LED_A", [r1b, d1a], 0.5); trk("PI_GND", [d1k, (d1k[0] + 1.6, d1k[1])], 0.5); via("PI_GND", d1k[0] + 1.6, d1k[1])
tp5 = pp("TP5", 1); trk("PI_GND", [tp5, (tp5[0] - 1.6, tp5[1])], 0.8); via("PI_GND", tp5[0] - 1.6, tp5[1])
u6 = pp("U1", 6); r3a, r3b = pp("R3", 1), pp("R3", 2)
trk("TRIM", [u6, r3a], 0.5)
trk("PI_GND", [r3b, (r3b[0] - 1.1, r3b[1] + 1.0)], 0.5); via("PI_GND", r3b[0] - 1.1, r3b[1] + 1.0)
# ground pours (B.Cu): 12V_GND over the primary area (x >= 43.5), PI_GND over the secondary area (x <= 32.5): 11 mm copper-free lane between them
zone("12V_GND", pcbnew.B_Cu, [(43.5, 1.5), (63.5, 1.5), (63.5, 42.5), (43.5, 42.5)], 0, 0.4)
zone("PI_GND", pcbnew.B_Cu, [(6.0, 1.5), (32.5, 1.5), (32.5, 49.0), (1.5, 49.0), (1.5, 29.3), (6.0, 29.3), (6.0, 17.5), (1.5, 17.5), (1.5, 11.5), (6.0, 11.5)], 0, 0.4)   # bay at module pin 5 (PI_GND)
TEXTS = [("ISO LANE", 33.8, 30.0, 0.8), ("NO COPPER", 33.6, 31.6, 0.8), (REL + " NOT FOR FAB", 33.4, 41.8, 0.8),
         ("OSBAMS Pi Power Carrier Rev.C", 26.4, 8.0, 1.3, "B", 1), ("9-36 V IN > ISOLATED 5 V 8 A > Pi + DISPLAY", 26.4, 11.5, 0.8, "B", 1),
         ("ISOLATED 5 V SIDE", 14.0, 20.0, 0.8, "B", 1), ("PRIMARY 12 V SIDE", 47.0, 20.0, 0.8, "B", 1), ("RSDW40F-05 1.6 kVDC", 26.4, 22.5, 0.8, "B", 1)]
