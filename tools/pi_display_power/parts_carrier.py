"""Single source of truth for OSBAMS_Pi_Power_Carrier_RevB (combined power board + Pi interposer): BOM, schematic, PCB, mechanical checks.
Board frame: origin top-left of the carrier, +x right, +y down (mm). Pi frame (Raspberry Pi 5 drawing RP-008347): origin = Pi top-left corner, header axis y = 3.5,
header centre x = 32.5. board = Pi + (PI_OX, PI_OY): the carrier overhangs the Pi's header edge (outward = Pi y < 0)."""
NAME = "OSBAMS_Pi_Power_Carrier_RevB"
PI_OX, PI_OY = 7.5, 60.0
BOARD_W = 85.0; MAIN_H = 59.5                      # main body x 0..85, y 0..59.5 (Pi y -60 .. -0.5: outside the Pi outline)
TAB = (7.5, 59.5, 72.5, 67.5)                      # plug tab over the header: Pi x 0..65, y -0.5 .. 7.5 (same footprint as the RC2 interposer)
BOARD_H = 67.5
def pi2b(x, y): return (x + PI_OX, y + PI_OY)
X0_HDR = 32.5 - 19 * 2.54 / 2                      # Pi pin-1 column (Pi frame) 8.37
HDR = pi2b(X0_HDR, 3.5)                            # board coords of the pin-1 column / header axis: (15.87, 63.5)
def pin_xy(n):                                     # board coords of Pi header pin n (odd = inner row, even = outer row)
    col = (n + 1) // 2
    return HDR[0] + (col - 1) * 2.54, HDR[1] + (1.27 if n % 2 else -1.27)
PIN_NETS = {2: "5V_PI", 4: "5V_PI", 6: "PI_GND", 9: "PI_GND", 14: "PI_GND", 20: "PI_GND"}
U1_C = (28.0, 26.9)                                # RSDW40F-05 centre, long axis along y, secondary pins (4,5,6) at the bottom end
MECH_HOLES = {"K1": (4.0, 13.0), "K2": (57.5, 37.0), "S3": (81.0, 4.0), "S4": (81.5, 55.3)}   # M3 NPTH: enclosure standoffs = key / support posts
PI_HOLES = {"M1": pi2b(3.5, 3.5), "M2": pi2b(61.5, 3.5)}                                      # M2.5 NPTH to the Pi header-end mounting holes

# ref, value, description, manufacturer, mpn, footprint, mount, note
PARTS = [
 ("U1", "RSDW40F-05", "DC-DC isolated 9-36V in, 5V/8A/40W, 2x1in through-hole", "Mean Well", "RSDW40F-05", "OSBAMS_PiPwr:RSDW40F-05_MeanWell_2x1in", "THT", "Consign if PCBWay cannot source"),
 ("F1", "8A TIME-LAG 24V", "407 Series 1206 time-lag SMD fuse, 8 A, 24 V max, 60 A@24VDC interrupt (input; Mean Well recommends 8 A delay type)", "Littelfuse", "0407008.WR", "OSBAMS_PiPwr:Fuse_1206_Littelfuse407", "SMD", "Datasheet-verified: 9 mOhm nominal, I2t 24.12 A2s"),
 ("F2", "8A 125V", "Nano2 SMD fuse, fast-acting, 8 A, 125 VAC/VDC (5 V output, protects the Pi and display branches)", "Littelfuse", "0451008.MRL", "Fuse:Fuse_Littelfuse-NANO2-451_453", "SMD", "Datasheet-verified: 7.7 mOhm cold"),
 ("TVS1", "SMBJ15A", "TVS unidirectional 15 V standoff, 600 W, DO-214AA", "Littelfuse", "SMBJ15A", "Diode_SMD:D_SMB", "SMD", "Cathode to +12V_F; electrical data user-relayed"),
 ("J_IN", "12V IN", "Micro-Fit 3.0 header, right-angle, 2 circuits", "Molex", "430450200", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0200_2x01_P3.00mm_Horizontal", "THT", "Mate: 43025-0200 + 43030-0038 terminals (18 AWG)"),
 ("J_DISP", "DISPLAY 5V OUT", "Micro-Fit 3.0 header, right-angle, 2 circuits (direct 5 V feed for the Waveshare display; pin 1 +5 V, pin 2 GND)", "Molex", "430450200", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0200_2x01_P3.00mm_Horizontal", "THT", "Mate: 43025-0200 + 43030-0038 terminals (18 AWG)"),
 ("J2", "SSW-120-01-L-D", "Samtec 2x20, 2.54 mm, THT vertical receptacle, 10 uin Au mating, tin tails; mounted from the UNDERSIDE onto the Pi 5 header (+5 V pins 2,4; GND 6,9,14,20)", "Samtec", "SSW-120-01-L-D", "OSBAMS_PiPwr:SSW-120-01-L-D_RPi_TopView", "THT", "Dimensions verified (catalog F-226); MPN user-relayed"),
 ("C1", "100nF 50V", "MLCC X7R 0603 input bypass", "Murata", "GRM188R71H104KA93D", "Capacitor_SMD:C_0603_1608Metric", "SMD", ""),
 ("C2", "100uF 50V", "Aluminium electrolytic 8x11.5 mm radial, input bulk", "Panasonic", "EEU-FM1H101", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", "THT", "Verify body size/pitch"),
 ("C4", "680uF 16V", "Low-ESR aluminium electrolytic radial D10, output bulk", "Panasonic", "EEU-FR1C681", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "THT", "Verify body size/pitch"),
 ("C5", "10uF 25V", "MLCC X5R 0805 output bulk", "Murata", "GRM21BR61E106KA73L", "Capacitor_SMD:C_0805_2012Metric", "SMD", ""),
 ("C6", "100nF 50V", "MLCC X7R 0603 output bypass", "Murata", "GRM188R71H104KA93D", "Capacitor_SMD:C_0603_1608Metric", "SMD", ""),
 ("R1", "1.5k", "Resistor 0603 1% 0.1 W (PG LED, ~2 mA)", "Yageo", "RC0603FR-071K5L", "Resistor_SMD:R_0603_1608Metric", "SMD", ""),
 ("D1", "GREEN", "LED green 0603 (5V_PI power-good)", "Wurth Elektronik", "150060GS75000", "LED_SMD:LED_0603_1608Metric", "SMD", "Cathode to PI_GND"),
 ("R3", "SELECT", "Trim-UP resistor TRIM->-VOUT, 0603 1 %, value selected per unit at first-article calibration (61.9k / 71.5k / 84.5k E96 kit); NOT fitted at assembly, module runs at nominal 5.00 V until calibrated", "Yageo", "RC0603FR-0771K5L (nominal) / -0761K9L / -0784K5L", "Resistor_SMD:R_0603_1608Metric", "SMD", "DNP"),
 ("TP1", "12V_IN", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP2", "12V_GND", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP3", "5V_ISO_RAW", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP4", "5V_PI", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP5", "PI_GND", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
]
# centre positions (board frame, mm) and rotation (deg)
POS = {
 "U1": (U1_C[0], U1_C[1], 270),
 "J_IN": (75.9, 14.0, 270), "F1": (68.0, 9.0, 180), "TVS1": (61.0, 12.0, 0), "C1": (45.0, 12.0, 0), "C2": (50.0, 16.0, 0),
 "TP1": (72.0, 4.5, 0), "TP2": (62.0, 4.5, 0),
 "F2": (11.5, 55.0, 270), "TP3": (7.0, 47.0, 0),
 "R3": (42.2, 52.0, 0),
 "C4": (50.0, 47.0, 90), "C5": (58.0, 53.2, 0), "C6": (62.0, 53.2, 0), "R1": (72.5, 40.5, 0), "D1": (77.0, 40.5, 180),
 "TP4": (66.75, 42.0, 0), "TP5": (66.0, 36.0, 0), "J_DISP": (75.9, 47.0, 270),
}
FLAG_NETS = ["+12V_IN", "12V_GND", "+12V_F"]
