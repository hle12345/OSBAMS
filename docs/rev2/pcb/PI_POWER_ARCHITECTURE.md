# Pi 5 + 10.1" display power — separate architecture decision (OPEN)

Not part of the controller-PCB revision. No converter is added to the PCB on the strength of the audit. Decision belongs to the user after V9/V10-adjacent facts are known (how the Pi is powered today, rail dip at boot).

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
