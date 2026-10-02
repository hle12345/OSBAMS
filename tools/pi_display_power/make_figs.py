#!/usr/bin/env python3
import sys, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
import os
D = sys.argv[1]; REL = os.environ.get('REL', 'RC1')

def box(ax, x, y, w, h, t, fc="#eef3ff", ec="#1f3864", fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.4))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")
def line(ax, pts, c="k", lw=2, ls="-"): ax.plot(*zip(*pts), color=c, lw=lw, ls=ls, solid_capstyle="round")

# 1. System / Pi power wiring diagram
fig, ax = plt.subplots(figsize=(14, 7.5)); ax.set_xlim(0, 28); ax.set_ylim(0, 15); ax.axis("off")
ax.set_title(f"OSBAMS Pi/Display Power Rev.A - system and Pi power wiring ({REL})", fontsize=13, fontweight="bold")
box(ax, 0.3, 6, 3.4, 3, "120 VAC\nMean Well\nXDR-75-12\n12 V bus", "#fff4d6", "#8a6d00", 9, True)
ax.add_patch(Rectangle((5.6, 9.4), 6.8, 4.4, fc="#e8f5e9", ec="#2e7d32", lw=1.4)); ax.text(9, 13.4, "BRANCH 1: OSBAMS Rev.2 controller PCB #1", ha="center", fontsize=9, fontweight="bold")
ax.text(9, 11.6, "STM32 / INA228 / relay logic\nISO7721 data isolation to Pi\n(PCB #1 ground = 12V_GND)", ha="center", va="center", fontsize=8.5)
ax.add_patch(Rectangle((5.6, 0.6), 22, 8.2, fc="#fdecea", ec="#c62828", lw=1.4, ls="--"))
ax.text(6, 8.35, "BRANCH 2: PCB #2  OSBAMS_Pi_Display_Power_RevA", fontsize=9, fontweight="bold", va="top")
box(ax, 6.2, 4.2, 2.2, 2.2, "J_IN\nMicro-Fit\n430450200", fs=8)
box(ax, 9.2, 4.2, 1.6, 2.2, "F1\n8 A\ntime-lag", "#fff", fs=8); box(ax, 11.4, 4.2, 1.6, 2.2, "TVS1\nSMBJ15A\nC1/C2", "#fff", fs=7.5)
box(ax, 13.8, 3.2, 4.6, 4.2, "U1  RSDW40F-05\n9-36 V in -> 5 V / 8 A\n1.6 kVDC isolation\nON/OFF, TRIM: unused", "#e3f2fd", fs=8.5, bold=True)
ax.plot([16.1, 16.1], [1.2, 8.3], color="#c62828", lw=2.5, ls=(0, (6, 4))); ax.text(16.15, 1.0, "isolation barrier", fontsize=7.5, color="#c62828", ha="center")
box(ax, 19.2, 4.2, 1.6, 2.2, "F2\n8 A", "#fff", fs=8); box(ax, 21.2, 4.2, 2.4, 2.2, "C4 680 uF\nC5 10 uF\nC6 100 nF\nPG LED", "#fff", fs=7.5)
box(ax, 24.2, 3.6, 3.2, 3.4, "J_OUT\n430450400\n1,2 = +5V_PI\n3,4 = PI_GND", "#fff", fs=8)
line(ax, [(3.7, 7.5), (6.2, 5.9)], "#c62828"); line(ax, [(3.7, 7.5), (5.6, 11)], "#c62828"); line(ax, [(3.7, 7.5), (5.6, 11)], "#c62828")
ax.text(4.0, 8.4, "+12 V / GND", fontsize=8)
for a, c in [((8.4, 5.3), (9.2, 5.3)), ((10.8, 5.3), (11.4, 5.3)), ((13.0, 5.3), (13.8, 5.3)), ((18.4, 5.3), (19.2, 5.3)), ((20.8, 5.3), (21.2, 5.3)), ((23.6, 5.3), (24.2, 5.3))]: line(ax, [a, c], "#c62828")
# harness to Pi
box(ax, 20.0, 10.6, 7.6, 3.6, "RASPBERRY PI 5 (GPIO header)\n5V pins 2 & 4   |   GND 6, 9, 14, 20 (via keyed interposer)\nUSB-C power input: NOT connected\nPSU_MAX_CURRENT=5000 (after bench checks)", "#f3e5f5", "#6a1b9a", 8.5, True)
line(ax, [(25.8, 7.0), (25.8, 10.6)], "#2e7d32", 3); ax.text(26.0, 8.8, "crimped keyed harness\n4x 16 AWG, <=150 mm\nkeyed interposer\n(no Dupont jumpers)", fontsize=8, color="#2e7d32")
box(ax, 14.0, 10.6, 5.2, 3.6, "Waveshare 10.1\" DSI display\n22-pin DSI to Pi (video/data)\n5 V / GND from J_DISP (direct,\nsame isolated 5 V domain)", "#fff3e0", "#e65100", 8.5)
line(ax, [(19.2, 12.4), (20.0, 12.4)], "#e65100", 2)
box(ax, 24.2, 1.0, 3.2, 2.0, "J_DISP\n430450200\n1=+5V_PI  2=PI_GND", "#fff3e0", "#e65100", fs=7.5)
line(ax, [(27.4, 2.0), (27.9, 2.0), (27.9, 14.6), (11.6, 14.6), (11.6, 12.4), (14.0, 12.4)], "#e65100", 2, "--")
ax.text(12.0, 14.75, "display 5 V feed (J_DISP -> display, separate from the Pi branch)", fontsize=7.5, color="#e65100")
ax.text(0.3, 0.2, "PI_GND is isolated from 12V_GND. Do not connect the isolated 5 V ground to the controller ground.", fontsize=9, color="#c62828", fontweight="bold")
fig.savefig(f"{D}/docs/Pi_power_wiring_diagram.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{D}/docs/Pi_power_wiring_diagram.pdf", bbox_inches="tight"); plt.close(fig)

# 2. Harness drawing
fig, ax = plt.subplots(figsize=(14, 6.5)); ax.set_xlim(0, 28); ax.set_ylim(0, 13); ax.axis("off")
ax.set_title(f"5 V harness: J_OUT (Micro-Fit 3.0, 4 ckt) -> Raspberry Pi 5 GPIO header   [{REL} - terminal and wire part numbers to be confirmed]", fontsize=12, fontweight="bold")
box(ax, 0.5, 4.5, 5.2, 4.2, "Molex 43025-0400\nreceptacle housing\n(mates 430450400)\nkeyed / latched", "#e3f2fd", fs=9)
for i, (lab, c) in enumerate([("1  +5V_PI (red)", "#c62828"), ("2  +5V_PI (red)", "#c62828"), ("3  PI_GND (black)", "k"), ("4  PI_GND (black)", "k")]):
    y = 8.0 - i * 1.1; line(ax, [(5.7, y), (21.5, y)], c, 3.5); ax.text(6.0, y + 0.25, lab, fontsize=8.5, color=c)
box(ax, 21.5, 3.6, 5.5, 5.6, "KEYED INTERPOSER J1\nMicro-Fit 430450400\n2x20 socket on Pi header\n5V: pins 2,4  GND: 6,9,14,20\nkey standoffs (3D check)", "#f3e5f5", "#6a1b9a", 9)
ax.text(12, 2.6, "Wire: 16 AWG stranded silicone preferred (18 AWG min), length <= 150 mm, twisted pairs per rail.\n16 AWG 1:1 to the interposer, 43025-0400 housings both ends (Molex 43030 terminals - confirm AWG range).\nCircuit 1+2 = +5 V pair (outer row), 3+4 = GND pair (inner row) - Molex dual-row numbering runs along rows.\nKey: housing is polarised - cannot be mated backwards. Mark pin 1 on harness label.\nPI USB-C must not be connected to any power source when this harness is fitted.", ha="center", va="top", fontsize=9)
fig.savefig(f"{D}/docs/Harness_drawing.png", dpi=150, bbox_inches="tight"); fig.savefig(f"{D}/docs/Harness_drawing.pdf", bbox_inches="tight"); plt.close(fig)
print("figs ok")
