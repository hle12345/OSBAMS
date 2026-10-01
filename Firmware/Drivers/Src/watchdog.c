/*
 * watchdog.c — Independent Watchdog (IWDG) with subsystem-heartbeat gating
 *
 * The IWDG is clocked by the ~32 kHz LSI. With prescaler /32 the counter ticks
 * at ~1 kHz, so a reload value of timeout_ms gives roughly timeout_ms of
 * timeout. LSI tolerance is wide, so the timeout is approximate by design; it
 * is set comfortably longer than the supervision interval.
 *
 * Refresh is gated: the reload only happens when every required activity has
 * reported since the last refresh. A stalled subsystem withholds the refresh and the
 * IWDG resets the MCU.
 */

#include "watchdog.h"

#ifdef OSBAMS_TARGET_STM32
#include "stm32l476xx.h"
#endif

#define IWDG_KEY_RELOAD   0x0000AAAAU
#define IWDG_KEY_ENABLE   0x0000CCCCU
#define IWDG_KEY_ACCESS   0x00005555U
#define LSI_APPROX_HZ     32000U
#define IWDG_PRESCALER    32U
#define IWDG_TICK_HZ      (LSI_APPROX_HZ / IWDG_PRESCALER)   /* ~1 kHz */

static volatile uint32_t s_reported = 0U;
static bool              s_started  = false;

reset_cause_t Watchdog_GetResetCause(void)
{
    reset_cause_t cause = RESET_CAUSE_UNKNOWN;
#ifdef OSBAMS_TARGET_STM32
    uint32_t csr = RCC->CSR;
    if      (csr & RCC_CSR_IWDGRSTF) cause = RESET_CAUSE_WATCHDOG;
    else if (csr & RCC_CSR_SFTRSTF)  cause = RESET_CAUSE_SOFTWARE;
    else if (csr & RCC_CSR_PINRSTF)  cause = RESET_CAUSE_PIN;
    else if (csr & RCC_CSR_BORRSTF)  cause = RESET_CAUSE_BROWNOUT;
    else if (csr & RCC_CSR_PORRSTF)  cause = RESET_CAUSE_POWER_ON;
    RCC->CSR |= RCC_CSR_RMVF;   /* clear reset flags */
#endif
    return cause;
}

osbams_status_t Watchdog_Init(uint32_t timeout_ms)
{
    if (timeout_ms == 0U) return OSBAMS_STATUS_INVALID_ARGUMENT;

    uint32_t reload = (timeout_ms * IWDG_TICK_HZ) / 1000U;
    if (reload == 0U)     reload = 1U;
    if (reload > 0x0FFFU) reload = 0x0FFFU;   /* 12-bit reload */

#ifdef OSBAMS_TARGET_STM32
    IWDG->KR  = IWDG_KEY_ENABLE;     /* start IWDG */
    IWDG->KR  = IWDG_KEY_ACCESS;     /* enable register writes */
    IWDG->PR  = 3U;                  /* prescaler /32 */
    IWDG->RLR = (uint16_t)reload;
    while (IWDG->SR != 0U) { /* wait for PR/RLR update */ }
    IWDG->KR  = IWDG_KEY_RELOAD;     /* refresh once */
#endif

    s_reported = 0U;
    s_started  = true;
    return OSBAMS_STATUS_OK;
}

void Watchdog_ReportHeartbeat(watchdog_heartbeat_t task)
{
    s_reported |= (uint32_t)task;
}

osbams_status_t Watchdog_Refresh(void)
{
    if (!s_started) return OSBAMS_STATUS_NOT_READY;

    if ((s_reported & WATCHDOG_REQUIRED_HEARTBEATS) != WATCHDOG_REQUIRED_HEARTBEATS) {
        /* Not all critical subsystems have run — withhold the refresh so the
         * IWDG will fire if this persists. */
        return OSBAMS_STATUS_BUSY;
    }

#ifdef OSBAMS_TARGET_STM32
    IWDG->KR = IWDG_KEY_RELOAD;
#endif
    s_reported = 0U;   /* require a fresh round before the next refresh */
    return OSBAMS_STATUS_OK;
}
