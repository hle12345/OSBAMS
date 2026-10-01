/*
 * acquisition_timer.c — Deterministic sample timing (TIM6)
 *
 * TIM6 is a basic 16-bit timer on APB1. With PCLK1 = 40 MHz and the APB1 timer
 * clock doubled to 80 MHz, a prescaler of 8000 gives a 10 kHz tick (100 us),
 * and an auto-reload of (period_ms * 10) yields the requested period. A 500 ms
 * period needs ARR = 5000, well within the 16-bit range.
 *
 * The ISR sets a flag only. The measurement loop polls SampleDue() and takes
 * one timestamped sample per elapsed period, so acquisition timing does not
 * depend on how long the main loop takes elsewhere.
 */

#include "acquisition_timer.h"
#include "app_config.h"

#ifdef OSBAMS_TARGET_STM32
#include "stm32l476xx.h"
#endif

/* APB1 timer clock after the ×2 multiplier when APB1 prescaler != 1.
 * system_clock.c sets PCLK1 = 40 MHz, so the timer clock is 80 MHz. */
#define TIM6_TIMER_CLOCK_HZ   80000000UL
#define TIM6_TICK_HZ          10000UL          /* 100 us tick */
#define TIM6_PRESCALER        ((TIM6_TIMER_CLOCK_HZ / TIM6_TICK_HZ) - 1U)

static volatile uint32_t s_pending_samples = 0U;  /* ISR increments, foreground decrements */
static bool          s_initialised = false;

osbams_status_t AcquisitionTimer_Init(uint32_t period_ms)
{
    if (period_ms == 0U) return OSBAMS_STATUS_INVALID_ARGUMENT;

    uint32_t arr = (period_ms * (TIM6_TICK_HZ / 1000UL));
    if (arr == 0U || arr > 0xFFFFU) return OSBAMS_STATUS_INVALID_ARGUMENT;

#ifdef OSBAMS_TARGET_STM32
    RCC->APB1ENR1 |= RCC_APB1ENR1_TIM6EN;

    TIM6->CR1  = 0U;                 /* stop, defaults */
    TIM6->PSC  = (uint16_t)TIM6_PRESCALER;
    TIM6->ARR  = (uint16_t)(arr - 1U);
    TIM6->CNT  = 0U;
    TIM6->EGR  = TIM_EGR_UG;         /* load PSC/ARR */
    TIM6->SR   = 0U;                 /* clear pending */
    TIM6->DIER = TIM_DIER_UIE;       /* update interrupt */

    NVIC_SetPriority(TIM6_DAC_IRQn, 2U);
    NVIC_EnableIRQ(TIM6_DAC_IRQn);
#endif

    s_pending_samples = 0U;
    s_initialised     = true;
    return OSBAMS_STATUS_OK;
}

osbams_status_t AcquisitionTimer_Start(void)
{
    if (!s_initialised) return OSBAMS_STATUS_NOT_READY;
#ifdef OSBAMS_TARGET_STM32
    TIM6->CNT = 0U;
    TIM6->CR1 |= TIM_CR1_CEN;
#endif
    return OSBAMS_STATUS_OK;
}

osbams_status_t AcquisitionTimer_Stop(void)
{
    if (!s_initialised) return OSBAMS_STATUS_NOT_READY;
#ifdef OSBAMS_TARGET_STM32
    TIM6->CR1 &= ~TIM_CR1_CEN;
#endif
    return OSBAMS_STATUS_OK;
}

bool AcquisitionTimer_SampleDue(void)
{
    /*
     * FIX: `volatile` guarantees the compiler won't cache/reorder this
     * variable, but it does NOT make read-modify-write atomic against
     * the ISR. Without a critical section, this sequence is possible:
     *   foreground reads s_pending_samples == 1
     *   <TIM6 ISR fires here, increments to 2>
     *   foreground writes s_pending_samples = 0   (its own decrement,
     *     computed from the STALE value 1, not the current 2)
     * One pending sample is silently lost. Brief global-IRQ-disable
     * critical section around the read-modify-write closes this; the
     * masked window is a handful of instructions, negligible next to a
     * 500ms sample period.
     */
#ifdef OSBAMS_TARGET_STM32
    __disable_irq();
    bool due = false;
    if (s_pending_samples > 0U) {
        s_pending_samples--;
        due = true;
    }
    __enable_irq();
    return due;
#else
    if (s_pending_samples > 0U) {
        s_pending_samples--;
        return true;
    }
    return false;
#endif
}

uint32_t AcquisitionTimer_PendingCount(void)
{
    return s_pending_samples;
}

void AcquisitionTimer_OnUpdate(void)
{
#ifdef OSBAMS_TARGET_STM32
    if (TIM6->SR & TIM_SR_UIF) {
        TIM6->SR &= ~TIM_SR_UIF;
        if (s_pending_samples < 0xFFFFFFFFU) s_pending_samples++;
    }
#else
    if (s_pending_samples < 0xFFFFFFFFU) s_pending_samples++;
#endif
}
