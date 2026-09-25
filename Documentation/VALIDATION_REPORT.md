# OSBAMS Validation Report

**Build:** 0.9.0-dev1 — Engineering Prototype
**Date of this revision:** 2026-07-22
**Status:** Interim. Host-side verification is recorded below. Hardware
acceptance testing has not yet been performed and every hardware row is marked
NOT RUN, not passed.

This report is deliberately honest about what has and has not been demonstrated.
A row is only PASS if there is evidence for it in this build. Hardware-dependent
rows cannot pass until the fixture exists.

---

## 1. Test environment

| Item | Value |
|---|---|
| Firmware version | 0.9.0-dev1 |
| Desktop version | 0.9.0-dev1 |
| Protocol version | 1 |
| Database schema | 6 |
| Hardware | Engineering Prototype (not built/frozen) |
| Host test toolchain | gcc (firmware host tests), pytest (desktop) |
| Reference instruments | none yet — to be recorded when bench testing begins |

Instrument identity fields (electronic load make/model/serial, reference DMM,
controller serial, calibration due dates) are to be captured per test session
once hardware exists. They are empty now by necessity, not by omission.

---

## 2. Automated test results (host, no hardware)

These run on a clean checkout and are the evidence behind the "Host-tested"
column of `MODULE_STATUS.md`.

| Suite | Command | Result |
|---|---|---|
| Desktop + cross-language protocol | `pytest tests/` | 72 passed |
| Firmware measurement engine | `firmware/Tests` → `make` | 11 passed |
| Watchdog gating + ADC predicate + safety response | `firmware/Tests` → `make` | 10 passed |

What these prove: measurement math, scoring determinism, suitability logic,
protocol encode/decode byte-identical between C and Python, watchdog
subsystem-heartbeat gating policy, the ADC agreement predicate, and the Safety
Manager's response to a disagreement flag.

What these do NOT prove: any measurement is numerically correct against a
reference, any timing is met on hardware, or any physical safety action occurs.
Host compilation proves API consistency, not sensor correctness.

---

## 3. Acceptance test status

Mapped to the System Specification (§10). "Verifiable now" means the criterion
can be met at least partly by host tests; full sign-off still needs hardware for
anything touching a sensor, timer, or contactor.

| ID | Test | Requirement(s) | Status | Notes / evidence |
|---|---|---|---|---|
| ACC-01 | Boot and self-test | REQ-109 | NOT RUN | needs hardware; sensor health logic host-tested |
| ACC-02 | 60 s telemetry capture | REQ-104, REQ-108 | PARTIAL | frame format + sequence numbering host-verified; on-hardware period NOT RUN |
| ACC-03 | Known-load integration | REQ-105, REQ-106 | PARTIAL | Ah/Wh math host-verified vs synthetic data; reference-load comparison NOT RUN |
| ACC-04 | Overtemperature injection | REQ-201/205/206 | NOT RUN | fault + latch logic host-tested; physical response NOT RUN |
| ACC-05 | Undervoltage injection | REQ-202 | NOT RUN | logic host-tested; physical response NOT RUN |
| ACC-06 | Host disconnect during test | REQ-205, REQ-603 | NOT RUN | requires hardware |
| ACC-07 | Sensor disconnect | REQ-109 | NOT RUN | health-transition logic host-tested; physical NOT RUN |
| ACC-08 | Stuck I2C recovery | REQ-109 | NOT RUN | recovery routine implemented; bench NOT RUN |
| ACC-09 | Quarantine gate | REQ-207 | PASS | desktop test blocks start for QUARANTINE/FAIL |
| ACC-10 | Score determinism | REQ-302 | PASS | identical input → identical score (host test) |
| ACC-11 | Rule weight floor | REQ-304 | PASS | ML weight never exceeds 0.50 (host test) |
| ACC-12 | Report reproducibility | REQ-406 | PASS | report includes the full version block |
| ACC-13 | Database backup | REQ-405 | PARTIAL | backup-before-migration logic present; long-run NOT RUN |
| ACC-14 | Prediction retention | REQ-403 | PASS | prior predictions retained after re-assessment |
| ACC-15 | Endurance run (4–8 h) | REQ-104 | NOT RUN | requires hardware |
| ACC-16 | TIM6 acquisition timing | REQ-110, REQ-111 | NOT RUN | backlog-counter logic host-tested; period/jitter must be measured on a logic analyser |
| ACC-17 | Watchdog and safe reset | REQ-210, REQ-211 | PARTIAL | gating policy host-tested; real IWDG timeout, reset cause, safe-boot NOT RUN |
| ACC-18 | Redundant voltage cross-check | REQ-212, REQ-506 | PARTIAL | disagreement→fault path host-tested; INA228-vs-reference and real divergence NOT RUN |
| ACC-19 | Contactor and E-stop chain | REQ-213, REQ-214 | NOT RUN | requires hardware; this is the most important missing physical proof |

Summary: 6 PASS (all software-only), 6 PARTIAL (logic verified, hardware
pending), 7 NOT RUN. 0 of the hardware-dependent criteria are validated.

---

## 4. Calibration status

No channel has been calibrated. See `CALIBRATION.md` for the procedure and the
record tables to be filled in. No measurement tolerance is claimed anywhere in
this package because no calibration data supports one.

---

## 5. Deviations

None recorded yet — no hardware test has been run from which a deviation could
arise. This section will list any acceptance criterion that hardware testing
fails to meet, with the disposition.

---

## 6. Remaining limitations

Carried from `known_limitations.md`:

- INA228 software is implemented but uncalibrated and unverified on the part.
- The ADC redundant channel is a diverse cross-check, not a certified
  independent protection device (both channels share pack wiring and ground).
- Watchdog reset behaviour is not bench-validated.
- TIM6 timing accuracy and jitter are unverified until measured.
- Physical fault response (contactor de-energising on fault and on reset,
  E-stop independent of firmware) is unverified.

---

## 7. Conclusion

The software architecture is verified to the extent host testing allows. The
system is **not** validated as an instrument and must not be represented as one
until the hardware acceptance tests above are executed with recorded results.
This is why the build is `0.9.0-dev1` and not a release candidate.

When the hardware rows carry real PASS results and recorded data, this report —
with equipment, serial numbers, dates, procedures, raw data, and pass/fail —
becomes the evidence that justifies promotion to 0.9.0-rc1 and, after the
hardware is frozen, to 1.0.0 / Hardware Rev A.
