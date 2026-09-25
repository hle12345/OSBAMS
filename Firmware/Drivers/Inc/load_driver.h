/*
 * load_driver.h — Electronic Load Control with Fail-Safe Disconnect
 *
 * Load_Disable() returns OSBAMS_STATUS_OK only when a real hardware action
 * occurred AND feedback confirmed it. With no feedback wired it returns
 * OSBAMS_STATUS_NOT_SUPPORTED so the caller knows the state is unverified.
 */
#ifndef LOAD_DRIVER_H
#define LOAD_DRIVER_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

osbams_status_t Load_Init(void);
osbams_status_t Load_Enable(void);
osbams_status_t Load_Disable(void);
void Load_EmergencyDisable(void);
osbams_status_t Load_ConfirmOffByCurrent(int32_t measured_current_ma);
osbams_status_t Load_SetCurrent_mA(uint32_t current_ma);

/**
 * @brief Pure polarity decode for PC9 K1 feedback (VO610A), exposed for
 * host-side regression testing — same pattern as INA228_CalcShuntCal.
 *
 * FROZEN: PC9 = K1 voltage-feedback, ACTIVE LOW. Raw bit CLEAR (0) means
 * K1 closed / HV present downstream = confirmed ON. Raw bit SET (1)
 * means K1 open = confirmed OFF.
 *
 * @param raw_bit_is_set  true if the raw IDR bit read HIGH, false if LOW
 * @return true if this decodes to "load/contactor confirmed ON"
 */
bool Load_DecodeFeedbackActiveLow(bool raw_bit_is_set);

bool     Load_IsEnabled(void);
bool     Load_HasFeedback(void);
uint32_t Load_DisableCount(void);
uint32_t Load_ConfirmFailCount(void);

#endif /* LOAD_DRIVER_H */
