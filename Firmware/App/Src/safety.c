#include "safety.h"
#include "sensor_manager.h"

/*
 * CRITICAL sensor fault mask — deliberately EXCLUDES SENSOR_CH_POWER.
 *
 * FIX: sensor_manager.c's own `mandatory` mask (see SensorManager_ReadAll)
 * already excludes POWER — a POWER-only failure doesn't fail that
 * function's return status. But this file previously did
 * `else if (s->flags) f = FAULT_SENSOR_TIMEOUT;`, treating ANY set bit
 * in flags — including a POWER-only failure — as an immediate critical
 * fault. That contradicted sensor_manager.c's own policy: POWER is
 * derivable from voltage x current, both of which ARE mandatory here, so
 * losing POWER alone shouldn't force a fault. This mask makes the two
 * files agree.
 */
#define SAFETY_CRITICAL_SENSOR_MASK \
    ((1U << SENSOR_CH_BUS_VOLTAGE) | (1U << SENSOR_CH_CURRENT) | (1U << SENSOR_CH_TEMP_PACK))

void Safety_Init(safety_context_t *ctx)
{
    if (!ctx) return;
    ctx->latched_fault = FAULT_NONE;
    ctx->fault_timestamp_us = 0;
    ctx->fault_latched = false;
}

fault_code_t Safety_Evaluate(safety_context_t *ctx, const safety_limits_t *l, const measurement_sample_t *s, uint32_t elapsed_s)
{
    if (!ctx || !l || !s) return FAULT_SENSOR_TIMEOUT;
    fault_code_t f = FAULT_NONE;
    /* Diverse-redundancy cross-check first: if the INA228 metrology path and
     * the independent ADC divider disagree (flag set by the Sensor Manager),
     * one path is wrong. A single trusted sensor is not enough to run a battery
     * test, so this is critical and takes priority over value-based faults. */
    if (s->voltage_disagreement) f = FAULT_SENSOR_DISAGREEMENT;
    else if (s->flags & SAFETY_CRITICAL_SENSOR_MASK) f = FAULT_SENSOR_TIMEOUT;
    else if (s->pack_temp_c10 >= l->max_temp_c10) f = FAULT_OVERTEMP;
    else if (s->sensor_voltage_mv > l->max_voltage_mv) f = FAULT_OVERVOLTAGE;
    else if (s->sensor_voltage_mv < l->min_voltage_mv) f = FAULT_UNDERVOLTAGE;
    else if (s->current_ma > l->max_current_ma) f = FAULT_OVERCURRENT;
    else if (s->current_ma < -100) f = FAULT_REVERSE_CURRENT;
    else if (elapsed_s > l->max_duration_s) f = FAULT_MAX_DURATION;
    if (f != FAULT_NONE) {
        ctx->latched_fault = f;
        ctx->fault_timestamp_us = s->timestamp_us;
        ctx->fault_latched = true;
    }
    return f;
}

void Safety_Acknowledge(safety_context_t *ctx)
{
    if (!ctx) return;
    ctx->latched_fault = FAULT_NONE;
    ctx->fault_timestamp_us = 0;
    ctx->fault_latched = false;
}
