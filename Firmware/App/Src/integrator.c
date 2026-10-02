/* integrator.c — see integrator.h for the contract. Pure logic: no hardware, no safety/relay/load code. */
#include "integrator.h"
#include <string.h>

#define UNIT_DEN2   7200000LL      /* mA*us (x2) -> uAh and mW*us (x2) -> uWh: value / 3.6e6, trapezoid /2 folded in */

static int64_t abs64(int64_t v) { return v < 0 ? -v : v; }

void Integrator_Init(integrator_t *it, uint64_t max_gap_us)
{
    if (!it) return;
    memset(it, 0, sizeof *it);
    it->max_gap_us = max_gap_us ? max_gap_us : INTEG_DEFAULT_MAX_GAP_US;
}

void Integrator_Reset(integrator_t *it)
{
    if (!it) return;
    Integrator_Init(it, it->max_gap_us);
}

static void rebase(integrator_t *it, uint64_t t, int64_t i, int64_t p)
{
    it->have_base = true; it->base_t_us = t; it->base_i_ma_abs = i; it->base_p_mw_abs = p;
}

integ_result_t Integrator_Add(integrator_t *it, uint64_t t_us, int32_t i_ma, int32_t p_mw, bool valid)
{
    if (!it) return INTEG_BAD_ARG;
    if (it->flags & INTEG_F_OVERFLOW) return INTEG_OVERFLOW;
    it->samples++;

    if (!valid) {
        it->invalid_count++; it->flags |= INTEG_F_INVALID_SAMPLE;
        return INTEG_SKIP_INVALID;
    }
    int64_t i = abs64(i_ma), p = abs64(p_mw);

    if (!it->have_base) { rebase(it, t_us, i, p); return INTEG_BASELINE; }

    if (t_us <= it->base_t_us) {
        it->time_jump_count++; it->flags |= INTEG_F_TIME_JUMP;
        rebase(it, t_us, i, p);
        return INTEG_SKIP_TIME;
    }
    uint64_t dt = t_us - it->base_t_us;
    if (dt > it->max_gap_us) {
        it->gap_count++; it->flags |= INTEG_F_GAP;
        rebase(it, t_us, i, p);
        return INTEG_SKIP_GAP;
    }

    int64_t si = it->base_i_ma_abs + i, sp = it->base_p_mw_abs + p;          /* <= 2^32, fits */
    if ((si > 0 && (uint64_t)si > (uint64_t)INT64_MAX / dt) || (sp > 0 && (uint64_t)sp > (uint64_t)INT64_MAX / dt)) {
        it->flags |= INTEG_F_OVERFLOW; return INTEG_OVERFLOW;
    }
    int64_t di = si * (int64_t)dt, dp = sp * (int64_t)dt;
    if (di > INT64_MAX - it->acc_ma_us2 || dp > INT64_MAX - it->acc_mw_us2) {
        it->flags |= INTEG_F_OVERFLOW; return INTEG_OVERFLOW;
    }
    it->acc_ma_us2 += di; it->acc_mw_us2 += dp;
    it->intervals++;
    rebase(it, t_us, i, p);
    return INTEG_ADDED;
}

static bool get(const integrator_t *it, int64_t acc, int64_t *out)
{
    if (!it || !out || (it->flags & INTEG_F_OVERFLOW) || it->intervals == 0) return false;
    *out = (acc + UNIT_DEN2 / 2) / UNIT_DEN2;
    return true;
}
bool Integrator_GetUah(const integrator_t *it, int64_t *out) { return get(it, it ? it->acc_ma_us2 : 0, out); }
bool Integrator_GetUwh(const integrator_t *it, int64_t *out) { return get(it, it ? it->acc_mw_us2 : 0, out); }
uint8_t  Integrator_Flags(const integrator_t *it)         { return it ? it->flags : 0; }
uint32_t Integrator_Samples(const integrator_t *it)       { return it ? it->samples : 0; }
uint32_t Integrator_GapCount(const integrator_t *it)      { return it ? it->gap_count : 0; }
uint32_t Integrator_TimeJumpCount(const integrator_t *it) { return it ? it->time_jump_count : 0; }
uint32_t Integrator_InvalidCount(const integrator_t *it)  { return it ? it->invalid_count : 0; }
