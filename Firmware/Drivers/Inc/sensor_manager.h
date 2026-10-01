/*
 * sensor_manager.h — RECONSTRUCTED from sensor_manager.c, measurement.c,
 * and main.c usage. Every field/function here is exercised by real code.
 *
 * ONE VALUE IS AN UNGROUNDED GUESS, flagged where it is:
 * SENSOR_FAIL_THRESHOLD — sensor_manager.c references it but no uploaded
 * file states its value. Set to 3 as a reasonable default; confirm
 * against the real header.
 *
 * SENSOR_CH_COUNT is 4 — the four channels sensor_manager.c actually
 * reads (BUS_VOLTAGE, CURRENT, POWER, TEMP_PACK). temp_connector_c10 /
 * temp_ambient_c10 exist in sensor_reading_t (measurement.c reads them)
 * but sensor_manager.c's own comments mark those "optional, not yet
 * implemented" with no channel enum entry — so they're not counted here.
 */
#ifndef SENSOR_MANAGER_H
#define SENSOR_MANAGER_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

typedef enum {
    SENSOR_CH_BUS_VOLTAGE = 0,
    SENSOR_CH_CURRENT,
    SENSOR_CH_POWER,
    SENSOR_CH_TEMP_PACK,
    SENSOR_CH_COUNT
} sensor_channel_t;

typedef enum {
    SENSOR_HEALTH_UNKNOWN = 0,
    SENSOR_HEALTH_ONLINE,
    SENSOR_HEALTH_DEGRADED,
    SENSOR_HEALTH_OFFLINE,
    SENSOR_HEALTH_NOT_FITTED
} sensor_health_t;

/* Consecutive failures before a DEGRADED channel is marked OFFLINE.
 * UNGROUNDED GUESS — confirm against the real header. */
#ifndef SENSOR_FAIL_THRESHOLD
#define SENSOR_FAIL_THRESHOLD  3U
#endif

typedef struct {
    int32_t offset;
    int32_t slope_ppm;
    bool    valid;
} sensor_calibration_t;

typedef struct {
    sensor_health_t       health;
    sensor_calibration_t  cal;
    uint32_t               total_reads;
    uint32_t               total_failures;
    uint32_t               consecutive_failures;
    osbams_status_t        last_status;
} sensor_channel_state_t;

typedef struct {
    sensor_channel_state_t channels[SENSOR_CH_COUNT];
    bool                    initialized;
    uint32_t                read_cycles;
} sensor_manager_t;

typedef struct {
    int32_t  bus_voltage_mv;
    int32_t  current_ma;
    int32_t  power_mw;
    int16_t  temp_pack_c10;
    int16_t  temp_connector_c10;   /* reserved: not yet driven by any channel */
    int16_t  temp_ambient_c10;     /* reserved: not yet driven by any channel */
    int32_t  adc_voltage_mv;
    bool     voltage_disagreement;
    uint32_t fault_mask;
    bool     all_valid;
} sensor_reading_t;

osbams_status_t SensorManager_Init(sensor_manager_t *mgr);
osbams_status_t SensorManager_ReadAll(sensor_manager_t *mgr, sensor_reading_t *out);
sensor_health_t SensorManager_GetHealth(const sensor_manager_t *mgr, sensor_channel_t ch);
osbams_status_t SensorManager_SetCalibration(sensor_manager_t *mgr, sensor_channel_t ch,
                                              int32_t offset, int32_t slope_ppm);
void            SensorManager_SetNotFitted(sensor_manager_t *mgr, sensor_channel_t ch);
const char     *SensorManager_ChannelName(sensor_channel_t ch);
const char     *SensorManager_HealthName(sensor_health_t h);
osbams_status_t SensorManager_AttemptRecovery(sensor_manager_t *mgr);

#endif /* SENSOR_MANAGER_H */
