"""
services/chemistry_profiles.py — Battery Chemistry Profiles

Each chemistry knows:
  - Nominal cell voltage
  - Max charge voltage per cell
  - Cutoff voltage per cell
  - SOC-to-OCV lookup table (for SOC estimation)
  - Safe temperature limits
  - Notes on degradation behavior

Testing profiles use chemistry profiles to set correct voltage thresholds
automatically when a battery is registered with a known chemistry and
cell count (series_count).

Supported:
  NMC   — Lithium Nickel Manganese Cobalt Oxide (most scooters)
  NCA   — Lithium Nickel Cobalt Aluminium Oxide (high-energy)
  LFP   — Lithium Iron Phosphate (safer, longer life)
  LTO   — Lithium Titanate (ultra-safe, fast charge, short life)
  NiMH  — Nickel Metal Hydride (older packs)
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChemistryProfile:
    name:               str
    abbreviation:       str
    nominal_cell_v:     float       # V per cell
    max_cell_v:         float       # V per cell (full charge)
    cutoff_cell_v:      float       # V per cell (empty)
    max_temp_charge_c:  float       # °C — max temp during charging
    max_temp_discharge_c: float     # °C — max temp during discharge
    cycle_life_est:     int         # typical cycle count to 80% SOH
    energy_density_whkg: float      # Wh/kg typical
    description:        str = ""
    degradation_note:   str = ""

    # SOC-to-OCV lookup table: list of (soc_pct, ocv_per_cell_v)
    # Sorted descending SOC (100% → 0%). Linear interpolation used between points.
    soc_ocv_table: list[tuple[float, float]] = field(default_factory=list)

    def pack_max_voltage(self, series: int) -> float:
        return round(self.max_cell_v * series, 1)

    def pack_nominal_voltage(self, series: int) -> float:
        return round(self.nominal_cell_v * series, 1)

    def pack_cutoff_voltage(self, series: int) -> float:
        return round(self.cutoff_cell_v * series, 1)

    def soc_from_ocv(self, ocv_per_cell_v: float) -> Optional[float]:
        """Estimate SOC % from open-circuit voltage using lookup table."""
        if not self.soc_ocv_table:
            return None
        table = sorted(self.soc_ocv_table, key=lambda x: x[0], reverse=True)
        for i in range(len(table) - 1):
            soc_hi, v_hi = table[i]
            soc_lo, v_lo = table[i + 1]
            if v_lo <= ocv_per_cell_v <= v_hi:
                frac = (ocv_per_cell_v - v_lo) / (v_hi - v_lo)
                return round(soc_lo + frac * (soc_hi - soc_lo), 1)
        if ocv_per_cell_v >= table[0][1]:
            return 100.0
        if ocv_per_cell_v <= table[-1][1]:
            return 0.0
        return None


# ── Chemistry registry ────────────────────────────────────────────────────────

CHEMISTRIES: dict[str, ChemistryProfile] = {

    "NMC": ChemistryProfile(
        name                 = "Lithium Nickel Manganese Cobalt Oxide",
        abbreviation         = "NMC",
        nominal_cell_v       = 3.60,
        max_cell_v           = 4.20,
        cutoff_cell_v        = 3.00,
        max_temp_charge_c    = 45.0,
        max_temp_discharge_c = 60.0,
        cycle_life_est       = 500,
        energy_density_whkg  = 200.0,
        description          = "Most common chemistry in electric scooters and e-bikes. "
                               "Good energy density. Moderate safety margin.",
        degradation_note     = "Capacity fade accelerates above 80% SOH if frequently "
                               "charged to 100% or stored hot.",
        soc_ocv_table        = [
            (100, 4.20), (90, 4.10), (80, 4.00), (70, 3.90),
            (60, 3.82), (50, 3.75), (40, 3.70), (30, 3.65),
            (20, 3.58), (10, 3.45), (5, 3.30), (0, 3.00),
        ],
    ),

    "NCA": ChemistryProfile(
        name                 = "Lithium Nickel Cobalt Aluminium Oxide",
        abbreviation         = "NCA",
        nominal_cell_v       = 3.65,
        max_cell_v           = 4.20,
        cutoff_cell_v        = 3.00,
        max_temp_charge_c    = 45.0,
        max_temp_discharge_c = 55.0,
        cycle_life_est       = 500,
        energy_density_whkg  = 220.0,
        description          = "Higher energy density than NMC. Used in high-performance "
                               "packs. Slightly less thermally stable.",
        degradation_note     = "More sensitive to overcharge and high temperature than NMC. "
                               "Temperature monitoring is especially important.",
        soc_ocv_table        = [
            (100, 4.20), (90, 4.12), (80, 4.02), (70, 3.92),
            (60, 3.83), (50, 3.76), (40, 3.70), (30, 3.63),
            (20, 3.55), (10, 3.42), (5, 3.25), (0, 3.00),
        ],
    ),

    "LFP": ChemistryProfile(
        name                 = "Lithium Iron Phosphate",
        abbreviation         = "LFP",
        nominal_cell_v       = 3.20,
        max_cell_v           = 3.65,
        cutoff_cell_v        = 2.50,
        max_temp_charge_c    = 45.0,
        max_temp_discharge_c = 60.0,
        cycle_life_est       = 2000,
        energy_density_whkg  = 130.0,
        description          = "Longest cycle life. Very thermally stable — will not "
                               "enter thermal runaway under most fault conditions. "
                               "Lower energy density than NMC. Flat SOC-OCV curve "
                               "makes SOC estimation from OCV less accurate.",
        degradation_note     = "Very flat discharge curve makes voltage-based SOC "
                               "estimation inaccurate. Rely on coulomb counting. "
                               "Long cycle life — 2000+ cycles typical.",
        soc_ocv_table        = [
            (100, 3.65), (90, 3.38), (80, 3.33), (70, 3.31),
            (60, 3.30), (50, 3.29), (40, 3.28), (30, 3.26),
            (20, 3.22), (10, 3.15), (5, 3.00), (0, 2.50),
        ],
    ),

    "LTO": ChemistryProfile(
        name                 = "Lithium Titanate",
        abbreviation         = "LTO",
        nominal_cell_v       = 2.40,
        max_cell_v           = 2.85,
        cutoff_cell_v        = 1.80,
        max_temp_charge_c    = 55.0,
        max_temp_discharge_c = 55.0,
        cycle_life_est       = 10000,
        energy_density_whkg  = 80.0,
        description          = "Extremely long cycle life (10,000+ cycles). "
                               "Ultra-safe — no lithium plating risk. Supports fast "
                               "charge. Very low energy density. Used in grid storage "
                               "and some transit applications.",
        degradation_note     = "Minimal capacity fade over lifetime. If degraded LTO "
                               "is found, suspect cell imbalance rather than wear.",
        soc_ocv_table        = [
            (100, 2.85), (90, 2.65), (80, 2.56), (70, 2.52),
            (60, 2.50), (50, 2.47), (40, 2.45), (30, 2.43),
            (20, 2.40), (10, 2.30), (5, 2.10), (0, 1.80),
        ],
    ),

    "NiMH": ChemistryProfile(
        name                 = "Nickel Metal Hydride",
        abbreviation         = "NiMH",
        nominal_cell_v       = 1.20,
        max_cell_v           = 1.45,
        cutoff_cell_v        = 1.00,
        max_temp_charge_c    = 45.0,
        max_temp_discharge_c = 50.0,
        cycle_life_est       = 300,
        energy_density_whkg  = 80.0,
        description          = "Older chemistry. Fewer second-life applications — "
                               "included for completeness and legacy pack support.",
        degradation_note     = "Memory effect possible if repeatedly partially discharged. "
                               "High self-discharge rate compared to lithium chemistries.",
        soc_ocv_table        = [
            (100, 1.45), (80, 1.35), (60, 1.30), (40, 1.25),
            (20, 1.20), (10, 1.15), (0, 1.00),
        ],
    ),

    "unknown": ChemistryProfile(
        name                 = "Unknown Chemistry",
        abbreviation         = "?",
        nominal_cell_v       = 3.60,
        max_cell_v           = 4.20,
        cutoff_cell_v        = 3.00,
        max_temp_charge_c    = 45.0,
        max_temp_discharge_c = 50.0,
        cycle_life_est       = 500,
        energy_density_whkg  = 150.0,
        description          = "Chemistry not identified. Using NMC defaults as a "
                               "conservative estimate — verify before testing.",
        degradation_note     = "Apply conservative temperature limits until chemistry "
                               "is confirmed.",
    ),
}


def get_chemistry(abbreviation: str) -> ChemistryProfile:
    """Return chemistry profile, defaulting to 'unknown' if not found."""
    return CHEMISTRIES.get(abbreviation.upper(), CHEMISTRIES["unknown"])


def derive_voltages(chemistry: str, series: int) -> dict:
    """
    Given a chemistry abbreviation and series cell count,
    return the correct pack-level voltage thresholds.

    Used by testing_profiles and the Battery Registration tab
    to auto-fill voltage fields when chemistry + cell count are known.
    """
    chem = get_chemistry(chemistry)
    return {
        "nominal_voltage":    chem.pack_nominal_voltage(series),
        "max_charge_voltage": chem.pack_max_voltage(series),
        "cutoff_voltage":     chem.pack_cutoff_voltage(series),
    }


def estimate_soc_from_ocv(chemistry: str, series: int,
                            pack_ocv_v: float) -> Optional[float]:
    """
    Estimate SOC % from a pack-level OCV measurement.
    Returns None if chemistry has no SOC-OCV table.
    """
    chem = get_chemistry(chemistry)
    if series <= 0:
        return None
    cell_ocv = pack_ocv_v / series
    return chem.soc_from_ocv(cell_ocv)


if __name__ == "__main__":
    print("OSBAMS Chemistry Profiles\n" + "=" * 50)

    for key, chem in CHEMISTRIES.items():
        if key == "unknown":
            continue
        print(f"\n{chem.abbreviation} — {chem.name}")
        print(f"  Cell: {chem.nominal_cell_v}V nominal  "
              f"{chem.max_cell_v}V max  {chem.cutoff_cell_v}V cutoff")

        # 10S pack example
        print(f"  10S pack: {chem.pack_nominal_voltage(10)}V nom  "
              f"{chem.pack_max_voltage(10)}V max  "
              f"{chem.pack_cutoff_voltage(10)}V cutoff")
        print(f"  Cycle life: ~{chem.cycle_life_est}  "
              f"Energy density: {chem.energy_density_whkg} Wh/kg")

        # SOC test
        if chem.soc_ocv_table:
            mid_v = chem.nominal_cell_v
            soc   = chem.soc_from_ocv(mid_v)
            print(f"  SOC at {mid_v}V/cell: ~{soc}%")

    print("\n--- Auto-derive 10S NMC pack voltages ---")
    v = derive_voltages("NMC", 10)
    print(v)

    print("\n--- SOC from OCV: OSB-005 (30.8V pack, 10S NMC) ---")
    soc = estimate_soc_from_ocv("NMC", 10, 30.8)
    print(f"  30.8V → SOC ≈ {soc}%")

    print("\n✓ chemistry_profiles.py self-test passed.")
