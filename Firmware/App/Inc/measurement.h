/*
 * measurement.h — RECONSTRUCTED. Every field is read or written by
 * measurement.c, safety.c, protocol.c, or main.c in the uploaded sources.
 */
#ifndef MEASUREMENT_H
#define MEASUREMENT_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"
#include "sensor_manager.h"

typedef struct {
    uint32_t sequence;
    uint64_t timestamp_us;

    int32_t  sensor_voltage_mv;
    int32_t  adc_voltage_mv;
    bool     voltage_disagreement;

    int32_t  current_ma;
    int32_t  power_mw;

    int16_t  pack_temp_c10;
    int16_t  connector_temp_c10;
    int16_t  ambient_temp_c10;

    uint32_t flags;

    int64_t  accumulated_ma_ms;
    int64_t  accumulated_mw_ms;
} measurement_sample_t;

typedef struct {
    int32_t  min_voltage_mv;
    int32_t  max_current_ma;
    int32_t  max_power_mw;
    int16_t  max_temp_c10;

    measurement_sample_t latest;

    sensor_manager_t *sensors;
    bool               initialized;
} measurement_context_t;

void Measurement_Init(measurement_context_t *ctx, sensor_manager_t *sensors);

void Measurement_Integrate(measurement_context_t *ctx,
                            const measurement_sample_t *previous,
                            measurement_sample_t *current);

osbams_status_t Measurement_Acquire(measurement_context_t *ctx,
                                     uint64_t timestamp_us);

double Measurement_GetAh(const measurement_context_t *ctx);
double Measurement_GetWh(const measurement_context_t *ctx);

#endif /* MEASUREMENT_H */
