# 6060B GPIB interface — confirmation checklist

```
6060B_REMOTE_CONTROL = BLOCKED_BY_INTERFACE_CONFIRMATION
```

Nothing in this repo assumes a GPIB path exists. Manual front-panel operation
(`Manual6060B`) remains available.

Confirm which (if any) the SFSU lab has — tick and record asset IDs:

- [ ] USB ↔ GPIB adapter (e.g. a VISA-compatible adapter) — model: ____
- [ ] LAN ↔ GPIB gateway — model/address: ____
- [ ] GPIB-equipped PC — host/card: ____
- [ ] GPIB address of the 6060B (front-panel setting): ____
- [ ] VISA backend installed on the OSBAMS PC; `pip install pyvisa`

When confirmed:
1. Read the official **Agilent 6060B/6063B Operating Manual** and **Electronic Load Family Programming Reference Guide (06060-90005)**.
2. For each entry in `desktop/equipment/drivers/keysight_6060b/commands.py`
   with status `UNVERIFIED`, check the syntax, fix it, set `MANUAL_CONFIRMED`, and note the page.
3. Construct `Keysight6060B(resource="GPIB0::<addr>::INSTR", interface_confirmed=True)`.
4. Run steps J1–J4 in `BENCH_CHECKLIST.md`.

The official PDFs could not be downloaded when the driver was written (network
egress blocked), so only commands seen in public excerpts (`MODE CURR`,
`CURR <n>`, `INP ON|OFF`, `MEAS:CURR?`, `CURR:TLEV`, `TRAN:MODE CONT`) and
IEEE-488.2/SCPI-standard queries are enabled by default.
