/*
 * acquisition_timer.h — RECONSTRUCTED from acquisition_timer.c and its
 * call sites in main.c.
 */
#ifndef ACQUISITION_TIMER_H
#define ACQUISITION_TIMER_H

#include <stdint.h>
#include <stdbool.h>
#include "osbams_status.h"

osbams_status_t AcquisitionTimer_Init(uint32_t period_ms);
osbams_status_t AcquisitionTimer_Start(void);
osbams_status_t AcquisitionTimer_Stop(void);
bool            AcquisitionTimer_SampleDue(void);
uint32_t        AcquisitionTimer_PendingCount(void);
void            AcquisitionTimer_OnUpdate(void);

#endif /* ACQUISITION_TIMER_H */
