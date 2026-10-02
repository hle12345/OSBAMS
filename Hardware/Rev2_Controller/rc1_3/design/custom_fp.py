"""Custom footprints for the OSBAMS_Rev2 project library."""
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRJ = os.path.join(ROOT, "OSBAMS_Rev2_RC13")


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


def ftsh_105():
    """Samtec FTSH-105-01-L-DV-K, 10-pin (2 x 5) 1.27 mm vertical SMT shrouded header.
    Land pattern from Samtec drawing FTSH-1XX-XX-XXX-DV-XXX-FOOTPRINT rev H (8/27/2019, ECN-364793), Fig 1 (option -K: no alignment pegs / no NPTH):
    pitch 1.27 mm; pads 0.74 x 2.79 mm; pad-row overall 6.86 mm (rows at +-2.035 mm, 1.28 mm between rows); connector outline = N x 1.27 = 6.35 mm wide x 3.43 mm,
    all symmetric about the centerline. Numbering (drawing): 01 bottom-left, 02 directly above it, 03 bottom 2nd column ... (odd pins bottom row, even pins top row).
    Stencil (sheet 2): apertures equal to the pads, 0.152 mm stencil. The key-notch position of the -K shroud is NOT on the supplied sheets (only pin 1 is)."""
    s = '(footprint "FTSH-105-01-L-DV-K"\n  (version 20240108)\n  (generator "osbams")\n  (layer "F.Cu")\n'
    s += '  (descr "Samtec FTSH-105-01-L-DV-K 2x5 1.27 mm vertical SMT keyed shrouded header; land pattern from Samtec FTSH-1XX-XX-XXX-DV-XXX footprint drawing rev H (VERIFIED_LOCAL). Pin 1 bottom-left (square-marked); key notch position not on the supplied sheets.")\n'
    s += '  (tags "FTSH Samtec 1.27mm SWD Cortex debug")\n  (attr smd)\n'
    s += '  (property "Reference" "REF**" (at 0 -5.0 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))\n'
    s += '  (property "Value" "FTSH-105-01-L-DV-K" (at 0 5.0 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))\n'
    for n in range(1, 11):
        col = (n - 1) // 2
        x = round((col - 2) * 1.27, 3)
        y = 2.035 if n % 2 == 1 else -2.035
        s += f'  (pad "{n}" smd rect (at {x} {y}) (size 0.74 2.79) (layers "F.Cu" "F.Paste" "F.Mask"))\n'
    s += rect(-3.175, -1.715, 3.175, 1.715, "F.Fab", 0.1)
    s += line(-3.175, -1.715, -3.175, 1.715, "F.SilkS", 0.2) + line(3.175, -1.715, 3.175, 1.715, "F.SilkS", 0.2)
    s += '  (fp_text user "1" (at -3.9 3.0 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
    s += '  (fp_text user "KEY NOTCH: verify vs Samtec print" (at 0 0 0) (layer "F.Fab") (effects (font (size 0.4 0.4) (thickness 0.06))))\n'
    s += rect(-3.4, -3.7, 3.4, 3.7, "F.CrtYd", 0.05)
    s += ')\n'
    return s


def write_all():
    d = os.path.join(PRJ, "OSBAMS_Rev2.pretty")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "EB21A-02-C.kicad_mod"), "w").write(eb21a())
    open(os.path.join(d, "FTSH-105-01-L-DV-K.kicad_mod"), "w").write(ftsh_105())


if __name__ == "__main__":
    write_all()
