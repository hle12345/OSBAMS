/*
 * app_config.h — RECONSTRUCTED. Two kinds of values here:
 *
 * (a) FROZEN per DESIGN_DECISIONS.md / the build-order review:
 *     OSBAMS_SHUNT_MICRO_OHM, OSBAMS_INA228_IMAX_MA,
 *     OSBAMS_DEFAULT_MAX_CURRENT_MA.
 *
 * (b) Evidence-based defaults: pulled verbatim from the `safety_limits_t
 *     lim = {...}` literal in test_safety_modules.c, which is the only
 *     real source-of-truth for these numbers seen anywhere in the
 *     uploaded files. Diff against the real app_config.h if you have one
 *     — these are NOT independently frozen the way the current
 *     thresholds are; DESIGN_DECISIONS.md explicitly says voltage/temp
 *     limits are chemistry- and sensor-placement-dependent and were
 *     deliberately left open.
 *
 * KNOWN GAP, not fixed here: the frozen fault architecture calls for
 * THREE current tiers (17.0 A warn / 18.5 A trip-with-debounce / 20.0 A
 * immediate-trip) with a "2 consecutive FRESH readings" debounce using
 * the freshness flag INA228_ReadCurrent_mA() now returns. The real
 * safety.c only implements a single `max_current_ma` threshold with no
 * debounce and doesn't consume the freshness flag at all (sensor_manager.c
 * passes NULL for it — see that file's comment). Implementing the
 * three-tier debounced logic is real work still open in safety.c, not
 * something a header change can paper over. Flagging it here so it isn't
 * lost.
 */
#ifndef APP_CONFIG_H
#define APP_CONFIG_H

/* ── INA228 / shunt — FROZEN ─────────────────────────────────────────
 * RSA-20-50 shunt: 2.5 mOhm, 20 A / 50 mV physical rating.
 * i_max scale deliberately set ABOVE the shunt rating and above the
 * firmware trip (30 A digital range) so the 20-bit CURRENT register
 * doesn't saturate/sign-wrap at the values we actually trip on. */
#define OSBAMS_SHUNT_MICRO_OHM       2500U
#define OSBAMS_INA228_IMAX_MA        30000U

/* ── Current protection — FROZEN (hard trip only; see KNOWN GAP above
 * for the still-unimplemented 17.0/18.5 warn+debounce tiers) ────────── */
#define OSBAMS_DEFAULT_MAX_CURRENT_MA  18500

/* ── Voltage / temperature / duration — evidence-based defaults from
 * test_safety_modules.c's lim struct, NOT independently frozen ─────── */
#define OSBAMS_DEFAULT_MAX_TEMP_C10    600     /* 60.0 C */
#define OSBAMS_DEFAULT_MIN_VOLTAGE_MV  30000   /* 30.0 V */
#define OSBAMS_DEFAULT_MAX_VOLTAGE_MV  44000   /* 44.0 V, margin above 42V pack max */
#define OSBAMS_MAX_TEST_DURATION_S     36000U  /* 10 hours */

/* ── Acquisition period — matches acquisition_timer.c's own worked
 * example (500 ms -> ARR=5000) ──────────────────────────────────────── */
#define OSBAMS_SAMPLE_PERIOD_MS        500U

/*
 * NOTE ON OSBAMS_TARGET_STM32: deliberately NOT defined here. Every
 * driver (i2c_bus.c is the one exception — see its own file note) gates
 * real register access behind `#ifdef OSBAMS_TARGET_STM32`, and that
 * macro is expected to come from the BUILD, not from this header — pass
 * -DOSBAMS_TARGET_STM32 on the arm-none-eabi-gcc command line for the
 * real target build; omit it entirely for host tests, matching how
 * test_measurement.c / test_safety_modules.c already build and run with
 * plain gcc.
 */

#endif /* APP_CONFIG_H */
