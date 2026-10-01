/*
 * system_clock.c — STM32L476 clock configuration
 * HSI16 → PLL → 80 MHz SYSCLK
 *
 * All BRR, TIMINGR, and SysTick values are derived from
 * constants in system_clock.h — never hardcoded here.
 */

#include "system_clock.h"

void SystemClock_Config_80MHz(void)
{
    /* ── 1. Enable HSI16 ─────────────────────────────────────────── */
    RCC->CR |= RCC_CR_HSION;
    while (!(RCC->CR & RCC_CR_HSIRDY));

    /* ── 2. Set flash latency to 4 WS before increasing SYSCLK ──── */
    /* Required at 80 MHz in voltage range 1 (Vcore = 1.2 V)        */
    FLASH->ACR = (FLASH->ACR & ~FLASH_ACR_LATENCY) | FLASH_ACR_LATENCY_4WS;
    /* Verify it was accepted */
    while ((FLASH->ACR & FLASH_ACR_LATENCY) != FLASH_ACR_LATENCY_4WS);

    /* ── 3. Configure PLL: HSI16 (16 MHz) → /2 → ×20 = 160 MHz VCO
     *       PLLR = /2 → SYSCLK = 80 MHz
     *       PLLQ = /2 → USB/SDMMC = 80 MHz (not used in Phase 1)   */
    RCC->PLLCFGR =
        RCC_PLLCFGR_PLLSRC_HSI         /* source = HSI16              */
        | (1UL << RCC_PLLCFGR_PLLM_Pos)   /* /M = /2 (PLLM=1 → div2) */
        | (20UL << RCC_PLLCFGR_PLLN_Pos)  /* ×N = ×20                 */
        | (0UL << RCC_PLLCFGR_PLLR_Pos)   /* /R = /2 (PLLR=00)        */
        | RCC_PLLCFGR_PLLREN;             /* enable R output           */

    /* ── 4. Enable PLL and wait ────────────────────────────────────── */
    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY));

    /* ── 5. Set AHB/APB prescalers before switching:
     *       HCLK  = SYSCLK / 1 = 80 MHz
     *       PCLK1 = HCLK   / 2 = 40 MHz  (APB1: USART2, I2C1)
     *       PCLK2 = HCLK   / 1 = 80 MHz  (APB2: USART1, SPI1)      */
    RCC->CFGR = (RCC->CFGR & ~(RCC_CFGR_HPRE | RCC_CFGR_PPRE1 | RCC_CFGR_PPRE2))
        | RCC_CFGR_HPRE_DIV1            /* AHB  /1 */
        | RCC_CFGR_PPRE1_DIV2           /* APB1 /2 */
        | RCC_CFGR_PPRE2_DIV1;          /* APB2 /1 */

    /* ── 6. Switch SYSCLK to PLL ────────────────────────────────────── */
    RCC->CFGR = (RCC->CFGR & ~RCC_CFGR_SW) | RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL);

    /* ── 7. Update SystemCoreClock for any CMSIS code that uses it ──── */
    SystemCoreClock = OSBAMS_SYSCLK_HZ;
}
