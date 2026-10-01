/*
 * test_ina228_power_decode.c — regression test for the POWER register
 * decode bug: rd24() shifts right by 4 (correct for VBUS/VSHUNT/CURRENT,
 * which are 20-bit results left-justified in a 24-bit field) but POWER is
 * a real 24-bit unsigned result with no reserved bits. Using the shifted
 * path divided POWER by 16.
 *
 * Mocks I2C1_ReadReg/WriteReg (same technique test_measurement.c uses for
 * SensorManager_ReadAll) so this runs on the host with no hardware, and
 * feeds a KNOWN raw register value so the exact expected decode can be
 * computed independently and compared.
 */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ina228.h"
#include "i2c_bus.h"

/* ── Mock I2C: scripted register responses ─────────────────────────── */
static uint8_t s_mfr_id[2]    = { 0x54, 0x49 };   /* 'T','I' */
static uint8_t s_dev_id[2]    = { 0x22, 0x80 };   /* INA228 */
static uint8_t s_power_reg[3] = { 0, 0, 0 };       /* set per test case */

osbams_status_t I2C1_ReadReg(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len)
{
    (void)addr;
    if (reg == INA228_REG_MFR_ID)   { memcpy(data, s_mfr_id, 2); return OSBAMS_STATUS_OK; }
    if (reg == INA228_REG_DEV_ID)   { memcpy(data, s_dev_id, 2); return OSBAMS_STATUS_OK; }
    if (reg == INA228_REG_POWER)    { memcpy(data, s_power_reg, 3); return OSBAMS_STATUS_OK; }
    (void)len;
    return OSBAMS_STATUS_NOT_READY;   /* anything else unscripted for this test */
}

osbams_status_t I2C1_WriteReg(uint8_t addr, uint8_t reg, const uint8_t *data, uint8_t len)
{
    (void)addr; (void)reg; (void)data; (void)len;
    return OSBAMS_STATUS_OK;   /* INA228_Init()'s config writes succeed silently */
}

int main(void)
{
    /* Bring the driver up exactly as sensor_manager.c does: RSA-20-50
     * (2.5 mOhm) with 30 A digital scale headroom. */
    osbams_status_t st = INA228_Init(2500U, 30000U);
    assert(st == OSBAMS_STATUS_OK);

    /* current_lsb_nA for i_max=30000mA: (30000*1e6)/524288 = 57220 (nA)
     * (matches test_ina228_calibration.c's independently-verified value). */
    const int64_t current_lsb_nA = 57220;

    /* ── Case 1: known raw POWER code ────────────────────────────────
     * Pick a raw 24-bit code that is NOT a multiple of 16, specifically
     * so a lingering >>4 bug would silently truncate/lose bits rather
     * than just scaling cleanly — a stronger test than a round number.
     * raw = 0x030D41 (200,001 decimal). */
    uint32_t raw = 0x030D41U;
    s_power_reg[0] = (uint8_t)(raw >> 16);
    s_power_reg[1] = (uint8_t)(raw >> 8);
    s_power_reg[2] = (uint8_t)(raw);

    int32_t mw = 0;
    st = INA228_ReadPower_mW(&mw);
    assert(st == OSBAMS_STATUS_OK);

    /* Correct formula (no shift): mW = raw * 32 * CURRENT_LSB_nA / 1e7 */
    int64_t expected_correct = ((int64_t)raw * 32 * current_lsb_nA) / 10000000LL;
    /* The bug's formula, for contrast: same math but on (raw >> 4). */
    int64_t buggy_would_give = (((int64_t)(raw >> 4)) * 32 * current_lsb_nA) / 10000000LL;

    printf("raw=0x%06X  correct_mW=%lld  buggy_mW_would_be=%lld  got_mW=%d\n",
           raw, (long long)expected_correct, (long long)buggy_would_give, mw);

    assert((int64_t)mw == expected_correct);
    /* Explicitly prove we did NOT reproduce the bug's (much smaller,
     * ~16x-off) answer -- guards against a future edit reintroducing the
     * shift on this path without anyone noticing the value just got
     * quietly smaller. */
    assert((int64_t)mw != buggy_would_give);
    assert(expected_correct > buggy_would_give * 10);  /* confirms the ~16x gap is real */

    printf("POWER decode test passed: full 24-bit value used, no spurious >>4.\n");
    return 0;
}
