/*
 * tc74.h — TC74_I2C_ADDR CONFIRMED against actual purchase, not the BOM
 * spreadsheet. OSBAMS_BOM.xlsx lists U3 as TC74A0-5.0VAT (-> 0x48), but
 * that line is stale: the Mouser order record for the part actually
 * bought is TC74A5-3.3VAT (Mouser #579-TC74A5-3.3VAT), which is the A5
 * address variant -> 0x4D, and the 3.3V-native part (correct choice for
 * the Nucleo's 3V3 rail; the A0 part was the 5.0V variant, which would
 * have been a rail mismatch). The BOM spreadsheet should be updated to
 * match this — it's the source of the earlier 0x48 confusion, not the
 * firmware.
 *
 * Same pre-shifted 8-bit convention as ina228.h's INA228_I2C_ADDR
 * (i2c_bus.c masks with &0xFE, treating bit0 as R/W).
 */
#ifndef TC74_H
#define TC74_H

#include <stdint.h>
#include "osbams_status.h"

#define TC74_I2C_ADDR   (0x4DU << 1)   /* TC74A5-3.3VAT, confirmed via Mouser order */

osbams_status_t TC74_Init(void);
osbams_status_t TC74_ReadTemperature_C10(int16_t *t);

#endif /* TC74_H */
