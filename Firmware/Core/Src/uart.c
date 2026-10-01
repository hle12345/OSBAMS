/*
 * uart.c — USART2 driver using system_clock.h constants
 * PA2=TX (AF7), PA3=RX (AF7) → ST-Link virtual COM
 *
 * BRR is derived from UART2_BRR_VALUE in system_clock.h.
 * Do NOT hardcode 35 or 139 here — change the clock header instead.
 */

#include "uart.h"
#include "system_clock.h"
#include "stm32l476xx.h"

void UART2_Init(void)
{
    /* 1. Enable clocks */
    RCC->AHB2ENR  |= RCC_AHB2ENR_GPIOAEN;
    RCC->APB1ENR1 |= RCC_APB1ENR1_USART2EN;

    /* 2. PA2 TX, PA3 RX → AF7 */
    GPIOA->MODER  &= ~(GPIO_MODER_MODE2 | GPIO_MODER_MODE3);
    GPIOA->MODER  |=  (GPIO_MODER_MODE2_1 | GPIO_MODER_MODE3_1);
    GPIOA->AFR[0] &= ~(0xFF << 8);
    GPIOA->AFR[0] |=  (0x77 << 8);   /* AF7 on PA2 and PA3 */

    /* 3. BRR derived from system_clock.h — correct for any PCLK1 value */
    USART2->BRR = UART2_BRR_VALUE;    /* e.g. 347 at 40 MHz PCLK1 */
    USART2->CR1 = USART_CR1_TE
                | USART_CR1_RE
                | USART_CR1_UE;
}

void UART2_SendBytes(const uint8_t *buf, uint16_t len)
{
    for (uint16_t i = 0; i < len; i++) {
        while (!(USART2->ISR & USART_ISR_TXE));
        USART2->TDR = buf[i];
    }
    while (!(USART2->ISR & USART_ISR_TC));
}

void UART2_SendString(const char *s)
{
    while (*s) {
        while (!(USART2->ISR & USART_ISR_TXE));
        USART2->TDR = (uint8_t)(*s++);
    }
}

/*
 * UART2_TryReadByte — ADDED so the firmware can receive the operator ACK
 * command required by the frozen FAULT/E_STOP recovery sequence. CR1
 * already enabled RE, but nothing previously read RDR.
 *
 * Non-blocking, no interrupt, no ring buffer: at 115200 baud a byte
 * arrives every ~87 us; the main loop polls far faster than an operator
 * types, and an ACK command is not telemetry — if a byte is missed
 * because the loop was mid-I2C-transaction, the operator's terminal
 * simply resends. An RX interrupt + ring buffer is a reasonable future
 * upgrade, not a requirement for recovery to work correctly.
 */
bool UART2_TryReadByte(uint8_t *out)
{
    if (!out) return false;
    if (USART2->ISR & USART_ISR_RXNE) {
        *out = (uint8_t)USART2->RDR;
        return true;
    }
    if (USART2->ISR & USART_ISR_ORE) {
        USART2->ICR = USART_ICR_ORECF;   /* clear overrun, keep receiving */
    }
    return false;
}
