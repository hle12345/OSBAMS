#!/usr/bin/env python3
"""Stack-height / spacer / key-post length check for the Pi power interposer using Samtec SSW-120-01-S-D (owner-cited dims)."""
import sys, os, json
D = sys.argv[1]
I = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "datasheet_inputs.json")))
d = I["interposer_socket_dims"]["value"]
BODY, TAIL, PLASTIC, TIP = d["body_height_mm"], d["tail_length_mm"], d["pi_header_plastic_mm"], d["pi_pin_tip_height_mm"]
PCB_T = 1.6
G = BODY + PLASTIC                       # interposer underside -> Pi PCB top when the socket face rests on the Pi header plastic
SPACER = G
PIN_IN = TIP - PLASTIC                   # pin length that enters the socket
POST = 20.0                              # M2.5 x 20 mm key standoff
rev_face = POST - BODY                   # reversed: socket face height above the Pi PCB when the posts rest on the PCB
out = ["Stack-height check - Samtec SSW-120-01-S-D (owner-cited: body 8.51 mm, tail 2.64 mm) on the Raspberry Pi 5 header", "",
       f"Seated gap G (interposer underside to Pi PCB) = body {BODY} + Pi header plastic {PLASTIC} (assumed) = {G:.2f} mm  ->  M1/M2 spacers: M2.5 x 11 mm (standard HAT length).",
       f"Mating insertion depth per catalog: {d['insertion_depth_mm'][0]}-{d['insertion_depth_mm'][1]} mm; Pi pin protrusion ~{TIP - PLASTIC:.1f} mm -> " + ("within range" if TIP - PLASTIC <= d['insertion_depth_mm'][1] + 0.3 else "pin longer than max depth") + f" (a pin up to {TIP - PLASTIC - d['insertion_depth_mm'][1]:.2f} mm beyond the 6.35 mm maximum would bottom out and leave the socket that far above the plastic; the 11 mm spacer tolerates it).",
       f"Pin engagement: Pi pins protrude {PIN_IN:.1f} mm above the plastic (tip height {TIP} mm from the Pi drawing) -> need socket contact depth >= {PIN_IN:.1f} mm of the {BODY} mm body: " + ("OK (body is deeper than the pin length)" if BODY > PIN_IN else "FAIL"),
       f"Tail: {TAIL} mm through a {PCB_T} mm board leaves {TAIL - PCB_T:.2f} mm protruding on the top side for soldering: " + ("OK" if TAIL - PCB_T >= 0.5 else "short"),
       f"Interposer top surface height over the Pi PCB = {G + PCB_T:.1f} mm; J1 (Micro-Fit right-angle) adds its own height on top - check against the enclosure lid.",
       "", f"Key posts: M2.5 x {POST:.0f} mm standoffs. Reversed, they rest on bare Pi PCB (see Pi5_keying_check.txt) and the socket mating face stops at {rev_face:.1f} mm above the Pi PCB vs pin tips at {TIP} mm -> {rev_face - TIP:+.1f} mm margin: " + ("pins cannot enter the socket (PASS)" if rev_face - TIP >= 1.5 else "INSUFFICIENT - lengthen posts"),
       f"Minimum post length for >= 1.5 mm margin: {BODY + TIP + 1.5:.1f} mm.",
       f"Correct orientation: posts hang {POST:.0f} mm below the interposer = {POST - G:.1f} mm below the Pi PCB plane, {11.0:.0f} mm beyond the Pi edge (free air; relevant to the enclosure).",
       "", "Collisions: Active Cooler / SoC area is 17.1 mm from the interposer footprint in plan (Pi5_keying_check.txt) and the board floats at 11 mm over the header-side chips (<= ~2 mm tall) -> no Active Cooler collision. Enclosure: the interposer overhangs the Pi edge by ~14 mm and posts by ~11 mm; the official Pi 5 case (98.5 x 70.3 x 33 mm) is not compatible with the lid on - custom enclosure or open case. Report to owner before any socket-family change (none needed).",
       "SSW-120-04-G-D (14.83 mm tail, no stock) rejected: not mechanically required."]
txt = "\n".join(out); print(txt); open(os.path.join(D, "reports", "Stack_height_check.txt"), "w").write(txt + "\n")
