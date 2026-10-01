"""Render the PCB to PNG via kicad-cli (container) + cairosvg (host)."""
import subprocess, sys, os
W = "/work/Hardware/Rev2_Controller/OSBAMS_Rev2_RELEASE_CANDIDATE_1"
HOST = "/home/user/OSBAMS/Hardware/Rev2_Controller/OSBAMS_Rev2_RELEASE_CANDIDATE_1"
SCR = "/tmp/claude-0/-home-user-OSBAMS/897383b6-cae5-5014-a88d-0cb5d3a932a1/scratchpad"


def render(name, layers, pcb="OSBAMS_Rev2_RC1.kicad_pcb", scale=1.0):
    svg = f"{W}/_{name}.svg"
    subprocess.run(["/usr/local/bin/kc10", "/usr/bin/kicad-cli", "pcb", "export", "svg", "--layers", layers, "--page-size-mode", "2", "--exclude-drawing-sheet", "-o", svg, f"{W}/{pcb}"], check=True, capture_output=True)
    import cairosvg
    out = f"{SCR}/{name}.png"
    cairosvg.svg2png(url=f"{HOST}/_{name}.svg", write_to=out, output_width=int(1800 * scale))
    os.remove(f"{HOST}/_{name}.svg")
    return out


if __name__ == "__main__":
    print(render(sys.argv[1], sys.argv[2], *(sys.argv[3:4] or [])))
