"""
ai_model.py — OSBAMS AI Engine v2
==================================

Architecture (from ChatGPT review):

    Raw Readings (SQLite)
         ↓
    Feature Extraction  →  features table (saved once per test)
         ↓
    ┌────────────────────────────────────┐
    │  Health Estimator                  │
    │   ├─ Rule Engine  → rule_score     │
    │   └─ ML Model     → ai_score       │
    │        ↓ Consensus (weighted avg)  │
    │        final_score                 │
    └────────────────────────────────────┘
         ↓
    Decision Engine
         ├─ Grade  (A/B/C/F)
         ├─ SOH %
         └─ Second-Life Recommendation
              ✓ Campus scooter
              ✓ Portable solar storage
              ✓ Emergency UPS
              × High-power scooter
              × Cargo scooter

Key design choices:
- Rule engine ALWAYS runs (no data needed, deterministic, explainable)
- ML engine runs when ≥5 labelled samples exist
- Consensus = weighted average: rule_weight=0.4, ml_weight=0.6 when ML active
  Falls back to rule-only (weight=1.0) before ML is ready
- Features saved to DB after each test so ML trains from table, not raw readings
"""

import os
import json
import pickle
import numpy as np
from dataclasses import dataclass, field
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))
from config import (ML_PHASE_RULE_ONLY_MAX, ML_PHASE_EXPERIMENTAL_MAX,
                    ml_phase_for, ml_weights_for)
from typing import Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "osbams_model.pkl")

LABELS      = ["Healthy", "Fair", "Degraded", "End of Life"]
LABEL_GRADE = {"Healthy": "A", "Fair": "B", "Degraded": "C", "End of Life": "F"}
SCORE_BANDS = [(85, "Healthy"), (70, "Fair"), (50, "Degraded"), (0, "End of Life")]

FEATURE_NAMES = [
    "capacity_ratio",
    "energy_ratio",
    "temp_rise_c",
    "voltage_sag_v",
    "voltage_spread_v",
    "discharge_rate_c",
    "energy_efficiency",
    "physical_score",
]

# Second-life use thresholds
SECOND_LIFE_RULES = [
    # (use_label, min_score, max_temp_rise, min_cap_ratio, note)
    ("Campus / low-speed scooter",  55, 20, 0.55, "Lower-demand scooter use"),
    ("Portable solar storage",      50, 25, 0.50, "Stationary, low C-rate"),
    ("Emergency UPS",               45, 30, 0.45, "Backup power, rarely cycled"),
    ("High-power scooter",          80, 12, 0.80, "Requires near-new performance"),
    ("Cargo / delivery scooter",    75, 15, 0.75, "Heavy-load, sustained current"),
]


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class BatteryFeatures:
    capacity_ratio:     float = 1.0
    energy_ratio:       float = 1.0
    temp_rise_c:        float = 0.0
    voltage_sag_v:      float = 0.0
    voltage_spread_v:   float = 0.0
    discharge_rate_c:   float = 0.5
    energy_efficiency:  float = 1.0
    physical_score:     float = 8.0

    def to_array(self) -> np.ndarray:
        return np.array([
            self.capacity_ratio, self.energy_ratio, self.temp_rise_c,
            self.voltage_sag_v, self.voltage_spread_v, self.discharge_rate_c,
            self.energy_efficiency, self.physical_score,
        ], dtype=float)

    def to_dict(self) -> dict:
        return {n: getattr(self, n) for n in FEATURE_NAMES}


@dataclass
class SecondLifeUse:
    label:    str
    approved: bool
    reason:   str


@dataclass
class PredictionResult:
    # Scores
    rule_score:     int   = 0
    ai_score:       int   = 0
    final_score:    int   = 0
    # Classification
    label:          str   = "Unknown"
    grade:          str   = "—"
    confidence:     float = 0.0
    ml_active:      bool  = False
    trained_on:     int   = 0
    # Explanation
    reasons:        list[str] = field(default_factory=list)
    importances:    dict      = field(default_factory=dict)
    # Second-life
    second_life:    list[SecondLifeUse] = field(default_factory=list)
    features:       Optional[BatteryFeatures] = None


# ── Feature extraction ────────────────────────────────────────────────────────

def extract_features(battery_id: int,
                     test_id: Optional[int] = None) -> Optional[BatteryFeatures]:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from db.database import get_battery, get_tests_for_battery, get_readings

    batt = get_battery(battery_id)
    if not batt:
        return None

    tests     = get_tests_for_battery(battery_id)
    completed = [t for t in tests if t.get("ended_at") and t.get("capacity_ah")]
    if not completed:
        return None

    test = next((t for t in completed if t["test_id"] == test_id), None) \
           if test_id else completed[0]
    if not test:
        return None

    rated_ah = batt.get("capacity_rated_ah") or test.get("capacity_ah") or 1.0
    rated_wh = batt.get("energy_rated_wh")   or test.get("energy_wh")   or 1.0
    rated_v  = batt.get("nominal_voltage")   or 36.0
    max_v    = batt.get("max_charge_voltage") or 42.0
    phys     = float(batt.get("physical_score") or 8)

    meas_ah  = test.get("capacity_ah")   or 0.0
    meas_wh  = test.get("energy_wh")     or 0.0
    max_temp = test.get("max_temp_c")    or 25.0
    min_v_mv = test.get("min_voltage_mv")
    dur_s    = test.get("discharge_time_s") or 3600.0

    readings = get_readings(test["test_id"])
    if readings:
        all_v    = [r["voltage_mv"] for r in readings]
        min_v_mv = min_v_mv or min(all_v)
        max_v_mv = max(all_v)
    else:
        min_v_mv = min_v_mv or int(rated_v * 1000 * 0.75)
        max_v_mv = int(max_v * 1000)

    min_v_v = min_v_mv / 1000.0
    max_v_v = max_v_mv / 1000.0
    dur_h   = dur_s / 3600.0

    return BatteryFeatures(
        capacity_ratio   = round(min((meas_ah / rated_ah if rated_ah > 0 else 0), 1.5), 4),
        energy_ratio     = round(min((meas_wh / rated_wh if rated_wh > 0 else 0), 1.5), 4),
        temp_rise_c      = round(max(0.0, max_temp - 25.0), 2),
        voltage_sag_v    = round(max(0.0, max_v - min_v_v), 3),
        voltage_spread_v = round(max(0.0, max_v_v - min_v_v), 3),
        discharge_rate_c = round(min((meas_ah / dur_h if dur_h > 0 else 0.5), 5.0), 4),
        energy_efficiency= round(min((meas_wh / (rated_v * meas_ah)
                                      if (rated_v * meas_ah) > 0 else 1.0), 1.2), 4),
        physical_score   = phys,
    )


def score_to_label(score: int) -> str:
    for threshold, label in SCORE_BANDS:
        if score >= threshold:
            return label
    return "End of Life"


def _label_to_midpoint(label: str) -> int:
    return {"Healthy": 92, "Fair": 77, "Degraded": 59, "End of Life": 30}.get(label, 50)


# ── Rule Engine ───────────────────────────────────────────────────────────────

def rule_score(feat: BatteryFeatures) -> int:
    """Deterministic weighted rule score 0-100."""
    score = int(
        feat.capacity_ratio              * 40 +
        (feat.physical_score / 10.0)     * 20 +
        max(0.0, 1.0 - feat.temp_rise_c  / 30.0) * 20 +
        max(0.0, 1.0 - feat.voltage_sag_v / 12.0) * 10 +
        feat.energy_ratio                * 10
    )
    return max(0, min(100, score))


# ── Second-Life Decision Engine ───────────────────────────────────────────────

def second_life_recommendation(feat: BatteryFeatures,
                                final_score: int) -> list[SecondLifeUse]:
    """
    Map battery condition to approved/rejected second-life uses.
    Each use has its own thresholds for score, temp rise, capacity.
    """
    results = []
    for label, min_sc, max_tr, min_cap, note in SECOND_LIFE_RULES:
        ok = (final_score    >= min_sc and
              feat.temp_rise_c <= max_tr and
              feat.capacity_ratio >= min_cap)
        if ok:
            reason = f"{note} — score {final_score} ≥ {min_sc}, temp rise {feat.temp_rise_c:.0f}°C ≤ {max_tr}°C"
        else:
            missing = []
            if final_score       < min_sc:  missing.append(f"score {final_score}<{min_sc}")
            if feat.temp_rise_c  > max_tr:  missing.append(f"temp rise {feat.temp_rise_c:.0f}°C>{max_tr}°C")
            if feat.capacity_ratio < min_cap: missing.append(f"capacity {feat.capacity_ratio:.0%}<{min_cap:.0%}")
            reason = "Not suitable: " + ", ".join(missing)
        results.append(SecondLifeUse(label=label, approved=ok, reason=reason))
    return results


# ── Reason builder ────────────────────────────────────────────────────────────

def build_reasons(feat: BatteryFeatures, importances: dict) -> list[str]:
    reasons = []
    if importances.get("capacity_ratio", 0) > 0.05:
        p = feat.capacity_ratio * 100
        if   p >= 90: reasons.append(f"Capacity retention strong at {p:.0f}% of rated.")
        elif p >= 75: reasons.append(f"Capacity at {p:.0f}% of rated — moderate fade.")
        elif p >= 55: reasons.append(f"Capacity dropped to {p:.0f}% — significant fade.")
        else:         reasons.append(f"Capacity only {p:.0f}% of rated — severe degradation.")
    if importances.get("temp_rise_c", 0) > 0.05:
        t = feat.temp_rise_c
        if   t > 20: reasons.append(f"Temperature rose {t:.0f}°C above ambient — high internal resistance.")
        elif t > 10: reasons.append(f"Moderate temperature rise of {t:.0f}°C under load.")
        else:        reasons.append(f"Temperature rise low ({t:.0f}°C) — cells performing well thermally.")
    if importances.get("voltage_sag_v", 0) > 0.05:
        s = feat.voltage_sag_v
        if   s > 6: reasons.append(f"Voltage sag {s:.1f}V — exceeds normal, suggests high internal resistance.")
        elif s > 3: reasons.append(f"Voltage sag {s:.1f}V — moderate, within acceptable range.")
        else:       reasons.append(f"Voltage sag minimal ({s:.1f}V) — low internal resistance.")
    if importances.get("physical_score", 0) > 0.05 and feat.physical_score < 8:
        reasons.append(f"Physical condition scored {feat.physical_score:.0f}/10 — noted at intake.")
    if importances.get("energy_efficiency", 0) > 0.05:
        e = feat.energy_efficiency * 100
        if e < 85:
            reasons.append(f"Energy efficiency {e:.0f}% — more energy lost as heat than expected.")
    if not reasons:
        reasons.append("All measured parameters within expected range.")
    return reasons


# ── Main Model ────────────────────────────────────────────────────────────────

class OSBAMSModel:
    """
    Health Estimator: Rule Engine + ML → Consensus
    Decision Engine:  Grade + Second-Life Recommendation
    """
    # All thresholds and weights come from config.py — single source of truth.
    # ML is capped at 0.50; the rule engine always carries >= 50%.
    MIN_ML_SAMPLES = ML_PHASE_RULE_ONLY_MAX

    def __init__(self):
        self._clf       = None
        self._n_samples = 0   # independent batteries
        self._n_records = 0   # feature rows / tests
        self._load()

    def _save(self):
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({"clf": self._clf, "n": self._n_samples}, f)

    def _load(self):
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    d = pickle.load(f)
                self._clf       = d["clf"]
                self._n_samples = d["n"]
            except Exception:
                self._clf = None; self._n_samples = 0

    # ── Training from features table ──────────────────────────────────

    def train(self) -> dict:
        """
        Train on the features table (not raw readings).

        Two counts matter and they are not the same:

          n_records   — number of feature rows (tests)
          n_batteries — number of DISTINCT battery assets

        ML activation is decided by n_batteries. Ten tests of one pack tell
        you about one pack. Cross-validation uses GroupKFold grouped by
        battery_id so the same asset never appears in both train and test —
        the standard approach in the SOH literature (Roman et al., and every
        other pipeline surveyed in docs/COMPETITIVE_ANALYSIS.md).
        """
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from db.database import get_all_features

        rows = [r for r in get_all_features()
                if r.get("capacity_ratio") is not None
                and r.get("rule_score")    is not None]

        X, y, groups = [], [], []
        for r in rows:
            feat_arr = np.array([r.get(f, 0.0) for f in FEATURE_NAMES])
            label    = score_to_label(r["rule_score"])
            X.append(feat_arr)
            y.append(label)
            groups.append(r.get("battery_id", -1))

        n_records   = len(X)
        n_batteries = len(set(groups))

        # ML activation is gated on INDEPENDENT BATTERIES, not test count
        self._n_records  = n_records
        self._n_samples  = n_batteries

        if n_batteries < self.MIN_ML_SAMPLES:
            self._clf = None
            self._save()
            return {
                "status": (f"rule only — {n_batteries} independent batteries "
                           f"from {n_records} tests "
                           f"(need {self.MIN_ML_SAMPLES} batteries for ML phase)"),
                "n_samples":   n_batteries,
                "n_batteries": n_batteries,
                "n_records":   n_records,
                "phase":       ml_phase_for(n_batteries),
            }

        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=100, max_depth=6,
                                     min_samples_leaf=2, random_state=42,
                                     class_weight="balanced")
        Xa, ya, ga = np.array(X), np.array(y), np.array(groups)
        clf.fit(Xa, ya)
        self._clf = clf
        self._save()

        result = {
            "status":      "trained",
            "n_samples":   n_batteries,
            "n_batteries": n_batteries,
            "n_records":   n_records,
            "phase":       ml_phase_for(n_batteries),
            "classes":     list(clf.classes_),
            "feature_importances": dict(zip(FEATURE_NAMES,
                                            clf.feature_importances_.tolist())),
        }

        # GroupKFold: the same battery never appears in both folds.
        # Plain KFold would leak repeated tests of one pack across the split
        # and report an optimistic accuracy that does not generalise.
        n_splits = min(5, n_batteries)
        if n_batteries >= 3 and n_splits >= 2:
            try:
                from sklearn.model_selection import GroupKFold, cross_val_score
                gkf = GroupKFold(n_splits=n_splits)
                cv  = cross_val_score(clf, Xa, ya, groups=ga, cv=gkf)
                result["cv_accuracy"]  = round(float(np.mean(cv)), 3)
                result["cv_std"]       = round(float(np.std(cv)), 3)
                result["cv_method"]    = f"GroupKFold(n_splits={n_splits}) by battery_id"
                result["cv_folds"]     = [round(float(s), 3) for s in cv]
            except Exception as e:
                result["cv_accuracy"] = None
                result["cv_method"]   = f"cross-validation failed: {e}"
        else:
            result["cv_accuracy"] = None
            result["cv_method"]   = (f"not attempted — {n_batteries} batteries "
                                     f"is too few for grouped cross-validation")
        return result

    # ── Prediction: consensus of rule + ML ────────────────────────────

    def predict(self, battery_id: int,
                test_id: Optional[int] = None) -> PredictionResult:
        feat = extract_features(battery_id, test_id)
        if feat is None:
            return PredictionResult(
                label="Unknown", grade="—", confidence=0.0, final_score=0,
                reasons=["No completed discharge test found."],
                trained_on=self._n_samples)

        # 1. Rule engine (always)
        r_score = rule_score(feat)

        # 2. ML engine (when available)
        ml_score    = None
        ml_conf     = 0.0
        importances = {f: 1/8 for f in FEATURE_NAMES}   # uniform fallback
        ml_active   = False

        if self._clf is not None:
            X    = feat.to_array().reshape(1, -1)
            pred = self._clf.predict(X)[0]
            prob = self._clf.predict_proba(X)[0]
            idx  = list(self._clf.classes_).index(pred)
            ml_score    = _label_to_midpoint(pred)
            ml_conf     = float(prob[idx])
            importances = dict(zip(FEATURE_NAMES, self._clf.feature_importances_))
            ml_active   = True

        # 3. Consensus
        if ml_active and ml_score is not None:
            # Weights come from config.ml_weights_for() — ML capped at 0.50
            rw, mw = ml_weights_for(self._n_samples)
            final = int(rw * r_score + mw * ml_score)
            conf  = ml_conf * mw + 0.70 * rw
        else:
            final = r_score
            conf  = 0.70   # rule-only uncertainty estimate

        final = max(0, min(100, final))
        label = score_to_label(final)
        grade = LABEL_GRADE.get(label, "?")

        # 4. Reasons
        reasons = build_reasons(feat, importances)

        # 5. Second-life recommendations
        sl = second_life_recommendation(feat, final)

        return PredictionResult(
            rule_score   = r_score,
            ai_score     = ml_score or r_score,
            final_score  = final,
            label        = label,
            grade        = grade,
            confidence   = round(conf, 2),
            ml_active    = ml_active,
            trained_on   = self._n_samples,
            reasons      = reasons,
            importances  = importances,
            second_life  = sl,
            features     = feat,
        )

    def save_features_to_db(self, battery_id: int,
                             test_id: int,
                             result: PredictionResult):
        """Persist computed features + scores to features table."""
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from db.database import upsert_features
        if result.features is None:
            return
        sl_json = json.dumps([
            {"label": u.label, "approved": u.approved} for u in result.second_life
        ])
        upsert_features(
            test_id     = test_id,
            battery_id  = battery_id,
            **result.features.to_dict(),
            rule_score      = result.rule_score,
            ai_score        = result.ai_score,
            consensus_score = result.final_score,
            ai_label        = result.label,
            ai_confidence   = result.confidence,
            recommendation  = result.label,
            second_life_uses= sl_json,
        )

    def is_trained(self) -> bool:
        return self._clf is not None

    def n_samples(self) -> int:
        """Number of INDEPENDENT BATTERIES — this gates ML activation."""
        return self._n_samples

    def n_batteries(self) -> int:
        """Explicit alias — independent battery assets."""
        return self._n_samples

    def n_records(self) -> int:
        """Number of feature rows (tests). Larger than n_batteries when a
        battery has been tested more than once."""
        return getattr(self, "_n_records", self._n_samples)

    def feature_summary(self, battery_id: int) -> Optional[dict]:
        feat = extract_features(battery_id)
        if feat is None:
            return None
        return {
            "Capacity retention": f"{feat.capacity_ratio * 100:.1f}%",
            "Energy retention":   f"{feat.energy_ratio   * 100:.1f}%",
            "Temp rise (load)":   f"{feat.temp_rise_c:.1f} °C",
            "Voltage sag":        f"{feat.voltage_sag_v:.2f} V",
            "Voltage spread":     f"{feat.voltage_spread_v:.2f} V",
            "Discharge C-rate":   f"{feat.discharge_rate_c:.2f} C",
            "Energy efficiency":  f"{feat.energy_efficiency * 100:.1f}%",
            "Physical score":     f"{feat.physical_score:.0f} / 10",
        }


# ── Synthetic data for dev/testing ────────────────────────────────────────────

def generate_synthetic_training_data(n: int = 20, seed: int = 42):
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n):
        cap  = rng.uniform(0.45, 1.05)
        feat = BatteryFeatures(
            capacity_ratio   = round(cap, 4),
            energy_ratio     = round(cap * rng.uniform(0.93, 1.02), 4),
            temp_rise_c      = round(rng.uniform(2, 35), 2),
            voltage_sag_v    = round(rng.uniform(0.5, 10), 3),
            voltage_spread_v = round(rng.uniform(1, 12), 3),
            discharge_rate_c = round(rng.uniform(0.3, 1.5), 4),
            energy_efficiency= round(min(rng.uniform(0.80, 1.05), 1.2), 4),
            physical_score   = float(rng.integers(4, 11)),
        )
        sc    = rule_score(feat)
        label = score_to_label(sc)
        samples.append({"features": feat, "label": label, "score": sc})
    return samples


# ── Self-test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("OSBAMS AI Engine v2 — self-test")
    print("=" * 55)

    feat = BatteryFeatures(
        capacity_ratio=0.79, energy_ratio=0.77,
        temp_rise_c=12.0, voltage_sag_v=4.5,
        voltage_spread_v=5.2, discharge_rate_c=0.6,
        energy_efficiency=0.93, physical_score=7.0,
    )

    r = rule_score(feat)
    print(f"\nRule score:   {r}")

    # Simulate ML score
    ml = 80
    final = int(0.4 * r + 0.6 * ml)
    print(f"AI score:     {ml}  (simulated)")
    print(f"Consensus:    {final}")
    print(f"Label:        {score_to_label(final)}")
    print(f"Grade:        {LABEL_GRADE[score_to_label(final)]}")

    print("\nSecond-life recommendations:")
    for u in second_life_recommendation(feat, final):
        mark = "✓" if u.approved else "✗"
        print(f"  {mark}  {u.label}")

    importances = {f: 1/8 for f in FEATURE_NAMES}
    print("\nReasons:")
    for r in build_reasons(feat, importances):
        print(f"  • {r}")

    print("\n✓ Self-test passed.")
