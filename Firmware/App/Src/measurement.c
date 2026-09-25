/*
 * measurement.c — OSBAMS Measurement Engine
 *
 * ── Layer boundary ───────────────────────────────────────────────────
 * This file contains ZERO references to any specific sensor part or bus.
 * It asks the Sensor Manager for a validated reading and does math.
 *
 * Swapping the current sensor or adding a temperature channel changes
 * sensor_manager.c only — this file is untouched.
 */

#include "measurement.h"
#include <string.h>
#include <limits.h>

void Measurement_Init(measurement_context_t *ctx, sensor_manager_t *sensors)
{
    if (!ctx) return;
    memset(ctx, 0, sizeof(*ctx));
    ctx->min_voltage_mv = INT32_MAX;
    ctx->sensors        = sensors;
    ctx->initialized    = (sensors != NULL);
}

void Measurement_Integrate(measurement_context_t *ctx,
                            const measurement_sample_t *previous,
                            measurement_sample_t *current)
{
    if (!ctx || !previous || !current) return;
    if (current->timestamp_us <= previous->timestamp_us) return;

    uint64_t dt_ms = (current->timestamp_us - previous->timestamp_us) / 1000ULL;

    /* Trapezoidal rule: average of the two endpoints × interval */
    int64_t avg_i = ((int64_t)previous->current_ma + current->current_ma) / 2;
    int64_t avg_p = ((int64_t)previous->power_mw   + current->power_mw)   / 2;

    current->accumulated_ma_ms = previous->accumulated_ma_ms + avg_i * (int64_t)dt_ms;
    current->accumulated_mw_ms = previous->accumulated_mw_ms + avg_p * (int64_t)dt_ms;
}

osbams_status_t Measurement_Acquire(measurement_context_t *ctx,
                                     uint64_t timestamp_us)
{
    if (!ctx)              return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!ctx->initialized) return OSBAMS_STATUS_NOT_READY;
    if (!ctx->sensors)     return OSBAMS_STATUS_NOT_READY;

    /* ── Ask the Sensor Manager for a validated reading ──────────── */
    sensor_reading_t reading;
    memset(&reading, 0, sizeof(reading));

    osbams_status_t sensor_status = SensorManager_ReadAll(ctx->sensors, &reading);

    /* ── Build the next sample from the validated reading ────────── *
     * FIX: a failed channel leaves its field at 0 in `reading` (it was
     * zero-initialized above) with only a fault_mask bit set — nothing
     * previously stopped that 0 from being copied into `next` and then
     * integrated as if it were a real reading. A momentary current-read
     * failure mid-test used to silently inject a real zero into the
     * trapezoidal Ah integral, biasing the result.
     *
     * Fix: hold the LAST GOOD value for any channel whose fault_mask bit
     * is set this cycle, instead of taking the zeroed placeholder. The
     * fault bit itself is still copied into next.flags unchanged, so
     * downstream consumers (safety.c, telemetry) still see the failure —
     * only the Ah/Wh/min/max MATH stops being corrupted by it. */
    bool voltage_ok = !(reading.fault_mask & (1U << SENSOR_CH_BUS_VOLTAGE));
    bool current_ok = !(reading.fault_mask & (1U << SENSOR_CH_CURRENT));
    bool power_ok    = !(reading.fault_mask & (1U << SENSOR_CH_POWER));
    bool temp_ok     = !(reading.fault_mask & (1U << SENSOR_CH_TEMP_PACK));

    measurement_sample_t next = ctx->latest;
    next.sequence++;
    next.timestamp_us = timestamp_us;

    next.sensor_voltage_mv  = voltage_ok ? reading.bus_voltage_mv
                                          : ctx->latest.sensor_voltage_mv;
    next.adc_voltage_mv     = reading.adc_voltage_mv;   /* diagnostic only, not integrated */
    next.voltage_disagreement = reading.voltage_disagreement;
    next.current_ma         = current_ok ? reading.current_ma
                                          : ctx->latest.current_ma;
    next.power_mw            = power_ok ? reading.power_mw
                                         : ctx->latest.power_mw;
    next.pack_temp_c10      = temp_ok ? reading.temp_pack_c10
                                       : ctx->latest.pack_temp_c10;
    next.connector_temp_c10 = reading.temp_connector_c10;
    next.ambient_temp_c10   = reading.temp_ambient_c10;
    next.flags              = reading.fault_mask;   /* unchanged: failure still reported */

    /* ── Integrate against the previous sample ───────────────────── */
    if (ctx->latest.sequence > 0) {
        Measurement_Integrate(ctx, &ctx->latest, &next);
    }

    /* ── Running statistics ──────────────────────────────────────── */
    if (next.sensor_voltage_mv < ctx->min_voltage_mv)
        ctx->min_voltage_mv = next.sensor_voltage_mv;
    if (next.current_ma > ctx->max_current_ma)
        ctx->max_current_ma = next.current_ma;
    if (next.power_mw > ctx->max_power_mw)
        ctx->max_power_mw = next.power_mw;
    if (next.pack_temp_c10 > ctx->max_temp_c10)
        ctx->max_temp_c10 = next.pack_temp_c10;

    ctx->latest = next;
    return sensor_status;
}

/* ── Unit conversion ─────────────────────────────────────────────────
 * accumulated_ma_ms is milliamp-milliseconds.
 * 1 Ah = 1000 mA × 3600 s × 1000 ms/s = 3.6e9 mA·ms */
double Measurement_GetAh(const measurement_context_t *ctx)
{
    return ctx ? (double)ctx->latest.accumulated_ma_ms / 3600000000.0 : 0.0;
}

double Measurement_GetWh(const measurement_context_t *ctx)
{
    return ctx ? (double)ctx->latest.accumulated_mw_ms / 3600000000.0 : 0.0;
}
