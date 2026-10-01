/*
 * estop.c — E-stop sense monitoring (PA0). See estop.h for the fail-safe
 * contract this implements.
 *
 * Register-level, no HAL — matches i2c_bus.c / uart.c / load_driver.c.
 */

#include "estop.h"
#include "app_config.h"

#ifdef OSBAMS_TARGET_STM32
#include "stm32l476xx.h"
#endif

/* ── Pin configuration ───────────────────────────────────────────── */
#define ESTOP_SENSE_PORT   GPIOA
#define ESTOP_SENSE_PIN    0U     /* PA0: ESTOP_SENSE. LOW=healthy HIGH=tripped */

/* ── State ───────────────────────────────────────────────────────── */
static bool     s_initialized  = false;
static bool     s_cached_tripped = false;
static uint32_t s_trip_count   = 0;

/* ── Low-level read (isolated so the polarity mapping lives in one place) */
static bool read_pin_tripped(void)
{
#ifdef OSBAMS_TARGET_STM32
    return (ESTOP_SENSE_PORT->IDR & (1U << ESTOP_SENSE_PIN)) != 0;
#else
    /* Host build: no hardware present. Report healthy so higher layers'
     * host-testable logic paths (e.g. load_driver.c) aren't blocked by a
     * permanently-tripped E-stop with nothing wired. */
    return false;
#endif
}

osbams_status_t Estop_Init(void)
{
#ifdef OSBAMS_TARGET_STM32
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN;

    /* Input, no internal pull. See file header: the external NC-contact
     * circuit already supplies the pull-up; an internal pull here could
     * mask a broken wire or loose connector reading as healthy. */
    ESTOP_SENSE_PORT->MODER &= ~(3U << (ESTOP_SENSE_PIN * 2));
    ESTOP_SENSE_PORT->PUPDR &= ~(3U << (ESTOP_SENSE_PIN * 2));
#endif

    s_initialized    = true;
    s_trip_count     = 0;
    /* Seed cached state from an immediate read so a boot with the E-stop
     * already tripped is reflected right away, without counting it as a
     * transition event (there's no prior "healthy" state to transition
     * from at boot). */
    s_cached_tripped = read_pin_tripped();
    return OSBAMS_STATUS_OK;
}

void Estop_Poll(void)
{
    if (!s_initialized) return;

    bool tripped = read_pin_tripped();
    if (tripped && !s_cached_tripped) {
        s_trip_count++;
    }
    s_cached_tripped = tripped;
}

bool Estop_IsTripped(void)
{
    return s_cached_tripped;
}

bool Estop_IsHealthy(void)
{
    return !s_cached_tripped;
}

uint32_t Estop_TripCount(void)
{
    return s_trip_count;
}
