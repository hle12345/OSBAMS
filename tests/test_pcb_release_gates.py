"""Release-gate guard for the controller PCB: no fabrication package while any gate is open; plan/bench docs present."""
import json, os, re, subprocess, sys, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
PCB = os.path.join(ROOT, "docs", "rev2", "pcb")
MFG = os.path.join(ROOT, "manufacturing")
FAB_EXT = (".gbr", ".drl", ".xlsx", ".zip", ".gtl", ".gbl")

from tools.mfg.pcb_model import Board
from tools.mfg.schem_model import Schematic
from tools.mfg import review_checks


def gates():
    return json.load(open(os.path.join(PCB, "RELEASE_GATES.json")))


class TestReleaseGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b, cls.s = Board(), Schematic()

    def test_no_fabrication_files_while_a_gate_is_open(self):
        g = {k: v for k, v in gates().items() if not k.startswith("_")}
        self.assertEqual(len(g), 6)
        if all(g.values()):
            return
        found = []
        for d, _, fs in os.walk(MFG):
            found += [os.path.join(d, f) for f in fs if f.lower().endswith(FAB_EXT) or "CPL" in f or "BOM" in f.upper()]
        self.assertEqual(found, [], "fabrication outputs exist while release gates are open")

    def test_builder_refuses_without_candidate_flag(self):
        if all(v for k, v in gates().items() if not k.startswith("_")):
            self.skipTest("all gates closed")
        r = subprocess.run([sys.executable, "-m", "tools.mfg.build_package"], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("rev1_physical_observations_recorded", r.stdout + r.stderr)

    def test_bench_sheet_is_one_page_with_authoritative_v1_to_v10(self):
        data = open(os.path.join(PCB, "BENCH_V1_V10_ONE_PAGE.pdf"), "rb").read()
        self.assertEqual(len(re.findall(rb"/Type\s*/Page[^s]", data)), 1)
        md = open(os.path.join(PCB, "BENCH_V1_V10.md")).read()
        for i in range(1, 11):
            self.assertRegex(md, rf"\| V{i} \|")
        self.assertNotIn("reconstruct", md.lower())

    def test_rev2_architecture_doc_is_the_design_phase_deliverable(self):
        d = os.path.join(ROOT, "Hardware", "Rev2_Controller")
        t = open(os.path.join(d, "REV2_CONTROLLER_ARCHITECTURE.md")).read()
        for kw in ("Block diagram", "MCU: direct STM32", "Pin assignment", "Power tree", "Measurement",
                   "E-stop / ARM / relay-feedback", "Connectors and test points", "Preliminary BOM", "Open items",
                   "Locked decisions", "Relay driver"):
            self.assertIn(kw.lower(), t.lower(), kw)
        for must in ("I²C2", "no 5 V rail", "GND only", "not frozen", "SHUNT_CAL 1250"):
            self.assertIn(must.lower(), t.lower(), must)
        for f in ("REV2_CALCULATIONS.md", "REV2_PRELIM_BOM.csv", "REV2_BLOCK_DIAGRAM.png", "REV2_BLOCK_DIAGRAM.svg",
                  "DATASHEET_VERIFICATION.md"):
            self.assertTrue(os.path.getsize(os.path.join(d, f)) > 0, f)
        self.assertTrue(os.path.isdir(os.path.join(ROOT, "legacy", "reference", "rev1_kicad")))

    def _inputs(self):
        return json.load(open(os.path.join(ROOT, "Hardware", "Rev2_Controller", "calc", "datasheet_inputs.json")))["inputs"]

    def test_no_rev2_schematic_while_critical_datasheet_inputs_are_unverified(self):
        d = os.path.join(ROOT, "Hardware", "Rev2_Controller")
        crit = [k for k, v in self._inputs().items() if v.get("critical") and not v["verified"]]
        kicad = []
        for r, _, fs in os.walk(d):
            kicad += [f for f in fs if f.endswith((".kicad_sch", ".kicad_pcb", ".kicad_pro"))]
        if crit:
            self.assertEqual(kicad, [], f"KiCad files exist while critical datasheet inputs are unverified: {crit}")
        for k, v in self._inputs().items():
            if v["verified"]:
                self.assertTrue(v["doc"], f"{k} marked verified without a document reference")

    def test_calculations_are_current_and_say_blocked_while_unverified(self):
        d = os.path.join(ROOT, "Hardware", "Rev2_Controller")
        before = open(os.path.join(d, "REV2_CALCULATIONS.md")).read()
        subprocess.run([sys.executable, os.path.join(d, "calc", "rev2_calcs.py")], check=True, capture_output=True)
        after = open(os.path.join(d, "REV2_CALCULATIONS.md")).read()
        self.assertEqual(before, after, "REV2_CALCULATIONS.md is stale: re-run calc/rev2_calcs.py")
        if any(not v["verified"] for v in self._inputs().values()):
            self.assertIn("BLOCKED", after)

    def test_prelim_bom_columns_and_no_unverified_part_is_marked_verified(self):
        import csv
        rows = list(csv.DictReader(open(os.path.join(ROOT, "Hardware", "Rev2_Controller", "REV2_PRELIM_BOM.csv"))))
        for c in ("Ref", "Qty", "Manufacturer", "MPN", "KiCad footprint", "Status", "Datasheet verified"):
            self.assertIn(c, rows[0])
        verified = [r["Ref"] for r in rows if r["Datasheet verified"].upper() == "YES"]
        if any(not v["verified"] for v in self._inputs().values()):
            self.assertEqual(verified, [], "BOM claims datasheet verification that the input register does not support")
        self.assertNotIn("IRLZ44", " ".join(r["MPN"] for r in rows if r["Ref"] == "Q1"))

    def test_plan_covers_all_mandatory_items_and_is_not_applied(self):
        plan = open(os.path.join(PCB, "REV2_SCHEMATIC_PCB_PLAN.md")).read()
        for kw in ("polarity", "PA0", "PC9", "PA1", "Kelvin", "ARM", "MPN", "test point", "marking"):
            self.assertIn(kw.lower(), plan.lower(), kw)
        for f in ("RELAY_VERIFICATION.md", "PI_POWER_ARCHITECTURE.md", "MANUFACTURING_STATE.md"):
            self.assertTrue(os.path.getsize(os.path.join(PCB, f)) > 0, f)

    def test_schematic_and_pcb_agree(self):
        rv = review_checks.run(self.b, self.s)
        self.assertEqual(rv["netlist_diffs"], [])
        self.assertEqual(rv["ref_footprint_mismatch"], [])
        self.assertEqual(rv["dangling_track_ends"], [])
        self.assertEqual(rv["courtyard_overlaps"], [])

    def test_diode_polarity_mismatch_is_reproducible(self):
        """Symbol pin 1 = anode (triangle base); KiCad footprint pad 1 = cathode ('K' on silk / band at pad 1)."""
        from tools.mfg.sexp import find
        for lib in ("OSBAMS:D_H",):
            sym = self.s.libs[lib]
            tri = None
            for u in find(sym, "symbol"):
                for e in u[2:]:
                    if isinstance(e, list) and e[0] == "polyline":
                        pts = [(float(p[1]), float(p[2])) for p in find(find(e, "pts")[0], "xy")]
                        if len(pts) == 4:
                            tri = pts
            apex_x = max(p[0] for p in tri); base_x = min(p[0] for p in tri)
            pin1 = [p for u in find(sym, "symbol") for p in find(u, "pin") if find(p, "number")[0][1] == "1"][0]
            self.assertLess(float(find(pin1, "at")[0][1]), base_x)      # pin 1 on the triangle-base side = anode
            self.assertGreater(apex_x, base_x)
        for ref in ("D2", "D3"):
            fp = [f for f in self.b.footprints if f["ref"] == ref][0]
            k = [t for t in fp["texts"] if t["text"] == "K"]
            self.assertTrue(k, f"{ref} footprint has no 'K' marker")
            p1 = [p for p in fp["pads"] if p["num"] == "1"][0]
            p2 = [p for p in fp["pads"] if p["num"] == "2"][0]
            d1 = ((k[0]["x"] - p1["x"]) ** 2 + (k[0]["y"] - p1["y"]) ** 2) ** .5
            d2 = ((k[0]["x"] - p2["x"]) ** 2 + (k[0]["y"] - p2["y"]) ** 2) ** .5
            self.assertLess(d1, d2)                                       # K marker sits at pad 1

    def test_nothing_claims_production_ready(self):
        for f in os.listdir(PCB):
            if f.endswith(".md") and "SNAPSHOT" not in f:
                t = open(os.path.join(PCB, f)).read()
                self.assertNotRegex(t, r"(?i)\bis production[- ]ready\b")


if __name__ == "__main__":
    unittest.main()
