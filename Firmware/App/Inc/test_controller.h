#ifndef TEST_CONTROLLER_H
#define TEST_CONTROLLER_H

#include <stdbool.h>
#include <stdint.h>

/*
 * State machine changes vs the previous revision (frozen decisions):
 *
 * 1. TEST_ESTOP added, DISTINCT from TEST_FAULT. E-stop is an operator
 *    safety action with its own state/event history; it must not be
 *    collapsed into a fault code. TEST_EVT_ESTOP forces TEST_ESTOP from
 *    ANY state — including TEST_FAULT (E-stop outranks fault). While in
 *    TEST_ESTOP, TEST_EVT_FAULT does NOT demote the state to TEST_FAULT.
 *
 * 2. Recovery from BOTH latched states goes through SELF_TEST, never
 *    straight to IDLE:
 *        FAULT  + TEST_EVT_ACK_FAULT -> SELF_TEST
 *        E_STOP + TEST_EVT_ACK_FAULT -> SELF_TEST
 *    (The previous FAULT -> ACK -> IDLE transition skipped re-verification
 *    entirely: an ACK while the underlying condition persisted landed back
 *    in IDLE with nothing re-checking E-stop health, sensors, or K1_AUX.)
 *    From SELF_TEST, only TEST_EVT_PRECHECK_PASS proceeds to IDLE — and
 *    main() must only send that event after actually re-running the boot
 *    checks. If they fail, main() sends TEST_EVT_FAULT again.
 *
 * 3. The CALLER (main.c) gates the ACK: for TEST_ESTOP it must verify
 *    Estop_IsHealthy() before sending TEST_EVT_ACK_FAULT — i.e. the
 *    physical mushroom has been reset. The controller itself cannot read
 *    pins; it only enforces the state topology. Neither latched state
 *    ever transitions directly to READY/RESTING/DISCHARGING.
 *
 * TEST_ESTOP is appended at the END of the enum so all existing state
 * values keep their numeric positions (the StateName array and any logged
 * numeric states stay stable). The desktop protocol carries state NAMES,
 * not numbers, so the appended value is also protocol-safe.
 */

typedef enum {
    TEST_BOOT,
    TEST_SELF_TEST,
    TEST_IDLE,
    TEST_PACK_DETECTED,
    TEST_PRECHECK,
    TEST_READY,
    TEST_RESTING,
    TEST_DISCHARGING,
    TEST_PAUSED,
    TEST_CUTOFF,
    TEST_RECOVERY,
    TEST_COMPLETE,
    TEST_FAULT,
    TEST_ESTOP        /* appended: keep existing values stable */
} test_state_t;

typedef enum {
    TEST_EVT_INIT_DONE,
    TEST_EVT_PACK_PRESENT,
    TEST_EVT_PRECHECK_PASS,
    TEST_EVT_START,
    TEST_EVT_PAUSE,
    TEST_EVT_RESUME,
    TEST_EVT_STOP,
    TEST_EVT_CUTOFF,
    TEST_EVT_RECOVERY_DONE,
    TEST_EVT_FAULT,
    TEST_EVT_ACK_FAULT,   /* operator acknowledge — exits FAULT or ESTOP to SELF_TEST */
    TEST_EVT_ESTOP        /* E-stop tripped — forces TEST_ESTOP from any state */
} test_event_t;

void TestController_Init(void);
bool TestController_ProcessEvent(test_event_t event);
test_state_t TestController_GetState(void);
const char *TestController_StateName(test_state_t state);

#endif
