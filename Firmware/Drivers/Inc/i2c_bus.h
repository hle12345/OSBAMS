/*
 * i2c_bus.h — RECONSTRUCTED from i2c_bus.c's definitions and every call
 * site (ina228.c, tc74.c, sensor_manager.c).
 *
 * NOTE: unlike every other driver in this tree, i2c_bus.c includes
 * "stm32l476xx.h" UNCONDITIONALLY (no #ifdef OSBAMS_TARGET_STM32 guard).
 * That means i2c_bus.c cannot be host-compiled as-is — it was never
 * covered by any of the existing test_*.c files either, which is
 * consistent with this (test_measurement.c and test_safety_modules.c
 * both avoid touching it). This is a pre-existing property of the
 * uploaded file, not something introduced here.
 */
#ifndef I2C_BUS_H
#define I2C_BUS_H

#include <stdint.h>
#include "osbams_status.h"

void            I2C1_Init(void);
osbams_status_t I2C1_RecoverBus(void);
osbams_status_t I2C1_WriteReg(uint8_t addr, uint8_t reg, const uint8_t *data, uint8_t len);
osbams_status_t I2C1_ReadReg(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len);
uint8_t         I2C1_Scan(uint8_t *addresses, uint8_t capacity);

#endif /* I2C_BUS_H */
