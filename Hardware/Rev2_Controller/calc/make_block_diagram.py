#!/usr/bin/env python3
"""Rev.2 controller block diagram (merged decisions) -> ../REV2_BLOCK_DIAGRAM.svg/.png"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
fig, ax = plt.subplots(figsize=(16, 11)); ax.set_xlim(0, 160); ax.set_ylim(0, 110); ax.axis("off")
EXT, PCB = "#fff3d6", "#e6eefb"


def box(x, y, w, h, text, fc, fs=7.6, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1", fc=fc, ec="#555", lw=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal")


def arrow(x1, y1, x2, y2, label=None, c="#333"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="->", color=c, lw=1))
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.8, label, fontsize=6.5, color=c, ha="center")


ax.text(1, 108, "OSBAMS Rev.2 Controller — block diagram (merged architecture, design phase)", fontsize=13, fontweight="bold")
ax.text(1, 105.5, "Battery discharge current NEVER enters this PCB:  Battery → XT60 → 15 A fuse → disconnect → K1 contacts → RSA-20-50 → 6060B → battery return.   Pi requests, STM32 authorizes.  E-stop/ARM are in the 12 V COIL chain only.", fontsize=7.5, color="#444")
ax.add_patch(FancyBboxPatch((38, 6), 84, 96, boxstyle="round,pad=0.4", fc="none", ec="#222", lw=1.6, ls="--"))
ax.text(40, 99.5, "CONTROLLER PCB (4-layer, solid GND plane)", fontsize=9, fontweight="bold")
# external left
ext_l = [("XDR-75-12\n12 V control supply\n(set & verify 12.0 V)", 90), ("Eaton M22-PV-K02\nE-STOP (NC)", 76), ("C&K T102SHZQE\nARM switch", 64),
         ("Durakool DG57CM-5021-76-1012-R\nK1 coil 12 V", 52), ("RSA-20-50 shunt (2.5 mΩ)\nKelvin IN+ / IN−", 40), ("Pack upstream of K1 (PACK_INA, PACK_ADC)\nrelay output (RELAY_OUT), GND_SENSE", 26),
         ("Remote TC74A5-3.3VAT probe\n+ 100 nF, ≤1.5 m, ≤100 kHz", 12)]
for t, y in ext_l:
    box(2, y, 30, 9, t, EXT, 7)
# internal boxes
box(42, 88, 34, 9, "12 V INPUT\nJ1 → F1 1 A → Schottky\n→ SMBJ15A → +12V", PCB)
box(80, 88, 20, 9, "RAILS\nbuck → 3V3 (no 5 V)\n→ ferrite → 3V3A", PCB)
box(103, 88, 17, 9, "LEDs: 3V3,\nPA5, coil", PCB)
box(42, 70, 34, 14, "COIL SAFETY CHAIN (hardware)\n+12V → E-STOP → ARM → coil\n→ Q1 (SMD, low side)\n220 Ω · 10 k pull-down · flyback\n(+ DNP fast-release link)", PCB, 7)
box(42, 54, 34, 12, "STATUS SENSING (read-only)\nESTOP: VO610A (post-E-stop node)\nRELAY_FB: VO610A (after K1)\nARM: divider 270k/100k", PCB, 7)
box(42, 38, 34, 12, "INA228 (I²C1, 0x40)\nIN+/IN− 2×10 Ω + 100 nF, TVS\nVBUS from PACK_INA · ADCRANGE=0", PCB)
box(42, 22, 34, 12, "ADC CROSS-CHECK → PA1\n75k+75k / 10k · 1 k · 100 nF\nGND-only clamp · VREFINT correction", PCB)
box(42, 9, 34, 10, "TEMP INTERFACE (I²C2 PB10/PB11)\n100 Ω · ESD · 4.7 k pull-ups (DNP-able)\nSDA2/SCL2 test points", PCB)
box(80, 50, 40, 34, "STM32L476RGT6 (direct, LQFP-64)\nsafety authority\n\nPC8 LOAD_EN (default low)\nPA0 ESTOP_SENSE (low = healthy)\nPC9 RELAY_FB (active low)\nPC10 ARM_SENSE (high = armed)\nPA1 ADC_SENSE\nPB8/PB9 I²C1 (INA228)   PB10/PB11 I²C2 (TC74)\nPB0 INA_ALERT   PA5 heartbeat\nPA2/PA3 USART2\nPA13/PA14/PB3 SWD · NRST · BOOT0\nHSI16 → PLL 80 MHz, no crystal", PCB, 7.4, True)
box(80, 36, 18, 12, "ISO7721\nUART isolator", PCB)
box(102, 36, 18, 12, "CP2102N\nUSB-UART + ESD", PCB)
box(80, 20, 40, 12, "SWD J9 (2×5 1.27 mm) · reset · BOOT0 jumper", PCB)
box(80, 8, 40, 9, "TEST POINTS (24) · fiducials · 4×M3 · silkscreen/revision", PCB)
# external right
box(126, 34, 31, 14, "Raspberry Pi 5 + touchscreen\nown external 5 V supply\nrequests actions only", EXT, 7.4)
box(126, 18, 31, 9, "SWD programmer\n(Nucleo ST-LINK as probe)", EXT, 7.4)
# arrows
for y in (94.5, 80.5, 70, 58, 46, 30, 17):
    pass
arrow(32, 94.5, 42, 94.5, "12 V"); arrow(76, 92.5, 80, 92.5); arrow(100, 92.5, 103, 92.5)
arrow(32, 80.5, 42, 77, "E-stop"); arrow(32, 68.5, 42, 74, "ARM"); arrow(42, 72, 32, 58, None, "#a05a00")
arrow(76, 76, 80, 76, "PC8"); arrow(76, 60, 80, 64, "PA0/PC9/PC10")
arrow(32, 44.5, 42, 44.5, "IN+ IN−"); arrow(76, 44, 80, 55, "I²C1")
arrow(32, 30.5, 42, 28, "PACK"); arrow(76, 28, 80, 53, "PA1")
arrow(32, 16.5, 42, 14.5, "I²C2"); arrow(76, 14, 80, 52, "I²C2")
arrow(91, 50, 91, 48, None); arrow(98, 42, 102, 42); arrow(120, 42, 126, 42, "USB-C")
arrow(126, 22, 118, 25, "SWD")
plt.savefig(os.path.join(HERE, "..", "REV2_BLOCK_DIAGRAM.png"), dpi=110, bbox_inches="tight")
plt.savefig(os.path.join(HERE, "..", "REV2_BLOCK_DIAGRAM.svg"), bbox_inches="tight")
