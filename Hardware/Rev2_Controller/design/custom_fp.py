"""Custom footprints for the OSBAMS_Rev2 project library."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRJ = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1")


def line(x1, y1, x2, y2, layer, w=0.12):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(x1, y1, x2, y2, layer, w=0.12):
    return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)


def eb21a():
    """Adam Tech EB21A-02-C, 2-position 5.00 mm pitch right-angle screw terminal.
    PROVISIONAL GEOMETRY (VERIFY_MECHANICAL_DRAWING): pitch from the catalog; drill/pad/body are conservative placeholders.
    Pin 1 at the origin, pin 2 at y = +5.00, wire entry toward -x."""
    s = '(footprint "EB21A-02-C_PROVISIONAL"\n  (version 20240108)\n  (generator "osbams")\n  (layer "F.Cu")\n'
    s += '  (descr "Adam Tech EB21A-02-C 2-pos 5.00 mm right-angle terminal block. PROVISIONAL GEOMETRY: VERIFY_MECHANICAL_DRAWING before fabrication")\n'
    s += '  (tags "EB21A terminal block 5.00mm provisional")\n  (attr through_hole)\n'
    s += '  (property "Reference" "REF**" (at -4.5 -3.8 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += '  (property "Value" "EB21A-02-C" (at -4.5 8.8 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += rect(-9.2, -2.6, 1.2, 7.6, "F.SilkS")
    s += line(1.2, -2.6, 1.2, 7.6, "F.SilkS", 0.3)
    s += rect(-9.7, -3.1, 1.7, 8.1, "F.CrtYd", 0.05)
    s += rect(-9.2, -2.6, 1.2, 7.6, "F.Fab", 0.1)
    s += '  (fp_text user "VERIFY_MECHANICAL_DRAWING" (at -4 2.5 90) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.1))))\n'
    s += '  (pad "1" thru_hole rect (at 0 0) (size 2.6 2.6) (drill 1.4) (layers "*.Cu" "*.Mask"))\n'
    s += '  (pad "2" thru_hole circle (at 0 5) (size 2.6 2.6) (drill 1.4) (layers "*.Cu" "*.Mask"))\n)\n'
    return s


def write_all():
    d = os.path.join(PRJ, "OSBAMS_Rev2.pretty")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "EB21A-02-C_PROVISIONAL.kicad_mod"), "w").write(eb21a())


if __name__ == "__main__":
    write_all()
