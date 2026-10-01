"""OSBAMS Rev.2 remote TC74 temperature probe (small separate PCB)."""
from collections import OrderedDict
from . import rev2_design as R

PROJECT = "OSBAMS_Rev2_TC74_Probe_RC1"
SHEETS = OrderedDict([("01_Probe", "Remote TC74A5-3.3VAT probe")])
S = "01_Probe"
COMPS = OrderedDict()
P = {}
P.update({k: R.P[k] for k in ("C100n_owned", "R0603_4.7k", "J_PH4")})
P["TC74"] = dict(lib="OSBAMS_Rev2:TC74A5", fp="Package_TO_SOT_THT:TO-220-5_P3.4x3.7mm_StaggerOdd_Lead3.8mm_Vertical", mfr="Microchip", mpn="TC74A5-3.3VAT",
                 desc="TC74A5 I2C temperature sensor 3.3 V, address 0x4D, TO-220-5 (PIN MAP UNVERIFIED: from Rev.1 inventory). Leads must be formed to the staggered footprint (1.7 mm straight pitch gives only 0.085 mm annular ring)",
                 evid=R.UV, life="UNKNOWN (not checked)", alt="TC74A0-3.3VAT (address 0x48: firmware change)", src="CONSIGN (owned: 2)")
P["TP"] = R.P["TP"]; P["MH"] = R.P["MH"]


def add(ref, key, nets, value=None, dnp=False, note=""):
    d = dict(P[key]); d.update(ref=ref, key=key, sheet=S, nets=dict(nets), dnp=dnp, note=note, value=value or d["mpn"])
    COMPS[ref] = d


add("J1", "J_PH4", {1: "+3V3", 2: "SDA", 3: "SCL", 4: "GND"}, "TO_CONTROLLER", note="Mates J7 on the controller: 1 3V3, 2 SDA2, 3 SCL2, 4 GND")
add("U1", "TC74", {"SDA": "SDA", "GND": "GND", "SCLK": "SCL", "VDD": "+3V3"}, "TC74A5-3.3VAT")
add("C1", "C100n_owned", {1: "+3V3", 2: "GND"}, "100nF", note="Directly at U1 VDD/GND (owned VJ0805Y104JXXAT)")
add("R1", "R0603_4.7k", {1: "+3V3", 2: "SDA"}, "4.7k", dnp=True, note="Optional pull-up footprint (DNP: pull-ups are on the controller)")
add("R2", "R0603_4.7k", {1: "+3V3", 2: "SCL"}, "4.7k", dnp=True, note="Optional pull-up footprint (DNP)")
PWR_FLAGS = ["+3V3", "GND"]
POWER_SYMS = R.POWER_SYMS
CUSTOM = {"TC74A5": dict(ref="U", value="TC74A5-3.3VAT", fp="Package_TO_SOT_THT:TO-220-5_P3.4x3.7mm_StaggerOdd_Lead3.8mm_Vertical", desc="TC74A5 (pin map UNVERIFIED)",
                         pins=[("1", "NC", "no_connect", "L", 0), ("2", "SDA", "bidirectional", "L", 1), ("3", "GND", "power_in", "L", 2), ("4", "SCLK", "input", "R", 0), ("5", "VDD", "power_in", "R", 1)])}
