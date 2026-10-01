# Rev.2 baseline

| Item | Value |
|---|---|
| System / desktop / firmware version | 2.0.0-dev1 |
| Protocol / schema | 1 / 6 (+ `calibration_records` table by `migrate()`) |
| OSBAMS operating ceiling (provisional) | 10 A / 44 V (`config.SAFETY_MAX_CURRENT_A`, `OSBAMS_VALIDATED_MAX_VOLTAGE_V`) |
| Supported battery class | lithium-ion (NMC/NCA/LFP), ~10S, ~30–42 V |
| Equipment | 12 roles — `SFSU_EQUIPMENT_MATRIX.md` |
| 6060B envelope (instrument) | 3–60 V, 60 A, 300 W |
| 6060B remote control | BLOCKED_BY_INTERFACE_CONFIRMATION |
| Hardware | unbuilt / unvalidated |

Host tests at this baseline:
- `python3 -m pytest tests` — 158 passed (Rev.2 equipment, orchestrator, dashboard wiring under offscreen Qt, protocol cross-language, scoring, suitability). Needs `pytest numpy scikit-learn pyserial PySide6 pyqtgraph`.
- `make -C Firmware/Tests run` — all 12 C test binaries run, exit 0.

Status: orchestrator/dashboard are host- and simulator-tested only. 6060B remote control blocked (no confirmed GPIB path; no command VERIFIED). **Nothing is BENCH_TESTED or HARDWARE_VALIDATED**; next work is `BENCH_CHECKLIST.md`.

Fixed while establishing the baseline (pre-existing, unrelated to Rev.2 features):
tests assumed a different checkout layout (`services` on the root path, lowercase
`firmware/`, `protocol_version.h` under `Core/Inc`, C harness path). The
config-sync test now asserts desktop operating limits are at or below the
firmware hard trips: the firmware trip (18.5 A / 60 C) now mirrors `config.FIRMWARE_HARD_TRIP_*` exactly while the desktop operating ceiling (10 A / 50 C) is a separate, lower number. Also fixed: `OsbamsSample.time_s` was missing and the dashboard's `_finalize_test` used a scoring API that no longer exists; both are corrected.

Physical validation: `BENCH_CHECKLIST.md` — every step NOT_RUN.

Rev.2 scope cleanup at this baseline: NiMH/LTO chemistries, OWON, Dat Bike, MV/HV/EV and cycler concepts removed from active code (tested: `TestRev2ScopeCleanup`); simulator scenarios are 36–44 V lithium-ion only; the orchestrator gained an explicit hardware safety check; `HP 34401A` cross-check records and the 12-role equipment matrix were added.
