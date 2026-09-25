/*
 * ina228.h — INA228 Precision Current/Voltage/Power/Energy Monitor
 *
 * The INA228 is an 85 V, 20-bit I²C power monitor with an external shunt.
 * OSBAMS uses it because a fully charged 10S NMC pack reaches 42 V, which
 * exceeds the 36 V bus limit of an integrated-shunt part. Measuring a charged
 * pack safely REQUIRES a front end rated above the maximum pack voltage; the
 * INA228 provides that headroom.
 *
 * Bus voltage : 0–85 V, 195.3125 µV/LSB (Conversion register is 20-bit,
 *               left-justified in a 24-bit field; low 4 bits are status).
 * Shunt       : ±163.84 mV full scale, 312.5 nV/LSB (ADCRANGE = 0).
 * Temperature : internal die sensor, 7.8125 m°C/LSB (not the pack sensor —
 *               pack temperature is measured separately by the TC74).
 *
 * The shunt resistance and expected maximum current set the CURRENT_LSB and
 * the SHUNT_CAL register value per the datasheet:
 *
 *     CURRENT_LSB = I_max_expected / 2^19
 *     SHUNT_CAL   = 13107.2 × 10^6 × CURRENT_LSB × R_shunt   (ADCRANGE = 0)
 *
 * NOTE on i_max_milliamp: this sets the *digital scaling range* of the
 * INA228, not the operating limit. It must be given headroom ABOVE any
 * firmware protection threshold (see fault_manager.h), or a real fault
 * event at/above the threshold can saturate or sign-wrap the 20-bit
 * CURRENT register instead of reading correctly. OSBAMS calls this with
 * 30 A of scale even though the physical shunt (RSA-20-50) is rated 20 A
 * and the firmware hard trip is 18.5-20.0 A — see DESIGN_DECISIONS.md.
 *
 * All access goes through i2c_bus.c; this driver contains no bit-banging.
 */
#ifndef INA228_H
#define INA228_H

#include <stdint.h>
#include "osbams_status.h"

/* 7-bit I²C address, A0=GND A1=GND. Left-shifted for the 8-bit bus API. */
#define INA228_I2C_ADDR   (0x40U << 1)

/* Register map (subset used by OSBAMS) */
#define INA228_REG_CONFIG      0x00U   /* configuration, RST bit */
#define INA228_REG_ADC_CONFIG  0x01U   /* mode, conversion times, averaging */
#define INA228_REG_SHUNT_CAL   0x02U   /* calibration */
#define INA228_REG_VSHUNT      0x04U   /* shunt voltage, 24-bit */
#define INA228_REG_VBUS        0x05U   /* bus voltage, 24-bit */
#define INA228_REG_DIETEMP     0x06U   /* die temperature, 16-bit */
#define INA228_REG_CURRENT     0x07U   /* current, 24-bit */
#define INA228_REG_POWER       0x08U   /* power, 24-bit */
#define INA228_REG_DIAG_ALRT   0x0BU   /* diagnostic flags, incl. CNVRF (conversion-ready) */
#define INA228_REG_MFR_ID      0x3EU   /* returns 'TI' (0x5449) */
#define INA228_REG_DEV_ID      0x3FU   /* device ID, 0x228x */

#define INA228_MFR_ID_TI       0x5449U
#define INA228_DEV_ID_MASK     0xFFF0U
#define INA228_DEV_ID_228      0x2280U

/* DIAG_ALRT bit 1 = CNVRF (Conversion Ready Flag). Cleared on read of this
 * register or on a new read of a conversion result register per datasheet. */
#define INA228_DIAG_ALRT_CNVRF (1U << 1)

/**
 * @brief Compute the SHUNT_CAL register value for a given shunt and range.
 *
 * Pure function, no I²C traffic — exposed specifically so this arithmetic
 * can be unit-tested on the host without hardware. This is the same
 * computation INA228_Init() performs internally before writing the
 * register; keep the two in sync.
 *
 * @param shunt_micro_ohm  shunt resistance in micro-ohms (e.g. 2500 = 2.5 mΩ)
 * @param i_max_milliamp   digital full-scale current in mA (e.g. 30000 = 30 A)
 * @return SHUNT_CAL register value, clamped to the 15-bit field (0x7FFF max)
 */
uint16_t INA228_CalcShuntCal(uint32_t shunt_micro_ohm, uint32_t i_max_milliamp);

/**
 * @brief Configure the INA228 for the given shunt and expected current.
 *
 * Computes CURRENT_LSB and SHUNT_CAL, resets the device, then programs the
 * calibration and a continuous bus+shunt+temperature conversion mode.
 *
 * @param shunt_micro_ohm   shunt resistance in micro-ohms (e.g. 2000 = 2 mΩ)
 * @param i_max_milliamp    expected maximum current magnitude in mA
 * @return OSBAMS_STATUS_OK on success; a bus/verify error otherwise
 */
osbams_status_t INA228_Init(uint32_t shunt_micro_ohm, uint32_t i_max_milliamp);

/**
 * @brief Verify the device by reading the manufacturer and device IDs.
 * @return OSBAMS_STATUS_OK if both IDs match the INA228.
 */
osbams_status_t INA228_Probe(void);

/** @brief Bus voltage in millivolts (0–85000). Output param, typed status. */
osbams_status_t INA228_ReadBus_mV(int32_t *out_mv);

/**
 * @brief Current in milliamps; sign follows the shunt polarity.
 *
 * @param out_ma       output current, milliamps
 * @param out_is_fresh set true if this sample reflects a conversion that
 *                      completed since the last read (via DIAG_ALRT.CNVRF),
 *                      false if it may be a repeat of a previously-read
 *                      sample (e.g. caller is polling faster than the
 *                      ~50 ms conversion cycle). Fault-manager debounce
 *                      logic (e.g. "2 consecutive fresh readings") MUST
 *                      gate on this flag, not just on read count, or a
 *                      single real over-threshold event can be read twice
 *                      and satisfy a 2-sample debounce on its own.
 *                      Pass NULL if freshness isn't needed by the caller.
 */
osbams_status_t INA228_ReadCurrent_mA(int32_t *out_ma, uint8_t *out_is_fresh);

/** @brief Power in milliwatts (always positive per datasheet). */
osbams_status_t INA228_ReadPower_mW(int32_t *out_mw);

/** @brief Shunt voltage in microvolts (diagnostic / calibration use). */
osbams_status_t INA228_ReadShunt_uV(int32_t *out_uv);

#endif /* INA228_H */
