# Hardware workstreams: controller PCB vs Pi/display power (private repo)

OSBAMS Rev.2 has **two separate hardware workstreams**. They are separate boards with separate grounds, tools and release gates.

| | Rev.2 controller PCB | Pi/display power distribution board (+ Pi interposer) |
|---|---|---|
| Purpose | STM32L476RG safety controller, INA228, relay/E-stop/ARM chain, isolated USB-serial to the Pi | isolated 5 V supply for the Raspberry Pi 5 and the 10.1" DSI display |
| Location | `Hardware/Rev2_Controller/OSBAMS_Rev2_RELEASE_CANDIDATE_1/` (RC1.2e, frozen) | `OSBAMS_Pi_Display_Power_RevA_RC1/` and `OSBAMS_Pi_Power_Interposer_RevA_RC1/` |
| Generators / checks | `Hardware/Rev2_Controller/design/`, KiCad 10 container `tools/kc10` | `tools/pi_display_power/` (`build_all.sh`, `build_interposer.py`, `rc2_gate.py`, voltage-budget and keying/stack-height checks) |
| Status | release candidate, not bench-validated, not authorized for fabrication | RC1.1 / interposer RC1, **NOT FINAL, NOT authorized for fabrication**; nothing bench-validated |

Rule kept from the controller design: the Pi/display 5 V supply is external to the controller PCB; the controller PCB never carries it.

## Power path (Pi-power board)
`120 VAC → XDR-75-12 → 12 V bus → Pi-power board → RSDW40F-05 (isolated) → 5 V (8 A) → Pi 5 + display`.
There is no STM32, ADC, INA228, relay or safety logic on the Pi-power board, and `PI_GND` is not connected to the 12 V ground.

## Interposer
`OSBAMS_Pi_Power_Interposer_RevA_RC1/`: a keyed 65 × 22 mm board that plugs onto the Pi 5 40-pin header (Samtec SSW-120-01-S-D socket) and takes the 5 V rail through a keyed Molex Micro-Fit connector (+5 V on header pins 2 and 4, GND on 6, 9, 14, 20), replacing the unpolarised housing at the Pi end of the harness.

## Validation status (as recorded in the board READMEs; none of it is bench data)
- 5 V drop budget (≥ 4.85 V at the Pi header at 5 A): closes only with per-unit trim calibration; contact resistance is a 20 mΩ placeholder to be measured on first article.
- KiCad ERC is OPEN (the build container only had KiCad 7); a custom connectivity check passes. DRC is partial (silkscreen/library warnings only). Isolation spacing is partially checked.
- Footprints are library-sourced, not manufacturer-drawing-verified, except the RSDW40F-05 module built from the Mean Well drawing. Interposer keying and stack height pass the plan-view checks against the Pi 5 drawing only.
- `rc2_gate.py` lists what must be verified before an RC2 is generated; RC2 has deliberately not been generated.
- First article (trim calibration, voltage under load, current, harness temperature, socket contact resistance, reversed-fit test) is OPEN.

Details and gate tables: the two board READMEs and `OSBAMS_Pi_Display_Power_RevA_RC1/docs/`. These folders contain generated Gerbers for review only; they do not change the controller PCB, and are not part of the public repository.
