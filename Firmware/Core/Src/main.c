/*
 * main.c — OSBAMS Firmware v4 (recoverable safety states)
 *
 * Layered flow (unchanged):
 *     main.c → Measurement Engine → Sensor Manager → I2C / INA228 / TC74
 *
 * WHAT CHANGED vs v3 (frozen decisions, see DESIGN_DECISIONS.md):
 *
 * 1. Fault() is no longer a while(1) dead end. A fault now: forces the
 *    load off via Load_EmergencyDisable(), transitions the controller to
 *    TEST_FAULT, reports over serial — and RETURNS. The main loop keeps
 *    running so it can stream telemetry, watch the E-stop, and accept the
 *    operator ACK. Recovery: ACK -> SELF_TEST -> re-run checks -> IDLE.
 *    A power cycle is only needed for catastrophic failures (watchdog
 *    reset, corrupt config), never for an ordinary operating fault.
 *
 * 2. E-stop (PA0, estop.c) polled every loop. Trip -> Load_EmergencyDisable()
 *    + TEST_ESTOP (distinct from FAULT). The PA0 path is MONITORING; the
 *    physical NC contact already cut the contactor coil in hardware.
 *
 * 3. Contactor supervision (PC9 via load_driver.c): "commanded OFF but
 *    AUX says ON" is checked every loop while not running — that is the
 *    welded-contactor case and is an immediate fault.
 *
 * 4. Operator ACK arrives over UART as the line "ACK". The ACK is GATED:
 *    ignored unless the controller is in TEST_FAULT or TEST_ESTOP, and
 *    for TEST_ESTOP additionally ignored until Estop_IsHealthy() (the
 *    mushroom is physically reset). On accepted ACK: Safety_Acknowledge(),
 *    controller -> SELF_TEST, checks re-run, PRECHECK_PASS or re-fault.
 *
 * 5. Single tick source: tick.c. SysTick_Handler calls Tick_OnSysTick()
 *    only; the local g_tick_ms is gone.
 *
 * INTEGRATION NOTES (for merging into the real tree):
 *  - Requires the FIXED ina228.c/h (SHUNT_CAL /1e10 + freshness flag) and
 *    the FIXED load_driver.c (PC9 enabled, tick-based timeouts) — the
 *    2026-08 uploads still contained the old versions of both.
 *  - sensor_manager.c must update its call:
 *        INA228_ReadCurrent_mA(&raw32)  ->  INA228_ReadCurrent_mA(&raw32, NULL)
 *    (or pass a real freshness flag once the safety layer consumes it).
 *  - uart.h needs the UART2_TryReadByte() prototype (uart_rx_addition.c).
 */

#include "stm32l476xx.h"
#include "app_config.h"
#include "system_clock.h"
#include "osbams_status.h"
#include "sensor_manager.h"
#include "measurement.h"
#include "safety.h"
#include "test_controller.h"
#include "uart.h"
#include "protocol.h"
#include "acquisition_timer.h"
#include "watchdog.h"
#include "adc_safety.h"
#include "load_driver.h"
#include "estop.h"
#include "tick.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>

/* dev3: this hardware/firmware synchronization pass -- POWER decode fix,
 * TC74 address, Durakool feedback correction, ADC channel config, fresh-
 * sample fault recovery, and the other fixes in this revision. Still a
 * single literal here rather than a shared version header — test_protocol_c.c
 * separately hardcodes "0.9.0-dev1" as a fixed TEST INPUT for exercising
 * the encoder (not a claim about the current firmware version), so that's
 * expected to differ and isn't a bug — but if this project grows a real
 * multi-file version story, centralize both behind one header. */
#define OSBAMS_FW_VERSION_STR  "0.9.0-dev3"

/* ── Globals ─────────────────────────────────────────────────────── */
static sensor_manager_t      g_sensors;
static measurement_context_t g_measure;
static safety_context_t      g_safety;

/* FIX: was a local `test_start_ms` in main()'s loop, set ONCE at boot and
 * never touched again -- so OSBAMS_MAX_TEST_DURATION_S measured "time
 * since boot", not "time since the current test started". A fixture
 * sitting in IDLE long enough could raise FAULT_MAX_DURATION with no
 * test running. Promoted to file scope so PollOperatorCommand()'s fresh
 * Safety_Evaluate() can read it too, and reset on the transition INTO
 * TEST_DISCHARGING (see the main loop) rather than only at boot. */
static uint32_t g_test_start_ms = 0;

static const safety_limits_t g_limits = {
    .max_temp_c10   = OSBAMS_DEFAULT_MAX_TEMP_C10,
    .min_voltage_mv = OSBAMS_DEFAULT_MIN_VOLTAGE_MV,
    .max_voltage_mv = OSBAMS_DEFAULT_MAX_VOLTAGE_MV,
    .max_current_ma = OSBAMS_DEFAULT_MAX_CURRENT_MA,
    .max_duration_s = OSBAMS_MAX_TEST_DURATION_S,
};

/* ── SysTick: sole increment site for the one tick counter ───────── */
void SysTick_Handler(void) { Tick_OnSysTick(); }
void TIM6_DAC_IRQHandler(void) { AcquisitionTimer_OnUpdate(); }

static void SysTick_Init(void) { SysTick_Config(SYSTICK_RELOAD); }

static void delay_ms(uint32_t ms)
{
    uint32_t start = Tick_GetMs();
    while (Tick_ElapsedMs(start) < ms);
}

/* ── LED ─────────────────────────────────────────────────────────── */
static void LED_Init(void)
{
    RCC->AHB2ENR |= RCC_AHB2ENR_GPIOAEN;
    GPIOA->MODER &= ~GPIO_MODER_MODE5;
    GPIOA->MODER |=  GPIO_MODER_MODE5_0;
}
static void LED_On(void)  { GPIOA->ODR |=  (1u << 5); }
static void LED_Off(void) { GPIOA->ODR &= ~(1u << 5); }

/* ── Fault handling: latch, disable, report, RETURN ──────────────── */
static void Fault(const char *reason)
{
    /* Hardware first: force the enable pin low with no waiting. The
     * confirming Load_Disable() check runs in the supervision below. */
    Load_EmergencyDisable();

    TestController_ProcessEvent(TEST_EVT_FAULT);

    char buf[80];
    size_t n = Protocol_EncodeFault(buf, sizeof(buf), reason);
    if (n) UART2_SendBytes((const uint8_t *)buf, (uint16_t)n);
    /* No while(1). The loop continues: telemetry, E-stop watch, ACK. */
}

static void EnterEstop(void)
{
    Load_EmergencyDisable();
    TestController_ProcessEvent(TEST_EVT_ESTOP);
    char buf[64];
    size_t n = Protocol_EncodeState(buf, sizeof(buf), TEST_ESTOP);
    if (n) UART2_SendBytes((const uint8_t *)buf, (uint16_t)n);
}

/* ── Boot / recovery self-test (shared by both paths) ────────────── */
/* Returns true if every startup requirement from the frozen design holds:
 * E-stop healthy, electrical + temperature channels ONLINE (via the Sensor
 * Manager — main.c names no chips, per the layering rule), contactor
 * confirmed open, no latched fault. Called at boot AND after every ACK. */
static bool RunSelfChecks(void)
{
    Estop_Poll();
    if (!Estop_IsHealthy())               return false;

    /* Chip-level probing stays inside the Sensor Manager; main.c only
     * asks for channel health. A recovery attempt first gives an OFFLINE
     * channel its chance to come back before we judge it. */
    SensorManager_AttemptRecovery(&g_sensors);
    if (SensorManager_GetHealth(&g_sensors, SENSOR_CH_BUS_VOLTAGE)
            != SENSOR_HEALTH_ONLINE)      return false;
    if (SensorManager_GetHealth(&g_sensors, SENSOR_CH_CURRENT)
            != SENSOR_HEALTH_ONLINE)      return false;
    if (SensorManager_GetHealth(&g_sensors, SENSOR_CH_TEMP_PACK)
            != SENSOR_HEALTH_ONLINE)      return false;

    /* Contactor: LOAD_FEEDBACK_PRESENT is now 1 (FROZEN) -- PC9 carries
     * real, definitive K1 feedback via the VO610A optocoupler, active
     * low. Load_Disable() here returns LOAD_STUCK if PC9 still reads
     * "closed" after commanding the pin low -- a genuinely welded
     * contactor, confirmed by actual HV presence downstream, not just
     * an inference. This is now a real, meaningful self-test gate. */
    if (Load_IsEnabled())                 return false;
    if (Load_Disable() == OSBAMS_STATUS_LOAD_STUCK) return false;

    if (g_safety.fault_latched)           return false;

    return true;
}

/* ── Operator command input: reads "ACK" line, gated by state ────── */
/*
 * FIX: previously called Safety_Acknowledge() (clearing the latch)
 * BEFORE RunSelfChecks(), and RunSelfChecks() only checks sensor HEALTH
 * (is the chip answering?) and Estop/contactor STATE — it never
 * re-evaluates actual voltage/current/temperature against thresholds.
 * A persistent condition (e.g. a pack still sitting at 45 V) would clear
 * the latch, pass the health checks, reach IDLE, and only re-fault on
 * the NEXT periodic acquisition — a window where the system reports IDLE
 * while still genuinely out of limits.
 *
 * Fixed order: keep the OLD fault latched through SELF_TEST, acquire a
 * FRESH sample, run Safety_Evaluate() against it, and only clear the old
 * latch + proceed to IDLE if that fresh evaluation itself reports
 * FAULT_NONE. If it doesn't, Safety_Evaluate() has already re-latched
 * the (possibly new) fault, and Fault() is called again — the state
 * never leaves FAULT/E_STOP on a still-bad reading.
 */
static void PollOperatorCommand(void)
{
    static char    cmd[16];
    static uint8_t cmd_len = 0;

    uint8_t b;
    while (UART2_TryReadByte(&b)) {
        if (b == '\n' || b == '\r') {
            cmd[cmd_len] = '\0';
            uint8_t had = cmd_len;
            cmd_len = 0;
            if (had == 0) continue;

            if (strcmp(cmd, "ACK") == 0) {
                test_state_t st = TestController_GetState();
                if (st != TEST_FAULT && st != TEST_ESTOP) continue;

                /* E-stop ACK gate: mushroom must be physically reset. */
                Estop_Poll();
                if (st == TEST_ESTOP && !Estop_IsHealthy()) {
                    UART2_SendString("OSBAMS,NACK,ESTOP_STILL_TRIPPED\r\n");
                    continue;
                }

                /* Old latch stays SET through this — do NOT acknowledge yet. */
                TestController_ProcessEvent(TEST_EVT_ACK_FAULT); /* -> SELF_TEST */

                bool checks_ok = RunSelfChecks();
                bool sample_ok = false;

                if (checks_ok) {
                    /* Fresh sample, fresh evaluation — this is the check
                     * that was missing before. */
                    uint64_t ts_us = (uint64_t)Tick_GetMs() * 1000ULL;
                    Measurement_Acquire(&g_measure, ts_us);
                    uint32_t elapsed_s = Tick_ElapsedMs(g_test_start_ms) / 1000;
                    fault_code_t f = Safety_Evaluate(&g_safety, &g_limits,
                                                     &g_measure.latest, elapsed_s);
                    sample_ok = (f == FAULT_NONE);
                }

                if (checks_ok && sample_ok) {
                    /* Only NOW clear the old latch — proven safe on a
                     * sample acquired after the ACK, not on stale state. */
                    Safety_Acknowledge(&g_safety);
                    TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
                    char sb[64];
                    size_t n = Protocol_EncodeState(sb, sizeof(sb), TEST_IDLE);
                    if (n) UART2_SendBytes((const uint8_t *)sb, (uint16_t)n);
                } else {
                    /* checks_ok==false: RunSelfChecks() failed (sensor/
                     * estop/contactor). sample_ok==false: fresh evaluation
                     * still found a fault (already re-latched by
                     * Safety_Evaluate() above, if that's the branch taken).
                     * Either way: re-fault, stay latched, no path to IDLE. */
                    Fault("SELFTEST_RECHECK");
                }
            }
            /* Unknown commands ignored in v1; command set grows via
             * protocol.c, not ad-hoc strings here. */
        } else if (cmd_len < sizeof(cmd) - 1) {
            cmd[cmd_len++] = (char)b;
        } else {
            cmd_len = 0;   /* overlong line: discard */
        }
    }
}

/* ── Report sensor health at boot ────────────────────────────────── */
static void ReportSensorHealth(void)
{
    char buf[96];
    for (int ch = 0; ch < SENSOR_CH_COUNT; ch++) {
        sensor_health_t h = SensorManager_GetHealth(&g_sensors,
                                                     (sensor_channel_t)ch);
        snprintf(buf, sizeof(buf), "OSBAMS,SENSOR,%s,%s\r\n",
                 SensorManager_ChannelName((sensor_channel_t)ch),
                 SensorManager_HealthName(h));
        UART2_SendString(buf);
    }
}

/* ── Main ────────────────────────────────────────────────────────── */
int main(void)
{
    /* 1. Clock first */
    SystemClock_Config_80MHz();
    SysTick_Init();

    reset_cause_t reset_cause = Watchdog_GetResetCause();
    (void)reset_cause;   /* reported below once UART is up */

    /* 2. Basic I/O — E-stop sense and load driver come up before anything
     * that could energize hardware, so their fail-safe defaults hold. */
    LED_Init();
    UART2_Init();
    Load_Init();          /* PC8 low + PC9 input before all else */
    Estop_Init();         /* PA0 input, no pull */
    LED_On();

    {
        char boot[64];
        size_t bn = Protocol_EncodeBoot(boot, sizeof(boot), OSBAMS_FW_VERSION_STR);
        if (bn) UART2_SendBytes((const uint8_t *)boot, (uint16_t)bn);
    }
    delay_ms(50);

    /* 3. Test controller */
    TestController_Init();
    TestController_ProcessEvent(TEST_EVT_INIT_DONE);   /* BOOT -> SELF_TEST */

    /* 4. Sensor Manager */
    osbams_status_t sensor_st = SensorManager_Init(&g_sensors);

    AdcSafety_Init();
    AcquisitionTimer_Init(OSBAMS_SAMPLE_PERIOD_MS);
    AcquisitionTimer_Start();
    Watchdog_Init(OSBAMS_SAMPLE_PERIOD_MS * 4U);
    ReportSensorHealth();

    /* 5/6. Measurement + Safety */
    Measurement_Init(&g_measure, &g_sensors);
    Safety_Init(&g_safety);

    /* 7. Boot self-test: sensor init result + the shared checks. Failure
     * latches FAULT but no longer hangs the MCU — telemetry and the ACK
     * path stay alive so the operator can see why and recover. */
    if (sensor_st != OSBAMS_STATUS_OK) {
        Fault("SENSOR_INIT");
    } else if (!RunSelfChecks()) {
        Fault("SELFTEST_BOOT");
    } else {
        TestController_ProcessEvent(TEST_EVT_PRECHECK_PASS);
        UART2_SendString("OSBAMS,STATE,IDLE\r\n");
    }
    LED_Off();

    /* 8. Main loop */
    uint32_t last_recovery_ms = 0;
    g_test_start_ms = Tick_GetMs();     /* boot-time value; reset again on
                                          * entering DISCHARGING below */
    test_state_t prev_state = TestController_GetState();

    while (1)
    {
        test_state_t state = TestController_GetState();

        /* FIX: reset the test-duration clock on the transition INTO
         * DISCHARGING, not just once at boot. See g_test_start_ms's
         * declaration comment.
         * HONEST CAVEAT: main.c does not yet drive TEST_EVT_START anywhere
         * (that's the separate, larger "main.c doesn't implement the
         * actual discharge-test control loop" gap — Load_Enable() is
         * never called here either). So this transition is currently
         * unreachable in practice; it's here so the timer logic is
         * correct and ready the moment that control loop gets built,
         * rather than being a second bug discovered later. */
        if (state == TEST_DISCHARGING && prev_state != TEST_DISCHARGING) {
            g_test_start_ms = Tick_GetMs();
        }
        prev_state = state;

        /* Heartbeat: solid in FAULT/E_STOP, blink otherwise */
        if (state == TEST_FAULT || state == TEST_ESTOP) LED_On();
        else if ((Tick_GetMs() % 1000) < 50) LED_On(); else LED_Off();

        /* ── E-stop: every iteration, before anything else ────────── */
        Estop_Poll();
        if (Estop_IsTripped() && state != TEST_ESTOP) {
            EnterEstop();
            state = TEST_ESTOP;
        }

        /* ── Contactor supervision: commanded OFF but AUX ON = welded.
         * Only meaningful when we believe the load is off; the ON-path
         * confirmation happens inside Load_Enable() itself. ────────── */
        if (!Load_IsEnabled() && state != TEST_FAULT && state != TEST_ESTOP) {
            if (Load_ConfirmOffByCurrent(g_measure.latest.current_ma)
                    == OSBAMS_STATUS_LOAD_STUCK) {
                Fault("CONTACTOR_WELDED");
                state = TEST_FAULT;
            }
        }

        /* ── Operator commands (ACK) ──────────────────────────────── */
        PollOperatorCommand();
        state = TestController_GetState();   /* ACK may have changed it */

        /* ── Periodic sensor recovery (unchanged) ─────────────────── */
        if (Tick_ElapsedMs(last_recovery_ms) >= 10000) {
            last_recovery_ms = Tick_GetMs();
            SensorManager_AttemptRecovery(&g_sensors);
        }

        /* ── Deterministic acquisition ────────────────────────────── */
        if (!AcquisitionTimer_SampleDue()) {
            Watchdog_Refresh();
            continue;
        }
        Watchdog_ReportHeartbeat(WD_ACQUISITION_HEARTBEAT);

        uint64_t ts_us = (uint64_t)Tick_GetMs() * 1000ULL;
        osbams_status_t acq = Measurement_Acquire(&g_measure, ts_us);
        (void)acq;

        const measurement_sample_t *s = &g_measure.latest;

        /* ── Safety evaluation: runs in EVERY state, including FAULT and
         * E_STOP — a latched system still watches its sensors. New faults
         * while already latched are re-latched in the safety context (the
         * controller stays where it is; E_STOP is not demoted). ─────── */
        uint32_t elapsed_s = Tick_ElapsedMs(g_test_start_ms) / 1000;
        fault_code_t fault = Safety_Evaluate(&g_safety, &g_limits, s, elapsed_s);
        Watchdog_ReportHeartbeat(WD_SAFETY_HEARTBEAT);
        Watchdog_ReportHeartbeat(WD_CONTROLLER_HEARTBEAT);

        if (fault != FAULT_NONE && g_safety.fault_latched
            && state != TEST_FAULT && state != TEST_ESTOP) {
            char fb[32];
            snprintf(fb, sizeof(fb), "FAULT_%d", (int)fault);
            Fault(fb);
            state = TEST_FAULT;
        }

        /* ── Telemetry frame (CRC-protected, carries the state name) ── */
        char frame[PROTOCOL_FRAME_MAX];
        size_t n = Protocol_EncodeData(frame, sizeof(frame), s,
                                       TestController_GetState());
        if (n) UART2_SendBytes((const uint8_t *)frame, (uint16_t)n);
    }
}
