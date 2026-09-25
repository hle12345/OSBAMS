/*
 * uart.h — RECONSTRUCTED from uart.c. UART2_TryReadByte is the ADDED
 * function (see uart.c's inline note) that makes the operator ACK
 * command receivable — CR1 already enabled RE but nothing previously
 * read RDR.
 */
#ifndef UART_H
#define UART_H

#include <stdint.h>
#include <stdbool.h>

void UART2_Init(void);
void UART2_SendBytes(const uint8_t *buf, uint16_t len);
void UART2_SendString(const char *s);
bool UART2_TryReadByte(uint8_t *out);

#endif /* UART_H */
