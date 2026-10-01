/*
 * test_safety_power_optional.c — regression test: a POWER-only sensor
 * failure must NOT trigger FAULT_SENSOR_TIMEOUT, matching
 * sensor_manager.c's own `mandatory` mask (BUS_VOLTAGE|CURRENT|TEMP_PACK,
 * POWER excluded). Before this fix, safety.c's blanket `if (s->flags)`
 * contradicted that policy.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "safety.h"
#include "sensor_manager.h"

int main(void)
{
    safety_context_t sctx;
    Safety_Init(&sctx);
    safety_limits_t lim = { .max_temp_c10 = 600, .min_voltage_mv = 30000,
                            .max_voltage_mv = 44000, .max_current_ma = 18500,
                            .max_duration_s = 36000 };

    measurement_sample_t s;
    memset(&s, 0, sizeof(s));
    s.sensor_voltage_mv = 38000;
    s.current_ma        = 3000;
    s.pack_temp_c10      = 250;

    /* Baseline: everything healthy -> no fault. */
    fault_code_t f = Safety_Evaluate(&sctx, &lim, &s, 10);
    assert(f == FAULT_NONE);

    /* ── POWER-only failure: must NOT fault ──────────────────────── */
    Safety_Init(&sctx);
    s.flags = (1U << SENSOR_CH_POWER);
    f = Safety_Evaluate(&sctx, &lim, &s, 10);
    printf("POWER-only failure -> fault = %d (expect FAULT_NONE = %d)\n", f, FAULT_NONE);
    assert(f == FAULT_NONE);
    assert(!sctx.fault_latched);

    /* ── BUS_VOLTAGE failure: MUST still fault (mandatory channel) ── */
    Safety_Init(&sctx);
    s.flags = (1U << SENSOR_CH_BUS_VOLTAGE);
    f = Safety_Evaluate(&sctx, &lim, &s, 10);
    assert(f == FAULT_SENSOR_TIMEOUT);
    assert(sctx.fault_latched);

    /* ── CURRENT failure: MUST still fault (mandatory channel) ─────── */
    Safety_Init(&sctx);
    s.flags = (1U << SENSOR_CH_CURRENT);
    f = Safety_Evaluate(&sctx, &lim, &s, 10);
    assert(f == FAULT_SENSOR_TIMEOUT);

    /* ── TEMP_PACK failure: MUST still fault (mandatory channel) ───── */
    Safety_Init(&sctx);
    s.flags = (1U << SENSOR_CH_TEMP_PACK);
    f = Safety_Evaluate(&sctx, &lim, &s, 10);
    assert(f == FAULT_SENSOR_TIMEOUT);

    /* ── POWER failure combined with a mandatory-channel failure:
     * must still fault (the mandatory bit alone is sufficient). ────── */
    Safety_Init(&sctx);
    s.flags = (1U << SENSOR_CH_POWER) | (1U << SENSOR_CH_CURRENT);
    f = Safety_Evaluate(&sctx, &lim, &s, 10);
    assert(f == FAULT_SENSOR_TIMEOUT);

    printf("All safety/sensor-manager mandatory-mask agreement tests passed.\n");
    return 0;
}
