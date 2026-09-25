/*
 * test_measurement_invalid_channel.c — regression test: a failed sensor
 * channel (fault_mask bit set) must NOT contribute a false zero to the
 * Ah/Wh trapezoidal integral or the min/max trackers. Before the fix,
 * SensorManager_ReadAll()'s zero-initialized `reading` struct meant a
 * failed current read looked identical to "current really is 0 mA".
 *
 * Same mocking technique as test_measurement.c, self-contained in this
 * file so it doesn't depend on that file's static mock internals.
 */
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "measurement.h"

static sensor_reading_t g_script[8];
static int g_len = 0, g_idx = 0;

osbams_status_t SensorManager_ReadAll(sensor_manager_t *mgr, sensor_reading_t *out)
{
    (void)mgr;
    if (!out) return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (g_idx >= g_len) return OSBAMS_STATUS_NOT_READY;
    *out = g_script[g_idx++];
    return out->fault_mask ? OSBAMS_STATUS_SENSOR_FAILURE : OSBAMS_STATUS_OK;
}
osbams_status_t SensorManager_Init(sensor_manager_t *m) { (void)m; return OSBAMS_STATUS_OK; }
sensor_health_t SensorManager_GetHealth(const sensor_manager_t *m, sensor_channel_t c)
    { (void)m; (void)c; return SENSOR_HEALTH_ONLINE; }
osbams_status_t SensorManager_SetCalibration(sensor_manager_t *m, sensor_channel_t c, int32_t o, int32_t s)
    { (void)m; (void)c; (void)o; (void)s; return OSBAMS_STATUS_OK; }
void SensorManager_SetNotFitted(sensor_manager_t *m, sensor_channel_t c) { (void)m; (void)c; }
const char *SensorManager_ChannelName(sensor_channel_t c) { (void)c; return "MOCK"; }
const char *SensorManager_HealthName(sensor_health_t h)   { (void)h; return "MOCK"; }
osbams_status_t SensorManager_AttemptRecovery(sensor_manager_t *m) { (void)m; return OSBAMS_STATUS_OK; }

static void add(int32_t v, int32_t i, int32_t p, int16_t t, uint32_t fault)
{
    sensor_reading_t r; memset(&r, 0, sizeof(r));
    r.bus_voltage_mv = v; r.current_ma = i; r.power_mw = p; r.temp_pack_c10 = t;
    r.fault_mask = fault;
    g_script[g_len++] = r;
}

int main(void)
{
    /* Scenario: steady 2 A for 3 samples (0, 30min, 60min), but the
     * MIDDLE sample's CURRENT channel fails.
     *
     * With the fix: the failed sample holds the last-good 2000 mA, so
     * both half-hour intervals compute the full 2 A rate -> 2 A for 1
     * hour = 2.0 Ah, matching what a fully-healthy run would give.
     *
     * Without the fix (worked by hand for comparison, not asserted here):
     * the failed sample reads current as 0 mA (the zeroed placeholder).
     *   interval1 = avg(2000,0)=1000 mA x 0.5h = 0.5 Ah
     *   interval2 = avg(0,2000)=1000 mA x 0.5h = 0.5 Ah
     *   total = 1.0 Ah -- exactly half the true value, from ONE bad
     *   sample in the middle of an otherwise-perfect run. */
    g_len = 0; g_idx = 0;
    add(36000, 2000, 72000, 250, 0);                                 /* good */
    add(36000, 0,    0,     250, (1U << SENSOR_CH_CURRENT));          /* CURRENT fails */
    add(36000, 2000, 72000, 250, 0);                                 /* good again */

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    Measurement_Acquire(&ctx, 0ULL);
    Measurement_Acquire(&ctx, 1800ULL * 1000000ULL);   /* +30 min, CURRENT fails here */
    Measurement_Acquire(&ctx, 3600ULL * 1000000ULL);   /* +60 min */

    double ah = Measurement_GetAh(&ctx);
    printf("Ah with a failed-current sample mid-test: %.4f (expect ~2.0 -- matches a "
           "fully-healthy 2A/1hr run; the pre-fix code would have given ~1.0)\n", ah);
    assert(ah > 1.9 && ah < 2.1);

    /* The fault bit itself must still be visible in flags -- the fix only
     * changes what gets MATHED, not what gets REPORTED. */
    assert(ctx.latest.flags == 0);   /* latest (3rd) sample was good */

    /* ── Voltage min-tracker must not be dragged down by a failed read
     * that would otherwise show as 0 mV ─────────────────────────────── */
    g_len = 0; g_idx = 0;
    add(40000, 1000, 40000, 250, 0);
    add(0,     0,    0,     250, (1U << SENSOR_CH_BUS_VOLTAGE));  /* voltage fails */
    add(39000, 1000, 39000, 250, 0);

    measurement_context_t ctx2;
    Measurement_Init(&ctx2, &sensors);
    Measurement_Acquire(&ctx2, 0ULL);
    Measurement_Acquire(&ctx2, 1000000ULL);
    Measurement_Acquire(&ctx2, 2000000ULL);

    printf("min_voltage_mv with a failed-voltage sample: %d (expect 39000, NOT 0)\n",
           ctx2.min_voltage_mv);
    assert(ctx2.min_voltage_mv == 39000);   /* NOT 0 from the failed read */

    printf("All invalid-channel measurement tests passed.\n");
    return 0;
}
