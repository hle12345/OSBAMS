# OSBAMS_Pi_Power_Interposer_RevA — {REL}

Keyed Pi-end interposer for the isolated 5 V supply: Molex Micro-Fit 430450400 (J1) → Samtec SSW-120-01 2 × 20 socket (J2, mounted from the underside) → Raspberry Pi 5 header. **No Gerbers are included; not a fabrication authorization.**

- +5 V on Pi pins **2 and 4**; GND on **6, 9, 14, 20**; the other 34 pins unconnected.
- **Key standoffs K1/K2 (M2.5 × 20 mm) are mandatory**: they prevent the 180° fit that would put +5 V on Pi pin 39 (GND) and GPIO26. Spacers at M1/M2: M2.5 × 11 mm.
- KiCad 10.0.6: ERC 0, DRC 0 (incl. schematic parity), 0 unconnected, 0 footprint errors (`reports/*_kicad10.rpt`).
- Evidence and limits: `docs/Mechanical_verification.md` (Pi 5 drawing, HAT+ geometry, stack height, key), `docs/Keying_analysis.md`, `reports/`.
- Open owner items: orderable Samtec code (plating letter of `-S-D`), Molex terminals/wire for the harness, physical reversed-fit test with a real Pi 5 (first article).
- Project libraries: `kicad/OSBAMS_PiPwr.pretty`, `kicad/OSBAMS_PiPwr.kicad_sym`.
