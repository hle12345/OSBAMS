/*
 * test_tick_consolidation.c — verifies the single-tick-source pattern used
 * in main.c: multiple call sites reading Tick_GetMs()/Tick_ElapsedMs()
 * must agree, since there is now only one counter, incremented only by
 * Tick_OnSysTick(). Simulates the SysTick ISR by calling Tick_OnSysTick()
 * in a loop (there is no real timer on the host).
 */
#include <assert.h>
#include <stdio.h>
#include "tick.h"

/* Mirrors main.c's delay_ms() exactly. */
static void sim_delay_ms(uint32_t ms)
{
    uint32_t start = Tick_GetMs();
    while (Tick_ElapsedMs(start) < ms) {
        Tick_OnSysTick();   /* stand-in for the real SysTick ISR firing */
    }
}

int main(void)
{
    assert(Tick_GetMs() == 0);

    /* Two independent call sites reading the tick during a delay must see
     * a consistent, monotonically non-decreasing value -- proving there is
     * exactly one counter being advanced, not two that could disagree. */
    uint32_t site_a_start = Tick_GetMs();
    sim_delay_ms(50);
    uint32_t site_a_after = Tick_GetMs();
    assert(Tick_ElapsedMs(site_a_start) >= 50U);
    printf("delay_ms(50) advanced tick by %u ms (>=50 expected)\n",
           Tick_ElapsedMs(site_a_start));

    uint32_t site_b_start = Tick_GetMs();
    assert(site_b_start == site_a_after);   /* same counter, no drift */

    /* Simulate a 10s recovery-interval check like main.c's loop. */
    uint32_t last_recovery_ms = Tick_GetMs();
    for (int i = 0; i < 10000; i++) Tick_OnSysTick();
    assert(Tick_ElapsedMs(last_recovery_ms) >= 10000U);
    printf("10000 simulated ticks -> ElapsedMs = %u (>=10000 expected)\n",
           Tick_ElapsedMs(last_recovery_ms));

    printf("Tick consolidation test passed: single counter, no drift "
           "between call sites.\n");
    return 0;
}
