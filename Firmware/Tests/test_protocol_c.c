/*
 * test_protocol_c.c — Host-side C protocol conformance harness
 *
 * Compiles the REAL protocol.c and prints frames to stdout so Python can
 * parse them. This proves the current C encoder and the current Python
 * parser agree — stronger than comparing against copied constants, which
 * can go stale when the C changes.
 *
 * Build and run:
 *     cd firmware/Tests && make test_protocol_c && ./test_protocol_c
 *
 * Modes:
 *     ./test_protocol_c frames   emit DATA/BOOT/STATE/FAULT frames
 *     ./test_protocol_c crc      read bodies on stdin, print CRC per line
 *     ./test_protocol_c version  print the compiled protocol version
 */

#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdlib.h>

#include "protocol.h"
#include "protocol_version.h"

int main(int argc, char **argv)
{
    const char *mode = (argc > 1) ? argv[1] : "frames";

    /* ── version: prove what the compiled firmware actually uses ──── */
    if (strcmp(mode, "version") == 0) {
        printf("%u\n", (unsigned)OSBAMS_PROTOCOL_VERSION);
        return 0;
    }

    /* ── crc: CRC of each stdin line, for reverse verification ────── */
    if (strcmp(mode, "crc") == 0) {
        char line[512];
        while (fgets(line, sizeof(line), stdin)) {
            size_t n = strlen(line);
            while (n && (line[n-1] == '\n' || line[n-1] == '\r')) line[--n] = 0;
            if (!n) continue;
            printf("%04X\n", Protocol_Crc16((const uint8_t *)line, n));
        }
        return 0;
    }

    /* ── frames: emit real encoder output ─────────────────────────── */
    char buf[PROTOCOL_FRAME_MAX];

    /* BOOT */
    if (Protocol_EncodeBoot(buf, sizeof(buf), "0.9.0-dev1")) fputs(buf, stdout);

    /* SENSOR */
    if (Protocol_EncodeSensor(buf, sizeof(buf), "TEMP_PACK", "ONLINE"))
        fputs(buf, stdout);

    /* STATE */
    if (Protocol_EncodeState(buf, sizeof(buf), TEST_READY)) fputs(buf, stdout);

    /* DATA frames covering nominal, negative current, and extremes */
    struct { uint32_t seq; uint64_t us; int32_t v, i, p; int16_t t;
             uint32_t f; test_state_t st; } cases[] = {
        {   42, 1500000ULL,  41820,  3000, 125460, 250, 0, TEST_DISCHARGING},
        {    0,       0ULL,  42000,     0,      0, 250, 0, TEST_READY},
        {  999, 499500000ULL, 31000,  2980,  92380, 410, 8, TEST_CUTOFF},
        { 1000, 500000000ULL, 30500, -1500, -45750, 300, 32, TEST_FAULT},
        { 4294967295u, 1000ULL, 40000, 3000, 120000, 240, 0, TEST_DISCHARGING},
        { 1001, 501000000ULL, 2147483647, -2147483648, 0, -32768, 65535, TEST_PAUSED},
    };

    for (size_t k = 0; k < sizeof(cases)/sizeof(cases[0]); k++) {
        measurement_sample_t s;
        memset(&s, 0, sizeof(s));
        s.sequence          = cases[k].seq;
        s.timestamp_us      = cases[k].us;
        s.sensor_voltage_mv = cases[k].v;
        s.current_ma        = cases[k].i;
        s.power_mw          = cases[k].p;
        s.pack_temp_c10     = cases[k].t;
        s.flags             = cases[k].f;
        if (Protocol_EncodeData(buf, sizeof(buf), &s, cases[k].st))
            fputs(buf, stdout);
        else
            fprintf(stderr, "encode failed for case %zu\n", k);
    }

    /* FAULT */
    if (Protocol_EncodeFault(buf, sizeof(buf), "OVERTEMP")) fputs(buf, stdout);

    return 0;
}
