/*
 * test_measurement.c — Host-side unit test for the Measurement Engine
 *
 * Proves the Sensor Manager abstraction works: this test compiles and
 * runs on a PC with NO STM32 headers, NO I2C, and NO real sensors.
 * It substitutes a mock Sensor Manager and verifies the integration math.
 *
 * Build and run:
 *     gcc -I../App/Inc -I../Core/Inc -I../Drivers/Inc \
 *         -DUNIT_TEST test_measurement.c ../App/Src/measurement.c \
 *         -o test_measurement && ./test_measurement
 *
 * This is only possible because measurement.c has no chip dependencies.
 * Before the Sensor Manager refactor, this test could not exist.
 */

#include <stdio.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include "measurement.h"

/* ── Mock Sensor Manager ─────────────────────────────────────────────
 * Replaces the real SensorManager_ReadAll() at link time.
 * Feeds a scripted sequence of readings to the Measurement Engine. */

static sensor_reading_t g_script[64];
static int              g_script_len   = 0;
static int              g_script_index = 0;

osbams_status_t SensorManager_ReadAll(sensor_manager_t *mgr,
                                       sensor_reading_t *out)
{
    (void)mgr;
    if (!out) return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (g_script_index >= g_script_len) return OSBAMS_STATUS_NOT_READY;
    *out = g_script[g_script_index++];
    return out->fault_mask ? OSBAMS_STATUS_SENSOR_FAILURE : OSBAMS_STATUS_OK;
}

/* Unused stubs so the linker is happy */
osbams_status_t SensorManager_Init(sensor_manager_t *m) { (void)m; return OSBAMS_STATUS_OK; }
sensor_health_t SensorManager_GetHealth(const sensor_manager_t *m, sensor_channel_t c)
    { (void)m; (void)c; return SENSOR_HEALTH_ONLINE; }
osbams_status_t SensorManager_SetCalibration(sensor_manager_t *m, sensor_channel_t c,
                                              int32_t o, int32_t s)
    { (void)m; (void)c; (void)o; (void)s; return OSBAMS_STATUS_OK; }
void SensorManager_SetNotFitted(sensor_manager_t *m, sensor_channel_t c)
    { (void)m; (void)c; }
const char *SensorManager_ChannelName(sensor_channel_t c) { (void)c; return "MOCK"; }
const char *SensorManager_HealthName(sensor_health_t h)   { (void)h; return "MOCK"; }
osbams_status_t SensorManager_AttemptRecovery(sensor_manager_t *m)
    { (void)m; return OSBAMS_STATUS_OK; }

/* ── Test helpers ────────────────────────────────────────────────────*/
static void script_reset(void) { g_script_len = 0; g_script_index = 0; }

static void script_add(int32_t v_mv, int32_t i_ma, int32_t p_mw,
                       int16_t t_c10, uint32_t fault_mask)
{
    sensor_reading_t r;
    memset(&r, 0, sizeof(r));
    r.bus_voltage_mv = v_mv;
    r.current_ma     = i_ma;
    r.power_mw       = p_mw;
    r.temp_pack_c10  = t_c10;
    r.fault_mask     = fault_mask;
    r.all_valid      = (fault_mask == 0);
    g_script[g_script_len++] = r;
}

static int g_tests_run = 0, g_tests_passed = 0;

#define CHECK(cond, msg) do {                                    \
    g_tests_run++;                                               \
    if (cond) { g_tests_passed++; printf("  PASS  %s\n", msg); } \
    else      { printf("  FAIL  %s\n", msg); }                   \
} while (0)

#define CHECK_NEAR(actual, expected, tol, msg) do {              \
    g_tests_run++;                                               \
    double _a = (actual), _e = (expected);                       \
    if (fabs(_a - _e) <= (tol)) {                                \
        g_tests_passed++;                                        \
        printf("  PASS  %s  (%.4f ≈ %.4f)\n", msg, _a, _e);      \
    } else {                                                     \
        printf("  FAIL  %s  (%.4f != %.4f)\n", msg, _a, _e);     \
    }                                                            \
} while (0)

/* ── Tests ───────────────────────────────────────────────────────────*/

static void test_constant_current_1a_1h(void)
{
    printf("\nTest: 1 A constant for 1 hour at 36 V → 1.0 Ah, 36.0 Wh\n");
    script_reset();
    /* 3 samples: t=0, t=30min, t=60min */
    script_add(36000, 1000, 36000, 250, 0);
    script_add(36000, 1000, 36000, 250, 0);
    script_add(36000, 1000, 36000, 250, 0);

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    Measurement_Acquire(&ctx, 0ULL);
    Measurement_Acquire(&ctx, 1800ULL * 1000000ULL);   /* +30 min */
    Measurement_Acquire(&ctx, 3600ULL * 1000000ULL);   /* +60 min */

    CHECK_NEAR(Measurement_GetAh(&ctx), 1.0,  0.01, "Ah = 1.0");
    CHECK_NEAR(Measurement_GetWh(&ctx), 36.0, 0.5,  "Wh = 36.0");
}

static void test_trapezoidal_vs_rectangular(void)
{
    printf("\nTest: varying current uses trapezoidal, not endpoint value\n");
    script_reset();
    /* 1 A → 3 A → 1 A over 1 hour.
     * Trapezoidal: (1+3)/2 × 0.5h + (3+1)/2 × 0.5h = 1.0 + 1.0 = 2.0 Ah
     * Naive (last value × total time) would give 1 A × 1 h = 1.0 Ah */
    script_add(36000, 1000, 36000,  250, 0);
    script_add(36000, 3000, 108000, 250, 0);
    script_add(36000, 1000, 36000,  250, 0);

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    Measurement_Acquire(&ctx, 0ULL);
    Measurement_Acquire(&ctx, 1800ULL * 1000000ULL);
    Measurement_Acquire(&ctx, 3600ULL * 1000000ULL);

    CHECK_NEAR(Measurement_GetAh(&ctx), 2.0, 0.05,
               "trapezoidal Ah = 2.0 (not 1.0)");
}

static void test_min_max_tracking(void)
{
    printf("\nTest: running min voltage / max current / max temp\n");
    script_reset();
    script_add(42000, 2000, 84000, 250, 0);
    script_add(38000, 3500, 133000, 320, 0);
    script_add(31000, 2000, 62000, 410, 0);

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    Measurement_Acquire(&ctx, 0ULL);
    Measurement_Acquire(&ctx, 1000000ULL);
    Measurement_Acquire(&ctx, 2000000ULL);

    CHECK(ctx.min_voltage_mv == 31000, "min voltage = 31000 mV");
    CHECK(ctx.max_current_ma == 3500,  "max current = 3500 mA");
    CHECK(ctx.max_temp_c10   == 410,   "max temp = 41.0 C");
}

static void test_sensor_fault_propagates(void)
{
    printf("\nTest: sensor fault mask propagates to sample flags\n");
    script_reset();
    script_add(36000, 1000, 36000, 250, 0);
    script_add(36000, 1000, 36000, 250, (1U << SENSOR_CH_TEMP_PACK));

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    Measurement_Acquire(&ctx, 0ULL);
    osbams_status_t st = Measurement_Acquire(&ctx, 500000ULL);

    CHECK(st == OSBAMS_STATUS_SENSOR_FAILURE, "returns SENSOR_FAILURE");
    CHECK(ctx.latest.flags & (1U << SENSOR_CH_TEMP_PACK),
          "TEMP_PACK fault bit set in sample flags");
}

static void test_sequence_increments(void)
{
    printf("\nTest: sequence number increments every sample\n");
    script_reset();
    for (int i = 0; i < 5; i++) script_add(36000, 1000, 36000, 250, 0);

    sensor_manager_t sensors;
    measurement_context_t ctx;
    Measurement_Init(&ctx, &sensors);

    for (int i = 0; i < 5; i++)
        Measurement_Acquire(&ctx, (uint64_t)i * 500000ULL);

    CHECK(ctx.latest.sequence == 5, "sequence = 5 after 5 acquisitions");
}

static void test_null_safety(void)
{
    printf("\nTest: NULL argument handling\n");
    CHECK(Measurement_Acquire(NULL, 0) == OSBAMS_STATUS_INVALID_ARGUMENT,
          "NULL context returns INVALID_ARGUMENT");

    measurement_context_t ctx;
    Measurement_Init(&ctx, NULL);
    CHECK(Measurement_Acquire(&ctx, 0) == OSBAMS_STATUS_NOT_READY,
          "NULL sensor manager returns NOT_READY");
}

/* ── Main ────────────────────────────────────────────────────────────*/
int main(void)
{
    printf("========================================\n");
    printf("OSBAMS Measurement Engine — Unit Tests\n");
    printf("(host build, no STM32 hardware required)\n");
    printf("========================================\n");

    test_constant_current_1a_1h();
    test_trapezoidal_vs_rectangular();
    test_min_max_tracking();
    test_sensor_fault_propagates();
    test_sequence_increments();
    test_null_safety();

    printf("\n========================================\n");
    printf("Results: %d/%d passed\n", g_tests_passed, g_tests_run);
    printf("========================================\n");

    return (g_tests_passed == g_tests_run) ? 0 : 1;
}
