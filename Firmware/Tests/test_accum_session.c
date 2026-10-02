/*
 * test_accum_session.c — explicit accumulator start/reset, ACCUM_START command gating, and protocol v2 field assembly (host).
 * Safety/relay/load control and the protocol version are independent of everything tested here.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include "accum_session.h"
#include "protocol.h"

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("  FAIL  %s\n", msg); failures++; } else printf("  PASS  %s\n", msg); } while (0)

static int hw_resets = 0; static osbams_status_t hw_result = OSBAMS_STATUS_OK;
static osbams_status_t fake_hw_reset(void) { hw_resets++; return hw_result; }

static void feed(accum_session_t *s, int n, int32_t i_ma)       /* n one-second samples */
{
    for (int k = 0; k < n; k++) AccumSession_OnSample(s, (uint64_t)(k + 1) * 1000000ULL, i_ma, 100000, true);
}

int main(void)
{
    printf("accumulator session tests\n");
    accum_session_t s;
    protocol_v2_extra_t x;
    char resp[PROTOCOL_V2_FRAME_MAX];

    /* ---- which states may start/reset ---- */
    const test_state_t ok_states[]  = { TEST_IDLE, TEST_PACK_DETECTED, TEST_PRECHECK, TEST_READY, TEST_COMPLETE };
    const test_state_t bad_states[] = { TEST_BOOT, TEST_SELF_TEST, TEST_RESTING, TEST_DISCHARGING, TEST_PAUSED, TEST_CUTOFF,
                                        TEST_RECOVERY, TEST_FAULT, TEST_ESTOP };
    bool all_ok = true, all_bad = true;
    for (unsigned k = 0; k < sizeof ok_states / sizeof ok_states[0]; k++) all_ok &= AccumSession_StateAllowsStart(ok_states[k]);
    for (unsigned k = 0; k < sizeof bad_states / sizeof bad_states[0]; k++) all_bad &= !AccumSession_StateAllowsStart(bad_states[k]);
    CHECK(all_ok, "start/reset allowed only before a run or after it completes (IDLE..READY, COMPLETE)");
    CHECK(all_bad, "start/reset refused during BOOT, SELF_TEST, RESTING, DISCHARGING, PAUSED, CUTOFF, RECOVERY, FAULT, E_STOP");

    /* ---- before any start: fields are unavailable, never 0 ---- */
    AccumSession_Init(&s, fake_hw_reset, 0);
    AccumSession_OnSample(&s, 1000000, 3000, 120000, true);
    AccumSession_BuildExtra(&s, true, 41790, NULL, 0, &x);
    CHECK(!x.q_ina_valid && !x.q_mcu_valid && !x.e_ina_valid && !x.e_mcu_valid, "before start every accumulator field is NA");
    CHECK(x.v_adc_valid && x.v_adc_mv == 41790, "independent ADC voltage is passed through");

    /* ---- start resets hardware and STM32 together ---- */
    hw_resets = 0;
    CHECK(AccumSession_Start(&s, TEST_READY) == ACCUM_START_OK && hw_resets == 1, "start from READY resets the INA228 accumulators once");
    feed(&s, 11, 3000);                                    /* 10 intervals of 1 s at 3 A */
    ina228_accum_snapshot_t ina = { .valid = true, .q_uah = 8330, .e_uwh = 333000, .flags = 0 };
    AccumSession_BuildExtra(&s, true, 41790, &ina, 0, &x);
    CHECK(x.q_mcu_valid && x.q_mcu_uah == 8333, "STM32 charge = 3 A x 10 s = 8333 uAh");
    CHECK(x.q_ina_valid && x.q_ina_uah == 8330 && x.e_ina_valid && x.e_ina_uwh == 333000, "INA228 values come from the snapshot");
    CHECK(x.e_mcu_valid && x.e_mcu_uwh == 277778, "STM32 energy = 100 W x 10 s = 277,778 uWh");
    CHECK(x.acq_count == 11 && x.sensor_status == 0, "acq_count counts samples since start; clean status");

    /* a measured zero is 0, not NA */
    accum_session_t z; AccumSession_Init(&z, NULL, 0);
    AccumSession_Start(&z, TEST_READY);
    AccumSession_OnSample(&z, 1000000, 0, 0, true); AccumSession_OnSample(&z, 2000000, 0, 0, true);
    ina228_accum_snapshot_t zi = { .valid = true, .q_uah = 0, .e_uwh = 0, .flags = 0 };
    AccumSession_BuildExtra(&z, true, 0, &zi, 0, &x);
    CHECK(x.q_mcu_valid && x.q_mcu_uah == 0 && x.q_ina_valid && x.q_ina_uah == 0 && x.v_adc_valid && x.v_adc_mv == 0, "measured zero stays 0 (valid), not NA");

    /* ---- reset during an active test is refused and changes nothing ---- */
    hw_resets = 0;
    int64_t keep = x.q_mcu_uah; (void)keep;
    uint32_t acq_before = s.acq_count;
    for (unsigned k = 0; k < sizeof bad_states / sizeof bad_states[0]; k++) {
        CHECK(AccumSession_Start(&s, bad_states[k]) == ACCUM_START_REFUSED_STATE, "refused in a disallowed state");
        if (failures) break;
    }
    CHECK(hw_resets == 0 && s.acq_count == acq_before, "refused start touched neither hardware nor STM32 accumulators");
    CHECK(AccumSession_Start(&s, TEST_READY) == ACCUM_START_OK && s.acq_count == 0, "start from READY resets the STM32 side and the counter");
    AccumSession_BuildExtra(&s, true, 1, &ina, 0, &x);
    CHECK(!x.q_mcu_valid, "after a reset the STM32 totals are NA until the first interval exists");

    /* ---- command gating ---- */
    hw_resets = 0;
    CHECK(AccumSession_HandleCommand(&s, "ACCUM_START", TEST_DISCHARGING, resp, sizeof resp) && strcmp(resp, "OSBAMS,ACCUM,REFUSED,STATE\r\n") == 0,
          "ACCUM_START during DISCHARGING is answered REFUSED,STATE");
    CHECK(hw_resets == 0, "refused command did not reset the INA228");
    CHECK(AccumSession_HandleCommand(&s, "ACCUM_START", TEST_READY, resp, sizeof resp) && strcmp(resp, "OSBAMS,ACCUM,STARTED\r\n") == 0 && hw_resets == 1,
          "ACCUM_START in READY is answered STARTED and resets");
    CHECK(!AccumSession_HandleCommand(&s, "ACK", TEST_FAULT, resp, sizeof resp), "ACK is not handled here (existing ACK path untouched)");
    CHECK(!AccumSession_HandleCommand(&s, "ACCUM_STARTX", TEST_READY, resp, sizeof resp), "near-miss command is not handled");
    CHECK(!AccumSession_HandleCommand(&s, NULL, TEST_READY, resp, sizeof resp), "NULL line is not handled");

    /* ---- hardware reset failure: STM32 still resets, INA fields NA, ACCUM_INVALID until a clean start ---- */
    hw_result = OSBAMS_STATUS_BUS_ERROR;
    CHECK(AccumSession_Start(&s, TEST_READY) == ACCUM_START_HW_RESET_FAILED, "INA228 reset failure is reported");
    feed(&s, 4, 3000);
    AccumSession_BuildExtra(&s, true, 41790, &ina, 0, &x);
    CHECK(!x.q_ina_valid && !x.e_ina_valid && x.q_mcu_valid, "after a failed hardware reset INA228 fields are NA, STM32 still integrates");
    CHECK(x.sensor_status & PROTO_SS_ACCUM_INVALID, "failed hardware reset => ACCUM_INVALID");
    hw_result = OSBAMS_STATUS_OK;
    AccumSession_Start(&s, TEST_READY); feed(&s, 3, 3000);
    AccumSession_BuildExtra(&s, true, 41790, &ina, 0, &x);
    CHECK(!(x.sensor_status & PROTO_SS_ACCUM_INVALID) && x.q_ina_valid, "a clean start clears it");

    /* ---- status bits ---- */
    AccumSession_BuildExtra(&s, false, 0, NULL, PROTO_SS_ADC_FAULT | PROTO_SS_INA_FAULT, &x);
    CHECK(!x.v_adc_valid && !x.q_ina_valid && (x.sensor_status & (PROTO_SS_ADC_FAULT | PROTO_SS_INA_FAULT)) == (PROTO_SS_ADC_FAULT | PROTO_SS_INA_FAULT),
          "unavailable ADC / INA228 -> NA and caller's fault bits preserved");
    ina228_accum_snapshot_t dec = { .valid = true, .q_uah = 1, .e_uwh = 1, .flags = INA228_ACCUM_F_DECREASE };
    AccumSession_BuildExtra(&s, true, 1, &dec, 0, &x);
    CHECK(x.sensor_status & PROTO_SS_ACCUM_INVALID, "INA228 energy decrease => ACCUM_INVALID");
    ina228_accum_snapshot_t bad = { .valid = false };
    AccumSession_BuildExtra(&s, true, 1, &bad, 0, &x);
    CHECK(!x.q_ina_valid, "invalid snapshot => NA, never zero");

    accum_session_t g; AccumSession_Init(&g, NULL, 5000000ULL);
    AccumSession_Start(&g, TEST_READY);
    AccumSession_OnSample(&g, 1000000, 1000, 1, true); AccumSession_OnSample(&g, 2000000, 1000, 1, true);
    AccumSession_OnSample(&g, 20000000, 1000, 1, true);           /* 18 s gap */
    AccumSession_OnSample(&g, 30000000, 1000, 1, false);          /* invalid sample */
    AccumSession_OnSample(&g, 20000000, 1000, 1, true);           /* time goes backwards */
    AccumSession_BuildExtra(&g, true, 1, NULL, 0, &x);
    CHECK((x.sensor_status & PROTO_SS_INTEG_GAP) && (x.sensor_status & PROTO_SS_SAMPLE_INVALID) && (x.sensor_status & PROTO_SS_TIME_JUMP),
          "integrator gap / invalid-sample / time-jump flags are exposed as status bits");
    CHECK(x.acq_count == 5, "every acquisition is counted, including skipped ones");

    /* ---- frame with these fields encodes and keeps NA ---- */
    measurement_sample_t m; memset(&m, 0, sizeof m); m.sequence = 7; m.timestamp_us = 9000000; m.sensor_voltage_mv = 41800; m.current_ma = 3000; m.power_mw = 125400;
    AccumSession_BuildExtra(&s, true, 41790, NULL, 0, &x);
    size_t n = Protocol_EncodeDataV2(resp, sizeof resp, &m, &x, TEST_DISCHARGING);
    CHECK(n > 0 && strstr(resp, ",41790,NA,") != NULL, "assembled fields encode with NA where unavailable");
    CHECK(OSBAMS_PROTOCOL_VERSION == 1U, "OSBAMS_PROTOCOL_VERSION is still 1 (v2 not switched on)");

    printf("%s (%d failure%s)\n", failures ? "FAILED" : "All accumulator session tests passed", failures, failures == 1 ? "" : "s");
    return failures ? 1 : 0;
}
