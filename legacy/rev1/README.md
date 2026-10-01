# legacy/rev1 — Rev.1 historical reference only

Archived for Rev.1 reproducibility. **Nothing in Rev.2 may import from here.**

| File | What it is |
|---|---|
| `electronic_load_rev1.py` | Rev.1 `ElectronicLoad` abstraction including `OwonLoad` (OWON OEL1515 over USB-CDC), `ManualLoad`, `SimulatorLoad` and placeholder stubs. |

The OWON OEL1515 is **no longer a supported or target load**. Rev.2 uses the
Keysight/Agilent 6060B via `desktop/equipment/` (see `docs/rev2/`).
`tests/test_rev2_no_legacy_deps.py` fails the build if active code references
OWON or imports `legacy`.
