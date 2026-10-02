/*
 * integrator.h — STM32-side timestamp-based Ah/Wh integration (protocol v2 fields Q_mcu / E_mcu).
 *
 * Integrates |current| and |power| with the ACTUAL elapsed time between samples (trapezoidal rule), accumulating
 * mA*us and mW*us (twice the integral, so the trapezoid's /2 never truncates). Magnitudes are integrated, matching the Pi
 * reconstruction (services/charge_integration.py) and the INA228 ENERGY register (unsigned).
 *
 * Defined behaviour (all latched in flags until Integrator_Reset):
 *   - first valid sample after reset is the baseline: nothing is integrated, totals are "unavailable";
 *   - invalid sample (caller says the channel failed): not integrated, NOT replaced by zero; the next valid sample
 *     integrates across it; flag INTEG_F_INVALID_SAMPLE;
 *   - timestamp equal to or earlier than the baseline: not integrated, flag INTEG_F_TIME_JUMP, the new sample becomes the baseline;
 *   - interval longer than max_gap_us: not integrated, flag INTEG_F_GAP, new sample becomes the baseline;
 *   - 64-bit overflow: flag INTEG_F_OVERFLOW, accumulators frozen (never wrapped), totals unavailable until reset.
 * Reset is explicit (Integrator_Reset); nothing here talks to hardware, the relay, the load or the safety state.
 * INTEG_DEFAULT_MAX_GAP_US is PROVISIONAL — set it from first-article acquisition-timing data (BENCH_REQUIRED).
 */
#ifndef INTEGRATOR_H
#define INTEGRATOR_H

#include <stdint.h>
#include <stdbool.h>

#define INTEG_DEFAULT_MAX_GAP_US   10000000ULL    /* PROVISIONAL: 10 s */

#define INTEG_F_GAP              (1U << 0)
#define INTEG_F_TIME_JUMP        (1U << 1)
#define INTEG_F_INVALID_SAMPLE   (1U << 2)
#define INTEG_F_OVERFLOW         (1U << 3)

typedef enum {
    INTEG_ADDED = 0,        /* interval integrated */
    INTEG_BASELINE,         /* first valid sample: stored as baseline */
    INTEG_SKIP_INVALID,
    INTEG_SKIP_GAP,
    INTEG_SKIP_TIME,
    INTEG_OVERFLOW,
    INTEG_BAD_ARG
} integ_result_t;

typedef struct {
    bool     have_base;
    uint64_t base_t_us;
    int64_t  base_i_ma_abs, base_p_mw_abs;
    int64_t  acc_ma_us2, acc_mw_us2;          /* 2 x integral */
    uint64_t max_gap_us;
    uint32_t samples, intervals, gap_count, time_jump_count, invalid_count;
    uint8_t  flags;
} integrator_t;

void           Integrator_Init(integrator_t *it, uint64_t max_gap_us);
void           Integrator_Reset(integrator_t *it);            /* keeps max_gap_us */
integ_result_t Integrator_Add(integrator_t *it, uint64_t t_us, int32_t i_ma, int32_t p_mw, bool valid);
bool           Integrator_GetUah(const integrator_t *it, int64_t *out_uah);   /* false = unavailable */
bool           Integrator_GetUwh(const integrator_t *it, int64_t *out_uwh);
uint8_t        Integrator_Flags(const integrator_t *it);
uint32_t       Integrator_Samples(const integrator_t *it);
uint32_t       Integrator_GapCount(const integrator_t *it);
uint32_t       Integrator_TimeJumpCount(const integrator_t *it);
uint32_t       Integrator_InvalidCount(const integrator_t *it);

#endif /* INTEGRATOR_H */
