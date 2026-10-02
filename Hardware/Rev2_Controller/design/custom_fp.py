"""Custom footprints for the OSBAMS_Rev2 project library."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRJ = os.path.join(ROOT, "OSBAMS_Rev2_RELEASE_CANDIDATE_1")


def line(x1, y1, x2, y2, layer, w=0.12):
    return f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) (layer "{layer}"))\n'


def rect(x1, y1, x2, y2, layer, w=0.12):
    return line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) + line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w)


def eb21a():
    """Adam Tech EB21A-02-C, 2-position 5.00 mm pitch right-angle screw terminal (drawing EB21A-XX-C rev B, 7/30/18).
    From the drawing: pitch 5.00; recommended PCB hole 1.30 mm (+/-0.25 mm hole tolerance); pins 0.90 x 0.60 mm, 4.00 mm tail;
    body 5.00*N + 0.60 = 10.60 mm wide (2.50 mm before pin 1, 3.10 mm after the last pin), 8.50 mm deep (pins 4.00 mm from the back,
    4.50 mm from the wire-entry face), 10.20 mm tall. Pad size, courtyard and silkscreen are design choices (the drawing gives none).
    Local frame: pin 1 at the origin, pin 2 at y = +5.00, wire-entry face toward -x (pin row 4.50 mm behind it), back wall at x = +4.00."""
    s = '(footprint "EB21A-02-C"\n  (version 20240108)\n  (generator "osbams")\n  (layer "F.Cu")\n'
    s += '  (descr "Adam Tech EB21A-02-C 2-pos 5.00 mm right-angle screw terminal; geometry from drawing EB21A-XX-C rev B (VERIFIED_LOCAL). Pin 1 = square pad; wire entry toward -x.")\n'
    s += '  (tags "EB21A terminal block 5.00mm")\n  (attr through_hole)\n'
    s += '  (property "Reference" "REF**" (at -4.5 -3.8 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += '  (property "Value" "EB21A-02-C" (at -4.5 9.3 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += rect(-4.5, -2.5, 4.0, 8.1, "F.SilkS")
    s += line(-4.5, -2.5, -4.5, 8.1, "F.SilkS", 0.3)            # heavy line = wire-entry face
    s += rect(-4.75, -2.75, 4.25, 8.35, "F.CrtYd", 0.05)
    s += rect(-4.5, -2.5, 4.0, 8.1, "F.Fab", 0.1)
    s += '  (fp_text user "WIRE ENTRY" (at -2.2 2.5 90) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.1))))\n'
    s += '  (pad "1" thru_hole rect (at 0 0) (size 2.6 2.6) (drill 1.3) (layers "*.Cu" "*.Mask"))\n'
    s += '  (pad "2" thru_hole circle (at 0 5) (size 2.6 2.6) (drill 1.3) (layers "*.Cu" "*.Mask"))\n)\n'
    return s


def ftsh105():
    """Samtec FTSH-105-01-L-DV-K, 10-pos (2x5) 1.27 mm double-row vertical SMT shrouded header.
    Land pattern from Samtec 'Recommended PCB layout for FTSH-1XX-XX-XXX-DV-XXX' rev H (VERIFIED_LOCAL): pads 0.74 x 2.79 mm,
    1.27 mm pitch, 6.86 mm overall pad span (pad rows 4.07 mm centre to centre, 1.28 mm between the rows); -K has no locating hole
    (table 1 'A' = N/A). Body from the product drawing FTSH-1XX-XX-XXX-DV-XXX-XXX-X-XX rev FX: 5 x 1.27 = 6.35 mm long, 3.43 mm wide.
    Local frame = the KiCad generic frame (origin = array centre, pin 1 top-left, pin 2 to its right, pitch along +y): rotating this
    footprint by +90 deg (CCW) reproduces the Samtec drawing view (pin 1 bottom-left, pin 2 above it, pin 3 to its right).
    The position of the -K key slot on the shroud is NOT resolved by the drawings (see CONNECTOR_FOOTPRINT_CHECK.md)."""
    s = '(footprint "FTSH-105-01-L-DV-K"\n  (version 20240108)\n  (generator "osbams")\n  (layer "F.Cu")\n'
    s += '  (descr "Samtec FTSH-105-01-L-DV-K 2x5 1.27 mm SMT shrouded header; land pattern from Samtec recommended PCB layout rev H (VERIFIED_LOCAL). Pin 1 top-left in this frame.")\n'
    s += '  (tags "SWD Cortex debug FTSH 1.27mm")\n  (attr smd)\n'
    s += '  (property "Reference" "REF**" (at 0 -4.2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += '  (property "Value" "FTSH-105-01-L-DV-K" (at 0 4.2 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    for n in range(1, 11):
        row = (n - 1) // 2
        x = -2.035 if n % 2 else 2.035
        y = -2.54 + 1.27 * row
        s += f'  (pad "{n}" smd rect (at {x} {y}) (size 2.79 0.74) (layers "F.Cu" "F.Mask" "F.Paste"))\n'
    s += rect(-1.715, -3.175, 1.715, 3.175, "F.Fab", 0.1)
    s += rect(-3.68, -3.43, 3.68, 3.43, "F.CrtYd", 0.05)
    s += line(-1.7, -3.3, 1.7, -3.3, "F.SilkS") + line(-1.7, 3.3, 1.7, 3.3, "F.SilkS")
    s += '  (fp_poly (pts (xy -3.95 -2.54) (xy -4.45 -2.84) (xy -4.45 -2.24)) (stroke (width 0.1) (type solid)) (fill solid) (layer "F.SilkS"))\n'
    s += '  (fp_text user "1" (at -4.9 -2.54 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n)\n'
    return s


def write_all():
    d = os.path.join(PRJ, "OSBAMS_Rev2.pretty")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "EB21A-02-C.kicad_mod"), "w").write(eb21a())
    open(os.path.join(d, "FTSH-105-01-L-DV-K.kicad_mod"), "w").write(ftsh105())


if __name__ == "__main__":
    write_all()
