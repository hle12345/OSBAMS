# First battery test procedure — Ninebot NEB1002-H (36 V, 5.2 Ah)

**Status: procedure only. Nothing here has been run; no result is claimed.** BENCH_TESTED may be
recorded only after the measurements in this procedure exist, with data stored (see `BENCH_CHECKLIST.md`,
`ValidationLog`). Use `HARDWARE_ACCEPTANCE_RECORD.md` and `CALIBRATION_RECORD_TEMPLATE.md` alongside this document.

```
Ninebot 36 V pack → XT60 → fuse → disconnect → relay → shunt → OSBAMS (INA228 / ADC / TC74) → Agilent 6060B → pack −
Reference: Keysight EDU34450A (voltage always; current in series only where stated)
Observation: Keysight EDUX1052G (timing / transients)
```

Measure and store: voltage, current, power, temperature, Ah, Wh, cutoff, recovery — then compare
OSBAMS voltage and current against the EDU34450A.

## 0. Numbers for this pack (from the code — `services/battery_profiles.py`, `config.py`)
| Item | Value |
|---|---|
| Pack | Ninebot/Segway NEB1002-H, nominal 36 V, max 42 V, rated 5.2 Ah / 187 Wh, lithium-ion NMC 10S |
| **Profile cutoff** | **30.0 V** (automatic stop) |
| Profile max voltage | 42.0 V (OSBAMS faults above 43.0 V) |
| Profile recommended / ceiling current | **1.0 A** / 5.2 A |
| 6060B power limit at 42 V / 36 V | 300 W / 42 V = **7.14 A** / 8.33 A |
| OSBAMS operating ceiling | **10 A, 44 V** (provisional) |
| **Final permitted current at 42 V** | min(5.2, 10, 60, 7.14) = **5.2 A** (limit: battery profile) — **the first runs use far less (0.5 A, then 1.0 A)** |
| Temperature stop | **50 °C** (OSBAMS); firmware hard trip 60 °C |
| Current layers | 10 A OSBAMS limit · 15 A fuse (abnormal fault current only) · 18.5 A firmware trip · 20 A shunt |
| Expected full run at 1.0 A | roughly 4–5 h, less for a degraded pack (energy ≈ 187 Wh × SOH) |

Allowed current = min(battery profile, OSBAMS hardware limit, 6060B current limit, 300 W / battery voltage), using the
**conservative** pack voltage (max of OCV and highest seen — sag never raises the current).

## 1. Preconditions (stop here if any is not true)
- [ ] `HARDWARE_ACCEPTANCE_RECORD.md` §2–§6 complete: installed part numbers read and recorded; fuse, disconnect, relay, shunt, XT60 identified.
- [ ] Bench steps **A1, A2, B1, B2, B3** PASS (records, power-path inspection, controller bring-up, source-free fault tests, relay coil-side timing) with data stored.
- [ ] A second person is present and the lab supervisor knows a Li-ion pack is being tested; eye protection on; non-conductive surface; no loose metal near the pack; Li-ion-appropriate extinguishing means known.
- [ ] E-stop within arm's reach of the operator; path to the 6060B front panel clear.
- [ ] OSBAMS software commit recorded: ____________   Tolerances for each comparison written in the calibration record **before** measuring.
- [ ] Registry row exists: chemistry NMC, cutoff 30 V, nominal 36 V, max charge 42 V, rated 5.2 Ah, safety status not Quarantine.

## 2. Battery inspection (pack disconnected, nothing powered)
- [ ] Case: no cracks, swelling, dents, heat marks, liquid, odour. Record photos (`PHOTOS_DIR`).
- [ ] Intake notes read (blinking blue / cut-wire / BMS anomalies?). Any anomaly → stop; a person judges it safe, or the pack is not tested.
- [ ] Connector/wire: XT60 present, pins undamaged, no melted housing, wire insulation intact. Record serial / label: ____________
- [ ] Pack LED/BMS status at rest recorded: ____________

## 3. Wiring check (power OFF, pack NOT connected, 6060B input OFF)
- [ ] Wiring matches `HARDWARE_FREEZE_CANDIDATE.md`: pack + → XT60 → fuse (15 A) → disconnect → relay → shunt (in series) → 6060B +; return to pack −.
- [ ] Disconnect (Blue Sea 6006) is **OFF**. Relay is de-energised (E-stop engaged, ARM off).
- [ ] Shunt sense (Kelvin) leads on the shunt's sense terminals, not on the power studs.
- [ ] Continuity with the EDU34450A: each joint low resistance, no short between + and −, relay contacts open (reading open) with the coil off.
- [ ] 6060B leads: correct polarity at the 6060B input terminals; wire gauge appropriate for the currents used (12 AWG in the BOM).
- [ ] EDU34450A voltage leads ready across the OSBAMS pack-voltage sense point (same point the INA228 bus input sees); current-mode leads NOT yet in circuit.

## 4. Polarity check
- [ ] With the EDU34450A in DC-voltage mode, touch the pack's XT60 contacts **before** mating: red lead on the contact expected to be +. Reading positive: ____ V. If negative or ambiguous → stop.
- [ ] Mate the pack to the OSBAMS XT60 **only** with the disconnect OFF and the relay open.

## 5. OCV measurement and profile selection (relay OPEN, no load) — steps C1–C4
- [ ] Close the Blue Sea disconnect (relay still open, 6060B input OFF). Confirm the dashboard shows pack voltage.
- [ ] **Relay-open verification:** relay not energised; PC9 feedback reads OFF; downstream of the relay reads ~0 V on the EDU34450A; current ≈ 0 A.
- [ ] Read OCV on the EDU34450A: ____ V. OSBAMS INA228: ____ V. ADC: ____ V. Record with `make_record('voltage', …)`.
- [ ] Sanity: OCV between 30.0 V (cutoff) and 42.5 V. At/below 30 V → pack deeply discharged: do not test, charge first. Above 43 V → stop, investigate.
- [ ] TC74 temperature: ____ °C vs EDU34450A ____ °C. TC74 not reading → the safety check will refuse to start (thermal protection unvalidated) — fix first.
- [ ] Select profile `ninebot_neb1002` in the dashboard. Read the limit panel: pack voltage, 6060B rating 60 A, power-derived limit, OSBAMS limit 10 A, profile limit 5.2 A, FINAL PERMITTED (expect 5.2 A at 42 V, 7.14 A is the instrument limit), limiting factor "battery profile". Matches the formula? ☐ yes ☐ no (stop)

## 6. 6060B setup (manual; remote control is blocked)
- [ ] Power the 6060B, run its self-test, record the settings (GPIB address, protection settings) — consult the 6060B Operating Manual for the exact front-panel procedure; do not guess keys.
- [ ] Input **OFF**. Mode **CC**. Current setpoint **0 A**. Leads connected only after the instrument is OFF.
- [ ] Confirm the setpoint you will use is ≤ FINAL PERMITTED (dashboard) **and** ≤ 0.5 A for the first load, ≤ 1.0 A for the profile run. Never enter a value because "the 6060B can do 60 A".
- [ ] Do not deliberately exceed 300 W on the instrument at any time.

## 7. First load — low current (steps D1, D2)
- [ ] EDU34450A: voltage across the pack at the sense point. For current comparison put it **in series** in current mode (check its current range/fuse and burden first) or skip the series current reading and rely on the 6060B readback + INA228 if the DMM burden is a concern; record which.
- [ ] EDUX1052G: probes on load-enable (PC8), relay downstream voltage, and the shunt/current signal; rated probes, good grounding, never an unrated probe on the pack path.
- [ ] Arm OSBAMS (ARM on, E-stop released), start the dashboard Capacity test; wait for READY (the hardware safety check must pass: registry status, temperature present and in limits, voltage envelope, positive permitted current, idle load).
- [ ] Confirm → relay closes → on the 6060B set **0.1 A**, input ON. Record OSBAMS I/V, 6060B readback, EDU34450A. Repeat at **0.25 A** and **0.5 A**, one minute each.
- [ ] Input OFF on the 6060B; verify measured current ≈ 0 (OSBAMS reports load-off confirmed).
- [ ] E-stop test at ≤ 0.5 A (D2): press E-stop while loaded; record fault-to-zero-current and E-stop-to-open on the scope; no unexpected transient. Re-arm only after verifying the pack and wiring.

## 8. Full test — orchestrated CC capacity (step E1)
Only if every earlier step passed with records saved.
- [ ] Dashboard Capacity test, profile `ninebot_neb1002`, requested current **1.0 A** (the profile's recommended value; the panel must show ≥ 1.0 A permitted).
- [ ] READY → confirm → on the 6060B CC **1.0 A**, input ON. Watch: current within 10 % of setpoint after 5 s; power ≈ V × 1 A (about 30–42 W); temperature rise.
- [ ] EDU34450A voltage spot checks at start, middle and end (record each with `make_record`).
- [ ] Do not leave the pack unattended. Re-read the pack temperature by hand at least every 30 minutes.
- [ ] Run ends automatically at the **30.0 V** profile cutoff → OSBAMS requests load OFF → **you** set the 6060B input OFF → OSBAMS confirms load-off from measured current → recovery rest (OSBAMS records recovery voltage at 30 s, 120 s, 300 s).
- [ ] Results saved: Ah, Wh, duration, min/end voltage, max temperature, initial sag, recovery voltages, SOH_capacity. Generate the report/passport.

## 9. Start conditions (all must hold)
Preconditions §1 satisfied · inspection, wiring and polarity checks done · OCV between 30.0 and 42.5 V · TC74 reading present and below 50 °C · relay-open verification done · FINAL PERMITTED ≥ setpoint · hardware safety check PASS · load input OFF and measured current ≈ 0 · operator + second person present.

## 10. Stop conditions
**Automatic (OSBAMS):** voltage ≤ 30.0 V on 3 consecutive samples (normal end); temperature ≥ 50 °C; voltage > 43 V; measured current more than 10 % (min 0.05 A) from the setpoint after 5 s, or above 115 % + 0.1 A of the commanded value; measured power > 300 W or `commanded × conservative V` > 300 W; no samples for 10 s; sensor/firmware fault flag; 8 h maximum; load current never appears after confirm (120 s); load-off not confirmed within 30 s → FAULT with an operator alert.
**Firmware (independent of the PC):** hard trip 18.5 A / 60 °C, E-stop, watchdog, host loss.
**Operator:** any smell, hissing, swelling, discolouration, unexpected heat at the pack, connector or relay, any unexplained reading, any doubt.

## 11. Emergency stop procedure
1. Press the **E-stop** (removes relay-coil power independently of the software).
2. Set the **6060B input OFF** at the front panel.
3. Confirm current ≈ 0 (dashboard and, if connected, the EDU34450A).
4. Only with current at zero, switch the **Blue Sea disconnect OFF** (it is not for routine switching under load).
5. If the pack is hot, swollen, smoking or venting: leave it where it is, move people away, do not touch it, and follow the laboratory's emergency procedure.
6. Record time, what was observed, and the dashboard state; do not retest until a person has reviewed the cause.

## 12. Data to record
| Item | Where |
|---|---|
| Operator, second person, date, software commit | calibration record header |
| Pack serial/label, photos, intake notes, polarity result | registry + this record |
| OCV (EDU34450A / INA228 / ADC), temperature (TC74 / reference) | calibration records (C1–C3) |
| Limit-panel values and limiting factor at start | screenshot |
| Low-current comparison table (OSBAMS / 6060B / EDU34450A) | calibration records (D1) |
| Scope captures: load-enable, E-stop, shutdown, transients | files named by step ID (B3, D1, D2) |
| Full run: readings, Ah, Wh, duration, cutoff, recovery, max temperature, SOH | database + report/passport (E1) |
| Anything unexpected | notes field of the acceptance record |

After the run: update `ValidationLog` with PASS/FAIL per step (needs operator and data location). Claim BENCH_TESTED only for what was actually measured.
