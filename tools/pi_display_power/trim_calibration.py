#!/usr/bin/env python3
"""Per-unit trim calibration for RSDW40F-05 (Mean Well trim-up formula, spec p.4).
Usage:  trim_calibration.py V_UNTRIMMED_NOLOAD  V_PI_LOADED_UNTRIMMED  I_LOAD  [V_PI_TARGET=4.85+margin]  [--margin 0.03]
 V_UNTRIMMED_NOLOAD : DC-DC output voltage at the Pi-end connector, R3 not fitted, no load
 V_PI_LOADED_UNTRIMMED : voltage measured AT THE PI-END CONNECTOR/header with I_LOAD drawn, R3 not fitted
Prints the R3 value (TRIM -> -Vout) to fit and the predicted loaded / no-load voltages."""
import sys, math
Vr, R1, R2, R3 = 1.24, 15.47, 5.1, 33.0           # kOhm; 5 V model (spec p.4)
PI_MIN_TARGET, PI_MAX = 4.85, 5.25
def e96(x):
    E = [1.00,1.02,1.05,1.07,1.10,1.13,1.15,1.18,1.21,1.24,1.27,1.30,1.33,1.37,1.40,1.43,1.47,1.50,1.54,1.58,1.62,1.65,1.69,1.74,1.78,1.82,1.87,1.91,1.96,2.00,2.05,2.10,2.15,2.21,2.26,2.32,2.37,2.43,2.49,2.55,2.61,2.67,2.74,2.80,2.87,2.94,3.01,3.09,3.16,3.24,3.32,3.40,3.48,3.57,3.65,3.74,3.83,3.92,4.02,4.12,4.22,4.32,4.42,4.53,4.64,4.75,4.87,4.99,5.11,5.23,5.36,5.49,5.62,5.76,5.90,6.04,6.19,6.34,6.49,6.65,6.81,6.98,7.15,7.32,7.50,7.68,7.87,8.06,8.25,8.45,8.66,8.87,9.09,9.31,9.53,9.76,10.0]
    d = 10 ** math.floor(math.log10(x)); return min((e * d for e in E), key=lambda c: abs(c - x))
def calibrate(v_nl, v_pi, i, target, margin=0.03):
    r_path = (v_nl - v_pi) / i                      # ohm, includes load regulation of the converter
    vref = v_nl / (1 + R1 / R2)                     # this unit's effective reference (nominal 1.24 V)
    need_loaded = max(target + margin, 0)
    dv = need_loaded - v_pi                         # required rise at the Pi
    vo_new = v_nl + dv                              # no-load setpoint after trim
    if dv <= 0: return None
    a = R1 / (vo_new / vref - 1)                    # effective lower divider = R2 || (R3 + Rt)
    if a >= R2: return None
    rt = a * R2 / (R2 - a) - R3
    e = e96(rt)
    a_e = 1 / (1 / R2 + 1 / (R3 + e)); vo_e = vref * (1 + R1 / a_e)
    return dict(r_path_mohm=r_path * 1e3, vo_new=vo_new, rt=rt, rt_e96=e, vo_e96=vo_e, v_pi_loaded=v_pi + (vo_e - v_nl), v_nl_after=vo_e)
if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3: print(__doc__); sys.exit(2)
    v_nl, v_pi, i = map(float, args[:3]); target = float(args[3]) if len(args) > 3 else PI_MIN_TARGET
    r = calibrate(v_nl, v_pi, i, target)
    if r is None: print("No trim needed (or out of +-10 % range): measured loaded voltage already >= target + margin."); sys.exit(0)
    print(f"effective path resistance (incl. load regulation): {r['r_path_mohm']:.1f} mOhm")
    print(f"required no-load setpoint {r['vo_new']:.3f} V  ->  R3 (TRIM to -Vout) = {r['rt']:.1f} kOhm, nearest E96 {r['rt_e96']:.1f} kOhm")
    print(f"predicted with E96 part: no-load {r['v_nl_after']:.3f} V (limit {PI_MAX} V), loaded at Pi {r['v_pi_loaded']:.3f} V (target >= {target} V)")
    ok = r['v_nl_after'] <= PI_MAX and r['v_pi_loaded'] >= target
    print("RESULT:", "ACCEPT (verify by measurement after fitting)" if ok else "REJECT: cannot satisfy both limits - investigate path resistance"); sys.exit(0 if ok else 1)
