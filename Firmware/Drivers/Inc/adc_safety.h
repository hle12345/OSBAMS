/*
 * adc_safety.h — RECONSTRUCTED from adc_safety.c and sensor_manager.c
 * call sites.
 */
#ifndef ADC_SAFETY_H
#define ADC_SAFETY_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

osbams_status_t AdcSafety_Init(void);
osbams_status_t AdcSafety_ReadVoltage_mV(int32_t *voltage_mv);
bool            AdcSafety_Disagrees(int32_t ina228_mv, int32_t adc_mv);

#endif /* ADC_SAFETY_H */
