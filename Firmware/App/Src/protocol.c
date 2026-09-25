/*
 * protocol.c — OSBAMS Serial Protocol v1
 *
 * AUTHORITATIVE FRAME (must match services/protocol.py exactly):
 *
 *   OSBAMS,<ver>,<seq>,<tick_ms>,<V_mV>,<I_mA>,<P_mW>,<T_C10>,<flags>,<state>,<CRC16>
 *
 * Example:
 *   OSBAMS,1,42,1500,41820,3000,125460,250,0,DISCHARGING,A1A4
 *
 * CRC-16/CCITT-FALSE: init 0xFFFF, poly 0x1021, no reflection, no final XOR.
 * Computed over the frame text from 'O' up to but NOT including the comma
 * that precedes the CRC field.
 */

#include "protocol.h"
#include <stdio.h>
#include <string.h>

uint16_t Protocol_Crc16(const uint8_t *d, size_t n)
{
    uint16_t c = 0xFFFFU;
    for (size_t i = 0; i < n; i++) {
        c ^= (uint16_t)d[i] << 8;
        for (unsigned b = 0; b < 8; b++)
            c = (c & 0x8000U) ? (uint16_t)((c << 1) ^ 0x1021U)
                              : (uint16_t)(c << 1);
    }
    return c;
}

const char *Protocol_StateName(test_state_t s)
{
    switch (s) {
        case TEST_BOOT:          return "BOOT";
        case TEST_SELF_TEST:     return "SELF_TEST";
        case TEST_IDLE:          return "IDLE";
        case TEST_PACK_DETECTED: return "PACK_DETECTED";
        case TEST_PRECHECK:      return "PRECHECK";
        case TEST_READY:         return "READY";
        case TEST_RESTING:       return "RESTING";
        case TEST_DISCHARGING:   return "DISCHARGING";
        case TEST_PAUSED:        return "PAUSED";
        case TEST_CUTOFF:        return "CUTOFF";
        case TEST_RECOVERY:      return "RECOVERY";
        case TEST_COMPLETE:      return "COMPLETE";
        case TEST_FAULT:         return "FAULT";
        case TEST_ESTOP:         return "E_STOP";   /* FIX: was falling through to UNKNOWN */
        default:                 return "UNKNOWN";
    }
}

size_t Protocol_EncodeData(char *out, size_t cap,
                            const measurement_sample_t *s,
                            test_state_t state)
{
    if (!out || !s || cap == 0) return 0;

    /* Body: everything except the CRC field */
    int n = snprintf(out, cap,
        "OSBAMS,%u,%lu,%lu,%ld,%ld,%ld,%d,%lu,%s",
        (unsigned)OSBAMS_PROTOCOL_VERSION,
        (unsigned long)s->sequence,
        (unsigned long)(s->timestamp_us / 1000ULL),   /* us -> ms */
        (long)s->sensor_voltage_mv,
        (long)s->current_ma,
        (long)s->power_mw,
        (int)s->pack_temp_c10,
        (unsigned long)s->flags,
        Protocol_StateName(state));

    if (n <= 0 || (size_t)n >= cap) return 0;

    uint16_t crc = Protocol_Crc16((const uint8_t *)out, (size_t)n);

    int m = snprintf(out + n, cap - (size_t)n, ",%04X\r\n", crc);
    if (m <= 0 || (size_t)(n + m) >= cap) return 0;

    return (size_t)(n + m);
}

size_t Protocol_EncodeBoot(char *out, size_t cap,
                            const char *fw_version)
{
    if (!out || cap == 0) return 0;
    int n = snprintf(out, cap, "OSBAMS,BOOT,%s,%u\r\n",
                     fw_version ? fw_version : "0.0.0",
                     (unsigned)OSBAMS_PROTOCOL_VERSION);
    return (n > 0 && (size_t)n < cap) ? (size_t)n : 0;
}

size_t Protocol_EncodeState(char *out, size_t cap, test_state_t state)
{
    if (!out || cap == 0) return 0;
    int n = snprintf(out, cap, "OSBAMS,STATE,%s\r\n",
                     Protocol_StateName(state));
    return (n > 0 && (size_t)n < cap) ? (size_t)n : 0;
}

size_t Protocol_EncodeFault(char *out, size_t cap, const char *reason)
{
    if (!out || cap == 0) return 0;
    int n = snprintf(out, cap, "OSBAMS,FAULT,%s\r\n",
                     reason ? reason : "UNKNOWN");
    return (n > 0 && (size_t)n < cap) ? (size_t)n : 0;
}

size_t Protocol_EncodeSensor(char *out, size_t cap,
                              const char *channel, const char *health)
{
    if (!out || cap == 0) return 0;
    int n = snprintf(out, cap, "OSBAMS,SENSOR,%s,%s\r\n",
                     channel ? channel : "?", health ? health : "?");
    return (n > 0 && (size_t)n < cap) ? (size_t)n : 0;
}
