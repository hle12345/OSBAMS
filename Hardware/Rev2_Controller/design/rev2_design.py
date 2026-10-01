"""OSBAMS Rev.2 controller — single source of truth for the schematic, PCB and BOM (RC1).

Components are defined once here (reference, symbol, footprint, value, MPN, evidence, pin->net) and the schematic,
PCB, BOM and checks are all generated from it. Pin keys are pin numbers or (for ICs) pin names.

Evidence states:  VERIFIED_LOCAL | USER_RELAYED_MANUFACTURER | UNVERIFIED
"""
from collections import OrderedDict

PROJECT = "OSBAMS_Rev2_RC1"
VL, UR, UV = "VERIFIED_LOCAL", "USER_RELAYED_MANUFACTURER", "UNVERIFIED"

SHEETS = OrderedDict([
    ("01_Power_Input", "Power input and protection"),
    ("02_Buck_3V3", "12 V -> 3.3 V buck, filtered 3V3_A"),
    ("03_MCU", "STM32L476RGT6, reset/boot/SWD"),
    ("04_Host_Isolated", "USART2 -> ISO7721 -> CP2102N -> USB-C"),
    ("05_INA228_Shunt", "INA228 + shunt Kelvin interface"),
    ("06_ADC_PackSense", "Independent ADC channel and pack-sense connector"),
    ("07_Coil_Driver", "E-stop / ARM / K1 coil chain and MOSFET driver"),
    ("08_Status_Sense", "E-stop, ARM and relay-feedback sensing"),
    ("09_Temp_Probe", "Remote TC74 probe interface (I2C2)"),
    ("10_TestPoints_Mech", "Test points, mounting, fiducials"),
])

# ----------------------------------------------------------------------------- part families
# key -> dict(lib, fp, mfr, mpn, desc, evid, life, alt, src)
P = {}


def part(key, **kw):
    P[key] = kw


def _r(val, mpn_val, pkg="0603", note=""):
    fp = {"0603": "Resistor_SMD:R_0603_1608Metric", "1206": "Resistor_SMD:R_1206_3216Metric", "0805": "Resistor_SMD:R_0805_2012Metric"}[pkg]
    part(f"R{pkg}_{val}", lib="Device:R", fp=fp, mfr="Vishay Dale", mpn=f"CRCW{pkg}{mpn_val}FKEA", desc=f"{val} 1 % thick film {pkg}" + note,
         evid=UV, life="UNKNOWN (not checked)", alt="Yageo RC%s-FR-07 series" % pkg, src="PCBWay source")


for v, m in (("10", "10R0"), ("100", "100R"), ("220", "220R"), ("1k", "1K00"), ("2.2k", "2K20"), ("3.3k", "3K30"), ("4.7k", "4K70"),
             ("5.1k", "5K10"), ("5.6k", "5K60"), ("6.2k", "6K20"), ("10k", "10K0"), ("19.1k", "19K1"), ("33.2k", "33K2"), ("47k", "47K0"), ("47.5k", "47K5"), ("100k", "100K"), ("270k", "270K"), ("1M", "1M00")):
    _r(v, m)
_r("4.7k", "4K70", "1206", " (pulse-rated relay-feedback chain)")
for v, m in (("47", "47R0"), ("10", "10R0")):
    part(f"R1206_{v}p", lib="Device:R", fp="Resistor_SMD:R_1206_3216Metric", mfr="Panasonic", mpn=f"ERJ-P08F{m}V", desc=f"{v} ohm 1 % 1206 anti-surge (pulse-withstanding) thick film: pack-sense surge limiting",
         evid=UV, life="UNKNOWN (not checked)", alt="Vishay CRCW1206 pulse-rated series / Bourns CR1206-FX-pulse series (pulse rating to be confirmed)", src="PCBWay source (orderable suffix to be confirmed)")
for v, m in (("75k", "75K0"), ("10k", "10K0")):
    part(f"RTF_{v}", lib="Device:R", fp="Resistor_SMD:R_0805_2012Metric", mfr="Vishay Dale", mpn=f"TNPW0805{m}BEEA", desc=f"{v} 0.1 % 25 ppm thin film 0805 (ADC divider)",
         evid=UR, life="UNKNOWN (not checked)", alt="Susumu RG2012P-series 0.1 %/25 ppm", src="PCBWay source")
part("R0603_0", lib="Device:R", fp="Resistor_SMD:R_0603_1608Metric", mfr="Vishay Dale", mpn="CRCW06030000Z0EA", desc="0 ohm link", evid=UV, life="UNKNOWN (not checked)", alt="Yageo RC0603JR-070RL", src="PCBWay source")


def _c(key, val, mpn, fp, desc, mfr="Murata", evid=UV, alt="", src="PCBWay source", lib="Device:C"):
    part(key, lib=lib, fp=fp, mfr=mfr, mpn=mpn, desc=desc, evid=evid, life="UNKNOWN (not checked)", alt=alt, src=src)


_c("C100n", "100nF", "GRM188R71H104KA93D", "Capacitor_SMD:C_0603_1608Metric", "100 nF 50 V X7R 0603", alt="Samsung CL10B104KB8NNNC")
_c("C10n", "10nF", "GRM188R71H103KA01D", "Capacitor_SMD:C_0603_1608Metric", "10 nF 50 V X7R 0603", alt="Samsung CL10B103KB8NNNC")
_c("C1u", "1uF", "GRM21BR71C105KA01L", "Capacitor_SMD:C_0805_2012Metric", "1 uF 16 V X7R 0805", alt="Samsung CL21B105KOFNNNE")
_c("C4u7", "4.7uF", "GRM21BR61A475KA73L", "Capacitor_SMD:C_0805_2012Metric", "4.7 uF 10 V X5R 0805", alt="Samsung CL21A475KPFNNNE")
_c("C22u", "22uF", "GRM21BR61A226ME44L", "Capacitor_SMD:C_0805_2012Metric", "22 uF 10 V X5R 0805 (derates ~50 % at 3.3 V)", alt="Samsung CL21A226MPQNNNE")
_c("C10u50", "10uF", "GRM32ER71H106KA12L", "Capacitor_SMD:C_1210_3225Metric", "10 uF 50 V X7R 1210 (12 V rail / buck input)", alt="TDK C3225X7R1H106K250AC")
_c("C4n7", "4.7nF", "GRM21BR72A472KA01L", "Capacitor_SMD:C_0805_2012Metric", "4.7 nF 100 V X7R 0805 (USB shield)", alt="TDK C2012X7R2A472K125AA")
part("C100n_owned", lib="Device:C", fp="Capacitor_SMD:C_0805_2012Metric", mfr="Vishay", mpn="VJ0805Y104JXXAT", desc="100 nF 25 V X7R 5 % 0805 (owned)", evid=UR,
     life="UNKNOWN (not checked)", alt="Murata GRM21BR71E104KA01L", src="CONSIGN (owned: 2) or PCBWay equivalent")
part("L10u", lib="Device:L", fp="Inductor_SMD:L_Bourns_SRN6045TA", mfr="Bourns", mpn="SRN6045TA-100M", desc="10 uH shielded inductor 6x6 mm (10 uH +/-20 %, DCR 52 mohm, Irms 3.2 A, Isat 4.6 A: Bourns datasheet read locally)",
     evid=VL, life="UNKNOWN (not checked)", alt="Wurth 744043100", src="PCBWay source")
part("FB600", lib="Device:FerriteBead", fp="Inductor_SMD:L_0603_1608Metric", mfr="Murata", mpn="BLM18PG601SN1D", desc="Ferrite bead 600 ohm @ 100 MHz 0603",
     evid=UV, life="UNKNOWN (not checked)", alt="TDK MMZ1608B601CTAH0", src="PCBWay source")
part("F1A", lib="Device:Fuse", fp="Fuse:Fuse_1206_3216Metric", mfr="Littelfuse", mpn="0453001.MR", desc="1 A fast fuse 1206 32 V",
     evid=UV, life="UNKNOWN (not checked)", alt="Littelfuse 0466001.NR", src="PCBWay source")
part("D_SS14", lib="Device:D_Schottky", fp="Diode_SMD:D_SMA", mfr="Vishay", mpn="SS14-E3/61T", desc="1 A 40 V Schottky SMA (series reverse-polarity)",
     evid=UV, life="UNKNOWN (not checked)", alt="Diodes Inc SS14-13-F", src="PCBWay source")
part("D_S1M", lib="Device:D", fp="Diode_SMD:D_SMA", mfr="Diodes Inc.", mpn="S1M-13-F", desc="1 A 1000 V rectifier SMA (relay-coil flyback)",
     evid=UV, life="UNKNOWN (not checked)", alt="onsemi/owned 1N5408G (THT)", src="PCBWay source")
part("TVS15", lib="Device:D_Zener", fp="Diode_SMD:D_SMB", mfr="Littelfuse", mpn="SMBJ15A", desc="Unidirectional TVS 15 V standoff 600 W (K = pin 1)",
     evid=UR, life="UNKNOWN (not checked)", alt="Bourns SMBJ15A-Q", src="CONSIGN or PCBWay source")
part("TVS48", lib="Device:D_Zener", fp="Diode_SMD:D_SMB", mfr="Bourns", mpn="1.5SMBJ48A", desc="Unidirectional TVS 48 V standoff 1500 W (K = pin 1)",
     evid=UR, life="UNKNOWN (not checked)", alt="Littelfuse 1.5SMC / SMBJ48A", src="CONSIGN (owned: 2; 3 needed) or PCBWay source")
part("D1N4148", lib="Device:D", fp="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal", mfr="onsemi", mpn="1N4148", desc="Small-signal diode DO-35 (LED reverse clamp)",
     evid=UV, life="UNKNOWN (not checked)", alt="Vishay 1N4148", src="CONSIGN (owned: 2) or PCBWay source")
part("BAT54S", lib="Diode:BAT54S", fp="Package_TO_SOT_SMD:SOT-23", mfr="Nexperia", mpn="BAT54S,215", desc="Dual series Schottky SOT-23 (clamp)",
     evid=UV, life="UNKNOWN (not checked)", alt="onsemi BAT54SLT1G", src="PCBWay source")
part("LED_G", lib="Device:LED", fp="LED_SMD:LED_0805_2012Metric", mfr="Wurth Elektronik", mpn="150080GS75000", desc="LED green 0805",
     evid=UV, life="UNKNOWN (not checked)", alt="Kingbright APT2012SGC", src="PCBWay source")
part("LED_A", lib="Device:LED", fp="LED_SMD:LED_0805_2012Metric", mfr="Wurth Elektronik", mpn="150080AS75000", desc="LED amber 0805",
     evid=UV, life="UNKNOWN (not checked)", alt="Kingbright APT2012SYC", src="PCBWay source")
part("Q_RELAY", lib="Transistor_FET:IRLML0030", fp="Package_TO_SOT_SMD:SOT-23", mfr="Infineon", mpn="IRLML0060TRPBF", desc="N-MOSFET 60 V SOT-23 logic-level (relay low side). RDS(on) not specified at 3.3 V: gate-drive check required",
     evid=UR, life="UNKNOWN (not checked)", alt="Diodes DMN6140L-7 / AOS AO3400A (30 V)", src="PCBWay source")
part("SW_RST", lib="Switch:SW_Push", fp="Button_Switch_SMD:SW_SPST_PTS810", mfr="C&K", mpn="PTS810SJM250SMTRLFS", desc="Tactile switch (reset)",
     evid=UV, life="UNKNOWN (not checked)", alt="Wurth 434121025816", src="PCBWay source")
part("HDR2", lib="Connector_Generic:Conn_01x02", fp="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", mfr="Samtec", mpn="TSW-102-07-G-S", desc="2-pin header + jumper (BOOT0)",
     evid=UV, life="UNKNOWN (not checked)", alt="Wurth 61300211121", src="PCBWay source")
part("TP", lib="Connector:TestPoint", fp="TestPoint:TestPoint_Pad_D1.5mm", mfr="-", mpn="(PCB feature)", desc="Test point pad 1.5 mm", evid=UV, life="n/a", alt="", src="PCB feature")
part("MH", lib="Mechanical:MountingHole", fp="MountingHole:MountingHole_3.2mm_M3", mfr="-", mpn="(PCB feature)", desc="M3 mounting hole (NPTH)", evid=UV, life="n/a", alt="", src="PCB feature")
part("FID", lib="Mechanical:Fiducial", fp="Fiducial:Fiducial_1mm_Mask2mm", mfr="-", mpn="(PCB feature)", desc="Fiducial 1 mm", evid=UV, life="n/a", alt="", src="PCB feature")
part("U_MCU", lib="MCU_ST_STM32L4:STM32L476RGTx", fp="Package_QFP:LQFP-64_10x10mm_P0.5mm", mfr="STMicroelectronics", mpn="STM32L476RGT6", desc="STM32L476RG MCU LQFP-64",
     evid=UR, life="UNKNOWN (not checked)", alt="STM32L476RGT6TR (reel)", src="PCBWay source")
part("U_INA", lib="OSBAMS_Rev2:INA228", fp="Package_SO:MSOP-10_3x3mm_P0.5mm", mfr="Texas Instruments", mpn="INA228AIDGSR", desc="INA228 85 V 20-bit I2C power monitor VSSOP-10 (PIN MAP UNVERIFIED)",
     evid=UR, life="ACTIVE (user-confirmed)", alt="INA228AIDGST (small reel)", src="PCBWay source")
part("U_BUCK", lib="OSBAMS_Rev2:LMR14006Y", fp="Package_TO_SOT_SMD:SOT-23-6", mfr="Texas Instruments", mpn="LMR14006YDDCR", desc="LMR14006Y 4-40 V 0.6 A 2.1 MHz buck SOT-23-6 (PIN MAP UNVERIFIED)",
     evid=UR, life="ACTIVE (user-confirmed)", alt="LMR14006XDDCR (700 kHz variant: inductor change)", src="PCBWay source")
part("U_ISO", lib="OSBAMS_Rev2:ISO7721", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", mfr="Texas Instruments", mpn="ISO7721DR", desc="ISO7721 dual-channel digital isolator 1 fwd / 1 rev SOIC-8 (no isolated power)",
     evid=VL, life="UNKNOWN (not checked)", alt="ISO7721DWR (wide body)", src="PCBWay source")
part("U_CP", lib="Interface_USB:CP2102N-Axx-xQFN20", fp="Package_DFN_QFN:SiliconLabs_QFN-20-1EP_3x3mm_P0.5mm_EP1.8x1.8mm", mfr="Silicon Labs", mpn="CP2102N-A02-GQFN20", desc="CP2102N USB-UART bridge QFN-20 3x3",
     evid=VL, life="UNKNOWN (not checked)", alt="CP2102N-A02-GQFN24 (needs QFN24 footprint)", src="PCBWay source")
part("U_ESD", lib="Power_Protection:USBLC6-2SC6", fp="Package_TO_SOT_SMD:SOT-23-6", mfr="STMicroelectronics", mpn="USBLC6-2SC6", desc="2-line ESD protection SOT-23-6",
     evid=UV, life="UNKNOWN (not checked)", alt="Nexperia IP4220CZ6", src="PCBWay source")
part("OPTO", lib="Isolator:PC817", fp="Package_DIP:DIP-4_W7.62mm", mfr="Vishay", mpn="VO610A-1", desc="Optocoupler transistor output DIP-4, CTR bin -1 (13 % min @ 1 mA, 40 % min @ 10 mA: user-relayed)",
     evid=UR, life="UNKNOWN (not checked)", alt="Vishay VO610A-2 (63-125 % bin, resistor re-check)", src="CONSIGN (owned: 2) + spares")
part("J_EB21", lib="Connector_Generic:Conn_01x02", fp="OSBAMS_Rev2:EB21A-02-C", mfr="Adam Tech", mpn="EB21A-02-C", desc="2-pos 5.00 mm right-angle screw terminal, 8 A / 300 V (footprint from Adam Tech drawing EB21A-XX-C rev B)",
     evid=UR, life="UNKNOWN (not checked)", alt="Phoenix MKDS 1/2-5,08 (different footprint)", src="CONSIGN (owned: 5) or PCBWay source")
part("J_KK3", lib="Connector_Generic:Conn_01x03", fp="Connector_Molex:Molex_KK-254_AE-6410-03A_1x03_P2.54mm_Vertical", mfr="Molex", mpn="22-27-2031", desc="KK 254 3-pos vertical header (mate 22-01-3037 + 08-50-0114)",
     evid=UV, life="UNKNOWN (not checked)", alt="Molex 22-23-2031", src="PCBWay source")
part("J_KK4", lib="Connector_Generic:Conn_01x04", fp="Connector_Molex:Molex_KK-254_AE-6410-04A_1x04_P2.54mm_Vertical", mfr="Molex", mpn="22-27-2041", desc="KK 254 4-pos vertical header (mate 22-01-3047 + 08-50-0114)",
     evid=UV, life="UNKNOWN (not checked)", alt="Molex 22-23-2041", src="PCBWay source")
part("J_PH4", lib="Connector_Generic:Conn_01x04", fp="Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical", mfr="JST", mpn="B4B-PH-K-S", desc="PH 2.0 mm 4-pos vertical header (mate PHR-4 + SPH-002T-P0.5S)",
     evid=UV, life="UNKNOWN (not checked)", alt="JST B4B-PH-K-S(LF)(SN)", src="PCBWay source")
part("J_USBC", lib="Connector:USB_C_Receptacle_USB2.0_16P", fp="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal", mfr="GCT", mpn="USB4105-GF-A", desc="USB-C 2.0 receptacle 16-pin",
     evid=UV, life="UNKNOWN (not checked)", alt="Korean Hroparts TYPE-C-31-M-12", src="PCBWay source")
part("J_SWD", lib="Connector:Conn_ARM_JTAG_SWD_10", fp="Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical_SMD", mfr="Samtec", mpn="FTSH-105-01-L-DV-K", desc="Cortex-debug 2x5 1.27 mm shrouded keyed header",
     evid=UV, life="UNKNOWN (not checked)", alt="Harwin M50-3600542", src="PCBWay source")

# ----------------------------------------------------------------------------- components
COMPS = OrderedDict()   # ref -> dict


def add(ref, key, sheet, nets, value=None, dnp=False, note="", pos=None):
    d = dict(P[key]); d.update(ref=ref, key=key, sheet=sheet, nets=dict(nets), dnp=dnp, note=note)
    d["value"] = value or d.get("mpn")
    COMPS[ref] = d
    return d


S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 = list(SHEETS)

# ---- 01 power input
add("J1", "J_EB21", S1, {1: "12V_RAW", 2: "GND"}, "12V_IN", note="Pin 1 +12 V, pin 2 GND. XDR-75-12 set to 12.0 V")
add("F1", "F1A", S1, {1: "12V_RAW", 2: "12V_F"}, "1A fast")
add("D2", "D_SS14", S1, {"K": "+12V", "A": "12V_F"}, "SS14")
add("D1", "TVS15", S1, {"K": "+12V", "A": "GND"}, "SMBJ15A")
add("C1", "C10u50", S1, {1: "+12V", 2: "GND"}, "10uF 50V")

# ---- 02 buck
add("U3", "U_BUCK", S2, {"CB": "BUCK_CB", "GND": "GND", "FB": "BUCK_FB", "EN": "BUCK_EN", "VIN": "+12V", "SW": "BUCK_SW"}, "LMR14006Y")
add("C2", "C10u50", S2, {1: "+12V", 2: "GND"}, "10uF 50V")
add("C3", "C100n", S2, {1: "+12V", 2: "GND"}, "100nF")
add("C4", "C100n", S2, {1: "BUCK_CB", 2: "BUCK_SW"}, "100nF (bootstrap)")
add("L1", "L10u", S2, {1: "BUCK_SW", 2: "+3V3"}, "10uH")
add("R1", "R0603_33.2k", S2, {1: "+3V3", 2: "BUCK_FB"}, "33.2k")
add("R2", "R0603_10k", S2, {1: "BUCK_FB", 2: "GND"}, "10k")
add("R3", "R0603_100k", S2, {1: "+12V", 2: "BUCK_EN"}, "100k")
add("C5", "C22u", S2, {1: "+3V3", 2: "GND"}, "22uF")
add("C6", "C22u", S2, {1: "+3V3", 2: "GND"}, "22uF")
add("FB1", "FB600", S2, {1: "+3V3", 2: "3V3_A"}, "600R@100MHz")
add("C7", "C4u7", S2, {1: "3V3_A", 2: "GND"}, "4.7uF")
add("C8", "C100n", S2, {1: "3V3_A", 2: "GND"}, "100nF")
add("R4", "R0603_3.3k", S2, {1: "3V3_A", 2: "GND"}, "3.3k", note="Permanent bleeder: keeps 3V3A < 1 V if PACK+ back-feeds through PA1 with the board unpowered")
add("R5", "R0603_1k", S2, {1: "+3V3", 2: "LED_3V3"}, "1k")
add("D3", "LED_G", S2, {"A": "LED_3V3", "K": "GND"}, "3V3 ON")

# ---- 03 MCU
mcu = {"VBAT": "+3V3", "VDD": "+3V3", "VDDUSB": "+3V3", "VDDA": "3V3_A", "VSSA": "GND", "VSS": "GND", "NRST": "NRST", "BOOT0": "BOOT0",
       "PA0": "ESTOP_SENSE", "PA1": "ADC_SENSE", "PA2": "UART_TX_MCU", "PA3": "UART_RX_MCU", "PA5": "LED_HB_PIN", "PB0": "INA_ALERT",
       "PB8": "SCL1", "PB9": "SDA1", "PB10": "SCL2", "PB11": "SDA2", "PC8": "LOAD_EN", "PC9": "RELAY_FB", "PC10": "ARM_SENSE",
       "PA13": "SWDIO", "PA14": "SWCLK", "PB3": "SWO"}
add("U1", "U_MCU", S3, mcu, "STM32L476RGT6")
for i, (ref, a, b) in enumerate([("C10", "+3V3", "GND"), ("C11", "+3V3", "GND"), ("C12", "+3V3", "GND"), ("C13", "+3V3", "GND"), ("C14", "+3V3", "GND")]):
    add(ref, "C100n", S3, {1: a, 2: b}, "100nF", note=["VDD pin 19", "VDD pin 32", "VDD pin 64", "VDDUSB pin 48", "VBAT pin 1"][i])
add("C15", "C4u7", S3, {1: "+3V3", 2: "GND"}, "4.7uF")
add("C16", "C1u", S3, {1: "3V3_A", 2: "GND"}, "1uF", note="VDDA")
add("C17", "C100n", S3, {1: "3V3_A", 2: "GND"}, "100nF", note="VDDA")
add("C18", "C100n", S3, {1: "NRST", 2: "GND"}, "100nF")
add("SW1", "SW_RST", S3, {1: "NRST", 2: "GND"}, "RESET")
add("R6", "R0603_10k", S3, {1: "BOOT0", 2: "GND"}, "10k")
add("JP1", "HDR2", S3, {1: "+3V3", 2: "BOOT0"}, "BOOT0", note="Jumper fitted = ROM bootloader")
add("R7", "R0603_1k", S3, {1: "LED_HB_PIN", 2: "LED_HB"}, "1k")
add("D4", "LED_G", S3, {"A": "LED_HB", "K": "GND"}, "HEARTBEAT")
add("J9", "J_SWD", S3, {"VTref": "+3V3", "SWDIO/TMS": "SWDIO", "GND": "GND", "SWCLK/TCK": "SWCLK", "SWO/TDO": "SWO", "GNDDetect": "GND", "~{RESET}": "NRST"}, "SWD")

# ---- 04 host (isolated)
add("J8", "J_USBC", S4, {"VBUS": "VBUS_USB", "GND": "GND_HOST", "CC1": "USB_CC1", "CC2": "USB_CC2", "D+": "USB_DP_J", "D-": "USB_DM_J", "SHIELD": "USB_SHIELD"}, "USB-C HOST")
add("R8", "R0603_5.1k", S4, {1: "USB_CC1", 2: "GND_HOST"}, "5.1k")
add("R9", "R0603_5.1k", S4, {1: "USB_CC2", 2: "GND_HOST"}, "5.1k")
add("R10", "R0603_1M", S4, {1: "USB_SHIELD", 2: "GND_HOST"}, "1M")
add("C19", "C4n7", S4, {1: "USB_SHIELD", 2: "GND_HOST"}, "4.7nF 100V")
add("U9", "U_ESD", S4, {1: "USB_DP_J", 6: "USB_DP", 3: "USB_DM_J", 4: "USB_DM", 2: "GND_HOST", 5: "VBUS_USB"}, "USBLC6-2SC6")
add("U6", "U_CP", S4, {"VBUS": "CP_VBUS_SENSE", "VREGIN": "VBUS_USB", "VDD": "3V3_HOST", "9": "CP_RSTB", "D+": "USB_DP", "D-": "USB_DM", "GND": "GND_HOST", "RXD": "UART_RX_HOST", "TXD": "UART_TX_HOST"}, "CP2102N")
add("R38", "R0603_19.1k", S4, {1: "VBUS_USB", 2: "CP_VBUS_SENSE"}, "19.1k", note="CP2102N VBUS sense divider upper resistor: Silicon Labs reference uses 22.1 k; 19.1 k gives positive margin to VIH = VDD-0.6 V at VBUS 4.40 V / VDD 3.6 V / 1 % resistors (see calculations 8)")
add("R39", "R0603_47.5k", S4, {1: "CP_VBUS_SENSE", 2: "GND_HOST"}, "47.5k", note="CP2102N VBUS sense divider lower resistor (Silicon Labs reference value)")
add("R40", "R0603_1k", S4, {1: "CP_RSTB", 2: "3V3_HOST"}, "1k", note="CP2102N RSTb 1 kOhm pull-up to VDD (Silicon Labs datasheet 2.1, read locally)")
add("C20", "C4u7", S4, {1: "VBUS_USB", 2: "GND_HOST"}, "4.7uF")
add("C21", "C100n", S4, {1: "VBUS_USB", 2: "GND_HOST"}, "100nF")
add("C22", "C4u7", S4, {1: "3V3_HOST", 2: "GND_HOST"}, "4.7uF", note="CP2102N VDD: 4.7 uF + 0.1 uF required per power pin (Silicon Labs datasheet, read locally)")
add("C23", "C100n", S4, {1: "3V3_HOST", 2: "GND_HOST"}, "100nF")
add("U7", "U_ISO", S4, {"VCC1": "+3V3", "OUTA": "UART_RX_MCU", "INB": "UART_TX_MCU", "GND1": "GND", "GND2": "GND_HOST", "OUTB": "UART_RX_HOST", "INA": "UART_TX_HOST", "VCC2": "3V3_HOST"}, "ISO7721",
    note="Channel A (INA pin 7, host side) -> OUTA pin 2 (MCU RX); channel B (INB pin 3 <- MCU TX) -> OUTB pin 6 (CP2102N RXD)")
add("C24", "C100n", S4, {1: "+3V3", 2: "GND"}, "100nF", note="ISO7721 VCC1")
add("C25", "C100n", S4, {1: "3V3_HOST", 2: "GND_HOST"}, "100nF", note="ISO7721 VCC2")

# ---- 05 INA228
add("J5", "J_KK3", S5, {1: "SHUNT_INP_CON", 2: "SHUNT_INN_CON", 3: "GND"}, "SHUNT_KELVIN", note="1 IN+, 2 IN-, 3 cable shield (shield joined to GND at this end only)")
add("R42", "R1206_10p", S5, {1: "SHUNT_INP_CON", 2: "SHUNT_INP_RAW"}, "10", note="Surge-limiting series resistor UPSTREAM of the TVS (Rev.1.2): limits TVS current; 10 ohm + existing 10 ohm = 20 ohm per Kelvin line")
add("R43", "R1206_10p", S5, {1: "SHUNT_INN_CON", 2: "SHUNT_INN_RAW"}, "10", note="Surge-limiting series resistor UPSTREAM of the TVS (matched to R42)")
add("D5", "TVS48", S5, {"K": "SHUNT_INP_RAW", "A": "GND"}, "1.5SMBJ48A")
add("D6", "TVS48", S5, {"K": "SHUNT_INN_RAW", "A": "GND"}, "1.5SMBJ48A")
add("R11", "R0603_10", S5, {1: "SHUNT_INP_RAW", 2: "INA_INP"}, "10")
add("R12", "R0603_10", S5, {1: "SHUNT_INN_RAW", 2: "INA_INN"}, "10")
add("C26", "C100n", S5, {1: "INA_INP", 2: "INA_INN"}, "100nF 50V", note="Differential filter fc ~80 kHz")
add("U2", "U_INA", S5, {"IN+": "INA_INP", "IN-": "INA_INN", "VBUS": "INA_VBUS", "VS": "3V3_A", "GND": "GND", "SDA": "SDA1", "SCL": "SCL1", "ALERT": "INA_ALERT", "A0": "GND", "A1": "GND"}, "INA228")
add("C27", "C100n", S5, {1: "3V3_A", 2: "GND"}, "100nF", note="INA228 VS")
add("D7", "TVS48", S5, {"K": "PACK_INA", "A": "GND"}, "1.5SMBJ48A")
add("R13", "R0603_10", S5, {1: "PACK_INA", 2: "INA_VBUS"}, "10")
add("R41", "R1206_47p", S5, {1: "PACK_INA_CON", 2: "PACK_INA"}, "47", note="Surge-limiting series resistor UPSTREAM of D7 (Rev.1.2): VBUS input draws ~50 uA so the DC error is negligible")
add("C28", "C100n", S5, {1: "INA_VBUS", 2: "GND"}, "100nF 50V")
add("R14", "R0603_4.7k", S5, {1: "+3V3", 2: "SDA1"}, "4.7k")
add("R15", "R0603_4.7k", S5, {1: "+3V3", 2: "SCL1"}, "4.7k")
add("R16", "R0603_10k", S5, {1: "+3V3", 2: "INA_ALERT"}, "10k")

# ---- 06 ADC / pack sense
add("J6", "J_KK4", S6, {1: "PACK_INA_CON", 2: "PACK_ADC", 3: "RELAY_OUT", 4: "GND"}, "PACK_SENSE", note="1 PACK_INA (upstream of K1), 2 PACK_ADC (separate lead), 3 RELAY_OUT (K1 load side), 4 GND_SENSE = the single logic-GND / pack-negative bond")
add("R17", "RTF_75k", S6, {1: "PACK_ADC", 2: "ADC_MID"}, "75k 0.1%")
add("R18", "RTF_75k", S6, {1: "ADC_MID", 2: "ADC_TAP"}, "75k 0.1%")
add("R19", "RTF_10k", S6, {1: "ADC_TAP", 2: "GND"}, "10k 0.1%")
add("R20", "R0603_1k", S6, {1: "ADC_TAP", 2: "ADC_SENSE"}, "1k")
add("C29", "C100n", S6, {1: "ADC_SENSE", 2: "GND"}, "100nF")
add("D8", "BAT54S", S6, {1: "GND", 2: "VCLAMP", 3: "ADC_SENSE"}, "BAT54S", note="Lower clamp to GND; upper clamp to the ISOLATED rail VCLAMP (not 3V3)")
add("D14", "BAT54S", S6, {1: "+3V3", 3: "VCLAMP"}, "BAT54S", note="Blocks VCLAMP -> 3V3: PACK+ back-feed through D8 cannot reach the MCU rail")
add("R37", "R0603_10k", S6, {1: "VCLAMP", 2: "GND"}, "10k", note="Bleeds the isolated clamp rail")
add("C34", "C100n", S6, {1: "VCLAMP", 2: "GND"}, "100nF")

# ---- 07 coil driver
add("J2", "J_EB21", S7, {1: "+12V", 2: "ESTOP_OUT"}, "ESTOP", note="Eaton M22-PV-K02 NC contact in series: pin 1 +12 V, pin 2 post-E-stop node")
add("J3", "J_EB21", S7, {1: "ESTOP_OUT", 2: "COIL_V"}, "ARM", note="C&K T102SHZQE ARM switch in series")
add("J4", "J_EB21", S7, {1: "COIL_V", 2: "COIL_SW"}, "K1_COIL", note="Durakool DG57CM-5021-76-1012-R coil (12 V). Pin 1 +12 V side, pin 2 MOSFET drain")
add("Q1", "Q_RELAY", S7, {"G": "GATE", "S": "GND", "D": "COIL_SW"}, "IRLML0060")
add("R21", "R0603_220", S7, {1: "LOAD_EN", 2: "GATE"}, "220")
add("R22", "R0603_10k", S7, {1: "GATE", 2: "GND"}, "10k", note="Default OFF")
add("D9", "D_S1M", S7, {"K": "COIL_V", "A": "COIL_SW"}, "S1M", note="Flyback: cathode on +12 V side")
add("R23", "R0603_2.2k", S7, {1: "COIL_V", 2: "LED_COIL"}, "2.2k")
add("D10", "LED_A", S7, {"A": "LED_COIL", "K": "COIL_SW"}, "COIL ON")

# ---- 08 status sensing
add("R24", "R0603_5.6k", S8, {1: "ESTOP_OUT", 2: "ES_LED_A"}, "5.6k", note="IF >= 1.59 mA at 10.5 V (worst-case VF 1.6 V): 2x saturation margin with CTR_eff = 13 % x 0.8 x 0.8")
add("U4", "OPTO", S8, {1: "ES_LED_A", 2: "GND", 3: "GND", 4: "ESTOP_SENSE"}, "VO610A-1")
add("D11", "D1N4148", S8, {"K": "ES_LED_A", "A": "GND"}, "1N4148", note="Antiparallel across the LED")
add("R25", "R0603_47k", S8, {1: "+3V3", 2: "ESTOP_SENSE"}, "47k")
add("C30", "C10n", S8, {1: "ESTOP_SENSE", 2: "GND"}, "10nF")
add("R26", "R1206_4.7k", S8, {1: "RELAY_OUT", 2: "FB_R1"}, "4.7k")
add("R27", "R1206_4.7k", S8, {1: "FB_R1", 2: "FB_R2"}, "4.7k")
add("R28", "R1206_4.7k", S8, {1: "FB_R2", 2: "FB_LED_A"}, "4.7k")
add("U5", "OPTO", S8, {1: "FB_LED_A", 2: "GND", 3: "GND", 4: "RELAY_FB"}, "VO610A-1")
add("D12", "D1N4148", S8, {"K": "FB_LED_A", "A": "GND"}, "1N4148", note="Antiparallel across the LED")
add("R29", "R0603_47k", S8, {1: "+3V3", 2: "RELAY_FB"}, "47k")
add("C31", "C10n", S8, {1: "RELAY_FB", 2: "GND"}, "10nF")
add("R30", "R0603_270k", S8, {1: "COIL_V", 2: "ARM_DIV"}, "270k")
add("R31", "R0603_100k", S8, {1: "ARM_DIV", 2: "GND"}, "100k")
add("R32", "R0603_1k", S8, {1: "ARM_DIV", 2: "ARM_SENSE"}, "1k")
add("C32", "C100n", S8, {1: "ARM_SENSE", 2: "GND"}, "100nF")
add("D13", "BAT54S", S8, {1: "GND", 2: "+3V3", 3: "ARM_SENSE"}, "BAT54S", note="ARM_SENSE clamp: source impedance 73 k -> back-feed < 60 uA")

# ---- 09 temperature probe interface
add("J7", "J_PH4", S9, {1: "+3V3", 2: "SDA2_J", 3: "SCL2_J", 4: "GND"}, "TEMP_PROBE", note="1 3V3, 2 SDA2, 3 SCL2, 4 GND")
add("C33", "C100n", S9, {1: "+3V3", 2: "GND"}, "100nF", note="At J7")
add("U10", "U_ESD", S9, {1: "SDA2_J", 6: "SDA2_P", 3: "SCL2_J", 4: "SCL2_P", 2: "GND", 5: "+3V3"}, "USBLC6-2SC6", note="2-channel ESD on the probe cable lines")
add("R33", "R0603_100", S9, {1: "SDA2_P", 2: "SDA2"}, "100")
add("R34", "R0603_100", S9, {1: "SCL2_P", 2: "SCL2"}, "100")
add("R35", "R0603_4.7k", S9, {1: "+3V3", 2: "SDA2"}, "4.7k", note="Fitted; 2.2k alternative for long cables")
add("R36", "R0603_4.7k", S9, {1: "+3V3", 2: "SCL2"}, "4.7k", note="Fitted; 2.2k alternative for long cables")

# ---- 10 test points / mechanical
TPS = [("TP1", "+12V"), ("TP2", "+3V3"), ("TP3", "3V3_A"), ("TP4", "GND"), ("TP5", "GND"), ("TP6", "SDA1"), ("TP7", "SCL1"), ("TP8", "SDA2"), ("TP9", "SCL2"),
       ("TP10", "INA_INP"), ("TP11", "INA_INN"), ("TP12", "INA_VBUS"), ("TP13", "ADC_SENSE"), ("TP14", "GATE"), ("TP15", "COIL_SW"), ("TP16", "COIL_V"),
       ("TP17", "ESTOP_SENSE"), ("TP18", "ARM_SENSE"), ("TP19", "RELAY_FB"), ("TP20", "UART_TX_MCU"), ("TP21", "UART_RX_MCU"), ("TP22", "NRST"),
       ("TP23", "SWDIO"), ("TP24", "SWCLK"), ("TP25", "GND_HOST"), ("TP26", "LOAD_EN"), ("TP27", "3V3_HOST")]
TP_LABEL = {"INA_INP": "INA_IN+", "INA_INN": "INA_IN-", "INA_VBUS": "VBUS", "UART_TX_MCU": "UART_TX", "UART_RX_MCU": "UART_RX", "GATE": "GATE", "+3V3": "3V3", "+12V": "+12V"}
for ref, net in TPS:
    add(ref, "TP", S10, {1: net}, TP_LABEL.get(net, net))
for i in range(1, 5):
    add(f"MH{i}", "MH", S10, {}, "M3")
for i in range(1, 4):
    add(f"FID{i}", "FID", S10, {}, "FID")

# nets that need a PWR_FLAG (driven by a connector / filter rather than a power output pin)
PWR_FLAGS = ["+12V", "GND", "+3V3", "3V3_A", "VBUS_USB", "GND_HOST", "3V3_HOST"]
POWER_SYMS = {"GND": "power:GND", "+3V3": "power:+3V3", "+12V": "power:+12V"}

# hand-written custom symbols (library OSBAMS_Rev2); type strings are KiCad pin electrical types
CUSTOM = {
    "INA228": dict(ref="U", value="INA228", fp="Package_SO:MSOP-10_3x3mm_P0.5mm", desc="INA228 (DGS VSSOP-10 pin map compared with the TI table relayed by the user: PASS)",
                   pins=[("1", "A1", "input", "L", 0), ("2", "A0", "input", "L", 1), ("3", "ALERT", "open_collector", "L", 2), ("4", "SDA", "bidirectional", "L", 3),
                         ("5", "SCL", "input", "L", 4), ("6", "VS", "power_in", "R", 0), ("7", "GND", "power_in", "R", 1), ("8", "VBUS", "input", "R", 2),
                         ("9", "IN-", "input", "R", 3), ("10", "IN+", "input", "R", 4)]),
    "LMR14006Y": dict(ref="U", value="LMR14006Y", fp="Package_TO_SOT_SMD:SOT-23-6", desc="LMR14006Y buck, DDC TSOT-6 (pin map compared with the TI table relayed by the user: PASS; pin 4 is /SHDN)",
                      pins=[("1", "CB", "passive", "L", 0), ("2", "GND", "power_in", "L", 1), ("3", "FB", "input", "L", 2), ("4", "EN", "input", "R", 0),
                            ("5", "VIN", "power_in", "R", 1), ("6", "SW", "output", "R", 2)]),
    "ISO7721": dict(ref="U", value="ISO7721", fp="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", desc="ISO7721 1 fwd / 1 rev (pin map per TI 8-pin pinout confirmed by the user: 1 VCC1, 2 OUTA, 3 INB, 4 GND1, 5 GND2, 6 OUTB, 7 INA, 8 VCC2; channel A side 2 to side 1, channel B side 1 to side 2)",
                    pins=[("1", "VCC1", "power_in", "L", 0), ("2", "OUTA", "output", "L", 1), ("3", "INB", "input", "L", 2), ("4", "GND1", "power_in", "L", 3),
                          ("5", "GND2", "power_in", "R", 3), ("6", "OUTB", "output", "R", 2), ("7", "INA", "input", "R", 1), ("8", "VCC2", "power_in", "R", 0)]),
}


def nets_of(c):
    return {str(k): v for k, v in c["nets"].items()}


def all_nets():
    s = {}
    for r, c in COMPS.items():
        for pin, n in c["nets"].items():
            s.setdefault(n, []).append((r, pin))
    return s
