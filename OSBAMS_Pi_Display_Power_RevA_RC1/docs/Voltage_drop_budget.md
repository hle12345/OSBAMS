# 5 V distribution voltage-drop budget (RC1.1)

Path: `RSDW40F-05 +VOUT -> PCB copper -> F2 -> J_OUT contacts -> harness -> Pi-end contacts -> Pi 5V pins` and return. 2 contacts paralleled for +5 V and for GND, 16 AWG <=150 mm (x1.2 hot), 2 oz copper from the layout.
Target: **>= 4.85 V at the Pi header at 5 A, worst case** (Pi floor 4.75 V, ceiling 5.25 V); nominal input 5.0-5.1 V.

## Inputs and status (`datasheet_inputs.json`)

| Input | Value | Status | Source |
|---|---|---|---|
| f2_resistance_cold_mohm | 7.7 | owner_cited | Littelfuse 0451008.MRL, 7.7 mOhm DC cold resistance (owner-cited; DigiKey lists active) |
| f2_hot_factor | 1.0 | unverified | Fuse resistance rises when loaded; main table uses cold value as instructed, sensitivity row applies 1.3x (ASSUMED) |
| j_out_contact_max_mohm | 10.0 | owner_cited | Molex Micro-Fit 3.0 family: 10 mOhm max contact resistance (owner-cited) |
| j_out_contact_typ_mohm | 5.24 | owner_cited | Molex wire-to-board test data, ~5.24 mOhm initial in one configuration (owner-cited; includes wire) |
| j_out_rating_a | 8.5 | owner_cited | Molex 43045-0400, 8.5 A max per contact (owner-cited) |
| rsdw_trim_range_pct | 10.0 | owner_cited | RSDW40F-05 output trim +-10 % (owner-cited, RS Components datasheet A700000011914648) |
| rsdw_trim_network | {'Vref': 1.24, 'R1_kohm': 15.47, 'R2_kohm': 5.1, 'R3_kohm': 33.0, 'trim_up': 'resistor from TRIM to -Vout'} | owner_cited | 5 V model trim network (owner-cited). Exact formula/topology of R3 vs R2 NOT given - see Trim_calculation in docs (assumed topology) |
| rsdw_tolerance_pct | 2.0 | unverified | ASSUMED +-2 % setpoint+line+load; need RSDW40F-05 datasheet |
| rsdw_footprint_drawing | False | unverified | Need Mean Well mechanical drawing (body, pin XY, pin dia, drill) |
| pi_end_connector_mpn | None | unverified | NOT SELECTED. Needs exact MPN with published per-contact current + contact resistance (see docs/Pi_end_connector_requirements.md) |
| pi_end_contact_max_mohm | 20.0 | unverified | PLACEHOLDER only - do not rely on it; replace with the selected connector's published value |
| pi_end_contact_typ_mohm | 8.0 | unverified | PLACEHOLDER |
| erc_clean_kicad10 | False | unverified | Run ERC in KiCad 10 locally |

`owner_cited` = given by the project owner with a source; the build environment cannot reach the manufacturer sites, so re-check against the PDFs. **The Pi-end contact value is a placeholder, not a design input** - the Pi-end connector has not been selected.

F2 = 7.7 mOhm cold (as instructed). Hot sensitivity: if F2 runs 1.3x hot in service, the worst-case path gains 2.3 mOhm = 12 mV at 5 A. J_OUT: 10.0 mOhm max / 5.24 typ per contact (max is conservative).

## Results vs the unknown Pi-end contact resistance

| Pi-end contact (mOhm, per contact) | R typ / max (mOhm) | 5 A typ / worst V | 3 A worst V | setpoint for 4.85 V (worst) | no-load max | fits <= 5.25 V |
|---|---|---|---|---|---|---|
| 5 | 20.5 / 27.3 | 4.90 / 4.76 | 4.82 | 5.088 V (+1.8 %) | 5.190 V | yes |
| 10 | 23.5 / 32.3 | 4.88 / 4.74 | 4.80 | 5.114 V (+2.3 %) | 5.216 V | yes |
| 15 | 26.5 / 37.3 | 4.87 / 4.71 | 4.79 | 5.139 V (+2.8 %) | 5.242 V | yes |
| 20 | 29.5 / 42.3 | 4.85 / 4.69 | 4.77 | 5.165 V (+3.3 %) | 5.268 V | NO |

With +-2 % source tolerance (assumed), one setpoint can satisfy both 4.85 V @ 5 A and <= 5.25 V no-load only if worst-case path R <= 38.8 mOhm, i.e. **the Pi-end connector must be <= ~16.5 mOhm per contact** (2 contacts in parallel per rail) with the other terms as above. This is the requirement for the connector selection.

## Trim calculation (ASSUMED topology - do not fit R2/R3 on this basis)

Given: Vref = 1.24 V, R1 = 15.47 k, R2 = 5.1 k, R3 = 33.0 k -> nominal Vout = Vref(1 + R1/R2) = 5.001 V (matches 5 V). Trim-up resistor Rt connects TRIM to -Vout (board pad **R3** = TRIM to PI_GND; pad R2 = TRIM to +VOUT is trim-down and is not needed).
Assumed network: Vout = Vref * (1 + R1 * (1/R2 + 1/(R3 + Rt))), i.e. R3 in series with Rt, both in parallel with R2. The source gave the component values but not this exact topology, so the Rt values below must be confirmed against the Mean Well datasheet formula before any resistor is fitted.

| Setpoint | +% | Rt (R3 DNP pad), calc | nearest E96 | resulting Vout | Vout if Rt +1 % |
|---|---|---|---|---|---|
| 5.05 V | +1.0 % | 361.2 kOhm | 365.0 kOhm | 5.050 V | 5.049 V |
| 5.10 V | +2.0 % | 161.4 kOhm | 162.0 kOhm | 5.100 V | 5.099 V |
| 5.15 V | +3.0 % | 96.0 kOhm | 95.3 kOhm | 5.151 V | 5.150 V |

Check: Rt -> 0 gives 5.58 V (+11.6 %), consistent with a +-10 % trim range under this assumed topology. Setpoint tolerance adds the unknown RSDW tolerance on top; E96 1 % resistors move Vout by only a few mV at these values.

## Still open before RC2

1. Select the Pi-end connector (exact MPN, published per-contact current and contact resistance <= the limit above) - `Pi_end_connector_requirements.md`.
2. RSDW40F-05 setpoint tolerance and the exact trim formula/topology; then pick the setpoint (likely 5.05-5.10 V) and keep R2/R3 DNP until then.
3. RSDW40F-05 mechanical drawing -> U1 footprint.  4. KiCad 10 ERC.  5. Bench voltage at the Pi header under real load.
