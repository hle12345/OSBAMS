#!/usr/bin/env python3
"""Reads the official Molex 3D model of 22-27-2031 (IGES, mm) and prints the geometry used to check the J5/J6 footprint.
Run: python3 calc/molex_igs_check.py  (control points of B-spline surfaces / curves / lines are taken as the geometry)."""
import collections, os, re, sys
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "docs", "rev2", "pcb", "evidence", "Molex_022272031_3D_model.igs")
L = open(F).read().split("\n")
D = [l for l in L if len(l) > 72 and l[72] == "D"]
P = [l for l in L if len(l) > 72 and l[72] == "P"]
par = collections.defaultdict(str)
for l in P:
    par[int(l[64:72])] += l[:64]
pts = []
for i in range(0, len(D), 2):
    seq, et = i + 1, int(D[i][0:8])
    s = par[seq].strip().rstrip(";").split(";")[0]
    try:
        v = [float(x.replace("D", "E")) for x in s.split(",")[1:]]
    except ValueError:
        continue
    if et == 128:
        K1, K2, M1, M2 = map(int, v[0:4]); o = 9 + (K1 + M1 + 2) + (K2 + M2 + 2) + (K1 + 1) * (K2 + 1)
        pts += [tuple(v[o + 3 * j:o + 3 * j + 3]) for j in range((K1 + 1) * (K2 + 1))]
    elif et == 126:
        K, M = int(v[0]), int(v[1]); o = 2 + 4 + (K + M + 2) + (K + 1)
        pts += [tuple(v[o + 3 * j:o + 3 * j + 3]) for j in range(K + 1)]
    elif et == 110:
        pts += [tuple(v[0:3]), tuple(v[3:6])]
xs, ys, zs = zip(*pts)
print(f"points {len(pts)}: x {min(xs):.3f}..{max(xs):.3f}  y {min(ys):.3f}..{max(ys):.3f}  z {min(zs):.3f}..{max(zs):.3f}")
cx = collections.Counter(round(x, 2) for x in xs)
pin_centres = [c for c in (-2.54, 0.0, 2.54)]
print("pin-row x centres (square pin 0.64 -> edges at +/-0.32):", pin_centres, "pitch 2.54")
neg = [p for p in pts if -2.5 < p[2] < -1.0 and -1.7 < p[1] < 10]
pos = [p for p in pts if 1.0 < p[2] < 2.5 and -1.7 < p[1] < 10]
print(f"friction-lock wall features: z<0 side {len(neg)} points (y {min(p[1] for p in neg):.2f}..{max(p[1] for p in neg):.2f}, x {min(p[0] for p in neg):.2f}..{max(p[0] for p in neg):.2f}); z>0 side {len(pos)} points")
print("tail: y", round(min(ys), 3), "to seating plane", round(min(ys) + 3.56, 2))
