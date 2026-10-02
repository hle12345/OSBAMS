/* accum_session.c — see accum_session.h. Pure logic; no safety/relay/load code. */
#include "accum_session.h"
#include <stdio.h>
#include <string.h>

void AccumSession_Init(accum_session_t *s, accum_hw_reset_fn hw_reset, uint64_t max_gap_us)
{
    if (!s) return;
    memset(s, 0, sizeof *s);
    s->hw_reset = hw_reset;
    Integrator_Init(&s->integ, max_gap_us);
}

bool AccumSession_StateAllowsStart(test_state_t st)
{
    switch (st) {
        case TEST_IDLE: case TEST_PACK_DETECTED: case TEST_PRECHECK: case TEST_READY: case TEST_COMPLETE:
            return true;
        default:
            return false;       /* BOOT, SELF_TEST, RESTING, DISCHARGING, PAUSED, CUTOFF, RECOVERY, FAULT, E_STOP, unknown */
    }
}

accum_start_result_t AccumSession_Start(accum_session_t *s, test_state_t st)
{
    if (!s) return ACCUM_START_BAD_ARG;
    if (!AccumSession_StateAllowsStart(st)) return ACCUM_START_REFUSED_STATE;       /* nothing is touched */

    bool hw_ok = true;
    if (s->hw_reset) hw_ok = (s->hw_reset() == OSBAMS_STATUS_OK);
    Integrator_Reset(&s->integ);                  /* reset together; STM32 side is reset even if the INA228 reset failed */
    s->acq_count = 0;
    s->started = true;
    s->hw_reset_failed = !hw_ok;
    return hw_ok ? ACCUM_START_OK : ACCUM_START_HW_RESET_FAILED;
}

void AccumSession_OnSample(accum_session_t *s, uint64_t t_us, int32_t i_ma, int32_t p_mw, bool valid)
{
    if (!s) return;
    s->acq_count++;
    Integrator_Add(&s->integ, t_us, i_ma, p_mw, valid);
}

bool AccumSession_HandleCommand(accum_session_t *s, const char *line, test_state_t st, char *resp, size_t cap)
{
    if (!s || !line || !resp || cap == 0 || strcmp(line, "ACCUM_START") != 0) return false;
    const char *r;
    switch (AccumSession_Start(s, st)) {
        case ACCUM_START_OK:               r = "OSBAMS,ACCUM,STARTED\r\n"; break;
        case ACCUM_START_HW_RESET_FAILED:  r = "OSBAMS,ACCUM,STARTED_HW_RESET_FAILED\r\n"; break;
        default:                           r = "OSBAMS,ACCUM,REFUSED,STATE\r\n"; break;
    }
    snprintf(resp, cap, "%s", r);
    return true;
}

void AccumSession_BuildExtra(const accum_session_t *s, bool adc_valid, int32_t adc_mv, const ina228_accum_snapshot_t *ina,
                             uint16_t base_status, protocol_v2_extra_t *out)
{
    if (!out) return;
    memset(out, 0, sizeof *out);
    out->sensor_status = base_status;
    out->v_adc_valid = adc_valid;
    if (adc_valid) out->v_adc_mv = adc_mv;
    if (!s) return;
    out->acq_count = s->acq_count;
    if (!s->started) return;                                  /* accumulators only exist after an explicit start */

    int64_t v;
    if (Integrator_GetUah(&s->integ, &v)) { out->q_mcu_valid = true; out->q_mcu_uah = v; }
    if (Integrator_GetUwh(&s->integ, &v)) { out->e_mcu_valid = true; out->e_mcu_uwh = v; }

    uint8_t f = Integrator_Flags(&s->integ);
    if (f & INTEG_F_TIME_JUMP)      out->sensor_status |= PROTO_SS_TIME_JUMP;
    if (f & INTEG_F_GAP)            out->sensor_status |= PROTO_SS_INTEG_GAP;
    if (f & INTEG_F_INVALID_SAMPLE) out->sensor_status |= PROTO_SS_SAMPLE_INVALID;
    if (f & INTEG_F_OVERFLOW)       out->sensor_status |= PROTO_SS_ACCUM_INVALID;
    if (s->hw_reset_failed)         out->sensor_status |= PROTO_SS_ACCUM_INVALID;

    if (ina && ina->valid && !s->hw_reset_failed) {
        out->q_ina_valid = true; out->q_ina_uah = ina->q_uah;
        out->e_ina_valid = true; out->e_ina_uwh = ina->e_uwh;
        if (ina->flags & INA228_ACCUM_F_DECREASE) out->sensor_status |= PROTO_SS_ACCUM_INVALID;
    }
}
