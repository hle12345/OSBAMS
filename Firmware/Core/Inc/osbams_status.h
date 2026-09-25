/*
 * osbams_status.h — RECONSTRUCTED from usage across every uploaded .c
 * file. This exact set of members is the complete set referenced
 * anywhere in the codebase (grep-verified against ina228.c, load_driver.c,
 * i2c_bus.c, sensor_manager.c, watchdog.c, adc_safety.c, tc74.c,
 * acquisition_timer.c, estop.c, measurement.c). The real header was never
 * uploaded — diff against it before treating this as authoritative,
 * particularly if it defines additional members not exercised by any
 * file seen so far.
 */
#ifndef OSBAMS_STATUS_H
#define OSBAMS_STATUS_H

typedef enum {
    OSBAMS_STATUS_OK = 0,
    OSBAMS_STATUS_INVALID_ARGUMENT,
    OSBAMS_STATUS_NOT_READY,
    OSBAMS_STATUS_TIMEOUT,
    OSBAMS_STATUS_BUS_ERROR,
    OSBAMS_STATUS_NACK,
    OSBAMS_STATUS_WRONG_DEVICE,
    OSBAMS_STATUS_LOAD_STUCK,
    OSBAMS_STATUS_NOT_SUPPORTED,
    OSBAMS_STATUS_BUSY,
    OSBAMS_STATUS_SENSOR_FAILURE
} osbams_status_t;

#endif /* OSBAMS_STATUS_H */
