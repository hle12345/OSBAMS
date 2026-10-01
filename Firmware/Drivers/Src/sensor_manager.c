/*
 * sensor_manager.c — OSBAMS Sensor Abstraction Layer
 *
 * This is the ONLY application-layer file that names specific sensor
 * chips. If a sensor part changes or a channel is added, this file changes
 * and nothing above it does.
 *
 * Layer position:
 *     measurement.c   (integration math, no chip names)
 *          ↓
 *     sensor_manager.c   ← YOU ARE HERE (chip names live only below)
 *          ↓
 *     ina228.c / tc74.c / i2c_bus.c
 */

#include "sensor_manager.h"
#include "i2c_bus.h"
#include "app_config.h"
#include "ina228.h"
#include "adc_safety.h"

/* Diverse redundancy: the INA228 is the metrology path; the ADC divider is an
 * independent cross-check. A disagreement beyond tolerance sets this bit in the
 * reading's fault_mask. The Safety Manager decides what to do about it — the
 * Sensor Manager only measures and reports. */
#define SENSOR_DISAGREE_BIT  (1U << 30)
#include "tc74.h"
#include <string.h>

/* ── Calibration helper ──────────────────────────────────────────────
 * corrected = (raw × slope_ppm / 1e6) + offset
 * Uses int64 intermediate to avoid overflow at large raw values. */
static int32_t apply_cal(int32_t raw, const sensor_calibration_t *cal)
{
    if (!cal || !cal->valid) return raw;
    int64_t scaled = ((int64_t)raw * (int64_t)cal->slope_ppm) / 1000000LL;
    return (int32_t)(scaled + cal->offset);
}

/* ── Health bookkeeping ──────────────────────────────────────────────*/
static void record_result(sensor_channel_state_t *st, osbams_status_t status)
{
    st->total_reads++;
    st->last_status = status;

    if (status == OSBAMS_STATUS_OK) {
        st->consecutive_failures = 0;
        if (st->health != SENSOR_HEALTH_NOT_FITTED) {
            st->health = SENSOR_HEALTH_ONLINE;
        }
    } else {
        st->total_failures++;
        st->consecutive_failures++;
        if (st->health == SENSOR_HEALTH_NOT_FITTED) {
            return;   /* do not promote an unfitted channel to OFFLINE */
        }
        if (st->consecutive_failures >= SENSOR_FAIL_THRESHOLD) {
            st->health = SENSOR_HEALTH_OFFLINE;
        } else {
            st->health = SENSOR_HEALTH_DEGRADED;
        }
    }
}

static inline bool channel_fitted(const sensor_manager_t *mgr,
                                   sensor_channel_t ch)
{
    return mgr->channels[ch].health != SENSOR_HEALTH_NOT_FITTED;
}

/* ── Init ────────────────────────────────────────────────────────────*/
osbams_status_t SensorManager_Init(sensor_manager_t *mgr)
{
    if (!mgr) return OSBAMS_STATUS_INVALID_ARGUMENT;

    memset(mgr, 0, sizeof(*mgr));

    /* Default calibration = unity gain, zero offset, marked invalid
     * so raw values pass through until real calibration is loaded. */
    for (int i = 0; i < SENSOR_CH_COUNT; i++) {
        mgr->channels[i].health     = SENSOR_HEALTH_UNKNOWN;
        mgr->channels[i].cal.slope_ppm = 1000000;
        mgr->channels[i].cal.offset    = 0;
        mgr->channels[i].cal.valid     = false;
    }

    /* Optional channels default to NOT_FITTED — the board integrator
     * calls SensorManager_SetNotFitted() or leaves them enabled. */

    /* ── Bring up the I2C bus first ─────────────────────────────── */
    I2C1_Init();

    /* ── Mandatory: INA228 (V/I/P) ───────────────────────────────── */
    osbams_status_t ina = INA228_Init(OSBAMS_SHUNT_MICRO_OHM,
                                      OSBAMS_INA228_IMAX_MA);
    if (ina != OSBAMS_STATUS_OK) {
        mgr->channels[SENSOR_CH_BUS_VOLTAGE].health = SENSOR_HEALTH_OFFLINE;
        mgr->channels[SENSOR_CH_CURRENT].health     = SENSOR_HEALTH_OFFLINE;
        mgr->channels[SENSOR_CH_POWER].health       = SENSOR_HEALTH_OFFLINE;
    } else {
        mgr->channels[SENSOR_CH_BUS_VOLTAGE].health = SENSOR_HEALTH_ONLINE;
        mgr->channels[SENSOR_CH_CURRENT].health     = SENSOR_HEALTH_ONLINE;
        mgr->channels[SENSOR_CH_POWER].health       = SENSOR_HEALTH_ONLINE;
    }

    /* ── Mandatory: TC74 pack temperature ────────────────────────── */
    osbams_status_t tc = TC74_Init();
    mgr->channels[SENSOR_CH_TEMP_PACK].health =
        (tc == OSBAMS_STATUS_OK) ? SENSOR_HEALTH_ONLINE : SENSOR_HEALTH_OFFLINE;

    mgr->initialized = true;

    /* System is usable if the mandatory electrical channels came up */
    bool electrical_ok =
        (mgr->channels[SENSOR_CH_BUS_VOLTAGE].health == SENSOR_HEALTH_ONLINE);

    return electrical_ok ? OSBAMS_STATUS_OK : OSBAMS_STATUS_SENSOR_FAILURE;
}

/* ── Read all channels ───────────────────────────────────────────────*/
osbams_status_t SensorManager_ReadAll(sensor_manager_t *mgr,
                                       sensor_reading_t *out)
{
    if (!mgr || !out)      return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!mgr->initialized) return OSBAMS_STATUS_NOT_READY;

    mgr->read_cycles++;
    out->fault_mask = 0;

    osbams_status_t st;
    int32_t raw32;
    int16_t raw16;

    /* ── Bus voltage ─────────────────────────────────────────────── */
    if (channel_fitted(mgr, SENSOR_CH_BUS_VOLTAGE)) {
        st = INA228_ReadBus_mV(&raw32);
        record_result(&mgr->channels[SENSOR_CH_BUS_VOLTAGE], st);
        if (st == OSBAMS_STATUS_OK) {
            out->bus_voltage_mv =
                apply_cal(raw32, &mgr->channels[SENSOR_CH_BUS_VOLTAGE].cal);
        } else {
            out->fault_mask |= (1U << SENSOR_CH_BUS_VOLTAGE);
        }
    }

    /* ── Current ─────────────────────────────────────────────────── */
    if (channel_fitted(mgr, SENSOR_CH_CURRENT)) {
        st = INA228_ReadCurrent_mA(&raw32, NULL);   /* freshness flag added; sensor_manager
                                                       doesn't gate on it yet (see note below) */
        record_result(&mgr->channels[SENSOR_CH_CURRENT], st);
        if (st == OSBAMS_STATUS_OK) {
            out->current_ma =
                apply_cal(raw32, &mgr->channels[SENSOR_CH_CURRENT].cal);
        } else {
            out->fault_mask |= (1U << SENSOR_CH_CURRENT);
        }
    }

    /* ── Power ───────────────────────────────────────────────────── */
    if (channel_fitted(mgr, SENSOR_CH_POWER)) {
        st = INA228_ReadPower_mW(&raw32);
        record_result(&mgr->channels[SENSOR_CH_POWER], st);
        if (st == OSBAMS_STATUS_OK) {
            out->power_mw =
                apply_cal(raw32, &mgr->channels[SENSOR_CH_POWER].cal);
        } else {
            out->fault_mask |= (1U << SENSOR_CH_POWER);
        }
    }

    /* ── Pack temperature ────────────────────────────────────────── */
    if (channel_fitted(mgr, SENSOR_CH_TEMP_PACK)) {
        st = TC74_ReadTemperature_C10(&raw16);
        record_result(&mgr->channels[SENSOR_CH_TEMP_PACK], st);
        if (st == OSBAMS_STATUS_OK) {
            out->temp_pack_c10 = (int16_t)apply_cal(
                (int32_t)raw16, &mgr->channels[SENSOR_CH_TEMP_PACK].cal);
        } else {
            out->fault_mask |= (1U << SENSOR_CH_TEMP_PACK);
        }
    }

    /* ── Connector temperature (optional second TC74) ────────────── */

    /* ── Ambient temperature (optional third TC74) ───────────────── */

    /* Diverse redundant voltage channel (independent ADC divider). The INA228
     * bus voltage above is the metrology value; this is the cross-check. */
    int32_t adc_mv = 0;
    if (AdcSafety_ReadVoltage_mV(&adc_mv) == OSBAMS_STATUS_OK) {
        out->adc_voltage_mv = adc_mv;
        if (AdcSafety_Disagrees(out->bus_voltage_mv, adc_mv)) {
            out->fault_mask |= SENSOR_DISAGREE_BIT;
        }
    } else {
        out->adc_voltage_mv = 0;
        /* ADC unavailable is itself a cross-check failure: fail safe. */
        out->fault_mask |= SENSOR_DISAGREE_BIT;
    }

    out->voltage_disagreement = (out->fault_mask & SENSOR_DISAGREE_BIT) != 0U;
    out->all_valid = (out->fault_mask == 0);

    /* Return OK if the mandatory electrical channels read successfully.
     * Optional channel failures are reported in fault_mask but do not
     * fail the whole read — the test can continue without them. */
    uint32_t mandatory =
        (1U << SENSOR_CH_BUS_VOLTAGE) |
        (1U << SENSOR_CH_CURRENT)     |
        (1U << SENSOR_CH_TEMP_PACK);

    return (out->fault_mask & mandatory)
               ? OSBAMS_STATUS_SENSOR_FAILURE
               : OSBAMS_STATUS_OK;
}

/* ── Queries ─────────────────────────────────────────────────────────*/
sensor_health_t SensorManager_GetHealth(const sensor_manager_t *mgr,
                                         sensor_channel_t ch)
{
    if (!mgr || ch >= SENSOR_CH_COUNT) return SENSOR_HEALTH_UNKNOWN;
    return mgr->channels[ch].health;
}

osbams_status_t SensorManager_SetCalibration(sensor_manager_t *mgr,
                                              sensor_channel_t ch,
                                              int32_t offset,
                                              int32_t slope_ppm)
{
    if (!mgr || ch >= SENSOR_CH_COUNT) return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (slope_ppm <= 0)                return OSBAMS_STATUS_INVALID_ARGUMENT;
    mgr->channels[ch].cal.offset    = offset;
    mgr->channels[ch].cal.slope_ppm = slope_ppm;
    mgr->channels[ch].cal.valid     = true;
    return OSBAMS_STATUS_OK;
}

void SensorManager_SetNotFitted(sensor_manager_t *mgr, sensor_channel_t ch)
{
    if (!mgr || ch >= SENSOR_CH_COUNT) return;
    mgr->channels[ch].health = SENSOR_HEALTH_NOT_FITTED;
}

const char *SensorManager_ChannelName(sensor_channel_t ch)
{
    switch (ch) {
        case SENSOR_CH_BUS_VOLTAGE:    return "BUS_VOLTAGE";
        case SENSOR_CH_CURRENT:        return "CURRENT";
        case SENSOR_CH_POWER:          return "POWER";
        case SENSOR_CH_TEMP_PACK:      return "TEMP_PACK";
        default:                       return "UNKNOWN";
    }
}

const char *SensorManager_HealthName(sensor_health_t h)
{
    switch (h) {
        case SENSOR_HEALTH_ONLINE:     return "ONLINE";
        case SENSOR_HEALTH_DEGRADED:   return "DEGRADED";
        case SENSOR_HEALTH_OFFLINE:    return "OFFLINE";
        case SENSOR_HEALTH_NOT_FITTED: return "NOT_FITTED";
        default:                       return "UNKNOWN";
    }
}

/* ── Recovery ────────────────────────────────────────────────────────
 * Called from a low-priority diagnostics task, never from the sample
 * loop — I2C bus recovery takes milliseconds of bit-banging. */
osbams_status_t SensorManager_AttemptRecovery(sensor_manager_t *mgr)
{
    if (!mgr) return OSBAMS_STATUS_INVALID_ARGUMENT;

    bool any_offline = false;
    for (int i = 0; i < SENSOR_CH_COUNT; i++) {
        if (mgr->channels[i].health == SENSOR_HEALTH_OFFLINE) {
            any_offline = true;
            break;
        }
    }
    if (!any_offline) return OSBAMS_STATUS_OK;

    /* Recover the shared I2C bus, then re-init the affected drivers */
    I2C1_RecoverBus();

    /* FIX: BUS_VOLTAGE, CURRENT, and POWER all come from the SAME INA228
     * chip. The previous condition only reinitialized INA228 when
     * BUS_VOLTAGE specifically was OFFLINE -- a CURRENT-only or
     * POWER-only failure (voltage reads still succeeding) never
     * triggered recovery of the chip that's actually failing. Check all
     * three, and on successful reinit bring all three back online
     * together, since they share one INA228_Init() call. */
    bool ina228_needs_recovery =
        (mgr->channels[SENSOR_CH_BUS_VOLTAGE].health == SENSOR_HEALTH_OFFLINE) ||
        (mgr->channels[SENSOR_CH_CURRENT].health     == SENSOR_HEALTH_OFFLINE) ||
        (mgr->channels[SENSOR_CH_POWER].health       == SENSOR_HEALTH_OFFLINE);

    if (ina228_needs_recovery) {
        if (INA228_Init(OSBAMS_SHUNT_MICRO_OHM,
                        OSBAMS_INA228_IMAX_MA) == OSBAMS_STATUS_OK) {
            mgr->channels[SENSOR_CH_BUS_VOLTAGE].health = SENSOR_HEALTH_ONLINE;
            mgr->channels[SENSOR_CH_CURRENT].health     = SENSOR_HEALTH_ONLINE;
            mgr->channels[SENSOR_CH_POWER].health       = SENSOR_HEALTH_ONLINE;
            mgr->channels[SENSOR_CH_BUS_VOLTAGE].consecutive_failures = 0;
            mgr->channels[SENSOR_CH_CURRENT].consecutive_failures     = 0;
            mgr->channels[SENSOR_CH_POWER].consecutive_failures       = 0;
        }
    }

    if (mgr->channels[SENSOR_CH_TEMP_PACK].health == SENSOR_HEALTH_OFFLINE) {
        if (TC74_Init() == OSBAMS_STATUS_OK) {
            mgr->channels[SENSOR_CH_TEMP_PACK].health = SENSOR_HEALTH_ONLINE;
            mgr->channels[SENSOR_CH_TEMP_PACK].consecutive_failures = 0;
        }
    }

    return OSBAMS_STATUS_OK;
}
