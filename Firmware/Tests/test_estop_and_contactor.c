/*
 * test_estop_and_contactor.c — host test for estop.c and the load_driver.c
 * PC9 supervision changes. Runs with plain gcc, no STM32 headers, no I2C,
 * no hardware — same approach as Tests/test_measurement.c per
 * firmware_architecture.md.
 *
 * This exercises the LOGIC PATHS (fail-safe defaults, honest status codes
 * when feedback is absent from the host's point of view) — it cannot
 * exercise real GPIO timing, which only runs under OSBAMS_TARGET_STM32.
 * Bench validation with the real board is still required per
 * MODULE_STATUS.md's maturity levels; this only proves the code is not
 * broken at the logic level before it ever reaches hardware.
 *
 * Build:
 *   gcc -I. -o test_estop_and_contactor \
 *       test_estop_and_contactor.c ../Drivers/Src/estop.c \
 *       ../Drivers/Src/load_driver.c ../Core/Src/tick.c
 */
#include <assert.h>
#include <stdio.h>
#include "estop.h"
#include "load_driver.h"

int main(void)
{
    /* ── E-stop ─────────────────────────────────────────────────── */
    osbams_status_t st = Estop_Init();
    assert(st == OSBAMS_STATUS_OK);

    /* Host build has no real PA0 -- read_pin_tripped() returns false, so
     * a fresh init must read healthy, not tripped. This is the fail-safe
     * default the design calls for being verified, not assumed. */
    assert(Estop_IsHealthy() == true);
    assert(Estop_IsTripped() == false);
    assert(Estop_TripCount() == 0);

    Estop_Poll();
    assert(Estop_IsHealthy() == true);
    assert(Estop_TripCount() == 0);   /* no transition on host build */

    printf("estop: OK (host build: always reads healthy, no hardware)\n");

    /* ── PC9 polarity decode — pure logic, host-testable directly ───
     * FROZEN: PC9 = K1 voltage-feedback via VO610A, ACTIVE LOW. */
    assert(Load_DecodeFeedbackActiveLow(false) == true);   /* LOW  -> confirmed ON  */
    assert(Load_DecodeFeedbackActiveLow(true)  == false);  /* HIGH -> confirmed OFF */
    printf("PC9 active-low polarity decode: LOW=on, HIGH=off -- OK\n");

    /* ── Contactor / load supervision ──────────────────────────────
     * LOAD_FEEDBACK_PRESENT is now 1 (FROZEN): PC9 carries real,
     * definitive K1 feedback via the VO610A (see load_driver.c header).
     * On host, feedback_says_load_on() still hits the #else branch
     * (no real GPIO), so Load_Enable()/Load_Disable() exercise the
     * "feedback never confirms" path deterministically -- this proves
     * the flow SHAPE (fail-safe timeout / honest non-claim), not the
     * on-target polarity itself, which is covered by the decode
     * assertions above instead. */
    st = Load_Init();
    assert(st == OSBAMS_STATUS_OK);
    assert(Load_HasFeedback() == true);   /* LOAD_FEEDBACK_PRESENT is 1 */
    assert(Load_IsEnabled() == false);

    st = Load_Enable();
    assert(st == OSBAMS_STATUS_TIMEOUT);
    assert(Load_IsEnabled() == false);
    printf("Load_Enable() on host (no real PC9) -> TIMEOUT, fails safe: OK\n");

    /* Disable: pin driven low; feedback_says_load_on() reads false on
     * host (no real GPIO), so "load confirmed off" -> OK immediately.
     * On target this only returns OK when PC9 genuinely reads LOW-then-
     * decoded-off, i.e. real confirmation, not this host stub path. */
    st = Load_Disable();
    assert(st == OSBAMS_STATUS_OK);
    assert(Load_DisableCount() >= 1U);
    printf("Load_Disable() on host (no real PC9) -> OK (stub reads off): OK\n");

    /* The current-based inference path (Load_ConfirmOffByCurrent) is the
     * documented replacement for a real aux contact. Confirm it still
     * works on its own terms. */
    st = Load_ConfirmOffByCurrent(50);    /* 50 mA, below the 100 mA threshold */
    assert(st == OSBAMS_STATUS_OK);
    st = Load_ConfirmOffByCurrent(5000);  /* 5 A still flowing after "off" */
    assert(st == OSBAMS_STATUS_LOAD_STUCK);
    printf("Load_ConfirmOffByCurrent() inferential check still works: OK\n");

    printf("All estop/contactor host logic tests passed.\n");
    return 0;
}
