/*
 * test_ina228_accum.c — INA228 CHARGE / ENERGY register support (host, fake I2C register file).
 * Formulas from the TI INA228 datasheet SLYS021A (docs/rev2/pcb/evidence/TI_INA228_datasheet_SLYS021A_revA.pdf):
 *   Charge [C] = CURRENT_LSB x CHARGE            (eq. 7, 40-bit two's complement, register 0x0A)
 *   Energy [J] = 16 x 3.2 x CURRENT_LSB x ENERGY (eq. 6, 40-bit unsigned,          register 0x09)
 *   CONFIG bit 14 RSTACC clears both (not self-clearing: write 1 then 0). Both registers roll over on overflow.
 * No real hardware: everything marked BENCH_REQUIRED in docs/rev2/PROTOCOL_V2_DESIGN.md is NOT asserted here.
 */
#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include "ina228.h"
#include "i2c_bus.h"

static int failures = 0;
#define CHECK(cond, msg) do { if (!(cond)) { printf("  FAIL  %s\n", msg); failures++; } else printf("  PASS  %s\n", msg); } while (0)

/* ---- fake I2C: INA228 register file, big-endian, widths per register ---- */
static uint8_t  regs[0x40][5];
static unsigned fail_reg = 0xFFFF;       /* NACK reads/writes of this register */
static uint8_t  cfg_writes[8]; static int n_cfg_writes;

static void set40(uint8_t reg, uint64_t v) { for (int i = 0; i < 5; i++) regs[reg][i] = (uint8_t)(v >> (8 * (4 - i))); }
static void set16(uint8_t reg, uint16_t v) { regs[reg][0] = (uint8_t)(v >> 8); regs[reg][1] = (uint8_t)v; }

osbams_status_t I2C1_ReadReg(uint8_t addr, uint8_t reg, uint8_t *d, uint8_t len)
{
    (void)addr;
    if (reg == fail_reg) return OSBAMS_STATUS_NACK;
    memcpy(d, regs[reg], len);
    return OSBAMS_STATUS_OK;
}
osbams_status_t I2C1_WriteReg(uint8_t addr, uint8_t reg, const uint8_t *d, uint8_t len)
{
    (void)addr;
    if (reg == fail_reg) return OSBAMS_STATUS_NACK;
    if (reg == INA228_REG_CONFIG) {
        uint16_t v = (uint16_t)((d[0] << 8) | d[1]);
        if (n_cfg_writes < 8) cfg_writes[n_cfg_writes++] = (uint8_t)(v >> 8);
        if (v & INA228_CONFIG_RSTACC) { set40(INA228_REG_ENERGY, 0); set40(INA228_REG_CHARGE, 0); }
        set16(reg, (uint16_t)(v & ~0x8000U));
        return OSBAMS_STATUS_OK;
    }
    memcpy(regs[reg], d, len);
    return OSBAMS_STATUS_OK;
}
void I2C1_Init(void) {} osbams_status_t I2C1_RecoverBus(void) { return OSBAMS_STATUS_OK; }
uint8_t I2C1_Scan(uint8_t *a, uint8_t c) { (void)a; (void)c; return 0; }

int main(void)
{
    printf("INA228 accumulator tests\n");

    /* ---- decode ---- */
    uint8_t pos[5] = {0x00, 0x00, 0x00, 0x00, 0x2A};            /*  42 */
    uint8_t neg[5] = {0xFF, 0xFF, 0xFF, 0xFF, 0xD6};            /* -42 */
    uint8_t minv[5] = {0x80, 0x00, 0x00, 0x00, 0x00};           /* -2^39 */
    uint8_t maxs[5] = {0x7F, 0xFF, 0xFF, 0xFF, 0xFF};           /* 2^39 - 1 */
    uint8_t maxu[5] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF};           /* 2^40 - 1 */
    CHECK(INA228_DecodeCharge40(pos) == 42, "charge decode +42");
    CHECK(INA228_DecodeCharge40(neg) == -42, "charge decode -42 (two's complement)");
    CHECK(INA228_DecodeCharge40(minv) == -(1LL << 39), "charge decode most negative");
    CHECK(INA228_DecodeCharge40(maxs) == (1LL << 39) - 1, "charge decode most positive");
    CHECK(INA228_DecodeEnergy40(maxu) == (1ULL << 40) - 1, "energy decode is unsigned 40-bit");

    /* ---- CURRENT_LSB matches what INA228_Init programs (20 A scale -> 38146 nA, truncated) ---- */
    CHECK(INA228_CurrentLsbNa(20000) == 38146U, "CURRENT_LSB for 20 A scale = 38146 nA (truncated, as Init uses)");

    /* ---- scaling: Charge [C] = lsb x code ; 1 Ah = 3600 C ---- */
    int64_t uah = 0, uwh = 0;
    /* choose code so that charge = exactly 1 Ah with lsb = 38146 nA is not integral; use lsb = 100000 nA (0.1 mA): 1 Ah = 3600 C = 36,000,000 codes */
    CHECK(INA228_ChargeToUah(36000000LL, 100000U, &uah) && uah == 1000000LL, "36,000,000 codes @100 uA/LSB = 1 Ah = 1,000,000 uAh");
    CHECK(INA228_ChargeToUah(-36000000LL, 100000U, &uah) && uah == -1000000LL, "negative charge keeps its sign");
    CHECK(INA228_ChargeToUah(0, 38146U, &uah) && uah == 0, "zero charge is a valid 0");
    /* Energy [J] = 16 x 3.2 x lsb x code ; 1 Wh = 3600 J. lsb=100000 nA -> J/code = 51.2 x 1e-4 = 5.12e-3 -> 703125 codes = 3600 J */
    CHECK(INA228_EnergyToUwh(703125ULL, 100000U, &uwh) && uwh == 1000000LL, "703,125 codes @100 uA/LSB = 3600 J = 1 Wh = 1,000,000 uWh");
    CHECK(INA228_EnergyToUwh(0, 38146U, &uwh) && uwh == 0, "zero energy is a valid 0");
    /* datasheet design example: Current LSB 19.073486 uA -> Power LSB 61.035156 uW, Energy LSB 976.5625 uJ, Charge LSB 19.073486 uC */
    CHECK(INA228_ChargeToUah(1, 19073U, &uah) && uah == 0, "single LSB charge (19.07 uC) rounds to 0 uAh");
    /* rounding is to nearest */
    CHECK(INA228_ChargeToUah(189, 19073U, &uah) && uah == 1, "rounds to nearest uAh (189 x 19.073 uC = 1.0013 uAh)");
    /* overflow guard: huge code x huge lsb must be refused, not wrapped */
    CHECK(!INA228_ChargeToUah((1LL << 39) - 1, 0xFFFFFFFFU, &uah), "charge conversion overflow is refused");
    CHECK(!INA228_EnergyToUwh((1ULL << 40) - 1, 0xFFFFFFFFU, &uwh), "energy conversion overflow is refused");
    CHECK(!INA228_ChargeToUah(1, 0U, &uah), "zero LSB is refused");
    CHECK(!INA228_ChargeToUah(1, 38146U, NULL), "NULL out refused");

    /* ---- device interaction through the fake register file ---- */
    set16(INA228_REG_MFR_ID, INA228_MFR_ID_TI); set16(INA228_REG_DEV_ID, 0x2281);
    CHECK(INA228_Init(2500U, 20000U) == OSBAMS_STATUS_OK, "Init succeeds on the fake device");

    ina228_accum_snapshot_t s;
    set40(INA228_REG_CHARGE, 36000000ULL * 38146ULL / 100000ULL);      /* arbitrary positive code */
    set40(INA228_REG_ENERGY, 703125ULL);
    CHECK(INA228_ReadAccumulators(&s) == OSBAMS_STATUS_OK && s.valid, "read accumulators OK");
    int64_t want_q = 0, want_e = 0;
    INA228_ChargeToUah((int64_t)(36000000ULL * 38146ULL / 100000ULL), 38146U, &want_q);
    INA228_EnergyToUwh(703125ULL, 38146U, &want_e);
    CHECK(s.q_uah == want_q && s.e_uwh == want_e, "snapshot uses the programmed CURRENT_LSB");
    CHECK(s.flags == 0, "no flags on a normal read");

    /* a bus error is reported, not turned into zero */
    fail_reg = INA228_REG_ENERGY;
    CHECK(INA228_ReadAccumulators(&s) != OSBAMS_STATUS_OK && !s.valid, "bus error -> status error and snapshot invalid");
    fail_reg = 0xFFFF;

    /* energy decrease (rollover or unexpected reset) is flagged, never silently unwrapped */
    set40(INA228_REG_ENERGY, 1000ULL);
    CHECK(INA228_ReadAccumulators(&s) == OSBAMS_STATUS_OK && (s.flags & INA228_ACCUM_F_DECREASE), "energy decrease latches DECREASE flag");
    set40(INA228_REG_ENERGY, 2000ULL);
    CHECK(INA228_ReadAccumulators(&s) == OSBAMS_STATUS_OK && (s.flags & INA228_ACCUM_F_DECREASE), "DECREASE stays latched until an explicit reset");

    /* explicit reset: RSTACC set then cleared, registers cleared, latch cleared */
    n_cfg_writes = 0;
    CHECK(INA228_ResetAccumulators() == OSBAMS_STATUS_OK, "reset OK");
    CHECK(n_cfg_writes == 2 && (cfg_writes[0] & 0x40) && !(cfg_writes[1] & 0x40), "RSTACC (CONFIG bit 14) written 1 then 0");
    CHECK(INA228_ReadAccumulators(&s) == OSBAMS_STATUS_OK && s.q_uah == 0 && s.e_uwh == 0 && s.flags == 0, "after reset: zero accumulators, flags clear");

    /* reset failure is reported */
    fail_reg = INA228_REG_CONFIG;
    CHECK(INA228_ResetAccumulators() != OSBAMS_STATUS_OK, "reset bus failure is reported");
    fail_reg = 0xFFFF;

    /* reset that does not clear the registers is detected (device stuck) */
    /* (the fake device always honours RSTACC, so the stuck-device rule is checked on the pure helper) */
    CHECK(INA228_ResetVerified(5000ULL, 5000ULL) == false && INA228_ResetVerified(5000ULL, 0ULL) == true && INA228_ResetVerified(0ULL, 0ULL) == true,
          "reset read-back must not be >= the pre-reset energy (unless it was already 0)");

    printf("%s (%d failure%s)\n", failures ? "FAILED" : "All INA228 accumulator tests passed", failures, failures == 1 ? "" : "s");
    return failures ? 1 : 0;
}
