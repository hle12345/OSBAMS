# Pi 5 + 10.1" display power — DECIDED: dedicated external supply (user, 2026-10-01)

Not part of the controller-PCB revision. **Decision: option A.** The precision controller board carries no Pi/display switching supply. The specification below is what the external supply must meet; the comparison that led to it is kept underneath.

Load: Pi 5 needs a 5 V / up to ~5 A source (27 W class); display adds ~1 A. Total ≈ 6 A at 5 V ≈ 30 W; from 12 V a buck draws ≈ 2.8 A at ~90 % efficiency.

| Criterion | A. Dedicated external 5 V supply/module (own enclosure/rail) | B. Converter on the controller PCB from the 12 V rail |
|---|---|---|
| Noise / measurement integrity | Switching noise stays away from INA228, ADC divider, TC74 and I²C; galvanic option available | Switcher ripple and 3 A step loads on the same 12 V and ground as the safety electronics; ground return error into the ADC/INA228 reference |
| Thermal load | Dissipation off-board | ~3 W on a 2-layer 80 mm board near TC74; needs heatsink/copper |
| 12 V rail budget | Coil + safety only (≈ 0.15 A) → XDR-75-12 headroom unchanged | +2.8 A on the XDR-75-12 and on D3/J1/tracks (needs 3 A-rated parts, wider tracks) |
| Serviceability | Swap the supply without touching the safety PCB; Pi brown-outs don't involve the safety board | PCB rework to service; failure of converter can drop the 12 V rail or short it |
| BOM / design risk | Off-the-shelf certified 5 V/5 A (e.g. official Pi 27 W PD or DIN-rail 5 V) — near zero | New high-current buck (inductor, layout, EMI), MPN selection, validation burden before release; delays PCBWay gates |
| Fault containment | Pi and safety board independent; E-stop/relay path not shared with Pi load | Pi inrush could trip TVS/coil droop → spurious relay behavior |
| Cost | One more supply to buy | Fewer boxes, but BOM + layout + test effort |

**Recommendation (not a decision):** A. Keep 5 V off the safety PCB; the Nucleo is powered over USB (as in Rev.1) or the PCB exposes at most a low-current 5 V pin header. Revisit B only if the enclosure forces a single input. Ground bonding (V10/G-13) must define exactly one bond point either way.

## Specification for the external 5 V supply (decision 1)
**Power budget.** Pi 5 5 V / 5 A (25 W) + 10.1" touchscreen ≈ 1 A (5 W; confirm the actual model's rating) → size the supply ≥ 5 V / 6 A (30 W) or, if the display has its own adapter, Pi 27 W PD (5.1 V / 5 A) plus a separate display feed. Peak USB-port budget on the Pi is not budgeted from the controller. Record the purchased model in `HARDWARE_ACCEPTANCE_RECORD.md`.
**Source.** Mains-derived certified module (Pi 27 W PD adapter, or a DIN-rail/enclosed 5 V ≥ 6 A) — NOT the 12 V rail of the safety supply and not the pack. The XDR-75-12 keeps only coil/safety/controller loads.
**Connector.** Pi: USB-C (PD supply) or 2-pin locking header/screw terminal from the module straight to the Pi; display per its own connector. Nothing from this path is routed through the controller PCB. Keyed/polarised, rated ≥ 7 A at 5 V if wired.
**Protection.** Fuse/PTC or the module's own OCP in the 5 V line (≤ 8 A); wire ≥ 18 AWG, short; reverse protection by connector polarisation (no diode in the high-current path).
**Grounding.** Pi 0 V is NOT bonded to pack-negative/controller GND at the supply. The only link is the host data link: use USB (Nucleo ST-LINK VCP) or UART with galvanic isolation if V10 shows a second ground path. One single bond point system-wide (G-13); the 5 V supply return stays floating or bonds at that same point, never a second one. Keep the 5 V cable away from the shunt/ADC sense wiring.
**Measurement integrity.** Verify on the bench (V10-style): no ripple/dip on 3V3 or the ADC reading when the Pi boots and the display backlight steps.
**Controller side.** Nucleo is powered over its USB link or its own 5 V pin from a low-current source, never from the Pi's 5 A path.
