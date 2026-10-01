OSBAMS_Rev2_CPL.csv lists the SMT components only (PCBWay assembles SMT from the CPL): D1 (SMBJ15A, SMB).
All other parts are through-hole; OSBAMS_Rev2_CPL_ALL_PARTS_reference_THT_included.csv lists every placed footprint for
reference (THT assembly instructions are in the assembly notes).
Coordinates: millimetres, origin = lower-left corner of the board outline, Y up (same origin as the Gerber and drill files).
Rotation: KiCad footprint orientation (degrees, counter-clockwise). D1 = 0 deg: pad 1 (cathode per KiCad's D_SMB footprint) on the
LEFT. D1's electrical polarity is an OPEN ISSUE (schematic puts the cathode on +12V; the PCB puts pad 1 = cathode on GND) - see the review.
Have PCBWay confirm D1 orientation against their library before assembly.
