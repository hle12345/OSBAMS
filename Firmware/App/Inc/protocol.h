/*
 * protocol.h — RECONSTRUCTED from protocol.c's implementation and every
 * call site (main.c, test_protocol_c.c).
 *
 * PROTOCOL_FRAME_MAX: test_protocol_c.c declares `char buf[PROTOCOL_FRAME_MAX]`
 * for the largest frame (a DATA frame with full-width negative int32/int16
 * values, e.g. the "2147483647,-2147483648,...,-32768,65535" stress case
 * in that file). Sized with margin above that worst case.
 */
#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "measurement.h"
#include "test_controller.h"
#include "protocol_version.h"

#define PROTOCOL_FRAME_MAX   160U

/* ── Protocol v2 (opt-in; v1 stays the default — see docs/rev2/PROTOCOL_V2_DESIGN.md) ──────────────
 * Extra fields for the three-way capacity cross-check. A field whose *_valid flag is false is sent as
 * the literal NA (never 0). The accumulators are filled by whoever owns them (INA228 CHARGE/ENERGY
 * registers, STM32 integration); this encoder only formats. */
#define PROTOCOL_V2_FRAME_MAX   256U

#define PROTO_SS_INA_FAULT      (1U << 0)
#define PROTO_SS_ADC_FAULT      (1U << 1)
#define PROTO_SS_TEMP_FAULT     (1U << 2)
#define PROTO_SS_ACCUM_INVALID  (1U << 3)
#define PROTO_SS_TIME_JUMP      (1U << 4)

typedef struct {
    bool     v_adc_valid; int32_t v_adc_mv;      /* independent STM32 ADC pack voltage            */
    bool     q_ina_valid; int64_t q_ina_uah;     /* INA228 CHARGE register, since test start       */
    bool     q_mcu_valid; int64_t q_mcu_uah;     /* STM32 integration of I over timestamps          */
    bool     e_ina_valid; int64_t e_ina_uwh;     /* INA228 ENERGY register, since test start        */
    bool     e_mcu_valid; int64_t e_mcu_uwh;     /* STM32 integration of V*I over timestamps        */
    uint32_t acq_count;                          /* acquisitions since test start                   */
    uint16_t sensor_status;                      /* PROTO_SS_* bits                                 */
} protocol_v2_extra_t;

uint16_t    Protocol_Crc16(const uint8_t *d, size_t n);
const char *Protocol_StateName(test_state_t s);

size_t Protocol_EncodeData(char *out, size_t cap,
                            const measurement_sample_t *s, test_state_t state);
size_t Protocol_EncodeDataV2(char *out, size_t cap,
                              const measurement_sample_t *s,
                              const protocol_v2_extra_t *x, test_state_t state);
size_t Protocol_EncodeBoot(char *out, size_t cap, const char *fw_version);
size_t Protocol_EncodeState(char *out, size_t cap, test_state_t state);
size_t Protocol_EncodeFault(char *out, size_t cap, const char *reason);
size_t Protocol_EncodeSensor(char *out, size_t cap,
                              const char *channel, const char *health);

#endif /* PROTOCOL_H */
