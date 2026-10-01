"""Single source of truth for OSBAMS_Pi_Display_Power_RevA parts (BOM, schematic, PCB)."""

NAME = "OSBAMS_Pi_Display_Power_RevA"
BOARD_W, BOARD_H = 100.0, 70.0

UNVERIFIED = "NOT VERIFIED (no datasheet access in build env)"

# ref, value, description, manufacturer, mpn, footprint key, mount type
PARTS = [
 ("U1", "RSDW40F-05", "DC-DC isolated 9-36V in, 5V/8A/40W, 2x1in through-hole", "Mean Well", "RSDW40F-05", "OSBAMS_PiPwr:RSDW40F-05_PLACEHOLDER_UNVERIFIED", "THT", "Consign if PCBWay cannot source"),
 ("F1", "5A 125V", "Nano2 SMD fuse, fast-acting, 5 A, 125 VAC/VDC (input)", "Littelfuse", "0451005.MRL", "Fuse:Fuse_Littelfuse-NANO2-451_453", "SMD", ""),
 ("F2", "8A 125V", "Nano2 SMD fuse, fast-acting, 8 A, 125 VAC/VDC (output)", "Littelfuse", "0451008.MRL", "Fuse:Fuse_Littelfuse-NANO2-451_453", "SMD", ""),
 ("TVS1", "SMBJ15A", "TVS unidirectional 15 V standoff, 600 W, DO-214AA", "Littelfuse", "SMBJ15A", "Diode_SMD:D_SMB", "SMD", "Cathode to +12V_F"),
 ("J_IN", "12V IN", "Micro-Fit 3.0 header, right-angle, 2 circuits", "Molex", "430450200", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0200_2x01_P3.00mm_Horizontal", "THT", "Mate: 43025-0200 + 43030 terminals"),
 ("J_OUT", "ISOLATED 5V OUT", "Micro-Fit 3.0 header, right-angle, dual row, 4 circuits", "Molex", "430450400", "Connector_Molex:Molex_Micro-Fit_3.0_43045-0400_2x02_P3.00mm_Horizontal", "THT", "Mate: 43025-0400 + 43030 terminals"),
 ("C1", "100nF 50V", "MLCC X7R 0603 input bypass", "Murata", "GRM188R71H104KA93D", "Capacitor_SMD:C_0603_1608Metric", "SMD", ""),
 ("C2", "100uF 50V", "Aluminium electrolytic 8x11.5 mm radial, input bulk", "Panasonic", "EEU-FM1H101", "Capacitor_THT:CP_Radial_D8.0mm_P3.50mm", "THT", "Verify body size/pitch"),
 ("C4", "680uF 16V", "Low-ESR aluminium electrolytic radial D10, output bulk", "Panasonic", "EEU-FR1C681", "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", "THT", "Verify body size/pitch"),
 ("C5", "10uF 25V", "MLCC X5R 0805 output bulk", "Murata", "GRM21BR61E106KA73L", "Capacitor_SMD:C_0805_2012Metric", "SMD", ""),
 ("C6", "100nF 50V", "MLCC X7R 0603 output bypass", "Murata", "GRM188R71H104KA93D", "Capacitor_SMD:C_0603_1608Metric", "SMD", ""),
 ("R1", "1.5k", "Resistor 0603 1% 0.1 W (PG LED, ~2 mA)", "Yageo", "RC0603FR-071K5L", "Resistor_SMD:R_0603_1608Metric", "SMD", ""),
 ("D1", "GREEN", "LED green 0603 (5V_PI power-good)", "Wurth Elektronik", "150060GS75000", "LED_SMD:LED_0603_1608Metric", "SMD", "Cathode to PI_GND"),
 ("R2", "DNP", "TRIM option resistor TRIM->+VOUT. DO NOT FIT unless Mean Well trim formula confirmed (value TBD)", "Yageo", "RC0603FR-07TBDL", "Resistor_SMD:R_0603_1608Metric", "SMD", "DNP"),
 ("R3", "DNP", "TRIM option resistor TRIM->-VOUT. DO NOT FIT unless Mean Well trim formula confirmed (value TBD)", "Yageo", "RC0603FR-07TBDL", "Resistor_SMD:R_0603_1608Metric", "SMD", "DNP"),
 ("TP1", "12V_IN", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP2", "12V_GND", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP3", "5V_ISO_RAW", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP4", "5V_PI", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
 ("TP5", "PI_GND", "SMT test point", "Keystone", "5015", "TestPoint:TestPoint_Pad_D1.5mm", "SMD", ""),
]

# Centre positions (mm), board origin top-left, +y down
POS = {
 "U1": (50.0, 31.0), "F1": (20.0, 8.0), "F2": (80.7, 46.0), "TVS1": (31.0, 8.5),
 "J_IN": (9.1, 14.0), "J_OUT": (88.0, 60.9),
 "C1": (31.0, 24.0), "C2": (28.75, 17.0), "C4": (76.0, 53.0),
 "C5": (86.5, 52.0), "C6": (86.5, 55.0),
 "R1": (91.0, 41.5), "D1": (91.0, 45.0), "R2": (75.5, 40.0), "R3": (75.5, 43.5),
 "TP1": (10.0, 4.5), "TP2": (14.0, 17.0), "TP3": (80.0, 26.0),
 "TP4": (87.5, 47.8), "TP5": (94.0, 50.0),
}
FLAG_NETS = ["+12V_IN", "12V_GND", "+12V_F"]  # PWR_FLAG on these nets (sources are upstream: XDR-75-12 harness)
