#!/usr/bin/env python3
"""2-D key check of the Pi power interposer against the official Raspberry Pi 5 mechanical drawing (RP-008347-DS-1).
Component boxes were digitised from the drawing at 300 dpi (+-0.3 mm); Pi frame: origin = board top-left corner, +x right, +y down
(header axis y = 3.5 mm, header centre x = 32.5 mm, mounting holes (3.5,3.5) and (61.5,3.5)). The interposer is aligned so its x equals the Pi x."""
import sys, os, re
D = sys.argv[1] if len(sys.argv) > 1 else "."
HDR_X, HDR_Y, BW = 32.5, 3.5, 65.0
POST_OUT = 14.5                      # key post distance outward of the header axis (matches build_interposer.py: YH - y_post)
POSTS_X = [18.5, 43.25]               # interposer x of K1, K2
POST_D = 5.0                         # conservative standoff diameter (hex/round) in mm
BOARD = (0.0, 0.0, 85.0, 56.0)
COMP = {                              # name: (x0, y0, x1, y1) mm, from the drawing
 "A  chip left of centre": (7.1, 7.0, 17.7, 20.2), "B  chip below header": (25.8, 11.9, 40.5, 22.0),
 "C  chip right": (52.3, 15.0, 64.5, 27.1), "D  SoC heat spreader": (24.5, 24.6, 41.7, 41.7),
 "E  small part under header (right)": (55.1, 6.5, 56.8, 9.5), "F  connector by right hole": (65.2, 1.0, 68.2, 7.0),
 "G  connector by right hole (2)": (65.3, 8.3, 69.7, 15.7), "H  feature (o3) by right hole": (60.0, 8.0, 63.0, 11.0),
 "USB/Ethernet stack": (70.8, 1.0, 85.0, 44.0)}
def dist_rect(px, py, r):
    dx = max(r[0] - px, 0, px - r[2]); dy = max(r[1] - py, 0, py - r[3]); return (dx * dx + dy * dy) ** 0.5
out = ["Pi 5 keying check - plan view, from the official mechanical drawing RP-008347-DS-1 (digitised, +-0.3 mm)", ""]
ok = True
out.append("Correct orientation: key posts K at x = " + ", ".join(f"{x}" for x in POSTS_X) + f", {POST_OUT} mm outward of the header axis -> Pi y = {HDR_Y - POST_OUT:.1f} mm (board edge is y = 0)")
for x in POSTS_X:
    y = HDR_Y - POST_OUT; free = y + POST_D / 2 < BOARD[1] - 0.5
    out.append(f"  post at ({x:.1f}, {y:.1f}): {'beyond the Pi edge in free air (PASS)' if free else 'OVER THE BOARD (FAIL)'}"); ok &= free
out.append(""); out.append("Reversed 180 deg about the header centre: x' = 65 - x, y' = 3.5 + 14.5 = 18.0 mm (inboard)")
for x in POSTS_X:
    xr, yr = BW - x, HDR_Y + POST_OUT
    d = min((dist_rect(xr, yr, r) - POST_D / 2, n) for n, r in COMP.items())
    inboard = BOARD[0] < xr < BOARD[2] and BOARD[1] < yr < BOARD[3]
    good = inboard and d[0] >= 1.0
    out.append(f"  post at ({xr:.1f}, {yr:.1f}): over the Pi PCB = {inboard}; clearance of a {POST_D:.0f} mm post to nearest component edge = {d[0]:.1f} mm ({d[1].strip()}) -> lands on bare PCB (PASS)" if good else
               f"  post at ({xr:.1f}, {yr:.1f}): over PCB = {inboard}; nearest component {d[1].strip()} at {d[0]:.1f} mm -> FAIL (would land on/near a component)"); ok &= good
out.append(""); out.append("Hole alignment: interposer M1/M2 at (3.5, 3.5) and (61.5, 3.5) in Pi coordinates = Pi mounting holes (drawing: 58 mm pitch, 3.5 mm from edges, dia 2.7).")
out.append("Interposer plan extent (correct orientation): x 0..65, y from -14.3 to +7.5 mm. Components under it in plan: " + (", ".join(n.strip() for n, r in COMP.items() if r[0] < 65 and r[2] > 0 and r[1] < 7.5 and r[3] > -14.3 and n != "USB/Ethernet stack") or "none") + " (the board floats at the seated gap G above them; height check needs G).")
def plan_gap(r):                      # gap in plan between the interposer rectangle (0..65, -14.3..7.5) and a component box (mm; negative = overlap)
    dx = max(r[0] - 65.0, 0 - r[2], 0); dy = max(r[1] - 7.5, -14.3 - r[3], 0); return (dx * dx + dy * dy) ** 0.5
for n in ("D  SoC heat spreader", "USB/Ethernet stack", "F  connector by right hole", "G  connector by right hole (2)", "C  chip right", "B  chip below header"):
    out.append(f"  plan gap to {n.strip()}: {plan_gap(COMP[n]):.1f} mm")
out.append("  (F, the small connector by the right mounting hole, is ~0.2 mm from the interposer's right edge in plan; the board floats at the seated gap G above it - check its height when G is known. DSI/CSI FFCs are on the left edge at y >= 20 mm and the PoE 2x2 header is at the bottom right: both > 12 mm from the footprint. The Active Cooler/SoC (D) is >= 17 mm away in plan.)")
out.append(""); out.append("RESULT (plan view): " + ("PASS" if ok else "FAIL"))
out.append("Not covered: heights (post length vs seated gap G, header/socket engagement) - need the SSW-120 drawing; optional STEP for a 3-D confirmation.")
txt = "\n".join(out); print(txt)
open(os.path.join(D, "reports", "Pi5_keying_check.txt"), "w").write(txt + "\n")
sys.exit(0 if ok else 1)
