/*
 * ina228.c — INA228 Precision Power Monitor driver
 *
 * Register-level implementation over i2c_bus.c. All conversions use the
 * datasheet-defined LSB sizes. See ina228.h for the scaling rationale.
 *
 * This driver replaces the earlier INA260 driver. The INA260's integrated
 * shunt caps bus voltage at 36 V, below the 42 V a fully charged 10S NMC pack
 * reaches; the INA228 measures bus voltage to 85 V with an external shunt and
 * is therefore the part OSBAMS uses to assess charged packs safely.
 *
 * --- FIX (see DESIGN_DECISIONS.md / build-order review) ---
 * The original SHUNT_CAL computation divided by 1e13 instead of 1e10, which
 * is a 1000x scaling error. Derivation of the correct divisor:
 *
 *   SHUNT_CAL = 13107.2e6 * CURRENT_LSB(A) * R_shunt(Ohm)
 *
 * With CURRENT_LSB in nA (CURRENT_LSB(A) = lsb_nA * 1e-9) and R_shunt in
 * micro-ohms (R_shunt(Ohm) = shunt_uOhm * 1e-6):
 *
 *   SHUNT_CAL = 13107.2e6 * lsb_nA * 1e-9 * shunt_uOhm * 1e-6
 *             = 13107.2e6 * 1e-15 * lsb_nA * shunt_uOhm
 *             = 1.31072e-5 * lsb_nA * shunt_uOhm
 *             = (131072 * lsb_nA * shunt_uOhm) / 1e10      <-- correct
 *
 * (131072 / 1e10 = 1.31072e-5, matching the coefficient above. The previous
 * code used /1e13, i.e. 131072/1e13 = 1.31072e-8 -- three decades too small,
 * which collapsed SHUNT_CAL for the RSA-20-50 (2.5 mOhm, 20 A) case to 1
 * instead of ~1250, making current/power reads ~1000x too small.)
 */

#include "ina228.h"
#include "i2c_bus.h"

/* ── Fixed-point scaling from the datasheet ─────────────────────────────── */
/* Bus voltage: 195.3125 µV/LSB. To get millivolts from the 20-bit code:
 *   mV = code × 195.3125 / 1000 = code × 3125 / 16000 (exact, integer-safe). */
#define VBUS_NUM   3125
#define VBUS_DEN   16000

/* Shunt voltage: 312.5 nV/LSB (ADCRANGE = 0).
 *   µV = code × 312.5 / 1000 = code × 5 / 16 (exact). */
#define VSHUNT_NUM 5
#define VSHUNT_DEN 16

/* Die temperature: 7.8125 m°C/LSB (unused for pack temp, provided for probe). */

/* SHUNT_CAL divisor. See file header derivation. Corrected from 1e13 -> 1e10. */
#define SHUNT_CAL_DIVISOR 10000000000ULL   /* 1e10 */

/* Runtime-computed current scaling. CURRENT_LSB is in nanoamps to keep the
 * arithmetic in integers: current_mA = code × CURRENT_LSB_nA / 1e6. */
static uint32_t s_current_lsb_nA = 0;
static uint8_t  s_ready          = 0;

/* ── Low-level register helpers (INA228 registers are big-endian) ───────── */

static osbams_status_t rd16(uint8_t reg, uint16_t *out)
{
    uint8_t b[2];
    osbams_status_t st = I2C1_ReadReg(INA228_I2C_ADDR, reg, b, 2);
    if (st != OSBAMS_STATUS_OK) return st;
    *out = (uint16_t)((b[0] << 8) | b[1]);
    return OSBAMS_STATUS_OK;
}

static osbams_status_t wr16(uint8_t reg, uint16_t val)
{
    uint8_t b[2] = { (uint8_t)(val >> 8), (uint8_t)(val & 0xFF) };
    return I2C1_WriteReg(INA228_I2C_ADDR, reg, b, 2);
}

/* 24-bit registers (VSHUNT, VBUS, CURRENT) return sign-extended or
 * unsigned 20-bit results left-justified in a 24-bit field; the low 4
 * bits are reserved and must be shifted out. */
static osbams_status_t rd24(uint8_t reg, int32_t *out, int is_signed)
{
    uint8_t b[3];
    osbams_status_t st = I2C1_ReadReg(INA228_I2C_ADDR, reg, b, 3);
    if (st != OSBAMS_STATUS_OK) return st;

    uint32_t raw = ((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2];
    raw >>= 4;                         /* drop 4 reserved LSBs → 20-bit code */

    if (is_signed && (raw & 0x00080000U))   /* sign-extend 20-bit negative */
        raw |= 0xFFF00000U;

    *out = (int32_t)raw;
    return OSBAMS_STATUS_OK;
}

/*
 * POWER (register 0x08) is a REAL 24-bit unsigned result — unlike VBUS/
 * VSHUNT/CURRENT it is NOT left-justified with 4 reserved low bits. Using
 * rd24() (which always shifts right by 4) on POWER silently divides the
 * true value by 16. This is the "POWER ~16x too small" bug: fixed by a
 * separate, unshifted 24-bit read path.
 */
static osbams_status_t rd24_power(int32_t *out)
{
    uint8_t b[3];
    osbams_status_t st = I2C1_ReadReg(INA228_I2C_ADDR, INA228_REG_POWER, b, 3);
    if (st != OSBAMS_STATUS_OK) return st;

    /* Full 24-bit unsigned value, no shift, no sign extension (POWER is
     * always positive per datasheet). */
    *out = (int32_t)(((uint32_t)b[0] << 16) | ((uint32_t)b[1] << 8) | b[2]);
    return OSBAMS_STATUS_OK;
}

/* ── Public API ─────────────────────────────────────────────────────────── */

uint16_t INA228_CalcShuntCal(uint32_t shunt_micro_ohm, uint32_t i_max_milliamp)
{
    if (shunt_micro_ohm == 0 || i_max_milliamp == 0) return 0U;

    /* CURRENT_LSB = I_max / 2^19. Work in nanoamps for integer precision:
     *   CURRENT_LSB_nA = (i_max_mA × 1e6) / 524288  */
    uint64_t lsb_nA = ((uint64_t)i_max_milliamp * 1000000ULL) / 524288ULL;
    if (lsb_nA == 0) lsb_nA = 1;

    /* SHUNT_CAL = (131072 × lsb_nA × shunt_µΩ) / 1e10 -- see file header. */
    uint64_t cal = (131072ULL * lsb_nA * (uint64_t)shunt_micro_ohm)
                   / SHUNT_CAL_DIVISOR;
    if (cal > 0x7FFFU) cal = 0x7FFFU;
    return (uint16_t)cal;
}

osbams_status_t INA228_Probe(void)
{
    uint16_t mfr = 0, dev = 0;
    osbams_status_t st = rd16(INA228_REG_MFR_ID, &mfr);
    if (st != OSBAMS_STATUS_OK) return st;
    st = rd16(INA228_REG_DEV_ID, &dev);
    if (st != OSBAMS_STATUS_OK) return st;

    if (mfr != INA228_MFR_ID_TI) return OSBAMS_STATUS_WRONG_DEVICE;
    if ((dev & INA228_DEV_ID_MASK) != INA228_DEV_ID_228)
        return OSBAMS_STATUS_WRONG_DEVICE;
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_Init(uint32_t shunt_micro_ohm, uint32_t i_max_milliamp)
{
    s_ready = 0;

    if (shunt_micro_ohm == 0 || i_max_milliamp == 0)
        return OSBAMS_STATUS_INVALID_ARGUMENT;

    /* Confirm the right part is on the bus before configuring it. */
    osbams_status_t st = INA228_Probe();
    if (st != OSBAMS_STATUS_OK) return st;

    /* Software reset (CONFIG bit 15), then allow the device to restart. */
    st = wr16(INA228_REG_CONFIG, 0x8000U);
    if (st != OSBAMS_STATUS_OK) return st;
    for (volatile uint32_t d = 0; d < 20000U; d++) { /* brief settle */ }

    uint64_t lsb_nA = ((uint64_t)i_max_milliamp * 1000000ULL) / 524288ULL;
    if (lsb_nA == 0) lsb_nA = 1;
    s_current_lsb_nA = (uint32_t)lsb_nA;

    uint16_t cal = INA228_CalcShuntCal(shunt_micro_ohm, i_max_milliamp);
    st = wr16(INA228_REG_SHUNT_CAL, cal);
    if (st != OSBAMS_STATUS_OK) return st;

    /* ADC_CONFIG: continuous bus+shunt+temp (MODE=0xF), 1052 µs conversions,
     * 16-sample averaging. VBUSCT/VSHCT/VTCT = 0x5, AVG = 0x2.
     * Layout: [15:12]=MODE [11:9]=VBUSCT [8:6]=VSHCT [5:3]=VTCT [2:0]=AVG.
     * NOTE: unchanged per build-order review -- bench-test noise with the
     * real RSA-20-50 before considering faster/less-averaged settings. */
    uint16_t adc_cfg = (0xFU << 12) | (0x5U << 9) | (0x5U << 6)
                     | (0x5U << 3) | (0x2U << 0);
    st = wr16(INA228_REG_ADC_CONFIG, adc_cfg);
    if (st != OSBAMS_STATUS_OK) return st;

    s_ready = 1;
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_ReadBus_mV(int32_t *out_mv)
{
    if (!out_mv)  return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;

    int32_t code;
    osbams_status_t st = rd24(INA228_REG_VBUS, &code, 0);  /* VBUS is positive */
    if (st != OSBAMS_STATUS_OK) return st;

    *out_mv = (int32_t)(((int64_t)code * VBUS_NUM) / VBUS_DEN);
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_ReadShunt_uV(int32_t *out_uv)
{
    if (!out_uv)  return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;

    int32_t code;
    osbams_status_t st = rd24(INA228_REG_VSHUNT, &code, 1);  /* signed */
    if (st != OSBAMS_STATUS_OK) return st;

    *out_uv = (int32_t)(((int64_t)code * VSHUNT_NUM) / VSHUNT_DEN);
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_ReadCurrent_mA(int32_t *out_ma, uint8_t *out_is_fresh)
{
    if (!out_ma)  return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;

    /* Freshness: DIAG_ALRT.CNVRF latches high when a conversion completes
     * and clears on read of DIAG_ALRT. Read it BEFORE the CURRENT register
     * so we know whether the sample we're about to read is new. This is
     * what makes "N consecutive fresh readings" debounce logic in the
     * fault manager actually mean N real samples, not N polls. */
    if (out_is_fresh) {
        uint16_t diag = 0;
        osbams_status_t dst = rd16(INA228_REG_DIAG_ALRT, &diag);
        if (dst != OSBAMS_STATUS_OK) return dst;
        *out_is_fresh = (diag & INA228_DIAG_ALRT_CNVRF) ? 1U : 0U;
    }

    int32_t code;
    osbams_status_t st = rd24(INA228_REG_CURRENT, &code, 1);  /* signed */
    if (st != OSBAMS_STATUS_OK) return st;

    /* mA = code × CURRENT_LSB_nA / 1e6 */
    *out_ma = (int32_t)(((int64_t)code * s_current_lsb_nA) / 1000000LL);
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_ReadPower_mW(int32_t *out_mw)
{
    if (!out_mw)  return OSBAMS_STATUS_INVALID_ARGUMENT;
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;

    int32_t code;
    osbams_status_t st = rd24_power(&code);   /* unshifted 24-bit read — see rd24_power() */
    if (st != OSBAMS_STATUS_OK) return st;

    /* Power LSB = 3.2 × CURRENT_LSB (datasheet). In nanowatts:
     *   P_nW = code × 3.2 × CURRENT_LSB_nA
     * mW = P_nW / 1e6 = code × 32 × CURRENT_LSB_nA / 1e7 */
    *out_mw = (int32_t)(((int64_t)code * 32 * s_current_lsb_nA) / 10000000LL);
    return OSBAMS_STATUS_OK;
}


/* ── CHARGE / ENERGY accumulators ───────────────────────────────────────────
 * Datasheet SLYS021A eq. 6/7. Integer math only:
 *   uAh  = lsb_nA x code / 3.6e6                      (Charge[C] = lsb x code; 1 Ah = 3600 C)
 *   uWh  = 51.2 x lsb_nA x code / 3.6e6 = lsb_nA x code x 4 / 281250   (Energy[J] = 16 x 3.2 x lsb x code)
 * Rounded to nearest (half away from zero). Products are checked against int64 range first. */
#define ACCUM_UAH_DEN   3600000ULL
#define ACCUM_UWH_NUM   4ULL
#define ACCUM_UWH_DEN   281250ULL

static uint8_t  s_energy_seen   = 0;
static uint64_t s_energy_last   = 0;
static uint8_t  s_decrease_flag = 0;

uint32_t INA228_CurrentLsbNa(uint32_t i_max_milliamp)
{
    uint64_t lsb_nA = ((uint64_t)i_max_milliamp * 1000000ULL) / 524288ULL;   /* same expression as INA228_Init() */
    return (uint32_t)(lsb_nA == 0 ? 1 : lsb_nA);
}

int64_t INA228_DecodeCharge40(const uint8_t b[5])
{
    uint64_t raw = ((uint64_t)b[0] << 32) | ((uint64_t)b[1] << 24) | ((uint64_t)b[2] << 16) | ((uint64_t)b[3] << 8) | b[4];
    if (raw & (1ULL << 39)) raw |= 0xFFFFFF0000000000ULL;     /* sign-extend 40 -> 64 */
    return (int64_t)raw;
}

uint64_t INA228_DecodeEnergy40(const uint8_t b[5])
{
    return ((uint64_t)b[0] << 32) | ((uint64_t)b[1] << 24) | ((uint64_t)b[2] << 16) | ((uint64_t)b[3] << 8) | b[4];
}

bool INA228_ChargeToUah(int64_t code, uint32_t lsb_nA, int64_t *out_uah)
{
    if (!out_uah || lsb_nA == 0) return false;
    uint64_t mag = (code < 0) ? (uint64_t)(-(code + 1)) + 1ULL : (uint64_t)code;
    if (mag > (uint64_t)INT64_MAX / lsb_nA) return false;
    uint64_t q = (mag * lsb_nA + ACCUM_UAH_DEN / 2ULL) / ACCUM_UAH_DEN;
    *out_uah = (code < 0) ? -(int64_t)q : (int64_t)q;
    return true;
}

bool INA228_EnergyToUwh(uint64_t code, uint32_t lsb_nA, int64_t *out_uwh)
{
    if (!out_uwh || lsb_nA == 0) return false;
    if (code > (uint64_t)INT64_MAX / (lsb_nA * ACCUM_UWH_NUM)) return false;
    *out_uwh = (int64_t)((code * lsb_nA * ACCUM_UWH_NUM + ACCUM_UWH_DEN / 2ULL) / ACCUM_UWH_DEN);
    return true;
}

bool INA228_ResetVerified(uint64_t energy_before, uint64_t energy_after)
{
    return energy_before == 0ULL || energy_after < energy_before;
}

osbams_status_t INA228_ReadAccumulators(ina228_accum_snapshot_t *out)
{
    if (!out) return OSBAMS_STATUS_INVALID_ARGUMENT;
    out->valid = false; out->q_uah = 0; out->e_uwh = 0; out->flags = s_decrease_flag;
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;

    uint8_t qb[5], eb[5];
    osbams_status_t st = I2C1_ReadReg(INA228_I2C_ADDR, INA228_REG_CHARGE, qb, 5);
    if (st != OSBAMS_STATUS_OK) return st;
    st = I2C1_ReadReg(INA228_I2C_ADDR, INA228_REG_ENERGY, eb, 5);
    if (st != OSBAMS_STATUS_OK) return st;

    uint64_t ecode = INA228_DecodeEnergy40(eb);
    if (s_energy_seen && ecode < s_energy_last) s_decrease_flag = INA228_ACCUM_F_DECREASE;   /* latched, never unwrapped */
    s_energy_seen = 1; s_energy_last = ecode;

    if (!INA228_ChargeToUah(INA228_DecodeCharge40(qb), s_current_lsb_nA, &out->q_uah)) return OSBAMS_STATUS_SENSOR_FAILURE;
    if (!INA228_EnergyToUwh(ecode, s_current_lsb_nA, &out->e_uwh)) return OSBAMS_STATUS_SENSOR_FAILURE;
    out->flags = s_decrease_flag;
    out->valid = true;
    return OSBAMS_STATUS_OK;
}

osbams_status_t INA228_ResetAccumulators(void)
{
    if (!s_ready) return OSBAMS_STATUS_NOT_READY;
    uint16_t cfg;
    osbams_status_t st = rd16(INA228_REG_CONFIG, &cfg);
    if (st != OSBAMS_STATUS_OK) return st;
    uint8_t eb[5];
    uint64_t before = 0;
    if (I2C1_ReadReg(INA228_I2C_ADDR, INA228_REG_ENERGY, eb, 5) == OSBAMS_STATUS_OK) before = INA228_DecodeEnergy40(eb);

    st = wr16(INA228_REG_CONFIG, (uint16_t)((cfg | INA228_CONFIG_RSTACC) & ~0x8000U));   /* never set the system-reset bit */
    if (st != OSBAMS_STATUS_OK) return st;
    st = wr16(INA228_REG_CONFIG, (uint16_t)(cfg & ~(INA228_CONFIG_RSTACC | 0x8000U)));  /* RSTACC does not self-clear */
    if (st != OSBAMS_STATUS_OK) return st;

    st = I2C1_ReadReg(INA228_I2C_ADDR, INA228_REG_ENERGY, eb, 5);
    if (st != OSBAMS_STATUS_OK) return st;
    uint64_t after = INA228_DecodeEnergy40(eb);
    if (!INA228_ResetVerified(before, after)) return OSBAMS_STATUS_SENSOR_FAILURE;   /* device did not clear */

    s_energy_seen = 0; s_energy_last = 0; s_decrease_flag = 0;
    return OSBAMS_STATUS_OK;
}
