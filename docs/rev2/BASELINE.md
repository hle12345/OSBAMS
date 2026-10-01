# Rev.2 baseline

| Item | Value |
|---|---|
| System / desktop / firmware version | 2.0.0-dev1 |
| Protocol / schema | 1 / 6 (+ `calibration_records` table by `migrate()`) |
| OSBAMS validated current limit | 10 A (`config.SAFETY_MAX_CURRENT_A`) |
| 6060B envelope (instrument) | 3–60 V, 60 A, 300 W |
| 6060B remote control | BLOCKED_BY_INTERFACE_CONFIRMATION |
| Hardware | unbuilt / unvalidated |

Host tests at this baseline:
- `python3 -m pytest tests` — 113 passed (includes 41 new Rev.2 tests; builds and runs the C protocol harness).
- `make -C Firmware/Tests run` — all 12 C test binaries run, exit 0.

Fixed while establishing the baseline (pre-existing, unrelated to Rev.2 features):
tests assumed a different checkout layout (`services` on the root path, lowercase
`firmware/`, `protocol_version.h` under `Core/Inc`, C harness path). The
config-sync test now asserts desktop operating limits are at or below the
firmware hard trips instead of equal to them, and asserts there is no global
minimum voltage.

Physical validation: see `PHYSICAL_VALIDATION_PLAN.md` — all NOT RUN.
