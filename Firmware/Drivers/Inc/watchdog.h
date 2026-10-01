/*
 * watchdog.h — RECONSTRUCTED from watchdog.c's use of s_reported as a
 * bitmask, main.c's three Watchdog_ReportHeartbeat() call sites
 * (WD_ACQUISITION_HEARTBEAT, WD_SAFETY_HEARTBEAT, WD_CONTROLLER_HEARTBEAT),
 * and test_safety_modules.c's proof that ALL THREE must report before a
 * refresh is granted ("all tasks reported -> refresh granted" only after
 * all three heartbeats). WATCHDOG_REQUIRED_HEARTBEATS is therefore the
 * OR of exactly these three bits — confirmed by that test's behavior,
 * not guessed.
 */
#ifndef WATCHDOG_H
#define WATCHDOG_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

typedef enum {
    RESET_CAUSE_UNKNOWN = 0,
    RESET_CAUSE_WATCHDOG,
    RESET_CAUSE_SOFTWARE,
    RESET_CAUSE_PIN,
    RESET_CAUSE_BROWNOUT,
    RESET_CAUSE_POWER_ON
} reset_cause_t;

typedef enum {
    WD_ACQUISITION_HEARTBEAT = (1U << 0),
    WD_SAFETY_HEARTBEAT      = (1U << 1),
    WD_CONTROLLER_HEARTBEAT  = (1U << 2)
} watchdog_heartbeat_t;

#define WATCHDOG_REQUIRED_HEARTBEATS \
    (WD_ACQUISITION_HEARTBEAT | WD_SAFETY_HEARTBEAT | WD_CONTROLLER_HEARTBEAT)

reset_cause_t   Watchdog_GetResetCause(void);
osbams_status_t Watchdog_Init(uint32_t timeout_ms);
void            Watchdog_ReportHeartbeat(watchdog_heartbeat_t task);
osbams_status_t Watchdog_Refresh(void);

#endif /* WATCHDOG_H */
