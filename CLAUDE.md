# OSBAMS — project memory for Claude Code sessions

**Rev.2 = SFSU lab-optimized.** Designed ONLY around equipment physically at SFSU:
Agilent/Keysight 6060B load (3–60 V, 60 A, 300 W), EDU34450A reference DMM,
EDU36311A commissioning supply, EDUX1052G scope, EDU33212A generator, Analog
Discovery 2, handheld DMM. Details: `docs/rev2/` (start with `ARCHITECTURE.md`,
`HARDWARE_FREEZE_CANDIDATE.md`, `BENCH_CHECKLIST.md`).

## Hard rules
- Permitted current = min(profile, OSBAMS ceiling 10 A, 60 A, 300 W / V, component limits). 42 V → 7.14 A. Never call it a "60 V / 60 A / 90 A" system. System ceiling is **≤ 44 V, ≤ 10 A (provisional)**; the 6060B rating is the instrument's, not OSBAMS's.
- Invariant: commanded current × conservative pack voltage ≤ 300 W; conservative voltage never decreases (sag can't raise current). Every load command goes through `equipment/capability.py`.
- Layers: firmware hard trip (18.5 A / 60 °C) = protection boundary; desktop/profile limits = operating boundary. Don't force them equal.
- No global minimum battery voltage; cutoff is per profile.
- 6060B remote control is BLOCKED (no confirmed GPIB path; no command VERIFIED against the official Keysight manuals — see `6060B_COMMAND_EVIDENCE.md`). Operations enable only when every command they need is VERIFIED. Manual6060B is the working mode.
- OWON removed (archive: `legacy/rev1/`, never import). Do NOT add Dat Bike, >60 V / MV / HV / EV packs, regenerative cyclers, Bitrode/Arbin/Chroma/Digatron/ITECH drivers.
- Current-sensing redesign deferred (existing ~20 A shunt + INA228 is sufficient for 36–42 V packs).
- Instrument asset IDs / calibration status stay UNKNOWN until read off the instrument. Never claim BENCH_TESTED / HARDWARE_VALIDATED without recorded data.

## Open items
Exact DG57CM suffix, shunt P/N, 12→5 V converter, fuse + holder P/N; fuse (15 A) is below firmware trip (18.5 A) — decide ordering; shunt high/low-side vs PCB; TC74 bring-up (thermal protection unvalidated); read the two official 6060B manuals (www.keysight.com was blocked in the cloud environment).

## Commands
`python3 -m pytest tests` (needs pytest numpy scikit-learn pyserial PySide6 pyqtgraph; `QT_QPA_PLATFORM=offscreen`) · `make -C Firmware/Tests run` · `python3 tools/gen_rev2_docs.py` after editing `commands.py` or `validation.py` (tests fail if the generated docs are stale).
