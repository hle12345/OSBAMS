/*
 * tick.c — the single authoritative millisecond timebase. See tick.h.
 */
#include "tick.h"

static volatile uint32_t s_tick_ms = 0;

void Tick_OnSysTick(void)
{
    s_tick_ms++;
}

uint32_t Tick_GetMs(void)
{
    return s_tick_ms;
}

uint32_t Tick_ElapsedMs(uint32_t since_ms)
{
    return Tick_GetMs() - since_ms;
}
