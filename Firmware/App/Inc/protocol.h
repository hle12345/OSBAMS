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
#include "measurement.h"
#include "test_controller.h"
#include "protocol_version.h"

#define PROTOCOL_FRAME_MAX   160U

uint16_t    Protocol_Crc16(const uint8_t *d, size_t n);
const char *Protocol_StateName(test_state_t s);

size_t Protocol_EncodeData(char *out, size_t cap,
                            const measurement_sample_t *s, test_state_t state);
size_t Protocol_EncodeBoot(char *out, size_t cap, const char *fw_version);
size_t Protocol_EncodeState(char *out, size_t cap, test_state_t state);
size_t Protocol_EncodeFault(char *out, size_t cap, const char *reason);
size_t Protocol_EncodeSensor(char *out, size_t cap,
                              const char *channel, const char *health);

#endif /* PROTOCOL_H */
