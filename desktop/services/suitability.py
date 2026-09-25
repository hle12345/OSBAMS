"""
services/suitability.py — Health / Safety / Suitability Engine

Implements Stage 5 and Stage 6 from the ChatGPT elevation:

Three SEPARATE engineering questions:

    Health      82%     — How much capacity/energy remains?
    Safety      PASS    — Is it safe to use at all?
    Suitability {app}   — What can it actually power?

These are intentionally decoupled:
  - A battery can be Health=A but Safety=Quarantine (cut lead)
  - A battery can be Safety=PASS but Suitability=limited
    (not enough SOH for high-power applications)

Application suitability matrix:
  Each application has threshold requirements for SOH, score,
  voltage sag, temperature rise, and physical condition.
  A battery is rated Suitable / Marginal / Not Suitable per app.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HealthResult:
    """Output of the Health Estimation Engine."""
    soh_ah_pct:     float   = 0.0   # SOH by capacity
    soh_wh_pct:     float   = 0.0   # SOH by energy
    soh_combined:   float   = 0.0   # 0.4×Ah + 0.6×Wh
    rule_score:     int     = 0     # 0-100
    ml_score:       Optional[int] = None
    consensus_score:int     = 0
    grade:          str     = "—"   # A/B/C/D/F
    confidence:     float   = 0.70
    ml_active:      bool    = False
    reasons:        list[str] = field(default_factory=list)


@dataclass
class SafetyResult:
    """Safety is a GATE — independent of health."""
    status:         str     = "Unknown"  # PASS / HOLD / QUARANTINE / FAIL
    blocks_testing: bool    = True
    reasons:        list[str] = field(default_factory=list)
    operator_notes: str     = ""

    @property
    def passes(self) -> bool:
        return self.status == "PASS"

    @property
    def color(self) -> str:
        return {
            "PASS":       "#16a34a",
            "HOLD":       "#d97706",
            "QUARANTINE": "#dc2626",
            "FAIL":       "#7f1d1d",
            "Unknown":    "#6b7280",
        }.get(self.status, "#6b7280")


@dataclass
class ApplicationSuitability:
    """Can this battery power a specific application?"""
    application:    str
    verdict:        str     = "Unknown"   # Suitable / Marginal / Not Suitable
    confidence_pct: int     = 0
    reason:         str     = ""
    expected_runtime_h: Optional[float] = None
    risk_level:     str     = "Unknown"   # Low / Medium / High

    @property
    def color(self) -> str:
        return {
            "Suitable":     "#16a34a",
            "Marginal":     "#d97706",
            "Not Suitable": "#dc2626",
            "Unknown":      "#6b7280",
        }.get(self.verdict, "#6b7280")


@dataclass
class SuitabilityResult:
    """Full suitability assessment across all applications."""
    applications: list[ApplicationSuitability] = field(default_factory=list)
    top_recommendation: str = "—"
    top_confidence: int = 0

    @property
    def suitable(self) -> list[ApplicationSuitability]:
        return [a for a in self.applications if a.verdict == "Suitable"]

    @property
    def marginal(self) -> list[ApplicationSuitability]:
        return [a for a in self.applications if a.verdict == "Marginal"]

    @property
    def not_suitable(self) -> list[ApplicationSuitability]:
        return [a for a in self.applications if a.verdict == "Not Suitable"]


# ── Application definitions ───────────────────────────────────────────────────
# Each entry: (display_name, min_score, min_soh, max_temp_rise, max_v_sag_v, typical_current_a)

APPLICATIONS = [
    ("Electric scooter — high performance", 82, 80, 12, 3.0,  5.0),
    ("Electric scooter — standard",         68, 68, 16, 4.5,  3.0),
    ("E-bike — standard",                   75, 75, 14, 3.5,  5.0),
    ("Portable solar storage",              55, 55, 25, 6.0,  2.0),
    ("UPS / emergency backup",              60, 60, 20, 5.0,  1.0),
    ("Robot / mobility device",             70, 70, 15, 3.5,  4.0),
    ("Educational / laboratory use",        45, 45, 30, 8.0,  2.0),
    ("Parts recovery",                      20, 20, 40, 12.0, 1.0),
]


# ── Safety evaluation ─────────────────────────────────────────────────────────

def evaluate_safety(battery_record: dict) -> SafetyResult:
    """
    Determine safety status from the battery intake record.
    Safety is a gate — it is evaluated BEFORE health, independent of capacity.
    """
    status_field = (battery_record.get("safety_status") or "Unknown").lower()
    notes        = battery_record.get("physical_notes") or ""
    connector    = (battery_record.get("connector_condition") or "").lower()
    physical     = (battery_record.get("physical_condition") or "").lower()
    bms          = (battery_record.get("bms_led_status") or "").lower()
    ocv          = battery_record.get("initial_ocv_v")
    max_v        = battery_record.get("max_charge_voltage") or 42.0

    reasons = []
    blocks  = False
    status  = "PASS"

    # Explicit quarantine / safety hold
    if "quarantine" in status_field:
        status = "QUARANTINE"
        blocks = True
        reasons.append("Battery is marked Quarantine. Resolve safety issue before any use.")

    elif "hold" in status_field or "verify" in status_field:
        status = "HOLD"
        blocks = True
        reasons.append("Battery is on hold pending verification.")

    elif "unsafe" in status_field or "recycle" in status_field:
        status = "FAIL"
        blocks = True
        reasons.append("Battery marked Unsafe — recycle or engineering review required.")

    else:
        # Check physical signals
        if any(w in physical for w in ["swollen", "swell", "bloat", "puffed"]):
            status = "QUARANTINE"
            blocks = True
            reasons.append("Pack appears swollen — thermal runaway risk.")

        if any(w in physical for w in ["burn", "scorch", "melt", "char"]):
            status = "QUARANTINE"
            blocks = True
            reasons.append("Burn or scorch marks visible.")

        if any(w in notes.lower() for w in ["cut", "severed", "broken lead"]):
            if status == "PASS":
                status = "HOLD"
                blocks = True
            reasons.append("Damaged or cut lead — repair required before testing.")

        if any(w in connector for w in ["cut", "damaged", "missing", "exposed"]):
            if status == "PASS":
                status = "HOLD"
                blocks = True
            reasons.append("Connector damage — inspect and repair before connecting.")

        # OCV anomaly
        if ocv and max_v and ocv > max_v * 1.02:
            if status == "PASS":
                status = "HOLD"
                blocks = True
            reasons.append(
                f"Initial OCV {ocv:.1f}V exceeds rated max {max_v:.1f}V — verify measurement.")

    if status == "PASS" and not reasons:
        reasons.append("No safety concerns identified at intake inspection.")

    return SafetyResult(
        status        = status,
        blocks_testing= blocks,
        reasons       = reasons,
        operator_notes= notes,
    )


# ── Suitability evaluation ────────────────────────────────────────────────────

def evaluate_suitability(health: HealthResult,
                          safety: SafetyResult,
                          temp_rise_c: float = 0.0,
                          voltage_sag_v: float = 0.0,
                          rated_ah: float = 10.0) -> SuitabilityResult:
    """
    Map battery health + safety → per-application suitability.
    Safety failure makes ALL applications Not Suitable.
    """
    apps = []

    for app_name, min_score, min_soh, max_tr, max_sag, curr_a in APPLICATIONS:
        if not safety.passes:
            apps.append(ApplicationSuitability(
                application  = app_name,
                verdict      = "Not Suitable",
                confidence_pct = 95,
                reason       = f"Safety gate: {safety.status}",
                risk_level   = "High",
            ))
            continue

        score = health.consensus_score
        soh   = health.soh_combined

        # Compute margins
        score_margin = score - min_score
        soh_margin   = soh   - min_soh
        temp_margin  = max_tr  - temp_rise_c
        sag_margin   = max_sag - voltage_sag_v

        # All must pass for "Suitable"
        all_pass = (score >= min_score and soh >= min_soh and
                    temp_rise_c <= max_tr and voltage_sag_v <= max_sag)

        # Any within 10% of threshold → "Marginal"
        marginal = (score >= min_score * 0.90 and soh >= min_soh * 0.90 and
                    temp_rise_c <= max_tr * 1.15 and voltage_sag_v <= max_sag * 1.15)

        if all_pass:
            verdict = "Suitable"
            conf    = min(95, 70 + int(min(score_margin, soh_margin) * 0.5))
            risk    = "Low" if score >= min_score + 10 else "Medium"
        elif marginal:
            verdict = "Marginal"
            conf    = 65
            risk    = "Medium"
        else:
            verdict = "Not Suitable"
            conf    = 80
            risk    = "High" if score < min_score * 0.75 else "Medium"

        # Reasons
        reasons = []
        if score_margin < 0:
            reasons.append(f"Score {score} below minimum {min_score}")
        if soh_margin < 0:
            reasons.append(f"SOH {soh:.0f}% below minimum {min_soh}%")
        if temp_rise_c > max_tr:
            reasons.append(f"Temperature rise {temp_rise_c:.0f}°C exceeds limit {max_tr}°C")
        if voltage_sag_v > max_sag:
            reasons.append(f"Voltage sag {voltage_sag_v:.1f}V exceeds limit {max_sag}V")
        if not reasons:
            reasons.append("All parameters meet requirements")

        # Estimated runtime
        runtime = None
        if soh > 0 and rated_ah > 0:
            runtime = round((rated_ah * soh / 100.0) / curr_a, 1) if curr_a > 0 else None

        apps.append(ApplicationSuitability(
            application        = app_name,
            verdict            = verdict,
            confidence_pct     = conf,
            reason             = " · ".join(reasons),
            expected_runtime_h = runtime,
            risk_level         = risk,
        ))

    # Top recommendation
    suitable = [a for a in apps if a.verdict == "Suitable"]
    top = suitable[0] if suitable else next(
        (a for a in apps if a.verdict == "Marginal"), None)

    return SuitabilityResult(
        applications      = apps,
        top_recommendation= top.application if top else "Engineering review required",
        top_confidence    = top.confidence_pct if top else 0,
    )


# ── Full lifecycle assessment ──────────────────────────────────────────────────

def full_assessment(battery_record: dict,
                    health: HealthResult,
                    temp_rise_c: float = 0.0,
                    voltage_sag_v: float = 0.0) -> tuple[SafetyResult, SuitabilityResult]:
    """
    Entry point: returns (SafetyResult, SuitabilityResult) together.
    Health is passed in (already computed by the scoring + AI pipeline).
    """
    safety      = evaluate_safety(battery_record)
    rated_ah    = battery_record.get("capacity_rated_ah") or 10.0
    suitability = evaluate_suitability(health, safety, temp_rise_c,
                                        voltage_sag_v, rated_ah)
    return safety, suitability


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Suitability Engine Self-Test ===\n")

    # OSB-005 style: decent pack, bottom open
    batt = {
        "safety_status":      "Pending - Inspect",
        "physical_condition": "Bottom cover open",
        "connector_condition":"XT60 intact",
        "initial_ocv_v":      30.8,
        "max_charge_voltage": 42.0,
        "physical_notes":     "Bottom cover open — inspect before testing.",
        "capacity_rated_ah":  15.3,
    }
    health = HealthResult(
        soh_ah_pct=76.0, soh_wh_pct=74.0, soh_combined=74.8,
        rule_score=69, consensus_score=69, grade="C",
    )

    safety, suitability = full_assessment(batt, health, temp_rise_c=10.0, voltage_sag_v=2.8)

    print(f"Safety: {safety.status}")
    for r in safety.reasons: print(f"  - {r}")

    print(f"\nTop recommendation: {suitability.top_recommendation}")
    print(f"\nApplication suitability:")
    for a in suitability.applications:
        mark = "✓" if a.verdict == "Suitable" else ("~" if a.verdict == "Marginal" else "✗")
        rt = f"  ~{a.expected_runtime_h}h" if a.expected_runtime_h else ""
        print(f"  {mark} {a.application:<40} {a.verdict:<15} {a.risk_level}{rt}")

    print("\n--- OSB-007 (cut lead, quarantine) ---")
    batt2 = {
        "safety_status": "Quarantine",
        "physical_notes": "Red lead cut near XT60",
        "connector_condition": "cut",
        "capacity_rated_ah": 15.3,
    }
    health2 = HealthResult(soh_combined=80.0, consensus_score=75, grade="B")
    safety2, suit2 = full_assessment(batt2, health2)
    print(f"Safety: {safety2.status}  blocks_testing={safety2.blocks_testing}")
    suitable_count = len([a for a in suit2.applications if a.verdict == "Suitable"])
    print(f"Suitable applications: {suitable_count} (expected 0 — safety blocks all)")

    print("\n✓ Self-test passed.")
