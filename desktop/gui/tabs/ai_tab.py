"""
ai_tab.py — OSBAMS AI Analysis Tab v2

Shows:
  - Model status (rule-only / ML active / consensus)
  - Health Estimator: Rule score | AI score | Consensus score
  - Feature table
  - Why? reasons
  - Feature importance chart
  - Second-Life Recommendation panel
  - Generate PDF Report button
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QGroupBox, QTextEdit,
    QMessageBox, QHeaderView, QFrame, QFileDialog,
    QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QFont, QColor
import pyqtgraph as pg

from gui.ai_model import OSBAMSModel, FEATURE_NAMES
from db.database  import get_all_batteries, get_battery, get_tests_for_battery

LABEL_COLORS = {
    "Healthy":     "#16a34a",
    "Fair":        "#2563eb",
    "Degraded":    "#d97706",
    "End of Life": "#dc2626",
    "Unknown":     "#6b7280",
}


class TrainThread(QThread):
    finished = Signal(dict)
    error    = Signal(str)
    def __init__(self, model):
        super().__init__()
        self._model = model
    def run(self):
        try:    self.finished.emit(self._model.train())
        except Exception as e: self.error.emit(str(e))


class ScoreBox(QFrame):
    """Single score display box (label + big number)."""
    def __init__(self, title: str, color: str = "#2563eb"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame{background:#fff;border:1px solid #e5e7eb;"
            "border-radius:8px;padding:4px;}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8,6,8,6); lay.setSpacing(2)
        self._title = QLabel(title)
        self._title.setStyleSheet("font-size:9px;color:#6b7280;font-weight:bold;")
        self._title.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._title)
        self._val = QLabel("—")
        self._val.setStyleSheet(f"font-size:26px;font-weight:bold;color:{color};")
        self._val.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._val)

    def set_value(self, v: str, color: str = None):
        self._val.setText(v)
        if color:
            self._val.setStyleSheet(
                f"font-size:26px;font-weight:bold;color:{color};")


class AITab(QWidget):
    def __init__(self):
        super().__init__()
        self._model   = OSBAMSModel()
        self._thread  = None
        self._last_result = None
        self._last_battery_id = None
        self._last_test_id    = None
        self._build_ui()
        self._refresh_battery_list()
        self._update_status_bar()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8); root.setContentsMargins(10,10,10,10)

        # ── Top bar ───────────────────────────────────────────────────
        top = QHBoxLayout()
        title = QLabel("📊  Health Estimation Engine  —  Rule Analysis + ML Assistance + Decision Support")
        title.setStyleSheet("font-size:16px;font-weight:bold;")
        top.addWidget(title); top.addStretch()

        self.train_btn = QPushButton("🔄 Update ML Model")
        self.train_btn.setStyleSheet(
            "background:#7c3aed;color:white;font-weight:bold;"
            "padding:5px 12px;border-radius:5px;")
        self.train_btn.clicked.connect(self._train)
        top.addWidget(self.train_btn)

        self.run_btn = QPushButton("▶ Run Analysis")
        self.run_btn.setStyleSheet(
            "background:#2563eb;color:white;font-weight:bold;"
            "padding:5px 12px;border-radius:5px;")
        self.run_btn.clicked.connect(self._run)
        top.addWidget(self.run_btn)

        self.pdf_btn = QPushButton("📄 Export PDF Report")
        self.pdf_btn.setEnabled(False)
        self.pdf_btn.clicked.connect(self._export_pdf)
        top.addWidget(self.pdf_btn)

        root.addLayout(top)

        # ── Status bar ────────────────────────────────────────────────
        self.status_lbl = QLabel("Model status: not loaded")
        self.status_lbl.setStyleSheet(
            "background:#fff3cd;border:1px solid #ffeeba;"
            "border-radius:5px;padding:5px;font-size:11px;")
        root.addWidget(self.status_lbl)

        # ── Battery selector ──────────────────────────────────────────
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("Battery:"))
        self.battery_combo = QComboBox()
        self.battery_combo.setMinimumWidth(250)
        sel_row.addWidget(self.battery_combo)
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(200)
        self.battery_combo.currentIndexChanged.connect(self._on_battery_changed)
        sel_row.addWidget(QLabel("Test:"))
        sel_row.addWidget(self.test_combo)
        sel_row.addStretch()
        root.addLayout(sel_row)

        # ── Score row: Rule | AI | Consensus + label/grade/conf ──────
        scores_box = QGroupBox("Health Estimator")
        sl = QHBoxLayout(scores_box)

        self._s_rule = ScoreBox("RULE ENGINE",  "#6b7280")
        self._s_ai   = ScoreBox("AI MODEL",     "#7c3aed")
        self._s_cons = ScoreBox("CONSENSUS",    "#2563eb")
        for sb in [self._s_rule, self._s_ai, self._s_cons]:
            sl.addWidget(sb)

        sl.addSpacing(16)
        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#e5e7eb;"); sl.addWidget(sep)
        sl.addSpacing(16)

        info_lay = QGridLayout()
        for row, (cap, attr) in enumerate([
            ("Label",      "_lbl_label"),
            ("Grade",      "_lbl_grade"),
            ("Confidence", "_lbl_conf"),
            ("ML active",  "_lbl_ml"),
        ]):
            c = QLabel(cap + ":"); c.setStyleSheet("color:#6b7280;font-size:10px;")
            v = QLabel("—"); v.setStyleSheet("font-weight:bold;font-size:12px;")
            info_lay.addWidget(c, row, 0)
            info_lay.addWidget(v, row, 1)
            setattr(self, attr, v)
        sl.addLayout(info_lay)
        root.addWidget(scores_box)

        # ── Middle: feature table | Why? ──────────────────────────────
        mid = QHBoxLayout(); mid.setSpacing(10)

        feat_box = QGroupBox("Feature Inputs")
        fl = QVBoxLayout(feat_box)
        self.feat_table = QTableWidget(8, 2)
        self.feat_table.setHorizontalHeaderLabels(["Feature", "Value"])
        self.feat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.feat_table.verticalHeader().hide()
        self.feat_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.feat_table.setMaximumHeight(200)
        fl.addWidget(self.feat_table)
        mid.addWidget(feat_box, 2)

        why_box = QGroupBox("Why?  —  Explanation")
        wl = QVBoxLayout(why_box)
        self.why_text = QTextEdit()
        self.why_text.setReadOnly(True)
        self.why_text.setMaximumHeight(200)
        self.why_text.setStyleSheet(
            "font-size:11px;background:#f9fafb;border:none;")
        wl.addWidget(self.why_text)
        mid.addWidget(why_box, 3)

        root.addLayout(mid)

        # ── Second-life panel ─────────────────────────────────────────
        sl_box = QGroupBox("Decision Engine — Second-Life Recommendation")
        sl_lay = QGridLayout(sl_box)
        sl_lay.setSpacing(6)
        self._sl_labels = {}
        uses = ["Campus / low-speed scooter", "Portable solar storage",
                "Emergency UPS", "High-power scooter", "Cargo / delivery scooter"]
        for i, use in enumerate(uses):
            mark = QLabel("◦")
            mark.setStyleSheet("font-size:16px; color:#9ca3af;")
            mark.setAlignment(Qt.AlignCenter)
            name = QLabel(use)
            name.setStyleSheet("font-size:11px;")
            sl_lay.addWidget(mark, i // 3, (i % 3) * 2)
            sl_lay.addWidget(name, i // 3, (i % 3) * 2 + 1)
            self._sl_labels[use] = (mark, name)
        root.addWidget(sl_box)

        # ── Feature importance chart ───────────────────────────────────
        imp_box = QGroupBox("Feature Importances")
        il = QVBoxLayout(imp_box)
        pg.setConfigOption("background", "#fafafa")
        pg.setConfigOption("foreground", "#222")
        self._imp_plot = pg.PlotWidget()
        self._imp_plot.setMaximumHeight(160)
        self._imp_plot.showGrid(x=False, y=True, alpha=0.3)
        self._imp_plot.setLabel("left", "Importance")
        self._imp_plot.setLabel("bottom", "Feature")
        ticks = [[(i, n.replace("_", " ")) for i, n in enumerate(FEATURE_NAMES)]]
        self._imp_plot.getAxis("bottom").setTicks(ticks)
        il.addWidget(self._imp_plot)
        root.addWidget(imp_box)

    # ── Battery / test selectors ──────────────────────────────────────

    def _refresh_battery_list(self):
        self.battery_combo.blockSignals(True)
        self.battery_combo.clear()
        for b in get_all_batteries():
            if not b.get("model"): continue
            oid   = b.get("osbams_id") or f"#{b['battery_id']}"
            label = f"{oid}  {b.get('manufacturer','?')} {b.get('model','')}"
            self.battery_combo.addItem(label, userData=b["battery_id"])
        self.battery_combo.blockSignals(False)
        self._on_battery_changed()

    def _on_battery_changed(self):
        bid = self.battery_combo.currentData()
        self.test_combo.clear()
        if bid is None: return
        tests = [t for t in get_tests_for_battery(bid) if t.get("ended_at")]
        for t in tests:
            date = (t.get("started_at") or "?")[:10]
            cap  = t.get("capacity_ah")
            lbl  = f"Test #{t['test_id']}  {date}  {f'{cap:.2f} Ah' if cap else '—'}"
            self.test_combo.addItem(lbl, userData=t["test_id"])

    def _update_status_bar(self):
        n       = self._model.n_samples()      # independent batteries
        records = self._model.n_records()       # feature rows / tests
        if self._model.is_trained():
            phase = ("Assisted phase (rule 50% + ML 50%)" if n >= 30
                     else "Experimental phase (rule 80% + ML 20%)")
            self.status_lbl.setText(
                f"✅  ML active  ·  {records} tests from {n} independent batteries  ·  "
                f"{phase}  ·  cross-validated with GroupKFold grouped by battery")
            self.status_lbl.setStyleSheet(
                "background:#d4edda;border:1px solid #c3e6cb;"
                "border-radius:5px;padding:5px;font-size:11px;")
        else:
            self.status_lbl.setText(
                f"⚠  Rule-only mode  ·  {records} tests from {n} independent batteries  "
                f"·  ML activates at 10 independent batteries  "
                f"(repeat tests of one pack do not count as independent samples)")
            self.status_lbl.setStyleSheet(
                "background:#fff3cd;border:1px solid #ffeeba;"
                "border-radius:5px;padding:5px;font-size:11px;")

    # ── Training ──────────────────────────────────────────────────────

    def _train(self):
        self.train_btn.setEnabled(False)
        self.train_btn.setText("⏳ Training...")
        self._thread = TrainThread(self._model)
        self._thread.finished.connect(self._on_train_done)
        self._thread.error.connect(self._on_train_error)
        self._thread.start()

    @Slot(dict)
    def _on_train_done(self, result: dict):
        self.train_btn.setEnabled(True)
        self.train_btn.setText("🔄 Train / Retrain")
        self._update_status_bar()
        nb  = result.get("n_batteries", result.get("n_samples", 0))
        nr  = result.get("n_records", nb)
        st  = result.get("status", "")
        cv  = result.get("cv_accuracy")
        cvm = result.get("cv_method", "")
        cvs = result.get("cv_std")

        msg = (f"Training complete.\n\n"
               f"Independent batteries: {nb}\n"
               f"Feature records (tests): {nr}\n"
               f"Phase: {result.get('phase', '?')}\n\n"
               f"Status: {st}")
        if cv is not None:
            msg += f"\n\nCross-validation: {cv:.0%}"
            if cvs is not None:
                msg += f" (SD {cvs:.0%})"
            msg += f"\nMethod: {cvm}"
        elif cvm:
            msg += f"\n\nCross-validation: {cvm}"
        QMessageBox.information(self, "Model Trained", msg)

    @Slot(str)
    def _on_train_error(self, msg: str):
        self.train_btn.setEnabled(True)
        self.train_btn.setText("🔄 Train / Retrain")
        QMessageBox.critical(self, "Training Error", msg)

    # ── Prediction ────────────────────────────────────────────────────

    def _run(self):
        bid = self.battery_combo.currentData()
        tid = self.test_combo.currentData()
        if bid is None:
            QMessageBox.information(self, "No Battery",
                "No batteries with completed tests found.")
            return

        result = self._model.predict(bid, tid)
        self._last_result     = result
        self._last_battery_id = bid
        self._last_test_id    = tid
        self._show_result(bid, result)

        # Save features to DB
        if tid:
            self._model.save_features_to_db(bid, tid, result)

        self.pdf_btn.setEnabled(True)

    def _show_result(self, battery_id: int, result):
        color = LABEL_COLORS.get(result.label, "#6b7280")

        self._s_rule.set_value(str(result.rule_score))
        self._s_ai.set_value(str(result.ai_score),
                             "#7c3aed" if result.ml_active else "#9ca3af")
        self._s_cons.set_value(str(result.final_score), color)

        self._lbl_label.setText(result.label)
        self._lbl_label.setStyleSheet(f"font-weight:bold;font-size:14px;color:{color};")
        self._lbl_grade.setText(result.grade)
        self._lbl_conf.setText(f"{result.confidence:.0%}")
        self._lbl_ml.setText("Yes ✓" if result.ml_active else "No (rule-based)")

        # Feature table
        fs = self._model.feature_summary(battery_id)
        if fs:
            self.feat_table.setRowCount(len(fs))
            for r, (name, val) in enumerate(fs.items()):
                self.feat_table.setItem(r, 0, QTableWidgetItem(name))
                vi = QTableWidgetItem(val)
                vi.setTextAlignment(Qt.AlignCenter)
                self.feat_table.setItem(r, 1, vi)

        # Why?
        self.why_text.setPlainText("\n".join(f"• {r}" for r in result.reasons))

        # Second-life
        sl_map = {u.label: u for u in result.second_life}
        for label, (mark_lbl, name_lbl) in self._sl_labels.items():
            u = sl_map.get(label)
            if u is None:
                mark_lbl.setText("◦")
                mark_lbl.setStyleSheet("font-size:16px;color:#9ca3af;")
            elif u.approved:
                mark_lbl.setText("✓")
                mark_lbl.setStyleSheet("font-size:16px;color:#16a34a;font-weight:bold;")
                name_lbl.setStyleSheet("font-size:11px;color:#16a34a;font-weight:bold;")
            else:
                mark_lbl.setText("✗")
                mark_lbl.setStyleSheet("font-size:16px;color:#dc2626;")
                name_lbl.setStyleSheet("font-size:11px;color:#6b7280;")

        # Importance chart
        self._imp_plot.clear()
        if result.importances:
            vals = [result.importances.get(f, 0.0) for f in FEATURE_NAMES]
            bars = pg.BarGraphItem(x=list(range(len(FEATURE_NAMES))),
                                   height=vals, width=0.6,
                                   brush=color, pen="#ffffff")
            self._imp_plot.addItem(bars)
            self._imp_plot.setXRange(-0.5, len(FEATURE_NAMES) - 0.5)
            self._imp_plot.setYRange(0, max(vals) * 1.3 if any(v > 0 for v in vals) else 1)

    # ── PDF export ────────────────────────────────────────────────────

    def _export_pdf(self):
        if not self._last_result or not self._last_battery_id:
            return
        batt = get_battery(self._last_battery_id)
        oid  = batt.get("osbams_id") or f"B{self._last_battery_id:04d}"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report",
            f"{oid}_report.pdf", "PDF Files (*.pdf)")
        if not path:
            return
        try:
            from gui.pdf_report import generate_pdf
            out = generate_pdf(self._last_battery_id,
                               self._last_test_id, path)
            QMessageBox.information(self, "PDF Saved",
                f"Report saved to:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "PDF Error", str(e))

    # ── Public ────────────────────────────────────────────────────────

    def set_battery(self, battery_id: int):
        self._refresh_battery_list()
        for i in range(self.battery_combo.count()):
            if self.battery_combo.itemData(i) == battery_id:
                self.battery_combo.setCurrentIndex(i)
                break
