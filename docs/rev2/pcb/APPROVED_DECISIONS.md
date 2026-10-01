# Approved decisions (user, 2026-10-01) — plan REV2_SCHEMATIC_PCB_PLAN.md approved

| # | Decision | Status |
|---|---|---|
| 1 | Pi 5 + touchscreen 5 V: dedicated **external** supply/DC-DC module. No converter on the controller PCB. Define connector, protection, grounding, power budget. | Approved — spec in `PI_POWER_ARCHITECTURE.md` |
| 2 | ARM-state sensing on a free STM32 GPIO. ARM stays a hardware series element in the contactor/relay enable path. Firmware sensing = status/diagnostics ONLY; it can never bypass, override or substitute for ARM. | Approved — pin candidate PC10 (confirm with V9) |
| 3 | Final temperature sensor = remote pack-surface TC74 probe **if V1 confirms TC74 is viable**. No redesign before V1. Remote spec: keyed 4-wire connector, 100 nF at the sensor, SDA/SCL test points, optional pull-ups (DNP), ≤100 kHz I²C, short cable. If cable length makes I²C unreliable → STOP and propose another remote-temperature interface. | Approved, conditional on V1 |
| 4 | E-stop sense topology (A: 2nd NC contact, B: opto) stays undecided until V6 confirms the Eaton contact-block NC count. | Open (V6) |

Order of work (fixed): V1–V10 bench → update truth inventory → revise existing KiCad schematic/PCB → ERC/DRC → close all BLOCKER/HIGH → only then generate PCBWay files. `RELEASE_GATES.json` stays all-false until each is evidenced.

## Where the work stands
- Step 1 (V1–V10) is physical and belongs to you at the bench: `BENCH_V1_V10_ONE_PAGE.pdf`. Nothing after it is started: the inventory update, KiCad edits, ERC/DRC and PCBWay files all wait for the filled sheet.
- Drafted ahead without touching KiCad: Pi power spec, ARM_SENSE contract, conditional TC74 remote spec (below and in the other docs).

## ARM_SENSE contract (decision 2)
- Hardware: ARM switch in series after the E-stop in the coil path (unchanged by sensing). A separate sense branch (resistor divider/opto from the switched side, 3V3-safe, ≥ 100 kΩ series so it cannot back-feed the coil path) feeds one GPIO, 100 nF + clamp.
- GPIO: candidate **PC10** (not referenced anywhere in firmware; verify it is unused and reachable on the actual Nucleo wiring — V9). Avoid PA5 (LED), PA2/PA3 (UART), PB8/PB9 (I²C), PC8/PC9, PA0/PA1.
- Firmware: read-only status (`ARM_STATE_ARMED/DISARMED/UNKNOWN`) for the UI and logs. Hard rules, to be unit-tested when implemented: no code path may set LOAD_EN or close K1 on the strength of the sense input; LOAD_EN stays low on any disagreement; sense/relay-feedback mismatch is a diagnostic flag, not a permission. Firmware work is deferred to the revision phase.
- Test point TP_ARM.

## Finding while preparing (affects the KiCad revision)
The current schematic's J5 is only 8 pins: 3V3, GND, SDA, SCL, GPIO_GATE, UART_TX, UART_RX, SPARE_GPIO. **PA0, PA1, PC9 are not on any connector at all**, so the E-stop, K1-feedback and ADC circuits cannot reach the Nucleo as drawn. The revision must widen the Nucleo interface (PA0, PA1, PC9, ARM_SENSE, plus extra GND) — a header or second header, with the wiring checked against the real Nucleo pins in V9.

## Update 2026-10-01 — Rev.2 integrated controller decisions (user)
Q1 direct STM32L476RGT6 · Q2 isolated host (USART2 → ISO7721 → CP2102N → USB-C) · Q3 XDR-75-12 set/verified 12.0 V · power: wide-input buck direct to 3.3 V + 3V3A, no internal 5 V rail · TC74 on I²C2 PB10/PB11 ≤ 100 kHz, INA228 on I²C1 · ARM_SENSE = protected divider (status only) · ESTOP_SENSE = opto, post-E-stop node · RELAY_FB = VO610A downstream of K1, **network not frozen until recomputed from the official datasheet (no assumed CTR)** · ADC divider 75k+75k/10k with no upper clamp able to back-feed 3V3 · relay MOSFET = production SMD logic-level part (not IRLZ44N) · flyback = plain diode + DNP fast-release option (no 27 V commitment) · E-stop baseline = one NC circuit · INA228 ADCRANGE 0, 20 A scale (SHUNT_CAL 1250 after verification) · TC74 baseline, DS18B20/NTC contingency only · order: verify datasheets → schematic → ERC → stop; no routing, no Gerbers. Authoritative document: `Hardware/Rev2_Controller/REV2_CONTROLLER_ARCHITECTURE.md` (rev B). Earlier items in this file about ARM_SENSE sensing hardware and the Rev.1 plan are superseded where they conflict.

## 2026-10-01 — RC1 authoritative build instruction
Manufacturer-PDF access no longer blocks KiCad work; evidence states VERIFIED_LOCAL / USER_RELAYED_MANUFACTURER / UNVERIFIED; manufacturer verification remains a fabrication gate. Deliverable: `Hardware/Rev2_Controller/OSBAMS_Rev2_RELEASE_CANDIDATE_1/` (review only). See its `PCBWAY_RELEASE_CANDIDATE_REPORT.md`.

## 2026-10-01 — EB21A-02-C footprint verified from the manufacturer drawing
Adam Tech drawing EB21A-XX-C rev B (committed: `docs/rev2/pcb/evidence/EB21A-XX-C_drawing_revB.pdf`) read locally: pitch 5.00, recommended hole 1.30 mm, body 10.6 x 8.5 x 10.2 mm, pins 4.00 mm from the back / 4.50 mm from the wire-entry face. Footprint `EB21A-02-C` replaces the provisional one; J1-J4 re-placed, board re-routed, ERC 0, DRC 0 electrical. Not on the drawing (design choices): pad diameter 2.6 mm, courtyard, silkscreen, edge clearance, pin-1 end. Fabrication is NOT authorized by this item.

## 2026-10-01 — RC1.2 (after independent review of RC1.1)
Protection: series surge resistors R41/R42/R43 upstream of the pack-sense TVS diodes. Isolation: >= 1.0 mm host-to-controller copper rule (custom DRC). Pack-level clearance 0.2 mm (IPC-2221B B4 basis). Buck: XDR 12.0 V +/-1 %, max continuous input 14.4 V. IRLML0060 kept (first-article measurements mandatory). Script-generated Gerbers removed; the owner exports final Gerbers from the final PCB in KiCad 10.
