/*
 * safety.h — RECONSTRUCTED for host testing from safety.c + main.c +
 * test_safety_modules.c usage. The real App/Inc/safety.h was never
 * uploaded; every field and enum member here appears verbatim in one of
 * those files, and fault enum members are declared in the order safety.c
 * evaluates them. RECONCILE against the real header before merging — if
 * the real enum ordering differs, keep the real one (numeric fault codes
 * appear in serial FAULT_%d messages, so ordering is externally visible).
 */
#ifndef SAFETY_H
#define SAFETY_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"
#include "measurement.h"

typedef enum {
    FAULT_NONE = 0,
    FAULT_SENSOR_DISAGREEMENT,
    FAULT_SENSOR_TIMEOUT,
    FAULT_OVERTEMP,
    FAULT_OVERVOLTAGE,
    FAULT_UNDERVOLTAGE,
    FAULT_OVERCURRENT,
    FAULT_REVERSE_CURRENT,
    FAULT_MAX_DURATION
} fault_code_t;

typedef struct {
    int16_t  max_temp_c10;
    int32_t  min_voltage_mv;
    int32_t  max_voltage_mv;
    int32_t  max_current_ma;
    uint32_t max_duration_s;
} safety_limits_t;

typedef struct {
    fault_code_t latched_fault;
    uint64_t     fault_timestamp_us;
    bool         fault_latched;
} safety_context_t;

void         Safety_Init(safety_context_t *ctx);
fault_code_t Safety_Evaluate(safety_context_t *ctx, const safety_limits_t *l,
                             const measurement_sample_t *s, uint32_t elapsed_s);
void         Safety_Acknowledge(safety_context_t *ctx);

#endif /* SAFETY_H */
