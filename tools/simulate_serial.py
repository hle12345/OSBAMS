#!/usr/bin/env python3
"""
tools/simulate_serial.py — Virtual serial port simulator for OSBAMS

Creates a virtual COM port pair and streams simulated discharge data
so the PySide6 GUI can be developed and tested without physical hardware.

Usage:
    python tools/simulate_serial.py                    # normal profile
    python tools/simulate_serial.py --profile degraded
    python tools/simulate_serial.py --profile hot
    python tools/simulate_serial.py --list

Available profiles: normal, degraded, hot, weak, fail

Requires:
    macOS/Linux: socat   (brew install socat  or  apt install socat)
    Windows:     com0com  (download from sourceforge)

macOS/Linux setup (run in a separate terminal first):
    socat -d -d pty,raw,echo=0 pty,raw,echo=0
    # note the two /dev/pts/N paths, use one as --port for simulator,
    # the other in the OSBAMS GUI port selector.

Simpler alternative — stdin mode:
    python tools/simulate_serial.py --stdout | cat
    # then manually note output format without needing socat

If socat is not available, the simulator prints lines to stdout.
Connect them to the GUI using a pipe or by writing to a named pipe.
"""

import sys
import os
import time
import argparse
import signal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "desktop"))
from equipment.drivers import Simulator6060B


def list_profiles():
    print("Available simulator profiles:")
    for name, p in Simulator6060B.PROFILES.items():
        print(f"  {name:<28}  SOH={p['soh']:.0%}  "
              f"start={p['start_v']}V  "
              f"temp_rise=+{p['temp_rise']}°C  "
              f"sag={p['sag_v']}V")


def run_stdout(profile: str, rate_ms: int, speed: float):
    """Stream simulated frames to stdout at real-time (or scaled) speed."""
    sim   = Simulator6060B(profile=profile, sample_rate_ms=rate_ms)
    lines = sim.generate_lines()

    print(f"# OSBAMS Simulator — profile={profile}  "
          f"samples={len(lines)}  rate={rate_ms}ms  speed={speed}x",
          flush=True)
    print(f"# {sim.name}", flush=True)

    sleep_s = (rate_ms / 1000.0) / speed

    for line in lines:
        print(line, flush=True)
        time.sleep(sleep_s)

    print("# OSBAMS,SIM_END,discharge complete", flush=True)


def run_port(profile: str, rate_ms: int, speed: float, port: str):
    """Write simulated frames to a serial port (works with socat virtual ports)."""
    import serial
    sim   = Simulator6060B(profile=profile, sample_rate_ms=rate_ms)
    lines = sim.generate_lines()

    with serial.Serial(port, 115200, timeout=1) as ser:
        print(f"[Simulator] Writing to {port}  profile={profile}  "
              f"samples={len(lines)}", flush=True)
        header = f"# OSBAMS Simulator  profile={profile}\r\n"
        ser.write(header.encode())
        sleep_s = (rate_ms / 1000.0) / speed
        for line in lines:
            ser.write((line + "\r\n").encode())
            time.sleep(sleep_s)
        ser.write(b"# SIM_END\r\n")
        print("[Simulator] Done.", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="OSBAMS serial discharge simulator")
    parser.add_argument("--profile", default="normal",
                        choices=list(Simulator6060B.PROFILES.keys()),
                        help="Battery profile to simulate")
    parser.add_argument("--rate", type=int, default=500,
                        help="Sample rate in ms (default: 500)")
    parser.add_argument("--speed", type=float, default=1.0,
                        help="Playback speed multiplier (default: 1.0, use 10.0 for fast test)")
    parser.add_argument("--port", type=str, default=None,
                        help="Serial port to write to (if omitted, writes to stdout)")
    parser.add_argument("--list", action="store_true",
                        help="List available profiles and exit")
    args = parser.parse_args()

    if args.list:
        list_profiles()
        return

    def _sigint(sig, frame):
        print("\n[Simulator] Interrupted.", flush=True)
        sys.exit(0)
    signal.signal(signal.SIGINT, _sigint)

    if args.port:
        run_port(args.profile, args.rate, args.speed, args.port)
    else:
        run_stdout(args.profile, args.rate, args.speed)


if __name__ == "__main__":
    main()
