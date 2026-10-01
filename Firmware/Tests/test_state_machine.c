/*
 * test_state_machine.c — host test for the frozen FAULT/E_STOP recovery
 * rules in test_controller.c. Plain gcc, no hardware.
 */
#include <assert.h>
#include <stdio.h>
#include "test_controller.h"

static int run = 0, pass = 0;
#define CHECK(cond, name) do { run++; \
    if (cond) pass++; else printf("  FAIL: %s\n", name); } while (0)

static void boot_to_idle(void)
{
    TestController_Init();
    TestController_ProcessEvent(TEST_EVT_INIT_DONE);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
}

static void idle_to_discharging(void)
{
    TestController_ProcessEvent(TEST_EVT_PACK_PRESENT);
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    TestController_ProcessEvent(TEST_EVT_START);
    TestController_ProcessEvent(TEST_EVT_START);
}

int main(void)
{
    /* ── FAULT recovery must pass through SELF_TEST, not jump to IDLE ── */
    boot_to_idle();
    idle_to_discharging();
    CHECK(TestController_GetState() == TEST_DISCHARGING, "reached DISCHARGING");

    TestController_ProcessEvent(TEST_EVT_FAULT);
    CHECK(TestController_GetState() == TEST_FAULT, "fault -> FAULT");

    /* ACK exits to SELF_TEST — the old code went straight to IDLE here. */
    CHECK(TestController_ProcessEvent(TEST_EVT_ACK_FAULT), "ACK accepted");
    CHECK(TestController_GetState() == TEST_SELF_TEST,
          "FAULT + ACK -> SELF_TEST (not IDLE)");

    /* From SELF_TEST, only PRECHECK_PASS proceeds; START is rejected. */
    CHECK(!TestController_ProcessEvent(TEST_EVT_START),
          "cannot START from SELF_TEST");
    CHECK(TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS),
          "prechecks re-passed");
    CHECK(TestController_GetState() == TEST_IDLE, "SELF_TEST -> IDLE");

    /* ── E_STOP is distinct, forced from any state ───────────────────── */
    idle_to_discharging();
    TestController_ProcessEvent(TEST_EVT_ESTOP);
    CHECK(TestController_GetState() == TEST_ESTOP, "estop -> E_STOP state");

    /* Fault must NOT demote an active E_STOP. */
    CHECK(!TestController_ProcessEvent(TEST_EVT_FAULT),
          "FAULT event rejected while in E_STOP");
    CHECK(TestController_GetState() == TEST_ESTOP, "still E_STOP after fault evt");

    /* E-stop outranks an existing FAULT (other direction). */
    TestController_ProcessEvent(TEST_EVT_ACK_FAULT);       /* -> SELF_TEST */
    TestController_ProcessEvent(TEST_EVT_FAULT);           /* -> FAULT */
    CHECK(TestController_GetState() == TEST_FAULT, "in FAULT");
    TestController_ProcessEvent(TEST_EVT_ESTOP);
    CHECK(TestController_GetState() == TEST_ESTOP, "ESTOP overrides FAULT");

    /* ── No latched state goes directly to an armed/running state ────── */
    CHECK(!TestController_ProcessEvent(TEST_EVT_START), "no START from E_STOP");
    CHECK(!TestController_ProcessEvent(TEST_EVT_RESUME), "no RESUME from E_STOP");
    CHECK(!TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS),
          "no PRECHECK_PASS from E_STOP (must ACK first)");

    /* E_STOP + ACK -> SELF_TEST -> IDLE, same shape as FAULT recovery. */
    TestController_ProcessEvent(TEST_EVT_ACK_FAULT);
    CHECK(TestController_GetState() == TEST_SELF_TEST, "E_STOP + ACK -> SELF_TEST");
    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
    CHECK(TestController_GetState() == TEST_IDLE, "recovered to IDLE");

    /* ── SELF_TEST failure path: prechecks fail -> back to FAULT ─────── */
    TestController_ProcessEvent(TEST_EVT_FAULT);
    TestController_ProcessEvent(TEST_EVT_ACK_FAULT);       /* -> SELF_TEST */
    TestController_ProcessEvent(TEST_EVT_FAULT);           /* checks failed */
    CHECK(TestController_GetState() == TEST_FAULT,
          "failed re-check in SELF_TEST -> FAULT again (explicit path)");

    /* ── State names ─────────────────────────────────────────────────── */
    CHECK(TestController_StateName(TEST_ESTOP)[0] == 'E', "E_STOP name present");
    CHECK(TestController_StateName(TEST_FAULT)[0] == 'F', "FAULT name intact");

    printf("%d/%d state machine tests passed.\n", pass, run);
    return (pass == run) ? 0 : 1;
}
