"""Generate the RC1 KiCad project skeleton: schematic sheets, custom symbol library, lib tables, .kicad_pro."""
import os, json, sys
from . import rev2_design as D, schgen, kilib, kisx
from .kisx import Str

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1")

NOTES = {
    "01_Power_Input": ["J1: 12 V control input (XDR-75-12 set and verified at 12.0 V). F1 1 A fast, D2 Schottky reverse-polarity block (0.4 V drop), TVS D1 SMBJ15A across +12V AFTER D2 (reverse polarity is blocked, not clamped).",
                       "Diode polarity: Device:D / D_Schottky / D_Zener pin 1 = cathode (K); KiCad SMA/SMB footprints pad 1 = cathode - verified by tools in checks.py (netlist polarity check)."],
    "02_Buck_3V3": ["LMR14006Y (4-40 V, 600 mA, 2.1 MHz, VREF 0.765 V: user-relayed). Vout = 0.765 x (1 + R1/R2) = 0.765 x (1 + 33.2k/10k) = 3.305 V.",
                    "Hot loop: C2/C3 - U3 VIN/GND - SW - L1 kept tiny in layout. No 5 V rail. 3V3_A = 3V3 through ferrite FB1 + 4.7 uF + 100 nF (VDDA, INA228).",
                    "R4 3.3k: permanent bleeder on 3V3_A; limits the rail to < 1 V if PACK+ back-feeds the MCU pin while the board is unpowered (calculations section 1.1)."],
    "03_MCU": ["STM32L476RGT6 direct. HSI16 -> PLL 80 MHz (no crystal), no LSE, USB unused. PA0 ESTOP_SENSE (LOW = healthy), PC9 RELAY_FB (active low), PC10 ARM_SENSE (HIGH = armed, status only).",
               "PA1 ADC_SENSE (VREFINT-corrected), PA2/PA3 USART2, PB8/PB9 I2C1 (INA228), PB10/PB11 I2C2 (TC74, <= 100 kHz), PB0 INA228 ALERT, PC8 LOAD_EN (default low), PA5 heartbeat, SWD on J9.",
               "Unused pins carry no-connect flags and are configured analog/pulled low in firmware. BOOT0: 10k pull-down + jumper JP1 to 3V3 (ROM bootloader)."],
    "04_Host_Isolated": ["USART2 -> ISO7721 -> CP2102N -> USB-C -> Raspberry Pi 5. ISO7721 has NO isolated power: VCC1 = +3V3 (controller side), VCC2 = 3V3_HOST from the CP2102N regulator (VREGIN from USB VBUS).",
                         "GND (controller) and GND_HOST (USB side) are separate nets: they are never joined. USB shield: 1 M || 4.7 nF to GND_HOST. CC1/CC2 5.1 k pull-downs. All values UNVERIFIED against the CP2102N reference design."],
    "05_INA228_Shunt": ["INA228 reads the external Bourns RSA-20-50 (2.5 mOhm, 20 A / 50 mV) through J5 (Kelvin). ADCRANGE = 0 (+/-163.84 mV); SHUNT_CAL = 1250 at IMAX = 20 A (firmware change pending).",
                        "IN+/IN- filter 2 x 10 ohm + 100 nF; TVS 1.5SMBJ48A (77.4 V clamp vs 85 V abs max) on each pack-level input. VBUS comes from PACK_INA (upstream of K1) on its own lead. A0 = A1 = GND -> address 0x40.",
                        "INA228 pin map is an INA226-family ANALOGY and is UNVERIFIED: verify against the TI datasheet before fabrication."],
    "06_ADC_PackSense": ["PACK_ADC -> 75k -> 75k -> ADC_TAP -> 10k -> GND (16:1; 44 V -> 2.750 V); 1 k + 100 nF; BAT54S clamp: lower diode to GND, upper diode to the isolated rail VCLAMP (fed from 3V3 through D14, bled by R37) -> PACK+ cannot back-power 3V3.",
                         "J6 pin 4 (GND_SENSE) is the single bond between controller GND and pack-negative. Separate PACK_ADC lead from the INA228 VBUS lead."],
    "07_Coil_Driver": ["Coil chain: +12V -> J2 E-stop (Eaton M22-PV-K02 NC) -> J3 ARM (C&K T102SHZQE) -> J4 K1 coil -> Q1 -> GND. E-stop and ARM physically open the coil supply; firmware cannot bypass either.",
                       "Q1 gate: 220 ohm series, 10k pull-down (default OFF). Flyback D9 cathode on the +12 V side. No fast-release TVS in RC1. Battery discharge current never flows through this board."],
    "08_Status_Sense": ["ESTOP_SENSE: ESTOP_OUT -> 5.6k -> VO610A LED; collector pull-up 47k -> PA0 (LOW = healthy; open/broken = HIGH). RELAY_FB: K1 load side -> 3 x 4.7k (1206) -> VO610A LED; pull-up 47k -> PC9 (active low).",
                        "Resistors sized from the user-relayed VO610A-1 CTR guarantee (min 13 % @ 1 mA, 40 % @ 10 mA) with temperature/aging derates and 2x saturation margin; supported 30-44 V pack range checked down to 24 V (calculations section 4).",
                        "ARM_SENSE: 270k/100k divider, 1k, 100 nF, BAT54S clamp - sensing only, never permission to energize."],
    "09_Temp_Probe": ["Remote TC74A5-3.3VAT probe on I2C2 (PB10/PB11), <= 100 kHz, cable <= 1.5 m. Probe has its own 100 nF at the sensor. 4.7k pull-ups fitted (2.2k alternative), 100 ohm series, 2-channel ESD."],
    "10_TestPoints_Mech": ["Test points: +12V, 3V3, 3V3_A, GND x2, SDA1, SCL1, SDA2, SCL2, INA_IN+, INA_IN-, VBUS, ADC_SENSE, GATE, COIL_SW, COIL_V, ESTOP_SENSE, ARM_SENSE, RELAY_FB, UART_TX, UART_RX, NRST, SWDIO, SWCLK (+ LOAD_EN, GND_HOST, 3V3_HOST)."],
}


def write_symlib():
    items = ['kicad_symbol_lib', ['version', 20220914], ['generator', 'osbams_schgen']]
    for name, c in D.CUSTOM.items():
        node = kilib.custom_symbol(f"{name}", c['ref'], c['value'], c['fp'], c['pins'], desc=c['desc'])
        items.append(node)
    open(os.path.join(OUT, "OSBAMS_Rev2.kicad_sym"), "w").write(kisx.dump(items) + "\n")


def write_tables():
    open(os.path.join(OUT, "sym-lib-table"), "w").write('(sym_lib_table\n  (version 7)\n  (lib (name "OSBAMS_Rev2")(type "KiCad")(uri "${KIPRJMOD}/OSBAMS_Rev2.kicad_sym")(options "")(descr "OSBAMS Rev.2 custom symbols (pin maps UNVERIFIED, see evidence register)"))\n)\n')
    open(os.path.join(OUT, "fp-lib-table"), "w").write('(fp_lib_table\n  (version 7)\n  (lib (name "OSBAMS_Rev2")(type "KiCad")(uri "${KIPRJMOD}/OSBAMS_Rev2.pretty")(options "")(descr "OSBAMS Rev.2 custom footprints"))\n)\n')


def write_pro():
    pro = {"meta": {"filename": D.PROJECT + ".kicad_pro", "version": 1}, "board": {"design_settings": {"rules": {"min_clearance": 0.1, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3, "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.19, "min_resolved_spacing": 0.0, "min_silk_clearance": 0.0, "min_text_height": 0.8, "min_text_thickness": 0.08, "solder_mask_to_copper_clearance": 0.0}}}, "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
           "sheets": [], "text_variables": {"REV": "RC1"}}
    # netclasses must match design/pcbgen.py (the .kicad_pro is the only place KiCad stores them)
    pro["net_settings"] = {"meta": {"version": 4}, "classes": [dict(name=n, clearance=c, track_width=w, via_diameter=0.6, via_drill=0.3) for n, c, w in
                           (("Default", 0.15, 0.2), ("POWER", 0.2, 0.3), ("RAIL", 0.15, 0.3), ("PACKLEVEL", 0.15, 0.2), ("KELVIN", 0.15, 0.2))],
                           "netclass_patterns": [dict(netclass=cls, pattern=n) for cls, nets in (
                               ("POWER", ["12V_RAW", "12V_F", "+12V", "COIL_V", "COIL_SW", "ESTOP_OUT", "3V3_HOST", "VBUS_USB", "BUCK_SW"]),
                               ("RAIL", ["+3V3", "3V3_A"]),
                               ("PACKLEVEL", ["PACK_INA", "PACK_ADC", "ADC_MID", "RELAY_OUT", "FB_R1", "FB_R2", "SHUNT_INP_RAW", "SHUNT_INN_RAW", "INA_VBUS"]),
                               ("KELVIN", ["INA_INP", "INA_INN"])) for n in nets]}
    open(os.path.join(OUT, D.PROJECT + ".kicad_pro"), "w").write(json.dumps(pro, indent=2))


def main():
    os.makedirs(OUT, exist_ok=True)
    g = schgen.SchGen(D, OUT, D.PROJECT)
    sheets = g.write_all(NOTES)
    write_symlib(); write_tables(); write_pro()
    if g.errors:
        print("\n".join(g.errors)); sys.exit(1)
    print("sheets:", [(s.name, s.paper) for s in sheets])


if __name__ == "__main__":
    main()
