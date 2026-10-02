/*
 * test_protocol_v2.c — protocol v2 encoder, written against the golden vectors in
 * docs/rev2/protocol_v2_test_vectors.json (tests/test_protocol_v2_and_data.py checks the literals below
 * against that JSON, and parses this encoder's output with the Python reference parser).
 *
 * v1 stays the default: OSBAMS_PROTOCOL_VERSION is still 1 and Protocol_EncodeData() is untouched.
 *
 *   ./test_protocol_v2           run the assertions
 *   ./test_protocol_v2 frames    print sample v2 frames for the Python cross-check
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

#include "protocol.h"

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("  FAIL  %s\n", msg); failures++; } else printf("  PASS  %s\n", msg); } while (0)

/* GOLDEN: keep identical to docs/rev2/protocol_v2_test_vectors.json */
static const char *GOLD_FULL = "OSBAMS,2,42,1500,41820,3000,125460,250,0,DISCHARGING,41790,1234,1230,51500,51400,2999,0,6F49\r\n";
static const char *GOLD_NA   = "OSBAMS,2,43,2000,41800,3000,125400,250,0,DISCHARGING,NA,NA,NA,NA,NA,3499,10,C394\r\n";
static const char *GOLD_V1   = "OSBAMS,1,42,1500,41820,3000,125460,250,0,DISCHARGING,A1A4\r\n";

static measurement_sample_t base(uint32_t seq, uint64_t t_ms, int32_t v, int32_t i, int32_t p)
{
    measurement_sample_t s;
    memset(&s, 0, sizeof s);
    s.sequence = seq; s.timestamp_us = t_ms * 1000ULL;
    s.sensor_voltage_mv = v; s.current_ma = i; s.power_mw = p; s.pack_temp_c10 = 250; s.flags = 0;
    return s;
}

int main(int argc, char **argv)
{
    char buf[PROTOCOL_V2_FRAME_MAX];

    protocol_v2_extra_t full = { .v_adc_valid = true, .v_adc_mv = 41790, .q_ina_valid = true, .q_ina_uah = 1234,
        .q_mcu_valid = true, .q_mcu_uah = 1230, .e_ina_valid = true, .e_ina_uwh = 51500, .e_mcu_valid = true,
        .e_mcu_uwh = 51400, .acq_count = 2999, .sensor_status = 0 };
    protocol_v2_extra_t na; memset(&na, 0, sizeof na);
    na.acq_count = 3499; na.sensor_status = PROTO_SS_ADC_FAULT | PROTO_SS_ACCUM_INVALID;   /* 2 + 8 = 10 */

    measurement_sample_t s1 = base(42, 1500, 41820, 3000, 125460);
    measurement_sample_t s2 = base(43, 2000, 41800, 3000, 125400);

    if (argc > 1 && strcmp(argv[1], "frames") == 0) {
        if (Protocol_EncodeDataV2(buf, sizeof buf, &s1, &full, TEST_DISCHARGING)) fputs(buf, stdout);
        if (Protocol_EncodeDataV2(buf, sizeof buf, &s2, &na, TEST_DISCHARGING)) fputs(buf, stdout);
        return 0;
    }

    printf("protocol v2 encoder tests\n");
    size_t n = Protocol_EncodeDataV2(buf, sizeof buf, &s1, &full, TEST_DISCHARGING);
    CHECK(n == strlen(GOLD_FULL) && strcmp(buf, GOLD_FULL) == 0, "golden v2_full frame matches byte for byte");

    n = Protocol_EncodeDataV2(buf, sizeof buf, &s2, &na, TEST_DISCHARGING);
    CHECK(n == strlen(GOLD_NA) && strcmp(buf, GOLD_NA) == 0, "golden v2_unavailable_fields frame matches (NA, status 10)");
    CHECK(strstr(buf, ",NA,NA,NA,NA,NA,") != NULL, "unavailable fields are the literal NA, never 0");

    /* a measured zero is a measurement and must stay 0, not NA */
    protocol_v2_extra_t zero = full; zero.q_ina_uah = 0; zero.e_mcu_uwh = 0;
    n = Protocol_EncodeDataV2(buf, sizeof buf, &s1, &zero, TEST_DISCHARGING);
    CHECK(n > 0 && strstr(buf, ",41790,0,1230,51500,0,") != NULL, "valid zero accumulator is encoded as 0");

    /* CRC covers everything before the comma preceding the CRC, same as v1 */
    n = Protocol_EncodeDataV2(buf, sizeof buf, &s1, &full, TEST_DISCHARGING);
    char *last = strrchr(buf, ',');
    unsigned crc_tx = 0; sscanf(last + 1, "%x", &crc_tx);
    CHECK(crc_tx == Protocol_Crc16((const uint8_t *)buf, (size_t)(last - buf)), "CRC is CRC-16/CCITT-FALSE over the body");

    /* 18 comma-separated fields */
    int commas = 0; for (char *p = buf; *p; p++) if (*p == ',') commas++;
    CHECK(commas == 17, "frame has 18 fields");

    /* extreme values fit the frame buffer */
    protocol_v2_extra_t big = { .v_adc_valid = true, .v_adc_mv = INT32_MIN, .q_ina_valid = true, .q_ina_uah = INT64_MIN,
        .q_mcu_valid = true, .q_mcu_uah = INT64_MAX, .e_ina_valid = true, .e_ina_uwh = INT64_MIN, .e_mcu_valid = true,
        .e_mcu_uwh = INT64_MAX, .acq_count = UINT32_MAX, .sensor_status = 0xFFFFU };
    measurement_sample_t sb = base(UINT32_MAX, 4294967295ULL * 1000ULL, INT32_MAX, INT32_MIN, INT32_MAX);
    sb.pack_temp_c10 = INT16_MIN; sb.flags = UINT32_MAX;
    n = Protocol_EncodeDataV2(buf, sizeof buf, &sb, &big, TEST_ESTOP);
    CHECK(n > 0 && n < PROTOCOL_V2_FRAME_MAX, "worst-case frame fits PROTOCOL_V2_FRAME_MAX");

    /* refusals */
    CHECK(Protocol_EncodeDataV2(buf, 20, &s1, &full, TEST_IDLE) == 0, "too-small buffer returns 0");
    CHECK(Protocol_EncodeDataV2(NULL, 100, &s1, &full, TEST_IDLE) == 0, "NULL out returns 0");
    CHECK(Protocol_EncodeDataV2(buf, sizeof buf, NULL, &full, TEST_IDLE) == 0, "NULL sample returns 0");
    CHECK(Protocol_EncodeDataV2(buf, sizeof buf, &s1, NULL, TEST_IDLE) == 0, "NULL extra returns 0");

    /* v1 untouched and still the default */
    CHECK(OSBAMS_PROTOCOL_VERSION == 1U, "default protocol version is still 1");
    n = Protocol_EncodeData(buf, sizeof buf, &s1, TEST_DISCHARGING);
    CHECK(n == strlen(GOLD_V1) && strcmp(buf, GOLD_V1) == 0, "v1 golden frame unchanged");

    printf("%s (%d failure%s)\n", failures ? "FAILED" : "All protocol v2 tests passed", failures, failures == 1 ? "" : "s");
    return failures ? 1 : 0;
}
