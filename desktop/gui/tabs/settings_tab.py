"""Settings → Calibration  and  Validation / Measurement Quality.

Calibration: enter reference-instrument readings against the OSBAMS raw readings (voltage and current points, zero-current
samples), fit gain/offset by least squares, review the residuals, save and activate the profile.  Limits are PROVISIONAL.
Validation panel: shows the active profile and the latest stored test's measurement-quality items.  A quantity that was not
measured is shown as NOT AVAILABLE — never as a pass.
"""
from __future__ import annotations

import json
from datetime import date

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit, QPushButton, QTabWidget,
                               QTableWidget, QTableWidgetItem, QGroupBox, QFormLayout, QMessageBox)

from db.database import get_connection
from services import calibration as cal
from services import calibration_store as store
from services.quality import PASS, REVIEW

NOT_AVAILABLE = "NOT AVAILABLE"


def parse_points(text: str) -> list:
    """'reference, raw' per line (blank/# lines ignored) -> [CalPoint]."""
    pts = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        a, b = [x.strip() for x in ln.replace(";", ",").split(",")[:2]]
        pts.append(cal.CalPoint(float(a), float(b)))
    return pts


def parse_samples(text: str) -> list:
    return [float(x) for x in text.replace(",", " ").split()]


def build_profile(v_text: str, i_text: str, zero_text: str, reference: str, operator: str = "", notes: str = "") -> cal.CalibrationProfile:
    """Pure function behind the Save button (unit-tested): raises CalibrationError on bad input."""
    vfit = cal.fit_linear(parse_points(v_text)) if v_text.strip() else cal.IDENTITY
    ifit = cal.fit_linear(parse_points(i_text)) if i_text.strip() else cal.IDENTITY
    zero = cal.zero_offset(parse_samples(zero_text))[0] if zero_text.strip() else None
    if not (reference or "").strip():
        raise cal.CalibrationError("name the reference instrument (make/model, serial and calibration status as read off it)")
    if vfit is cal.IDENTITY and ifit is cal.IDENTITY and zero is None:
        raise cal.CalibrationError("enter voltage points, current points and/or zero-current samples")
    return cal.CalibrationProfile(calibration_id=cal.make_calibration_id(date.today(), _next_seq()), voltage=vfit, current=ifit,
                                  zero_current_offset_a=zero, reference_instrument=reference.strip(), operator=operator, notes=notes)


def _next_seq() -> int:
    store._ensure()
    conn = get_connection()
    try:
        n = conn.execute("SELECT COUNT(*) FROM calibrations WHERE calibration_id LIKE ?", (f"CAL-{date.today().isoformat()}-%",)).fetchone()[0]
    finally:
        conn.close()
    return n + 1


def quality_rows(quality_json: str | None) -> list:
    """[(item, value, limit, status)] for display; unavailable items -> NOT AVAILABLE."""
    if not quality_json:
        return []
    q = json.loads(quality_json)
    rows = []
    for it in q["items"]:
        val = NOT_AVAILABLE if it["value"] is None else f"{it['value']:.4g} {it['unit']}".strip()
        lim = "" if it["limit"] is None else f"{it['limit']:g} {it['unit']}".strip()
        st = NOT_AVAILABLE if it["ok"] is None else ("OK" if it["ok"] else "OUT OF LIMIT")
        rows.append((it["name"], val, lim, st))
    return rows


class CalibrationPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Calibration against a reference instrument. Limits and the gain bounds are PROVISIONAL until real "
                             "reference data exist. One line per point: reference, raw (V or A)."))
        self.active = QLabel()
        lay.addWidget(self.active)
        box = QGroupBox("New calibration")
        form = QFormLayout(box)
        self.v_pts = QPlainTextEdit(); self.v_pts.setPlaceholderText("# voltage:  reference_V, raw_V\n30.00, 29.95")
        self.i_pts = QPlainTextEdit(); self.i_pts.setPlaceholderText("# current:  reference_A, raw_A\n5.000, 4.98")
        self.zero = QLineEdit(); self.zero.setPlaceholderText("raw current samples with NO current flowing, e.g. 0.002 0.001 0.003")
        self.ref = QLineEdit(); self.ref.setPlaceholderText("reference instrument (make/model; serial & cal status as read off it)")
        self.operator = QLineEdit()
        for lab, w in (("Voltage points", self.v_pts), ("Current points", self.i_pts), ("Zero-current samples", self.zero),
                       ("Reference instrument", self.ref), ("Operator", self.operator)):
            form.addRow(lab, w)
        lay.addWidget(box)
        row = QHBoxLayout()
        self.fit_btn = QPushButton("Fit && preview"); self.save_btn = QPushButton("Save && activate")
        self.fit_btn.clicked.connect(self.preview); self.save_btn.clicked.connect(self.save)
        row.addWidget(self.fit_btn); row.addWidget(self.save_btn); row.addStretch()
        lay.addLayout(row)
        self.out = QPlainTextEdit(); self.out.setReadOnly(True)
        lay.addWidget(self.out)
        self.refresh()

    def refresh(self):
        a = store.get_active()
        self.active.setText("Active profile: NONE (measurements will be marked REVIEW REQUIRED)" if a is None else
                            f"Active profile: {a.calibration_id}   created {a.created}   reference: {a.reference_instrument or NOT_AVAILABLE}")

    def _profile(self):
        return build_profile(self.v_pts.toPlainText(), self.i_pts.toPlainText(), self.zero.text(), self.ref.text(), self.operator.text())

    def preview(self):
        try:
            p = self._profile()
        except (cal.CalibrationError, ValueError) as e:
            self.out.setPlainText(f"ERROR: {e}")
            return None
        lines = [f"Profile {p.calibration_id}"]
        for lab, fit, txt in (("Voltage", p.voltage, self.v_pts.toPlainText()), ("Current", p.current, self.i_pts.toPlainText())):
            if fit.n:
                lines.append(f"{lab}: gain {fit.gain:.6f}, offset {fit.offset:+.6f}, n={fit.n}, RMSE {fit.rmse:.5f}, "
                             f"max residual {fit.max_abs_residual:.5f} ({'n/a' if fit.max_residual_pct is None else f'{fit.max_residual_pct:.3f} %'})")
                for r in cal.residual_table(parse_points(txt), fit):
                    lines.append(f"   ref {r['reference']:.4f}  raw {r['raw']:.4f}  corrected {r['corrected']:.4f}  err {r['error']:+.5f}")
            else:
                lines.append(f"{lab}: {NOT_AVAILABLE} (identity)")
        lines.append("Zero-current offset: " + (NOT_AVAILABLE if p.zero_current_offset_a is None else f"{p.zero_current_offset_a:+.5f} A"))
        self.out.setPlainText("\n".join(lines))
        return p

    def save(self):
        p = self.preview()
        if p is None:
            return
        store.save_calibration(p, activate=True)
        self.refresh()
        self.out.appendPlainText(f"\nSaved and activated {p.calibration_id}.")


class QualityPanel(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)
        self.head = QLabel(); self.head.setStyleSheet("font-weight:bold")
        self.profile = QLabel()
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Item", "Value", "Provisional limit", "Status"])
        btn = QPushButton("Refresh"); btn.clicked.connect(self.refresh)
        for w in (self.head, self.profile, self.table, btn):
            lay.addWidget(w)
        self.refresh()

    def refresh(self):
        a = store.get_active()
        lines = []
        if a is not None:
            lines.append(f"V gain {a.voltage.gain:.5f} / offset {a.voltage.offset:+.5f} V;  I gain {a.current.gain:.5f} / offset "
                         f"{a.current.offset:+.5f} A;  zero offset {NOT_AVAILABLE if a.zero_current_offset_a is None else f'{a.zero_current_offset_a:+.5f} A'}")
        self.profile.setText(f"Active profile: {a.calibration_id if a else 'NONE'}   " + (lines[0] if lines else ""))
        conn = get_connection()
        try:
            r = conn.execute("SELECT test_id, measurement_quality, quality_json FROM tests WHERE quality_json IS NOT NULL "
                             "ORDER BY test_id DESC LIMIT 1").fetchone()
        finally:
            conn.close()
        if r is None:
            self.head.setText(f"Latest test: {NOT_AVAILABLE} (no test with a quality report yet)")
            self.table.setRowCount(0)
            return
        status = r["measurement_quality"] if r["measurement_quality"] in (PASS, REVIEW) else REVIEW
        self.head.setText(f"Latest test #{r['test_id']}: {status}")
        rows = quality_rows(r["quality_json"])
        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, v in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(v))


class SettingsTab(QTabWidget):
    def __init__(self):
        super().__init__()
        self.calibration = CalibrationPanel()
        self.quality = QualityPanel()
        self.addTab(self.calibration, "Calibration")
        self.addTab(self.quality, "Validation / Measurement Quality")
        self.currentChanged.connect(lambda _i: (self.quality.refresh(), self.calibration.refresh()))
