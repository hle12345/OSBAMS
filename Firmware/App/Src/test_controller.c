#include "test_controller.h"

static test_state_t g_state = TEST_BOOT;

void TestController_Init(void) { g_state = TEST_BOOT; }
test_state_t TestController_GetState(void) { return g_state; }

bool TestController_ProcessEvent(test_event_t e)
{
    /* E-stop outranks everything, including an existing FAULT. */
    if (e == TEST_EVT_ESTOP) { g_state = TEST_ESTOP; return true; }

    /* Fault forces TEST_FAULT from any state EXCEPT TEST_ESTOP — an
     * active E-stop keeps its own state; the fault is still latched in
     * the safety layer and will be re-checked during SELF_TEST. */
    if (e == TEST_EVT_FAULT) {
        if (g_state == TEST_ESTOP) return false;
        g_state = TEST_FAULT;
        return true;
    }

    switch (g_state) {
        case TEST_BOOT: if (e == TEST_EVT_INIT_DONE) g_state = TEST_SELF_TEST; else return false; break;
        case TEST_SELF_TEST: if (e == TEST_EVT_PRECHECK_PASS) g_state = TEST_IDLE; else return false; break;
        case TEST_IDLE: if (e == TEST_EVT_PACK_PRESENT) g_state = TEST_PACK_DETECTED; else return false; break;
        case TEST_PACK_DETECTED: if (e == TEST_EVT_PRECHECK_PASS) g_state = TEST_READY; else return false; break;
        case TEST_READY: if (e == TEST_EVT_START) g_state = TEST_RESTING; else return false; break;
        case TEST_RESTING: if (e == TEST_EVT_START) g_state = TEST_DISCHARGING; else return false; break;
        case TEST_DISCHARGING:
            if (e == TEST_EVT_PAUSE) g_state = TEST_PAUSED;
            else if (e == TEST_EVT_CUTOFF || e == TEST_EVT_STOP) g_state = TEST_CUTOFF;
            else return false; break;
        case TEST_PAUSED:
            if (e == TEST_EVT_RESUME) g_state = TEST_DISCHARGING;
            else if (e == TEST_EVT_STOP) g_state = TEST_CUTOFF;
            else return false; break;
        case TEST_CUTOFF: if (e == TEST_EVT_RECOVERY_DONE) g_state = TEST_RECOVERY; else return false; break;
        case TEST_RECOVERY: if (e == TEST_EVT_RECOVERY_DONE) g_state = TEST_COMPLETE; else return false; break;
        case TEST_COMPLETE: if (e == TEST_EVT_PACK_PRESENT) g_state = TEST_PACK_DETECTED; else return false; break;

        /* ── Latched states: ACK exits to SELF_TEST, never to IDLE ───
         * The previous FAULT->ACK->IDLE transition skipped every
         * re-verification. Now the only way back to IDLE is SELF_TEST +
         * TEST_EVT_PRECHECK_PASS, which main() sends only after actually
         * re-running the boot checks. main() additionally gates the ACK
         * for TEST_ESTOP on Estop_IsHealthy() (mushroom physically
         * reset) — the controller can't read pins, so that check lives
         * at the call site. */
        case TEST_FAULT: if (e == TEST_EVT_ACK_FAULT) g_state = TEST_SELF_TEST; else return false; break;
        case TEST_ESTOP: if (e == TEST_EVT_ACK_FAULT) g_state = TEST_SELF_TEST; else return false; break;

        default: return false;
    }
    return true;
}

const char *TestController_StateName(test_state_t state)
{
    static const char *names[] = {"BOOT","SELF_TEST","IDLE","PACK_DETECTED",
        "PRECHECK","READY","RESTING","DISCHARGING","PAUSED","CUTOFF",
        "RECOVERY","COMPLETE","FAULT","E_STOP"};
    return (state <= TEST_ESTOP) ? names[state] : "UNKNOWN";
}
