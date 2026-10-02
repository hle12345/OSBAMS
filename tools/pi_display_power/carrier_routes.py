# executed inside build_carrier_pcb.py: tracks, vias, zones, texts (positions derived from the placed pads)
pp = padpos
# ---------------- primary (+12 V) ----------------
j1, j2p = pp("J_IN", 1), pp("J_IN", 2)
trk("+12V_IN", [j1, (j1[0], 9.0), pp("F1", 1)], 2.0)
tp1 = pp("TP1", 1); trk("+12V_IN", [tp1, (tp1[0], 9.0)], 0.8)
TY = 7.2                                                     # +12V_F trunk (clear of module pin 3 = ON/OFF, no-connect)
f2p = pp("F1", 2); u1p1 = pp("U1", 1)
trk("+12V_F", [f2p, (f2p[0] - 2.5, f2p[1]), (f2p[0] - 2.5, TY), (u1p1[0], TY), u1p1], 2.5)
t1 = pp("TVS1", 1); trk("+12V_F", [t1, (t1[0], TY)], 1.5)
c1 = pp("C1", 1); trk("+12V_F", [c1, (c1[0], TY)], 1.0)
c2 = pp("C2", 1); trk("+12V_F", [c2, (c2[0], TY)], 1.5)
tp2 = pp("TP2", 1); trk("12V_GND", [tp2, (tp2[0] + 2.4, tp2[1])], 0.8); via("12V_GND", tp2[0] + 2.4, tp2[1])
trk("12V_GND", [j2p, (j2p[0], j2p[1] + 2.6)], 2.0); via("12V_GND", j2p[0], j2p[1] + 2.6)
t2 = pp("TVS1", 2); trk("12V_GND", [t2, (t2[0] + 2.4, t2[1])], 1.5); via("12V_GND", t2[0] + 2.4, t2[1])
c1b = pp("C1", 2); trk("12V_GND", [c1b, (c1b[0], c1b[1] + 1.8)], 0.5); via("12V_GND", c1b[0], c1b[1] + 1.8)
# ---------------- secondary (isolated 5 V) ----------------
u4 = pp("U1", 4); f2a = pp("F2", 1); f2b = pp("F2", 2)
trk("5V_ISO_RAW", [u4, (f2a[0], u4[1]), f2a], 2.5)
tp3 = pp("TP3", 1); trk("5V_ISO_RAW", [tp3, (tp3[0], u4[1]), (f2a[0], u4[1])], 0.8)
# 5V_PI: F.Cu band under the module (F2 pad 2 -> Pi pins 2,4 and the branch to the right) + the stripe that feeds TP4 / J_DISP
x2, x4 = pin_xy(2)[0], pin_xy(4)[0]; yb0, yb1 = 55.9, 59.0
zone("5V_PI", pcbnew.F_Cu, [(9.6, yb0), (69.0, yb0), (69.0, yb1), (x4 + 0.95, yb1), (x4 + 0.95, 66.0), (x2 - 1.3, 66.0), (x2 - 1.3, 61.0), (9.6, 61.0)], 1)
zone("5V_PI", pcbnew.F_Cu, [(64.5, 40.0), (69.0, 40.0), (69.0, yb0 + 0.5), (64.5, yb0 + 0.5)], 2)
c4a, c4b = pp("C4", 1), pp("C4", 2)
trk("5V_PI", [c4a, (c4a[0], yb0 + 0.5)], 1.5)
for ref in ("C5", "C6"):
    a_, g_ = pp(ref, 1), pp(ref, 2)
    trk("5V_PI", [a_, (a_[0], yb0 + 0.5)], 1.0); trk("PI_GND", [g_, (g_[0], g_[1] - 1.6)], 0.5); via("PI_GND", g_[0], g_[1] - 1.6)
jd1, jd2 = pp("J_DISP", 1), pp("J_DISP", 2)
trk("5V_PI", [jd1, (jd1[0], jd1[1] + 3.6), (69.0, jd1[1] + 3.6)], 2.5)
r1a, r1b, d1k, d1a = pp("R1", 1), pp("R1", 2), pp("D1", 1), pp("D1", 2)
trk("5V_PI", [r1a, (69.0, r1a[1])], 0.5); trk("PG_LED_A", [r1b, d1a], 0.5); trk("PI_GND", [d1k, (d1k[0] + 1.8, d1k[1])], 0.5); via("PI_GND", d1k[0] + 1.8, d1k[1])
tp5 = pp("TP5", 1); trk("PI_GND", [tp5, (tp5[0] + 1.6, tp5[1])], 0.8); via("PI_GND", tp5[0] + 1.6, tp5[1])
# trim network: module pin 6 (TRIM) -> R3 pad 1 ; R3 pad 2 -> PI_GND (R3 is the trim-UP resistor)
u6 = pp("U1", 6); r3a, r3b = pp("R3", 1), pp("R3", 2)
trk("TRIM", [u6, (u6[0], r3a[1]), r3a], 0.5)
trk("PI_GND", [r3b, (r3b[0], r3b[1] + 1.6)], 0.5); via("PI_GND", r3b[0], r3b[1] + 1.6)
# ground planes (B.Cu): 12V_GND over the primary area, PI_GND over the secondary area and the plug tab; 13.5 mm copper-free lane between them
zone("12V_GND", pcbnew.B_Cu, [(1.5, 1.5), (83.5, 1.5), (83.5, 19.5), (1.5, 19.5)], 0, 0.4)
zone("PI_GND", pcbnew.B_Cu, [(1.5, 33.0), (83.5, 33.0), (83.5, 58.8), (72.0, 58.8), (72.0, 66.5), (8.0, 66.5), (8.0, 58.8), (1.5, 58.8)], 0, 0.4)
TEXTS = [("OSBAMS Pi Power Carrier Rev.B", 42.5, 1.4, 1.2, SIL, 1), ("PRIMARY 12V SIDE", 3.0, 22.0, 1.0), ("12V IN", 74.0, 21.0, 0.9),
         ("ISOLATION BARRIER - NO COPPER CROSSING (13.5 mm lane)", 42.5, 28.0, 0.8, SIL, 1), ("PI SIDE - ISOLATED", 3.0, 36.0, 1.0),
         ("DISPLAY 5V OUT 1=+5V 2=GND", 68.0, 57.0, 0.7), ("PI PIN 1", 6.0, 66.2, 0.7), ("Pi pins: +5V 2,4  GND 6,9,14,20", 22.0, 57.0, 0.7),
         ("K1/K2: M3 x 20 standoffs = key posts, FIT", 3.0, 8.0, 0.7), ("R3: SELECT-ON-TEST TRIM", 30.0, 54.5, 0.7), (REL + " - NOT FOR FAB", 42.5, 66.0, 0.8, SIL, 1)]
