"""
services/learning_mode.py — Learning Mode, rewritten around the actual SFSU lab.

Lessons are plain data (title, body) so the GUI, CLI and reports share them.
`power_limit_lesson()` is the live lesson: it computes from the capability
model, so the numbers on screen are the numbers the driver enforces.

    python -m services.learning_mode            # from desktop/
"""

from equipment import capability as cap

LESSONS = [
    ("Why 60 A does not mean 60 A at 42 V",
     "The 6060B has THREE simultaneous limits: 60 V, 60 A and 300 W. Current "
     "available is min(60 A, 300 W / V). At 5 V that is 60 A; at 42 V it is only "
     "7.14 A. Connector names are not current ratings either: an XT90 is a plug, "
     "not a 90 A test."),
    ("Why power matters",
     "P = V x I. A battery's voltage rises as it charges, so the same current "
     "means more watts on a full pack than on an empty one. The load must never "
     "be asked for more than 300 W, so OSBAMS uses the HIGHEST voltage the pack "
     "can show when it sizes the current."),
    ("OCV — open-circuit voltage",
     "Pack voltage with no current flowing, after resting. It reflects state of "
     "charge and is the starting point for every test. It also fixes the 300 W "
     "current limit, so it is measured first."),
    ("Capacity: Ah vs Wh",
     "Ah = integral of I dt counts charge; Wh = integral of V*I dt counts energy. "
     "Two packs with equal Ah can store different energy if their voltage "
     "differs, so OSBAMS reports both."),
    ("SOC and SOH",
     "SOC is how full the pack is now. SOH_capacity = measured usable capacity / "
     "reference usable capacity: how much the pack has aged. A pack can be 100% "
     "charged and still have a low SOH."),
    ("DCIR and voltage sag",
     "Step the load current and measure R_DC = dV / dI. Internal resistance makes "
     "the terminal voltage sag under load and recover (slowly) after it is "
     "removed. Higher DCIR = more heat and less usable power."),
    ("Cutoff voltage",
     "Discharge stops at a profile-specific cutoff voltage. There is no single "
     "global minimum: a 3S, a 10S and a 14S pack all differ."),
    ("BMS",
     "The pack's battery-management system protects its cells. OSBAMS measures "
     "from outside and never bypasses BMS protection. A BMS cut-off during a test "
     "is a result to record, not an obstacle to defeat."),
    ("Thermal limits",
     "Heat is I^2 * R. Pack temperature is monitored during discharge and the "
     "test stops at the profile's limit."),
    ("Instrument limits",
     "OSBAMS's allowed current is the minimum of the battery profile, OSBAMS "
     "validated hardware, connector/fuse/wiring/contactor/shunt ratings, the "
     "6060B's 60 A and its 300 W power limit."),
]


def power_limit_lesson(pack_voltage_v: float = 42.0,
                       profile_current_limit_a=None) -> str:
    """Live lesson text with real numbers from the capability model."""
    lim = cap.compute_permitted_current(pack_voltage_v, profile_current_limit_a)
    lines = ["6060B: 60 A maximum   |   300 W maximum",
             f"Battery: {pack_voltage_v:g} V",
             f"300 / {pack_voltage_v:g} = {cap.INSTRUMENT_POWER_MAX_W / pack_voltage_v:.2f} A",
             f"=> instrument current limit at this voltage = "
             f"{lim.power_limit_a:.2f} A" if lim.power_limit_a else
             "=> outside the 6060B voltage range",
             ""]
    lines += [f"  {k:<42} {v}" for k, v in lim.rows()]
    lines += ["", "Supported pack range (60 A exists only below 5 V — outside every supported pack):"]
    for v, a, final in cap.envelope_table((30, 33, 36, 37, 40, 42, 44)):
        shown = f"{final:5.2f} A" if final > 0 else "BLOCKED (above the OSBAMS voltage ceiling)"
        lines.append(f"  {v:>3} V -> {a:5.2f} A (6060B)   {shown} (OSBAMS permitted)")
    return "\n".join(lines)


if __name__ == "__main__":
    for title, body in LESSONS:
        print(f"\n## {title}\n{body}")
    print("\n## Live lesson\n" + power_limit_lesson(42.0))
