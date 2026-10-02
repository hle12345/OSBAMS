/*
 * test_ina228_calibration.c — regression test for the SHUNT_CAL scaling bug
 *
 * Exercises INA228_CalcShuntCal() only (pure math, no I2C traffic) so it
 * runs on the host with no hardware. This is the test both build-order
 * reviews called for: it must fail loudly if the /1e13 vs /1e10 divisor
 * bug (or anything equivalent) ever comes back.
 *
 * Build (host, no target toolchain needed):
 *   gcc -I../Inc -I. -o test_ina228_calibration \
 *       test_ina228_calibration.c ../Src/ina228.c
 *   ./test_ina228_calibration
 *
 * NOTE: this Makefile/include path assumes i2c_bus_stub.h and
 * osbams_status_stub.h are visible in place of the real headers -- see
 * those files' comments. Reconcile with the real Tests/Makefile and
 * host_stubs.h once available; this file's assertions are the part that
 * matters and should carry over unchanged.
 */
#include <assert.h>
#include <stdio.h>
#include "ina228.h"
#include "app_config.h"

int main(void)
{
    /* --- The case that was broken: RSA-20-50, 2.5 mOhm shunt, 20 A scale.
     * Expected ~1250 per the datasheet formula run independently:
     *   SHUNT_CAL = 13107.2e6 * 38.146e-6 A/LSB * 0.0025 Ohm ~= 1250
     * The old /1e13 divisor produced 1, which silently made current/power
     * reads ~1000x too small instead of erroring. */
    uint16_t cal_20A = INA228_CalcShuntCal(2500U, 20000U);
    printf("CalcShuntCal(2500uOhm, 20000mA) = %u (expect 1249-1251)\n", cal_20A);
    assert(cal_20A >= 1249U);
    assert(cal_20A <= 1251U);

    /* --- The scale actually used in INA228_Init() per the frozen decision
     * to give the digital range headroom above the 18.5-20.0 A firmware
     * trip (see fault threshold review). 30 A scale, same 2.5 mOhm shunt.
     * CURRENT_LSB GROWS with i_max_milliamp (coarser resolution at wider
     * range), and SHUNT_CAL is proportional to CURRENT_LSB -- so SHUNT_CAL
     * scales UP with i_max, not down. Expect ~1250 * (30/20) ~= 1875. */
    uint16_t cal_30A = INA228_CalcShuntCal(2500U, 30000U);
    printf("CalcShuntCal(2500uOhm, 30000mA) = %u (expect 1873-1876)\n", cal_30A);
    assert(cal_30A >= 1873U);
    assert(cal_30A <= 1876U);

    /* --- Rev.2 configuration actually compiled into the firmware: 20 A scale -> SHUNT_CAL 1250. */
    uint16_t cal_cfg = INA228_CalcShuntCal(OSBAMS_SHUNT_MICRO_OHM, OSBAMS_INA228_IMAX_MA);
    printf("CalcShuntCal(app_config) = %u (expect 1249-1251)\n", cal_cfg);
    assert(cal_cfg >= 1249U && cal_cfg <= 1251U);

    /* --- Guard against the old bug's specific failure mode: cal must
     * never come back as 0 or 1 for any physically sane shunt/range pair
     * OSBAMS would actually use. A value that small is the signature of
     * the 1000x scaling error, whatever caused it this time. */
    assert(cal_20A > 100U);
    assert(cal_30A > 100U);

    /* --- Degenerate inputs must fail safe (return 0), not divide-by-zero
     * or wrap around to a bogus nonzero register value. */
    assert(INA228_CalcShuntCal(0U, 20000U) == 0U);
    assert(INA228_CalcShuntCal(2500U, 0U) == 0U);

    /* --- Clamp check: an absurdly large shunt/range combination must
     * clamp to the 15-bit register field (0x7FFF), not overflow/truncate
     * into a small or negative-looking value on write. */
    uint16_t cal_clamped = INA228_CalcShuntCal(1000000U, 1U);
    printf("CalcShuntCal(clamp case) = %u (expect <= 0x7FFF)\n", cal_clamped);
    assert(cal_clamped <= 0x7FFFU);

    printf("All INA228 calibration tests passed.\n");
    return 0;
}
