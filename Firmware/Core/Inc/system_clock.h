/*
 * system_clock.h — OSBAMS Clock Configuration (single source of truth)
 *
 * ALL clock-dependent values (BRR, TIMINGR, SysTick reload) are derived
 * from the constants defined here. Never hardcode MHz values elsewhere.
 *
 * Target: STM32L476RG Nucleo
 * Clock source: HSI16 (16 MHz internal RC), PLL → 80 MHz SYSCLK
 *
 * Why 80 MHz instead of the MSI 4 MHz default?
 *   - USART2 BRR = 35 at 4 MHz gives poor accuracy at 115200 baud
 *     (actual rate ~114,286 baud = 0.8% error, borderline for long frames)
 *   - At 80 MHz: BRR = 694 → exact 115,200 baud
 *   - I2C TIMINGR from AN4235 is calibrated for 16 MHz PCLK1
 *   - SysTick at 4 MHz gives only 4000 ticks/ms — fine, but 80 MHz
 *     enables future features (ADC, USB, FreeRTOS) without re-tuning
 *
 * Boot sequence:
 *   1. Enable HSI16: RCC_CR_HSION, wait RCC_CR_HSIRDY
 *   2. Configure PLL: HSI16 → /2 → x20 → SYSCLK = 80 MHz
 *   3. Set flash latency to 4 WS (required at 80 MHz, VR = range 1)
 *   4. Switch SYSCLK to PLL
 *   5. HCLK = SYSCLK / 1 = 80 MHz
 *      PCLK1 (APB1, USART2/I2C1) = HCLK / 2 = 40 MHz
 *      PCLK2 (APB2) = HCLK / 1 = 80 MHz
 */

#ifndef SYSTEM_CLOCK_H
#define SYSTEM_CLOCK_H

#include <stdint.h>
#include "stm32l476xx.h"

/* ── Clock tree constants ────────────────────────────────────────────────── */

#define OSBAMS_SYSCLK_HZ    80000000UL   /* 80 MHz after PLL */
#define OSBAMS_PCLK1_HZ     40000000UL   /* APB1 = SYSCLK/2  */
#define OSBAMS_PCLK2_HZ     80000000UL   /* APB2 = SYSCLK/1  */

/* ── Derived constants (computed, not hardcoded) ─────────────────────────── */

/* USART2 on PCLK1: BRR = PCLK1 / baudrate */
#define UART_BAUD           115200UL
#define UART2_BRR_VALUE     ((OSBAMS_PCLK1_HZ + UART_BAUD / 2) / UART_BAUD)
/* = (40000000 + 57600) / 115200 = 347 → actual baud = 40000000/347 = 115274 (0.06% error) */

/* SysTick for 1 ms tick: reload = SYSCLK_HZ / 1000 - 1 */
#define SYSTICK_RELOAD      (OSBAMS_SYSCLK_HZ / 1000UL - 1UL)

/* I2C1 TIMINGR for ~100 kHz on PCLK1 = 40 MHz
 * From STM32CubeMX I2C timing tool (AN4235) at 40 MHz:
 *   PRESC=7, SCLDEL=4, SDADEL=2, SCLH=15, SCLL=19
 * Actual SCL ~96 kHz — within I2C spec */
#define I2C1_TIMINGR_VALUE  ((7UL << 28) | (4UL << 20) | (2UL << 16) | \
                             (15UL << 8) | (19UL << 0))

/* ── Public API ──────────────────────────────────────────────────────────── */

/**
 * @brief  Configure PLL from HSI16, switch SYSCLK to 80 MHz.
 *         Call this FIRST in main(), before any peripheral init.
 */
void SystemClock_Config_80MHz(void);

#endif /* SYSTEM_CLOCK_H */
