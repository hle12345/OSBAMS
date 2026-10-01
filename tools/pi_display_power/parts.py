"""Single source of truth for OSBAMS_Pi_Display_Power_RevA parts (BOM, schematic, PCB)."""

NAME = "OSBAMS_Pi_Display_Power_RevA"
BOARD_W, BOARD_H = 100.0, 70.0

UNVERIFIED = "NOT VERIFIED (no datasheet access in build env)"

# ref, value, description, manufacturer, mpn, footprint key, mount type
PARTS = [
 ("U1", "RSDW40F-05", "DC-DC isolated 9-36V in, 5V/8A/40W, 2x1in through-hole", "Mean Well", "RSDW40F-05", "RSDW40_PLACEHOLDER", "THT", "Consign if PCBWay cannot source"),
 ("F1", "5A 125V", "Nano2 SMD fuse, fast-acting, 5 A, 125 VAC/VDC (input)", "Littelfuse", "0451005.MRL", "FUSE_NANO2_H", "SMD", ""),
 ("F2", "8A 125V", "Nano2 SMD fuse, fast-acting, 8 A, 125 VAC/VDC (output)", "Littelfuse", "0451008.MRL", "FUSE_NANO2_V", "SMD", ""),
 ("TVS1", "SMBJ15A", "TVS unidirectional 15 V standoff, 600 W, DO-214AA", "Littelfuse", "SMBJ15A", "DO214AA", "SMD", "Cathode to +12V_F"),
 ("J_IN", "12V IN", "Micro-Fit 3.0 header, right-angle, 2 circuits", "Molex", "430450200", "MICROFIT_RA_2", "THT", "Mate: 43025-0200 + 43030 terminals"),
 ("J_OUT", "ISOLATED 5V OUT", "Micro-Fit 3.0 header, right-angle, dual row, 4 circuits", "Molex", "430450400", "MICROFIT_RA_4", "THT", "Mate: 43025-0400 + 43030 terminals"),
 ("C1", "100nF 50V", "MLCC X7R 0603 input bypass", "Murata", "GRM188R71H104KA93D", "C0603", "SMD", ""),
 ("C2", "100uF 50V", "Aluminium electrolytic 8x11.5 mm radial, input bulk", "Panasonic", "EEU-FM1H101", "CP_RADIAL_D8_P35", "THT", "Verify body size/pitch"),
 ("C4", "680uF 16V", "Low-ESR aluminium electrolytic radial D10, output bulk", "Panasonic", "EEU-FR1C681", "CP_RADIAL_D10_P50", "THT", "Verify body size/pitch"),
 ("C5", "10uF 25V", "MLCC X5R 0805 output bulk", "Murata", "GRM21BR61E106KA73L", "C0805", "SMD", ""),
 ("C6", "100nF 50V", "MLCC X7R 0603 output bypass", "Murata", "GRM188R71H104KA93D", "C0603", "SMD", ""),
 ("R1", "1.5k", "Resistor 0603 1% 0.1 W (PG LED, ~2 mA)", "Yageo", "RC0603FR-071K5L", "R0603", "SMD", ""),
 ("D1", "GREEN", "LED green 0603 (5V_PI power-good)", "Wurth Elektronik", "150060GS75000", "LED0603", "SMD", "Cathode to PI_GND"),
 ("TP1", "12V_IN", "SMT test point", "Keystone", "5015", "TP15", "SMD", ""),
 ("TP2", "12V_GND", "SMT test point", "Keystone", "5015", "TP15", "SMD", ""),
 ("TP3", "5V_ISO_RAW", "SMT test point", "Keystone", "5015", "TP15", "SMD", ""),
 ("TP4", "5V_PI", "SMT test point", "Keystone", "5015", "TP15", "SMD", ""),
 ("TP5", "PI_GND", "SMT test point", "Keystone", "5015", "TP15", "SMD", ""),
]

# Centre positions (mm), board origin top-left, +y down
POS = {
 "U1": (50.0, 31.0), "F1": (18.0, 8.0), "F2": (80.7, 46.0), "TVS1": (31.0, 8.5),
 "J_IN": (6.0, 14.0), "J_OUT": (81.7, 63.0),
 "C1": (31.0, 24.0), "C2": (30.5, 17.0), "C4": (71.0, 60.0),
 "C5": (74.5, 50.0), "C6": (74.5, 54.0),
 "R1": (88.0, 57.0), "D1": (88.0, 53.0),
 "TP1": (10.0, 4.5), "TP2": (14.0, 17.0), "TP3": (80.0, 26.0),
 "TP4": (80.5, 59.5), "TP5": (87.0, 59.5),
}

FLAG_NETS = ["+12V_IN", "12V_GND", "+12V_F"]  # PWR_FLAG on these nets (sources are upstream: XDR-75-12 harness)
