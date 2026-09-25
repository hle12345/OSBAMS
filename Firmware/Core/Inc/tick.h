/*
 * tick.h — the single authoritative millisecond timebase.
 *
 * REVISION NOTE: the first version of this file created a second,
 * independent counter alongside main.c's existing `g_tick_ms`. That was
 * wrong — two counters that are supposed to mean the same thing but are
 * incremented separately WILL drift (different start time, and nothing
 * guarantees they're read/written atomically relative to each other).
 * A module using Tick_GetMs() and main.c's own delay_ms() using g_tick_ms
 * could disagree about elapsed time by however many ms of drift had
 * accumulated, which is exactly the kind of thing that shows up once,
 * intermittently, on the bench and nowhere in review.
 *
 * Fixed: this is now the ONLY tick counter in the firmware. main.c's
 * SysTick_Handler must call ONLY Tick_OnSysTick() — it must NOT also keep
 * its own `g_tick_ms++`. All of main.c's internal timing (delay_ms(),
 * heartbeat, sample/recovery intervals, elapsed-time calc, the ts_us
 * passed to Measurement_Acquire(), and the tick value in the serial
 * frame) now reads Tick_GetMs() instead of a local static. See the
 * accompanying main.c diff.
 */
#ifndef TICK_H
#define TICK_H

#include <stdint.h>

/** @brief Call ONLY from SysTick_Handler (ISR context). This is the sole
 *         place the tick counter is incremented anywhere in the firmware. */
void Tick_OnSysTick(void);

/** @brief Current tick count in milliseconds since boot. Wraps at
 *         UINT32_MAX (~49.7 days @ 1 ms tick). */
uint32_t Tick_GetMs(void);

/**
 * @brief Milliseconds elapsed since a previous Tick_GetMs() snapshot.
 *
 * Unsigned subtraction wraps correctly across a rollover as long as the
 * elapsed duration itself is under ~49.7 days, true for every timeout in
 * this codebase.
 */
uint32_t Tick_ElapsedMs(uint32_t since_ms);

#endif /* TICK_H */
