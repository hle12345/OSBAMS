/*
 * i2c_bus_link_stub.c — link-only stub bodies for host tests. Matches the
 * REAL i2c_bus.c signatures exactly (uint8_t addr/reg/len, not the
 * placeholder uint16_t used before the real i2c_bus.c was available).
 * Never exercised by test_ina228_calibration.c, which only calls the
 * pure INA228_CalcShuntCal() function — these exist purely so the rest
 * of ina228.c links.
 */
#include "i2c_bus.h"

osbams_status_t I2C1_ReadReg(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len)
{
    (void)addr; (void)reg; (void)data; (void)len;
    return OSBAMS_STATUS_NOT_READY;
}

osbams_status_t I2C1_WriteReg(uint8_t addr, uint8_t reg, const uint8_t *data, uint8_t len)
{
    (void)addr; (void)reg; (void)data; (void)len;
    return OSBAMS_STATUS_NOT_READY;
}
