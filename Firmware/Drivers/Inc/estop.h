/*
 * estop.h — E-stop sense monitoring (PA0)
 *
 * MONITORING ONLY. The physical NC E-stop contact breaks the 12 V
 * contactor-coil supply in hardware, independent of the STM32
 * (HARDWARE_DESIGN.md §3). This module exists so firmware KNOWS the
 * E-stop tripped — to latch a fault state and report it — not to perform
 * the cutoff itself. Losing this GPIO, this driver, or the whole MCU does
 * not defeat the physical cutoff.
 *
 * Fail-safe polarity (frozen):
 *   PA0 LOW  = E-stop circuit HEALTHY  (NC contact closed, pulled to GND)
 *   PA0 HIGH = TRIPPED / wire broken / connector disconnected
 *                (external pull-up to 3V3 through the NC contact)
 *
 * Application code must never read GPIOA->IDR directly for this pin — the
 * polarity mapping lives entirely in estop.c, behind Estop_IsHealthy() /
 * Estop_IsTripped(), so callers never have to remember which level means
 * what.
 *
 * No debounce on the trip direction: a HIGH reading is reported as tripped
 * on the very next Estop_Poll(), matching the frozen rule that
 * ESTOP_SENSE HIGH -> LOAD_EN=0 happens immediately. Recovery (going back
 * LOW) does NOT auto-clear anything in this module — latching and the
 * ACK/RESET/SELF_TEST recovery sequence belong to the fault manager /
 * test controller layer, not here. This module only ever reports the
 * current raw (but polarity-corrected) state, plus a trip-event counter
 * for diagnostics.
 */
#ifndef ESTOP_H
#define ESTOP_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

/** @brief Configure PA0 as an input with no internal pull. An internal
 *         pull here would fight or mask a real wiring fault — the external
 *         circuit already provides the pull-up through the NC contact. */
osbams_status_t Estop_Init(void);

/**
 * @brief Sample PA0 and update cached state + trip-event counter.
 *
 * Call once per main-loop iteration (same pattern as
 * AcquisitionTimer_SampleDue() / Watchdog_ReportHeartbeat() in main.c).
 * Estop_IsHealthy()/Estop_IsTripped() read the cached value from the most
 * recent poll rather than re-touching the GPIO, so multiple call sites in
 * the same loop iteration agree with each other and trip-counting can't
 * double-count within one poll.
 */
void Estop_Poll(void);

/** @brief True if PA0 read LOW as of the last Estop_Poll() call. */
bool Estop_IsHealthy(void);

/** @brief True if PA0 read HIGH as of the last Estop_Poll() call. */
bool Estop_IsTripped(void);

/** @brief Count of HEALTHY->TRIPPED transitions observed since Estop_Init(). */
uint32_t Estop_TripCount(void);

#endif /* ESTOP_H */
