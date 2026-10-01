# Pi-end connector — selection requirements (NOT YET SELECTED)

No exact MPN is chosen. Choosing one without its published per-contact current and contact-resistance rating would repeat the placeholder problem, and the manufacturer datasheets are not reachable from the build environment. The connector must be selected from a datasheet and entered in `tools/pi_display_power/datasheet_inputs.json` (`pi_end_connector_mpn`, `pi_end_contact_max_mohm`).

## Electrical (from `Voltage_drop_budget.md`)
- Published contact resistance **<= 10 mOhm per contact** (design target). Hard ceiling **~16 mOhm** — above that no single trim setpoint meets both 4.85 V @ 5 A and 5.25 V no-load (assuming +-2 % RSDW tolerance, unverified).
- Published current rating **>= 3 A per contact** at the specified temperature rise (5 A split over 2 pins per rail = 2.5 A each, plus 0.5 A margin; >= 5 A/contact preferred).
- Use **both** Pi 5 V pins (2 and 4) and **>= 2 GND pins** (6 and 9); more GND pins (14, 20) welcome.

## Mechanical
- Female contacts for the Pi's 2.54 mm male GPIO pins (pins 1-10 area), crimped to **16 AWG** (<=150 mm) wire; crimp tool and wire range published by the manufacturer. No Dupont/jumper hardware, no hand-soldered pin sockets.
- Housing with positive retention/friction lock; polarisation by housing shape or a keyed shell where possible (the Pi header itself is unkeyed - mark pin 1 and fit a label).
- Cavities for unused positions (1, 3, 5, 7, 8, 10) left empty; confirm the housing allows partial population and does not short adjacent GPIO pins (3V3 pin 1, GPIO pins 3, 5, 8).
- Contact plating compatible with the Pi's header pin plating (confirm Pi 5 header plating).
- Height clearance over the Pi 5 / Waveshare display flex.

## Open question for you
Provide the chosen Pi-end connector datasheet (or a shortlist of MPNs) and I will enter the numbers, re-run the budget, and rebuild the harness drawing and BOM. A bench pull-out/temperature-rise test of the assembled 5 A harness remains a release gate.
