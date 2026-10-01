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
