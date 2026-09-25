/*
 * load_driver.c — Electronic Load Control with Fail-Safe Disconnect
 *
 * ── Why the previous version was unsafe ──────────────────────────────
 * The scaffold set a boolean and returned OSBAMS_STATUS_OK:
 *
 *     osbams_status_t Load_Disable(void) { enabled = false; return OK; }
 *
 * That reports success without performing any hardware action. Software
 * overtemperature detection was therefore a warning, not protection.
 *
 * ── Fail-safe design ─────────────────────────────────────────────────
 * The load-enable line is ACTIVE HIGH and defaults LOW:
 *
 *   - GPIO configured as output, driven LOW, before anything else
 *   - MCU reset, brown-out, or unprogrammed state leaves the pin LOW
 *   - LOW must correspond to LOAD OFF in the external wiring
 *   - A pull-down resistor on the enable line holds it LOW if the MCU
 *     is removed or the pin goes high-impedance
 *
 * ── PC9 — FROZEN: K1 voltage-feedback via VO610A, ACTIVE LOW ─────────
 * Earlier revisions of this file went through two incorrect states:
 *   1. Claimed PC9 was a genuine Durakool aux contact (it isn't — the
 *      DG57CM-5021-76-1012-R has no aux contact).
 *   2. Correctly disabled feedback (LOAD_FEEDBACK_PRESENT 0) as a result,
 *      but that threw out real signal along with the wrong assumption:
 *      PC9 IS wired to something real — switched HV (present only when
 *      K1 is actually closed and conducting) through a resistor chain
 *      into a VO610A optocoupler, output to PC9.
 *
 * Frozen final assignment: PC9 = K1 voltage-feedback, ACTIVE LOW.
 * The VO610A's phototransistor output is open-collector and pulls the
 * line LOW when its LED conducts (i.e. when switched HV is present,
 * i.e. when K1 is closed) — external pull-up brings it HIGH when the
 * LED is dark (K1 open). So:
 *
 *     PC9 LOW  = K1 closed, HV present downstream  (load ON, confirmed)
 *     PC9 HIGH = K1 open, no HV downstream           (load OFF, confirmed)
 *
 * This is the OPPOSITE polarity of the old (wrong) active-high aux-
 * contact assumption this file previously carried, and it is DEFINITIVE
 * position feedback (proves HV actually flows through the closed
 * contacts) — arguably stronger evidence than a mechanical aux contact
 * would have been, which only proves the armature moved.
 *
 * LOAD_FEEDBACK_PRESENT is back to 1. feedback_says_load_on() inverts
 * the raw read (see its own comment) so every caller above it keeps the
 * same "true = load confirmed on" contract regardless of the wire-level
 * polarity — nothing outside this file needs to know PC9 is active-low.
 *
 * PC9 / K1_AUX macro name kept as LOAD_FEEDBACK_PIN for continuity with
 * existing call sites; it is documented here as the VO610A signal, not
 * a mechanical aux contact.
 */

#include "load_driver.h"
#include "app_config.h"
#include "tick.h"

#ifdef OSBAMS_TARGET_STM32
#include "stm32l476xx.h"
#endif

/* ── Pin configuration ────────────────────────────────────────────── */
#define LOAD_ENABLE_PORT      GPIOC
#define LOAD_ENABLE_PIN       8U        /* PC8: load enable, ACTIVE HIGH */
#define LOAD_FEEDBACK_PORT    GPIOC
#define LOAD_FEEDBACK_PIN     9U        /* PC9: K1 voltage-feedback via
                                          * VO610A optocoupler, ACTIVE LOW.
                                          * See file header — frozen. */

/* FROZEN: PC9 carries real, definitive K1 position feedback (VO610A
 * sensing switched HV downstream of the contactor), active-low. */
#define LOAD_FEEDBACK_PRESENT 1

/* Current below this is treated as "load is off" when using method C. */
#define LOAD_OFF_CURRENT_MA   100

/* Real millisecond timeouts. */
#define LOAD_CLOSE_TIMEOUT_MS 250U   /* frozen: contactor close confirmation */
#define LOAD_OPEN_TIMEOUT_MS  250U   /* defensive default, not bench-confirmed */

/* ── State ───────────────────────────────────────────────────────── */
static bool     s_commanded_on   = false;
static bool     s_initialized    = false;
static uint32_t s_disable_count  = 0;
static uint32_t s_confirm_fails  = 0;

/* ── Low-level pin control ───────────────────────────────────────── */

static void enable_pin_low(void)
{
#ifdef OSBAMS_TARGET_STM32
    LOAD_ENABLE_PORT->BSRR = (1U << (LOAD_ENABLE_PIN + 16));  /* reset */
#endif
}

static void enable_pin_high(void)
{
#ifdef OSBAMS_TARGET_STM32
    LOAD_ENABLE_PORT->BSRR = (1U << LOAD_ENABLE_PIN);         /* set */
#endif
}

bool Load_DecodeFeedbackActiveLow(bool raw_bit_is_set)
{
    /* Active low: LOW (bit clear) = confirmed on. */
    return !raw_bit_is_set;
}

static bool feedback_says_load_on(void)
{
#if LOAD_FEEDBACK_PRESENT && defined(OSBAMS_TARGET_STM32)
    bool raw_high = (LOAD_FEEDBACK_PORT->IDR & (1U << LOAD_FEEDBACK_PIN)) != 0;
    return Load_DecodeFeedbackActiveLow(raw_high);
#else
    /* Host build, or feedback not wired: report false. On host this keeps
     * Load_Enable()/Load_Disable() from ever looping on real time (there's
     * no SysTick incrementing tick.h's counter outside the target), so
     * tests exercise the logic paths once and return deterministically —
     * see the single-check branches below. The polarity DECODE logic
     * itself (Load_DecodeFeedbackActiveLow) is still exercised directly
     * by the host test suite, independent of this hardware gate. */
    return false;
#endif
}

/* ── Init: fail-safe state first ─────────────────────────────────── */

osbams_status_t Load_Init(void)
{
#ifdef OSBAMS_TARGET_STM32
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOCEN;

    /* Drive LOW *before* switching the pin to output so the line never
     * glitches high during configuration. */
    enable_pin_low();

    /* Enable pin: push-pull output, low speed */
    LOAD_ENABLE_PORT->MODER &= ~(3U << (LOAD_ENABLE_PIN * 2));
    LOAD_ENABLE_PORT->MODER |=  (1U << (LOAD_ENABLE_PIN * 2));
    LOAD_ENABLE_PORT->OTYPER &= ~(1U << LOAD_ENABLE_PIN);
    /* Internal pull-down as a second line of defence */
    LOAD_ENABLE_PORT->PUPDR &= ~(3U << (LOAD_ENABLE_PIN * 2));
    LOAD_ENABLE_PORT->PUPDR |=  (2U << (LOAD_ENABLE_PIN * 2));

    enable_pin_low();

#if LOAD_FEEDBACK_PRESENT
    /* Feedback pin: input with internal pull-up as a fail-safe backup to
     * the VO610A circuit's own external pull-up. PC9 is ACTIVE LOW
     * (LOW = K1 closed/HV present), so the safe default if the pull-up
     * path fails is to read HIGH -- "K1 open" / "not confirmed closed"
     * -- not to default toward a false "closed" reading. A pull-DOWN
     * here would fight the active-low idle-high convention and risk a
     * floating pin misreading as "closed" if the external pull-up ever
     * fails open. */
    LOAD_FEEDBACK_PORT->MODER &= ~(3U << (LOAD_FEEDBACK_PIN * 2));
    LOAD_FEEDBACK_PORT->PUPDR &= ~(3U << (LOAD_FEEDBACK_PIN * 2));
    LOAD_FEEDBACK_PORT->PUPDR |=  (1U << (LOAD_FEEDBACK_PIN * 2));
#endif
#endif

    s_commanded_on  = false;
    s_initialized   = true;
    s_disable_count = 0;
    s_confirm_fails = 0;
    return OSBAMS_STATUS_OK;
}

/* ── Enable ──────────────────────────────────────────────────────── */

osbams_status_t Load_Enable(void)
{
    if (!s_initialized) return OSBAMS_STATUS_NOT_READY;

    enable_pin_high();
    s_commanded_on = true;

#if LOAD_FEEDBACK_PRESENT
#ifdef OSBAMS_TARGET_STM32
    uint32_t start = Tick_GetMs();
    while (Tick_ElapsedMs(start) < LOAD_CLOSE_TIMEOUT_MS) {
        if (feedback_says_load_on()) return OSBAMS_STATUS_OK;
    }
#else
    /* Host build: no real time source to wait on; check once. See
     * feedback_says_load_on() comment. */
    if (feedback_says_load_on()) return OSBAMS_STATUS_OK;
#endif
    /* Commanded on but feedback never confirmed within the timeout.
     * FAULT_CONTACTOR_NO_CLOSE per the frozen fault table — fail safe. */
    enable_pin_low();
    s_commanded_on = false;
    return OSBAMS_STATUS_TIMEOUT;
#else
    return OSBAMS_STATUS_OK;
#endif
}

/* ── Disable — the safety-critical path ──────────────────────────── */

osbams_status_t Load_Disable(void)
{
    /* Drive the pin low unconditionally, even if not initialized.
     * This must work in every reachable state including fault handlers. */
    enable_pin_low();
    s_commanded_on = false;
    s_disable_count++;

#if LOAD_FEEDBACK_PRESENT
#ifdef OSBAMS_TARGET_STM32
    uint32_t start = Tick_GetMs();
    while (Tick_ElapsedMs(start) < LOAD_OPEN_TIMEOUT_MS) {
        if (!feedback_says_load_on()) return OSBAMS_STATUS_OK;
    }
#else
    if (!feedback_says_load_on()) return OSBAMS_STATUS_OK;
#endif
    /* Pin commanded low but K1_AUX still shows closed within the timeout.
     * FAULT_CONTACTOR_WELDED per the frozen fault table. */
    s_confirm_fails++;
    return OSBAMS_STATUS_LOAD_STUCK;   /* pin low but load still conducting */
#else
    /* Pin driven low, but with no feedback wired we cannot confirm the
     * load actually stopped. Report that honestly rather than claiming OK. */
    return OSBAMS_STATUS_NOT_SUPPORTED;
#endif
}

/* ── Emergency disable — no timeout, no confirmation wait ─────────── */

void Load_EmergencyDisable(void)
{
    enable_pin_low();
    s_commanded_on = false;
    s_disable_count++;
}

/* ── Inferential confirmation via measured current (method C) ─────── */

osbams_status_t Load_ConfirmOffByCurrent(int32_t measured_current_ma)
{
    int32_t mag = (measured_current_ma < 0) ? -measured_current_ma
                                            :  measured_current_ma;
    if (s_commanded_on)              return OSBAMS_STATUS_BUSY;
    if (mag <= LOAD_OFF_CURRENT_MA)  return OSBAMS_STATUS_OK;
    return OSBAMS_STATUS_LOAD_STUCK;
}

/* ── Setpoint (remote-controlled loads only) ─────────────────────── */

osbams_status_t Load_SetCurrent_mA(uint32_t current_ma)
{
    (void)current_ma;
    /* Manual load: the operator sets current on the instrument panel.
     * A remote-controlled load implements SCPI here. */
    return OSBAMS_STATUS_NOT_SUPPORTED;
}

/* ── Queries ─────────────────────────────────────────────────────── */

bool Load_IsEnabled(void)          { return s_commanded_on; }
bool Load_HasFeedback(void)        { return LOAD_FEEDBACK_PRESENT != 0; }
uint32_t Load_DisableCount(void)   { return s_disable_count; }
uint32_t Load_ConfirmFailCount(void) { return s_confirm_fails; }
