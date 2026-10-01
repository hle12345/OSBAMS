/*
 * adc_safety.c — Redundant voltage measurement (STM32 ADC)
 *
 * Independent cross-check of the INA228 bus voltage through a protected
 * resistor divider. Single-conversion, software-triggered; called after each
 * INA228 read to compare the two paths.
 *
 * ── FIX: was missing real hardware configuration ────────────────────
 * The previous version enabled/calibrated ADC1 but never configured the
 * actual input: no GPIO analog mode, no regular-sequence channel
 * selection, no sampling time, no explicit resolution, and no bounded
 * timeouts (calibration, ADRDY, and EOC could each spin forever). The
 * divider could physically exist on the board and this code would still
 * never reliably read it.
 *
 * ── Pin choice — NOT YET CONFIRMED IN HARDWARE ──────────────────────
 * CONNECTION_TABLE.md documents only "Redundant voltage | ADC channel |
 * in | protected divider" with no specific pin ever assigned. PA1
 * (ADC1_IN6) is used here as a reasonable, currently-unused choice on
 * the Nucleo-64 header (I2C is PB8/PB9, load/contactor is PC8/PC9,
 * E-stop is PA0, UART is PA2/PA3, LED is PA5 — PA1 is free). CONFIRM
 * this against the actual schematic/wiring before trusting it, and
 * update CONNECTION_TABLE.md once it's real.
 *
 * ── Divider ──────────────────────────────────────────────────────────
 * pack_mV = adc_mV * 16 (matches the confirmed 150k-high / 10k-low
 * resistor split: 42V / 16 ≈ 2.625V at the ADC, comfortably inside the
 * 3.3V range).
 */

#include "adc_safety.h"
#include "app_config.h"

#ifdef OSBAMS_TARGET_STM32
#include "stm32l476xx.h"
#endif

/* Divider scales pack voltage into the 0–3.3 V ADC range.
 * Confirmed physical divider: 150 kOhm high-side, 10 kOhm low-side -> 16:1.
 * At 42 V pack, ADC sees ~2.625 V. */
#ifndef OSBAMS_ADC_DIVIDER_NUM
#define OSBAMS_ADC_DIVIDER_NUM   16U    /* pack_mV = adc_mV * NUM / DEN */
#define OSBAMS_ADC_DIVIDER_DEN    1U
#endif

#define ADC_VREF_MV        3300U
#define ADC_FULL_SCALE     4095U        /* 12-bit */

/* Pin/channel — see file header note: NOT YET CONFIRMED against the
 * real schematic. */
#define ADC_DIVIDER_GPIO_PORT   GPIOA
#define ADC_DIVIDER_PIN         1U      /* PA1 */
#define ADC_DIVIDER_CHANNEL     6U      /* ADC1_IN6, matches PA1 on L476 */

/* Bounded timeouts. These are CPU busy-loop counts (matching this
 * project's existing convention in i2c_bus.c), not calibrated
 * milliseconds -- generous enough that a healthy ADC clears them in a
 * small fraction of the count, tight enough to fail rather than hang
 * forever on a genuinely dead peripheral. */
#define ADC_TIMEOUT_LOOPS    100000

/* INA228 and ADC may legitimately differ by sensor tolerances plus divider
 * error. Beyond this, treat as a fault. Tightened after calibration. */
#ifndef OSBAMS_ADC_AGREEMENT_MV
#define OSBAMS_ADC_AGREEMENT_MV  1500   /* 1.5 V agreement window */
#endif

static bool s_initialised = false;

#ifdef OSBAMS_TARGET_STM32
/* Returns true if the condition became true before the timeout. */
static bool wait_until(volatile uint32_t *reg, uint32_t mask, bool want_set)
{
    int t = ADC_TIMEOUT_LOOPS;
    while (t--) {
        bool is_set = (*reg & mask) != 0U;
        if (is_set == want_set) return true;
    }
    return false;
}
#endif

osbams_status_t AdcSafety_Init(void)
{
#ifdef OSBAMS_TARGET_STM32
    RCC->AHB2ENR |= RCC_AHB2ENR_ADCEN | RCC_AHB2ENR_GPIOAEN;

    /* ── GPIO: PA1 to analog mode, no pull (analog inputs float in a
     * defined way electrically; a pull would just waste current and
     * slightly load the divider). MODER = 11 selects analog mode. */
    ADC_DIVIDER_GPIO_PORT->MODER |=  (3UL << (ADC_DIVIDER_PIN * 2U));
    ADC_DIVIDER_GPIO_PORT->PUPDR &= ~(3UL << (ADC_DIVIDER_PIN * 2U));

    /* ── ADC clock: synchronous HCLK/1 via the common control register.
     * Simplest correct choice for a single-shot, software-triggered
     * read; avoids needing a separate asynchronous clock (RCC->CCIPR
     * ADCSEL) setup for this one channel. */
    ADC123_COMMON->CCR = (ADC123_COMMON->CCR & ~ADC_CCR_CKMODE)
                        | (1UL << ADC_CCR_CKMODE_Pos);   /* HCLK/1 */

    ADC1->CR &= ~ADC_CR_DEEPPWD;         /* exit deep power down */
    ADC1->CR |=  ADC_CR_ADVREGEN;        /* enable regulator */
    for (volatile int i = 0; i < 4000; i++) { }   /* regulator startup, ~20us+ */

    /* ── Resolution: 12-bit. Set explicitly (matches the reset default,
     * but explicit so ADC_FULL_SCALE=4095 below is a documented
     * invariant, not an assumption about power-on state). RES=00. */
    ADC1->CFGR &= ~ADC_CFGR_RES;

    /* ── Calibration, bounded ─────────────────────────────────────── */
    ADC1->CR |= ADC_CR_ADCAL;
    if (!wait_until(&ADC1->CR, ADC_CR_ADCAL, false)) {
        return OSBAMS_STATUS_TIMEOUT;
    }

    /* ── Sampling time for the divider channel: divider source
     * impedance is a few hundred kOhm (150k+10k), which needs a long
     * sample time to settle within the ADC's input capacitance budget.
     * Use 92.5 ADC clock cycles (code 0b101) on channel 6 -- SMPR1 field
     * for channels 0-9 is 3 bits per channel at bit position
     * (channel*3). */
    ADC1->SMPR1 = (ADC1->SMPR1 & ~(7UL << (ADC_DIVIDER_CHANNEL * 3U)))
                | (5UL << (ADC_DIVIDER_CHANNEL * 3U));

    /* ── Regular sequence: one conversion, our channel. L=0000 (1
     * conversion), SQ1 = channel 6. */
    ADC1->SQR1 = (ADC1->SQR1 & ~(ADC_SQR1_L | ADC_SQR1_SQ1))
               | ((uint32_t)ADC_DIVIDER_CHANNEL << ADC_SQR1_SQ1_Pos);

    /* ── Enable, bounded wait for ADRDY ──────────────────────────────── */
    ADC1->ISR |= ADC_ISR_ADRDY;   /* clear stale flag before enabling */
    ADC1->CR  |= ADC_CR_ADEN;
    if (!wait_until(&ADC1->ISR, ADC_ISR_ADRDY, true)) {
        return OSBAMS_STATUS_TIMEOUT;
    }
#endif
    s_initialised = true;
    return OSBAMS_STATUS_OK;
}

osbams_status_t AdcSafety_ReadVoltage_mV(int32_t *voltage_mv)
{
    if (!voltage_mv)    return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!s_initialised) return OSBAMS_STATUS_NOT_READY;

    uint32_t raw = 0U;
#ifdef OSBAMS_TARGET_STM32
    ADC1->CR |= ADC_CR_ADSTART;
    if (!wait_until(&ADC1->ISR, ADC_ISR_EOC, true)) {
        return OSBAMS_STATUS_TIMEOUT;   /* FIX: was an unbounded wait */
    }
    raw = ADC1->DR;
#else
    raw = 0U;   /* host build: no hardware */
#endif

    uint32_t adc_mv  = (raw * ADC_VREF_MV) / ADC_FULL_SCALE;
    uint32_t pack_mv = (adc_mv * OSBAMS_ADC_DIVIDER_NUM) / OSBAMS_ADC_DIVIDER_DEN;
    *voltage_mv = (int32_t)pack_mv;
    return OSBAMS_STATUS_OK;
}

bool AdcSafety_Disagrees(int32_t ina228_mv, int32_t adc_mv)
{
    int32_t diff = ina228_mv - adc_mv;
    if (diff < 0) diff = -diff;
    return (diff > OSBAMS_ADC_AGREEMENT_MV);
}
