/*
 * test_integrator.c — STM32 timestamp-based Ah/Wh integration (host).
 * Integrates |I| and |P| with the ACTUAL elapsed time between samples (trapezoid), in mA*us / mW*us so no per-interval
 * truncation. Explicit reset. Defined behaviour for gaps, time going backwards, invalid samples and overflow.
 *
 *   ./test_integrator            assertions
 *   ./test_integrator csv        read "t_us,i_ma,p_mw,valid" lines from stdin, print "uAh,uWh,flags" (Python cross-check)
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include "integrator.h"

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("  FAIL  %s\n", msg); failures++; } else printf("  PASS  %s\n", msg); } while (0)

static int64_t uah(const integrator_t *it) { int64_t v = -1; Integrator_GetUah(it, &v); return v; }
static int64_t uwh(const integrator_t *it) { int64_t v = -1; Integrator_GetUwh(it, &v); return v; }

int main(int argc, char **argv)
{
    integrator_t it;
    Integrator_Init(&it, INTEG_DEFAULT_MAX_GAP_US);

    if (argc > 1 && strcmp(argv[1], "csv") == 0) {
        char line[128];
        while (fgets(line, sizeof line, stdin)) {
            unsigned long long t; long i, p; int v;
            if (sscanf(line, "%llu,%ld,%ld,%d", &t, &i, &p, &v) == 4) Integrator_Add(&it, t, (int32_t)i, (int32_t)p, v != 0);
        }
        printf("%lld,%lld,%u\n", (long long)uah(&it), (long long)uwh(&it), (unsigned)Integrator_Flags(&it));
        return 0;
    }

    printf("integrator tests\n");

    /* constant 3 A for 3600 s sampled every 1 s: exactly 3 Ah */
    for (uint64_t k = 0; k <= 3600; k++) Integrator_Add(&it, k * 1000000ULL, 3000, 120000, true);
    CHECK(uah(&it) == 3000000LL, "3 A for 1 h = 3.000000 Ah (3,000,000 uAh)");
    CHECK(uwh(&it) == 120000000LL, "120 W for 1 h = 120 Wh");
    CHECK(Integrator_Flags(&it) == 0, "no flags on clean data");

    /* irregular spacing uses the real dt, not an assumed period */
    Integrator_Reset(&it);
    const uint64_t ts[] = {0, 1000000, 1500000, 4000000, 4100000, 10000000};
    for (unsigned k = 0; k < 6; k++) Integrator_Add(&it, ts[k], 2000, 80000, true);
    CHECK(uah(&it) == 5556LL, "constant 2 A over irregular spacing = 2 A x 10 s = 5555.6 uAh (rounded)");

    /* sub-millisecond intervals are not truncated away (old ms-truncating path would lose them) */
    Integrator_Reset(&it);
    for (uint64_t k = 0; k <= 36000; k++) Integrator_Add(&it, k * 100000ULL + (k % 2) * 700ULL, 1000, 0, true);   /* 100.7/99.3 ms jitter */
    CHECK(uah(&it) >= 999990LL && uah(&it) <= 1000010LL, "jittered 100 ms sampling for 1 h at 1 A stays within 10 uAh of 1 Ah");

    /* trapezoid on a ramp: mean 2 A x 10 s = 20 A*s = 5555.6 uAh */
    Integrator_Reset(&it);
    Integrator_Add(&it, 0, 0, 0, true); Integrator_Add(&it, 10000000ULL, 4000, 0, true);
    CHECK(uah(&it) == 5556LL, "ramp 0->4 A over 10 s = 20 A*s = 5555.6 uAh (trapezoid)");

    /* zero current is a valid measurement and yields 0, not 'unavailable' */
    Integrator_Reset(&it);
    Integrator_Add(&it, 0, 0, 0, true); Integrator_Add(&it, 5000000ULL, 0, 0, true);
    CHECK(Integrator_GetUah(&it, &(int64_t){0}) && uah(&it) == 0, "zero current integrates to a valid 0");

    /* negative current is integrated as magnitude (matches the Pi |I| and the INA228 unsigned energy) */
    integrator_t neg; Integrator_Init(&neg, 4000000000ULL);          /* limit raised so one 3600 s interval is allowed */
    Integrator_Add(&neg, 0, -3000, 120000, true); Integrator_Add(&neg, 3600000000ULL, -3000, 120000, true);
    CHECK(uah(&neg) == 3000000LL, "-3 A for 1 h integrates as 3 Ah");

    /* before any interval there is nothing to report */
    Integrator_Reset(&it);
    CHECK(!Integrator_GetUah(&it, &(int64_t){0}), "no samples: GetUah reports unavailable");
    Integrator_Add(&it, 1000, 3000, 1, true);
    CHECK(!Integrator_GetUah(&it, &(int64_t){0}), "one sample (baseline only): still unavailable");
    Integrator_Add(&it, 2000, 3000, 1, true);
    CHECK(Integrator_GetUah(&it, &(int64_t){0}), "after the first interval a value exists");

    /* reset is explicit and total */
    Integrator_Reset(&it);
    CHECK(Integrator_Samples(&it) == 0 && Integrator_Flags(&it) == 0 && !Integrator_GetUah(&it, &(int64_t){0}), "reset clears accumulators, counters and flags");

    /* gap longer than the limit: not integrated across, flagged, and re-baselined */
    integrator_t g; Integrator_Init(&g, 5000000ULL);
    Integrator_Add(&g, 0, 1000, 0, true); Integrator_Add(&g, 1000000, 1000, 0, true);
    CHECK(Integrator_Add(&g, 30000000ULL, 1000, 0, true) == INTEG_SKIP_GAP, "29 s gap with 5 s limit is skipped");
    CHECK((Integrator_Flags(&g) & INTEG_F_GAP) && Integrator_GapCount(&g) == 1, "gap flagged and counted");
    int64_t before = uah(&g);
    Integrator_Add(&g, 31000000ULL, 1000, 0, true);
    CHECK(uah(&g) > before, "integration resumes after the gap (re-baselined)");
    CHECK(uah(&g) == 556LL, "gap interval contributes nothing (only the two 1 s intervals at 1 A = 555.6 uAh count)");

    /* an interval exactly at the limit is still integrated */
    Integrator_Init(&g, 5000000ULL);
    Integrator_Add(&g, 0, 1000, 0, true);
    CHECK(Integrator_Add(&g, 5000000ULL, 1000, 0, true) == INTEG_ADDED, "interval == limit is integrated");

    /* timestamps that do not advance: flagged, not integrated, re-baselined */
    Integrator_Init(&g, INTEG_DEFAULT_MAX_GAP_US);
    Integrator_Add(&g, 5000000ULL, 1000, 0, true);
    CHECK(Integrator_Add(&g, 5000000ULL, 1000, 0, true) == INTEG_SKIP_TIME, "equal timestamp is a time jump");
    CHECK(Integrator_Add(&g, 4000000ULL, 1000, 0, true) == INTEG_SKIP_TIME, "backwards timestamp is a time jump");
    CHECK((Integrator_Flags(&g) & INTEG_F_TIME_JUMP) && Integrator_TimeJumpCount(&g) == 2, "time jumps flagged and counted");
    CHECK(Integrator_Add(&g, 5000000ULL, 1000, 0, true) == INTEG_ADDED, "after a backwards jump the new time is the baseline");

    /* invalid samples are not integrated and not replaced by zero; the next valid sample integrates across them */
    Integrator_Init(&g, INTEG_DEFAULT_MAX_GAP_US);
    Integrator_Add(&g, 0, 2000, 0, true);
    CHECK(Integrator_Add(&g, 1000000ULL, 0, 0, false) == INTEG_SKIP_INVALID, "invalid sample skipped");
    Integrator_Add(&g, 2000000ULL, 2000, 0, true);
    CHECK(uah(&g) == 2000LL * 2000000LL / 3600000LL, "valid samples either side of an invalid one integrate across it (no zero injected)");
    CHECK((Integrator_Flags(&g) & INTEG_F_INVALID_SAMPLE) && Integrator_InvalidCount(&g) == 1, "invalid sample flagged and counted");

    /* overflow is latched and the accumulator is frozen, never wrapped */
    integrator_t o; Integrator_Init(&o, 3000000000000ULL);
    Integrator_Add(&o, 0, INT32_MAX, INT32_MAX, true);
    integ_result_t r = INTEG_ADDED;
    uint64_t t = 0;
    for (int k = 0; k < 2000 && r != INTEG_OVERFLOW; k++) { t += 1000000000ULL; r = Integrator_Add(&o, t, INT32_MAX, INT32_MAX, true); }
    CHECK(r == INTEG_OVERFLOW && (Integrator_Flags(&o) & INTEG_F_OVERFLOW), "overflow detected and latched");
    CHECK(!Integrator_GetUah(&o, &(int64_t){0}), "after overflow the totals are reported unavailable");
    CHECK(Integrator_Add(&o, t + 1000000ULL, 1, 1, true) == INTEG_OVERFLOW, "stays overflowed until reset");
    Integrator_Reset(&o);
    CHECK(Integrator_Flags(&o) == 0, "reset clears the overflow latch");

    CHECK(Integrator_Add(NULL, 0, 0, 0, true) == INTEG_BAD_ARG, "NULL integrator refused");

    printf("%s (%d failure%s)\n", failures ? "FAILED" : "All integrator tests passed", failures, failures == 1 ? "" : "s");
    return failures ? 1 : 0;
}
