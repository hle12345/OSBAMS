/*
 * test_safety_modules.c — Host tests for watchdog gating and ADC cross-check.
 *
 * These exercise the decision logic (not the hardware registers, which are
 * guarded out on the host build). Compiled with plain gcc, no STM32 headers.
 */
#include <stdio.h>
#include <assert.h>
#include "watchdog.h"
#include "adc_safety.h"
#include "safety.h"
#include "measurement.h"

static int tests_run = 0, tests_pass = 0;
#define CHECK(cond, name) do { \
    tests_run++; \
    if (cond) { tests_pass++; } \
    else { printf("  FAIL: %s\n", name); } \
} while (0)

int main(void)
{
    /* ── Watchdog: refresh withheld until all tasks report ──────────── */
    Watchdog_Init(2000);

    CHECK(Watchdog_Refresh() == OSBAMS_STATUS_BUSY,
          "no tasks reported -> refresh withheld");

    Watchdog_ReportHeartbeat(WD_SAFETY_HEARTBEAT);
    CHECK(Watchdog_Refresh() == OSBAMS_STATUS_BUSY,
          "only safety reported -> still withheld");

    Watchdog_ReportHeartbeat(WD_ACQUISITION_HEARTBEAT);
    Watchdog_ReportHeartbeat(WD_CONTROLLER_HEARTBEAT);
    CHECK(Watchdog_Refresh() == OSBAMS_STATUS_OK,
          "all tasks reported -> refresh granted");

    /* After a refresh the set clears; next refresh must wait again. */
    CHECK(Watchdog_Refresh() == OSBAMS_STATUS_BUSY,
          "report set cleared after refresh -> withheld again");

    /* ── ADC agreement predicate (pure, no hardware) ────────────────── */
    CHECK(AdcSafety_Disagrees(42000, 42000) == false,
          "identical readings -> agree");
    CHECK(AdcSafety_Disagrees(42000, 41800) == false,
          "small delta within window -> agree");
    CHECK(AdcSafety_Disagrees(42000, 0) == true,
          "42 V vs 0 V -> disagreement");
    CHECK(AdcSafety_Disagrees(20000, 38000) == true,
          "18 V apart -> disagreement");

    /* ── Safety response to sensor disagreement ─────────────────────── */
    safety_context_t sctx;
    Safety_Init(&sctx);
    safety_limits_t lim = { .max_temp_c10 = 600, .min_voltage_mv = 30000,
                            .max_voltage_mv = 44000, .max_current_ma = 10000,
                            .max_duration_s = 36000 };
    measurement_sample_t good = { .sensor_voltage_mv = 40000, .current_ma = 3000,
                                  .pack_temp_c10 = 250, .flags = 0,
                                  .voltage_disagreement = false };
    CHECK(Safety_Evaluate(&sctx, &lim, &good, 10) == FAULT_NONE,
          "agreeing sensors, in-range -> no fault");

    measurement_sample_t disagree = good;
    disagree.voltage_disagreement = true;
    CHECK(Safety_Evaluate(&sctx, &lim, &disagree, 10) == FAULT_SENSOR_DISAGREEMENT,
          "disagreement flag -> critical FAULT_SENSOR_DISAGREEMENT");

    printf("\n%d/%d safety-module tests passed.\n", tests_pass, tests_run);
    return (tests_pass == tests_run) ? 0 : 1;
}
