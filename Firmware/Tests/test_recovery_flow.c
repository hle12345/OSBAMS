/*
 * test_recovery_flow.c — integration test of the FULL recovery sequence
 * exactly as main.c performs it, using the REAL safety.c and the REAL
 * (updated) test_controller.c. Host build, plain gcc.
 *
 * This is the test for the two gaps found in review:
 *   Gap 1: FAULT + ACK previously jumped straight to IDLE with no re-check.
 *   Gap 2: E_STOP didn't exist as a state at all.
 */
#include <assert.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include "test_controller.h"
#include "safety.h"

static int run = 0, pass = 0;
#define CHECK(cond, name) do { run++; \
    if (cond) pass++; else printf("  FAIL: %s\n", name); } while (0)

/* ── Simulated hardware state (what estop.c / load_driver.c would read) */
static bool sim_estop_healthy   = true;
static bool sim_selfcheck_pass  = true;

/*
 * Mirrors main.c's FIXED ACK handler: the old latch stays SET through
 * SELF_TEST; a fresh sample is evaluated; the latch is only cleared if
 * that fresh evaluation itself reports FAULT_NONE. This is the fix for
 * the "persistent condition clears through on ACK" bug — see the
 * OVERVOLTAGE-persists scenario below.
 */
static void OperatorAck(safety_context_t *safety, const measurement_sample_t *fresh_sample,
                        const safety_limits_t *lim, uint32_t elapsed_s)
{
    test_state_t st = TestController_GetState();
    if (st != TEST_FAULT && st != TEST_ESTOP) return;

    if (st == TEST_ESTOP && !sim_estop_healthy) return;   /* NACK path */

    TestController_ProcessEvent(TEST_EVT_ACK_FAULT);      /* -> SELF_TEST; latch NOT cleared yet */

    bool checks_ok = sim_selfcheck_pass;
    bool sample_ok = false;
    if (checks_ok) {
        fault_code_t f = Safety_Evaluate(safety, lim, fresh_sample, elapsed_s);
        sample_ok = (f == FAULT_NONE);
    }

    if (checks_ok && sample_ok) {
        Safety_Acknowledge(safety);
        TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    } else {
        TestController_ProcessEvent(TEST_EVT_FAULT);      /* re-fault */
    }
}

int main(void)
{
    safety_context_t safety;
    safety_limits_t  lim = { .max_temp_c10 = 600, .min_voltage_mv = 30000,
                             .max_voltage_mv = 44000, .max_current_ma = 18500,
                             .max_duration_s = 36000 };

    /* ── Boot to DISCHARGING ─────────────────────────────────────── */
    Safety_Init(&safety);
    TestController_Init();
    TestController_ProcessEvent(TEST_EVT_INIT_DONE);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);
    CHECK(TestController_GetState() == TEST_DISCHARGING, "reached DISCHARGING");

    /* ── Overcurrent fault via the REAL Safety_Evaluate ──────────── */
    measurement_sample_t s;
    memset(&s, 0, sizeof(s));
    s.sensor_voltage_mv = 38000;
    s.current_ma        = 19000;    /* over the 18500 trip */
    s.pack_temp_c10     = 300;

    fault_code_t f = Safety_Evaluate(&safety, &lim, &s, 100);
    CHECK(f == FAULT_OVERCURRENT,      "real safety.c flags OVERCURRENT");
    CHECK(safety.fault_latched,        "fault latched in safety context");

    TestController_ProcessEvent(TEST_EVT_FAULT);
    CHECK(TestController_GetState() == TEST_FAULT, "controller in FAULT");

    /* ── Fault condition clears — must STILL be FAULT (latched) ──── */
    s.current_ma = 3000;
    (void)Safety_Evaluate(&safety, &lim, &s, 101);
    CHECK(safety.fault_latched,        "latch survives condition clearing");
    CHECK(TestController_GetState() == TEST_FAULT, "still FAULT before ACK");

    /* ── ACK with self-checks passing AND a fresh, in-range sample:
     * FAULT -> SELF_TEST -> IDLE ────────────────────────────────── */
    sim_selfcheck_pass = true;
    OperatorAck(&safety, &s, &lim, 101);   /* s is now 3000 mA: in range */
    CHECK(!safety.fault_latched,       "ACK cleared the safety latch");
    CHECK(TestController_GetState() == TEST_IDLE,
          "FAULT + ACK + fresh in-range sample -> IDLE (via SELF_TEST)");

    /* ══════════════════════════════════════════════════════════════
     * THE BUG FROM REVIEW: persistent OVERVOLTAGE clearing through on
     * ACK because the old code checked sensor health, not fresh VALUES.
     * "Battery remains at 45 V -> OVERVOLTAGE -> ACK -> latch cleared ->
     * sensor still ONLINE -> self-check passes -> IDLE" even though the
     * pack is STILL at 45 V. With the fix, the fresh Safety_Evaluate()
     * inside OperatorAck() must catch this and refuse to clear the latch.
     * ══════════════════════════════════════════════════════════════ */
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);

    measurement_sample_t ov;
    memset(&ov, 0, sizeof(ov));
    ov.sensor_voltage_mv = 45000;   /* over the 44000 mV limit */
    ov.current_ma        = 2000;
    ov.pack_temp_c10     = 300;

    f = Safety_Evaluate(&safety, &lim, &ov, 200);
    CHECK(f == FAULT_OVERVOLTAGE, "real safety.c flags OVERVOLTAGE");
    TestController_ProcessEvent(TEST_EVT_FAULT);
    CHECK(TestController_GetState() == TEST_FAULT, "controller in FAULT (overvoltage)");

    /* Operator ACKs, but the pack is STILL at 45 V (ov unchanged) and
     * sensor health checks all pass. Pre-fix, this cleared to IDLE. */
    sim_selfcheck_pass = true;
    OperatorAck(&safety, &ov, &lim, 201);
    CHECK(TestController_GetState() != TEST_IDLE,
          "persistent 45V overvoltage does NOT clear to IDLE on ACK (the fix)");
    CHECK(TestController_GetState() == TEST_FAULT,
          "stays in FAULT -- fresh evaluation re-caught the still-present overvoltage");
    CHECK(safety.fault_latched, "latch remains set -- never cleared on a still-bad sample");

    /* Now the pack actually recovers (voltage drops back in range) and
     * THEN an ACK should succeed. */
    ov.sensor_voltage_mv = 40000;
    OperatorAck(&safety, &ov, &lim, 202);
    CHECK(TestController_GetState() == TEST_IDLE,
          "ACK succeeds once the fresh sample is genuinely back in range");

    /* ── ACK with self-checks FAILING: must land back in FAULT ───── */
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);
    s.current_ma = 19000;
    (void)Safety_Evaluate(&safety, &lim, &s, 300);
    TestController_ProcessEvent(TEST_EVT_FAULT);
    s.current_ma = 3000;   /* back in range for the sample itself */

    sim_selfcheck_pass = false;   /* but self-checks (sensor/estop) fail */
    OperatorAck(&safety, &s, &lim, 301);
    CHECK(TestController_GetState() == TEST_FAULT,
          "ACK + failing self-check -> FAULT again, not IDLE (even with a good sample)");

    /* recover for the next scenario */
    sim_selfcheck_pass = true;
    OperatorAck(&safety, &s, &lim, 302);
    CHECK(TestController_GetState() == TEST_IDLE, "recovered to IDLE");

    /* ── E-stop flow with the physical-reset gate ────────────────── */
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);

    sim_estop_healthy = false;               /* mushroom pressed */
    TestController_ProcessEvent(TEST_EVT_ESTOP);
    CHECK(TestController_GetState() == TEST_ESTOP, "E_STOP entered");

    /* ACK while the mushroom is still physically tripped: REJECTED. */
    OperatorAck(&safety, &s, &lim, 400);
    CHECK(TestController_GetState() == TEST_ESTOP,
          "ACK rejected while E-stop still physically tripped");

    /* Mushroom reset, then ACK: E_STOP -> SELF_TEST -> IDLE. */
    sim_estop_healthy = true;
    OperatorAck(&safety, &s, &lim, 401);
    CHECK(TestController_GetState() == TEST_IDLE,
          "E_STOP + physical reset + ACK -> IDLE via SELF_TEST");

    /* ── A new fault while in E_STOP must not demote the state ───── */
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_ESTOP);
    (void)Safety_Evaluate(&safety, &lim, &s, 500);   /* keeps evaluating */
    TestController_ProcessEvent(TEST_EVT_FAULT);
    CHECK(TestController_GetState() == TEST_ESTOP,
          "fault during E_STOP: safety latches, state stays E_STOP");

    printf("%d/%d recovery-flow integration tests passed.\n", pass, run);
    return (pass == run) ? 0 : 1;
}
