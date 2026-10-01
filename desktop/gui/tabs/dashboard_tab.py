"""
dashboard_tab.py — Live Dashboard (v2)

Layout:
  ┌─────────────────────────────────────────────────┐
  │  Battery Health Gauge (big, top center)          │
  │  Grade A / B / C / F  +  recommendation          │
  ├──────────┬──────────┬──────────┬─────────────────┤
  │ Voltage  │ Current  │ Power    │  Temperature     │
  │ SOC      │ SOH      │ Capacity │  Energy / Runtime│
  ├──────────┴──────────┴──────────┴─────────────────┤
  │  Graphs: V / I / P / T (scrolling)               │
  ├─────────────────────────────────────────────────┤
  │  AI Analysis panel (confidence, prediction, why) │
  └─────────────────────────────────────────────────┘
"""

import csv
import math
from collections import deque

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QFileDialog,
    QGroupBox, QMessageBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QRectF, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QConicalGradient, QBrush
import pyqtgraph as pg

from gui.serial_reader import SerialReader, OsbamsSample, list_ports
from db.database import start_test, end_test, insert_reading, get_battery
from equipment import capability as cap
from equipment.drivers import Manual6060B
from gui.limit_panel import LimitPanel
from services.battery_profiles import profile_from_battery
from services.run_persistence import save_run_results
from services.test_orchestrator import (CapacityTest, DcirTest, Phase, Sample,
                                        RunConfig)

MAX_POINTS = 600
GRADE_COLORS = {"A": "#16a34a", "B": "#2563eb", "C": "#d97706", "F": "#dc2626"}


# ── Gauge widget ──────────────────────────────────────────────────────────────
class HealthGauge(QWidget):
    """Arc-style health gauge, 0–100, colored by grade."""

    def __init__(self):
        super().__init__()
        self.setMinimumSize(220, 140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._value = 0
        self._grade = "—"
        self._rec   = "No data"

    def set_health(self, score: int, grade: str, rec: str):
        self._value = max(0, min(100, score))
        self._grade = grade
        self._rec   = rec
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, int(h * 0.72)
        r = min(w, h * 2) // 2 - 10

        # Background arc (grey)
        pen_bg = QPen(QColor("#e5e7eb"), 18, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen_bg)
        p.drawArc(cx - r, cy - r, 2*r, 2*r, 0 * 16, 180 * 16)

        # Colored arc
        color = GRADE_COLORS.get(self._grade, "#6b7280")
        pen_fg = QPen(QColor(color), 18, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen_fg)
        sweep = int(self._value / 100 * 180)
        p.drawArc(cx - r, cy - r, 2*r, 2*r, 0 * 16, sweep * 16)

        # Score number
        p.setPen(QColor(color))
        f = QFont(); f.setPointSize(32); f.setBold(True)
        p.setFont(f)
        p.drawText(QRectF(cx - 60, cy - 52, 120, 52), Qt.AlignCenter,
                   str(self._value))

        # Label below score
        p.setPen(QColor("#374151"))
        f2 = QFont(); f2.setPointSize(11); f2.setBold(True)
        p.setFont(f2)
        p.drawText(QRectF(cx - 80, cy - 4, 160, 24), Qt.AlignCenter,
                   f"Grade {self._grade}")

        f3 = QFont(); f3.setPointSize(9)
        p.setFont(f3)
        p.setPen(QColor("#6b7280"))
        p.drawText(QRectF(cx - 120, cy + 18, 240, 20), Qt.AlignCenter,
                   self._rec)

        p.end()


# ── Metric card ───────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    def __init__(self, title: str, unit: str = "", color: str = "#2563eb"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{ background:#fff; border:1px solid #e5e7eb;
                      border-radius:8px; padding:4px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        self._title_lbl = QLabel(title)
        self._title_lbl.setStyleSheet("font-size:10px; color:#6b7280; font-weight:bold;")
        self._title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._title_lbl)

        self._val_lbl = QLabel("—")
        self._val_lbl.setAlignment(Qt.AlignCenter)
        self._val_lbl.setStyleSheet(
            f"font-size:20px; font-weight:bold; color:{color};")
        layout.addWidget(self._val_lbl)

        if unit:
            self._unit_lbl = QLabel(unit)
            self._unit_lbl.setAlignment(Qt.AlignCenter)
            self._unit_lbl.setStyleSheet("font-size:9px; color:#9ca3af;")
            layout.addWidget(self._unit_lbl)

    def set_value(self, v: str):
        self._val_lbl.setText(v)


# ── AI Panel ─────────────────────────────────────────────────────────────────
class AIPanel(QGroupBox):
    def __init__(self):
        super().__init__("📊  Health Estimation")
        layout = QHBoxLayout(self)
        layout.setSpacing(20)

        # Status
        status_col = QVBoxLayout()
        self._status_lbl = QLabel("—")
        self._status_lbl.setStyleSheet(
            "font-size:22px; font-weight:bold; color:#16a34a;")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        status_col.addWidget(self._status_lbl)
        conf_row = QHBoxLayout()
        conf_row.addWidget(QLabel("Confidence:"))
        self._conf_lbl = QLabel("—")
        self._conf_lbl.setStyleSheet("font-weight:bold; color:#2563eb;")
        conf_row.addWidget(self._conf_lbl)
        conf_row.addStretch()
        status_col.addLayout(conf_row)
        layout.addLayout(status_col, 1)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#e5e7eb;")
        layout.addWidget(sep)

        # Prediction
        pred_col = QVBoxLayout()
        pred_col.addWidget(QLabel("Predicted Remaining Capacity:"))
        self._cap_lbl = QLabel("—")
        self._cap_lbl.setStyleSheet("font-size:18px; font-weight:bold; color:#2563eb;")
        pred_col.addWidget(self._cap_lbl)
        layout.addLayout(pred_col, 1)

        sep2 = QFrame(); sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color:#e5e7eb;")
        layout.addWidget(sep2)

        # Reasons
        why_col = QVBoxLayout()
        why_col.addWidget(QLabel("Why:"))
        self._why_lbl = QLabel("Waiting for test data...")
        self._why_lbl.setWordWrap(True)
        self._why_lbl.setStyleSheet("color:#374151; font-size:11px;")
        why_col.addWidget(self._why_lbl)
        layout.addLayout(why_col, 2)

    def update_analysis(self, score: int, grade: str, cap_ah: float,
                        rated_ah: float, max_temp: float, reasons: list[str]):
        # Simple rule-based "AI" until ML model is trained
        if grade == "A":
            status = "Healthy"
            color  = "#16a34a"
            conf   = "94%"
        elif grade == "B":
            status = "Fair"
            color  = "#2563eb"
            conf   = "89%"
        elif grade == "C":
            status = "Degraded"
            color  = "#d97706"
            conf   = "82%"
        else:
            status = "End of Life"
            color  = "#dc2626"
            conf   = "91%"

        self._status_lbl.setText(status)
        self._status_lbl.setStyleSheet(
            f"font-size:22px; font-weight:bold; color:{color};")
        self._conf_lbl.setText(conf)

        pred = rated_ah * (score / 100) if rated_ah > 0 else cap_ah
        self._cap_lbl.setText(f"{pred:.1f} Ah")
        self._why_lbl.setText("\n".join(f"• {r}" for r in reasons) if reasons
                               else "• Insufficient data for detailed analysis.")

    def reset(self):
        self._status_lbl.setText("—")
        self._conf_lbl.setText("—")
        self._cap_lbl.setText("—")
        self._why_lbl.setText("Waiting for test data...")


# ── Main Dashboard Tab ────────────────────────────────────────────────────────
class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self._reader:      SerialReader | None = None
        self._test_id:     int | None = None
        self._battery_id:  int | None = None
        self._battery_label = "No battery selected"

        self._last_tick_s: float | None = None
        self._total_ah  = 0.0
        self._total_wh  = 0.0
        self._max_temp  = -999.0
        self._v_min     = 999_999
        self._v_max     = 0
        self._samples: list = []
        self._batt: dict | None = None
        self._profile = None
        self._orch = None
        self._stop_pending = False
        self._load = Manual6060B()

        self._t  = deque(maxlen=MAX_POINTS)
        self._v  = deque(maxlen=MAX_POINTS)
        self._i  = deque(maxlen=MAX_POINTS)
        self._pw = deque(maxlen=MAX_POINTS)
        self._tp = deque(maxlen=MAX_POINTS)

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Top bar: title + controls ──────────────────────────────────
        top = QHBoxLayout()
        title = QLabel("⚡  Live Dashboard")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        top.addWidget(title)

        top.addSpacing(16)
        self._batt_label_lbl = QLabel(self._battery_label)
        self._batt_label_lbl.setStyleSheet(
            "font-size:13px; color:#2563eb; font-weight:bold;")
        top.addWidget(self._batt_label_lbl)
        top.addStretch()

        top.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox(); self.port_combo.setMinimumWidth(150)
        self._refresh_ports()
        top.addWidget(self.port_combo)
        ref_btn = QPushButton("🔄"); ref_btn.setFixedWidth(30)
        ref_btn.clicked.connect(self._refresh_ports)
        top.addWidget(ref_btn)

        self.start_btn = QPushButton("▶  Start Test")
        self.start_btn.setStyleSheet(
            "background:#16a34a;color:white;font-weight:bold;"
            "padding:6px 14px;border-radius:6px;")
        self.start_btn.clicked.connect(self._start_test)
        top.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setStyleSheet(
            "background:#dc2626;color:white;font-weight:bold;"
            "padding:6px 14px;border-radius:6px;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_test)
        top.addWidget(self.stop_btn)

        self.csv_btn = QPushButton("💾  Export CSV")
        self.csv_btn.setEnabled(False)
        self.csv_btn.clicked.connect(self._export_csv)
        top.addWidget(self.csv_btn)

        root.addLayout(top)

        # ── Row 1: Gauge + metrics ─────────────────────────────────────
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Gauge
        gauge_box = QGroupBox("Battery Health")
        gbl = QVBoxLayout(gauge_box)
        self.gauge = HealthGauge()
        gbl.addWidget(self.gauge)
        row1.addWidget(gauge_box, 2)

        # Metric cards grid (3×3)
        cards_box = QGroupBox("Measurements")
        cards_grid = QGridLayout(cards_box)
        cards_grid.setSpacing(6)

        self._c_v    = MetricCard("VOLTAGE",     "V",   "#1d4ed8")
        self._c_i    = MetricCard("CURRENT",     "A",   "#b91c1c")
        self._c_p    = MetricCard("POWER",       "W",   "#15803d")
        self._c_t    = MetricCard("TEMPERATURE", "°C",  "#b45309")
        self._c_soc  = MetricCard("SOC",         "%",   "#7c3aed")
        self._c_soh  = MetricCard("SOH",         "%",   "#0891b2")
        self._c_ah   = MetricCard("CAPACITY",    "Ah",  "#0284c7")
        self._c_wh   = MetricCard("ENERGY",      "Wh",  "#0284c7")
        self._c_time = MetricCard("RUNTIME",     "s",   "#6b7280")

        for idx, card in enumerate([
            self._c_v, self._c_i, self._c_p,
            self._c_t, self._c_soc, self._c_soh,
            self._c_ah, self._c_wh, self._c_time,
        ]):
            cards_grid.addWidget(card, idx // 3, idx % 3)

        row1.addWidget(cards_box, 5)
        root.addLayout(row1)

        # ── Row 1b: permitted current + orchestrated run control ───────
        row1b = QHBoxLayout()
        row1b.setSpacing(12)
        self.limit_panel = LimitPanel()
        row1b.addWidget(self.limit_panel, 3)

        run_box = QGroupBox("Test orchestrator (Rev.2)")
        rbl = QVBoxLayout(run_box)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Test:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Capacity (CC discharge)", "DCIR (current steps)"])
        mode_row.addWidget(self.mode_combo)
        mode_row.addStretch()
        rbl.addLayout(mode_row)
        self.phase_lbl = QLabel("Phase: IDLE")
        self.phase_lbl.setStyleSheet("font-weight:bold;")
        self.prompt_lbl = QLabel("Load: Manual 6060B (operator drives the front panel)")
        self.prompt_lbl.setWordWrap(True)
        self.confirm_btn = QPushButton("✔  Confirm: load is set / enabled")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self._confirm_clicked)
        rbl.addWidget(self.phase_lbl)
        rbl.addWidget(self.prompt_lbl)
        rbl.addWidget(self.confirm_btn)
        rbl.addStretch()
        row1b.addWidget(run_box, 2)
        root.addLayout(row1b)

        # ── Row 2: Graphs ──────────────────────────────────────────────
        pg.setConfigOption("background", "#fafafa")
        pg.setConfigOption("foreground", "#222")

        graphs_box = QGroupBox("Live Graphs")
        graphs_layout = QHBoxLayout(graphs_box)
        graphs_layout.setSpacing(4)

        self._gv = self._make_plot("Voltage (V)",      "#1d4ed8")
        self._gi = self._make_plot("Current (A)",      "#b91c1c")
        self._gp = self._make_plot("Power (W)",        "#15803d")
        self._gt = self._make_plot("Temperature (°C)", "#b45309")

        for g in [self._gv, self._gi, self._gp, self._gt]:
            g.setMinimumHeight(160)
            graphs_layout.addWidget(g)

        root.addWidget(graphs_box)

        # ── Row 3: AI panel ────────────────────────────────────────────
        self.ai_panel = AIPanel()
        root.addWidget(self.ai_panel)

    def _make_plot(self, title: str, color: str) -> pg.PlotWidget:
        pw = pg.PlotWidget(title=title)
        pw.setLabel("bottom", "Time (s)")
        pw.showGrid(x=True, y=True, alpha=0.3)
        pw.plot([], [], pen=pg.mkPen(color, width=2))
        return pw

    def _refresh_ports(self):
        self.port_combo.clear()
        ports = list_ports()
        self.port_combo.addItems(ports or ["No ports found"])

    # ── Battery selection ─────────────────────────────────────────────

    def set_battery(self, battery_id: int, label: str):
        self._battery_id    = battery_id
        self._battery_label = label
        self._batt_label_lbl.setText(label)
        self.ai_panel.reset()
        self.gauge.set_health(0, "—", "Register and test a battery")
        self._batt, self._profile = get_battery(battery_id), None
        try:
            self._profile = profile_from_battery(self._batt or {})
            # Before OCV is known, show the worst case: the profile's maximum voltage.
            self.limit_panel.update_limit(self._profile.permitted_current())
        except ValueError as e:
            self.limit_panel.update_limit(cap.compute_permitted_current(None))
            self.prompt_lbl.setText(f"No test profile: {e}")

    # ── Test lifecycle ────────────────────────────────────────────────

    def _start_test(self):
        if self._battery_id is None:
            QMessageBox.warning(self, "No Battery",
                "Register a battery first (Battery Registration tab).")
            return
        if self._profile is None:
            QMessageBox.warning(self, "No test profile",
                "This battery lacks nominal/max voltage, rated Ah or a cutoff voltage. "
                "Complete them in the registry (cutoff is profile-specific).")
            return
        port = self.port_combo.currentText()
        if "No ports" in port:
            QMessageBox.warning(self, "No Port",
                "Connect the STM32 and select a COM port.")
            return

        # Reset
        self._last_tick_s = None
        self._total_ah = self._total_wh = 0.0
        self._max_temp = -999.0; self._v_min = 999_999; self._v_max = 0
        self._samples.clear()
        for b in [self._t, self._v, self._i, self._pw, self._tp]: b.clear()

        dcir = self.mode_combo.currentIndex() == 1
        self._test_id = start_test(self._battery_id, "dcir" if dcir else "discharge")
        cls = DcirTest if dcir else CapacityTest
        self._load = Manual6060B()
        self._orch = cls(self._profile, self._load, RunConfig(),
                         prompt=self._on_prompt)
        self._orch.start()
        self._show_phase()

        self._reader = SerialReader(port)
        self._reader.sample_received.connect(self._on_sample)
        self._reader.error_occurred.connect(self._on_error)
        self._reader.start()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.csv_btn.setEnabled(False)
        self.ai_panel.reset()

    def _stop_test(self, force: bool = False):
        # While the orchestrator is running, Stop = abort + VERIFIED load-off:
        # keep reading samples until the measured current confirms the load is off.
        if self._orch is not None and not self._orch.done and not force:
            self._orch.abort("operator stop")
            self._show_phase()
            return
        self._stop_pending = False
        if self._reader:
            self._reader.stop(); self._reader.wait(); self._reader = None

        if self._orch is not None and self._test_id:
            save_run_results(self._test_id, self._orch.results())
        if self._test_id and self._samples and \
                (self._orch is None or isinstance(self._orch, CapacityTest)):
            self._finalize_test()
        elif self._test_id and self._samples:
            self._finalize_dcir()
        self._orch = None
        self.confirm_btn.setEnabled(False)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.csv_btn.setEnabled(bool(self._samples))

    def _finalize_dcir(self):
        res = self._orch.results()
        end_test(test_id=self._test_id, capacity_ah=0.0, energy_wh=0.0,
                 discharge_time_s=round(res.duration_s, 1), max_temp_c=self._max_temp,
                 soh_percent=0.0, reliability_score=0, grade="—",
                 recommendation="DCIR test — see internal resistance",
                 notes=f"DCIR {res.dcir_mohm if res.dcir_mohm is None else round(res.dcir_mohm, 1)} mOhm; "
                       f"{res.stop_reason}")

    # ── Orchestrator glue ─────────────────────────────────────────────

    def _on_prompt(self, msg: str):
        self.prompt_lbl.setText(msg)
        if "DISABLE" in msg or "E-stop" in msg:
            # Non-modal: samples must keep flowing so load-off can be verified.
            box = QMessageBox(QMessageBox.Critical, "Operator action required",
                              msg, QMessageBox.Ok, self)
            box.setModal(False)
            box.show()
            self._alert = box

    def _confirm_clicked(self):
        if self._orch is not None:
            self._orch.confirm()
            self._show_phase()

    def _show_phase(self):
        if self._orch is None:
            return
        ph = self._orch.phase
        txt = f"Phase: {ph.value}"
        if self._orch.stop_reason:
            txt += f"  —  {self._orch.stop_reason}"
        self.phase_lbl.setText(txt)
        self.confirm_btn.setEnabled(ph is Phase.READY)
        self.limit_panel.update_live(self._orch)

    def _finalize_test(self):
        from gui.scoring import ScoringInputs, ScoringResult
        batt = get_battery(self._battery_id) or {}
        res = self._orch.results() if self._orch is not None else None
        # The orchestrator's trapezoidal Ah/Wh over the loaded phase is authoritative.
        ah = res.capacity_ah if res else self._total_ah
        wh = res.energy_wh if res else self._total_wh
        rated_ah = batt.get("capacity_rated_ah") or ah
        rated_wh = batt.get("energy_rated_wh")   or wh
        phys = batt.get("physical_score", 8)
        sag_mv = int(round(res.initial_sag_v * 1000)) if res and res.initial_sag_v else 0
        cutoff = self._profile.cutoff_voltage_v if self._profile else 0.0

        inputs = ScoringInputs(
            measured_ah    = ah,
            measured_wh    = wh,
            max_temp_c     = max(self._max_temp, 25.0),
            initial_voltage_sag_mv = max(0, sag_mv),
            voltage_cutoff_v = cutoff,
            rated_ah       = rated_ah,
            rated_wh       = rated_wh,
            physical_score = phys,
        )
        result = ScoringResult.from_inputs(inputs)

        t0 = self._samples[0][0]
        t1 = self._samples[-1][0]
        soh = round((wh / rated_wh) * 100, 1) if rated_wh > 0 else 0.0

        end_test(
            test_id           = self._test_id,
            capacity_ah       = round(ah, 3),
            energy_wh         = round(wh, 3),
            discharge_time_s  = round(res.duration_s if res else (t1 - t0), 1),
            max_temp_c        = self._max_temp,
            soh_percent       = soh,
            reliability_score = result.total_score,
            grade             = result.grade,
            recommendation    = result.recommendation,
            min_voltage_mv    = self._v_min,
        )

        # Update gauge + AI
        self.gauge.set_health(result.total_score, result.grade,
                              result.recommendation)

        reasons = []
        bd = result.breakdown
        if bd.get("Capacity retention (20)", 20) < 14:
            reasons.append(f"Capacity only {ah:.1f} Ah vs rated {rated_ah:.1f} Ah.")
        if bd.get("Thermal behavior (15)", 15) < 9:
            reasons.append(f"Temperature peaked at {self._max_temp:.0f}°C under load.")
        if bd.get("Voltage sag (15)", 15) < 8:
            reasons.append("Voltage sag exceeded expected range at load start.")
        if not reasons:
            reasons.append("All parameters within expected range.")

        self.ai_panel.update_analysis(
            result.total_score, result.grade,
            ah, rated_ah, self._max_temp, reasons)

        self._c_soh.set_value(f"{soh:.0f}")

    # ── Incoming sample ───────────────────────────────────────────────

    @Slot(object)
    def _on_sample(self, s: OsbamsSample):
        self._feed_orchestrator(s)
        t_s = s.time_s
        if self._last_tick_s is not None:
            dt = t_s - self._last_tick_s
            self._total_ah += abs(s.current_a) * dt / 3600.0
            self._total_wh += abs(s.power_w)   * dt / 3600.0
        self._last_tick_s = t_s

        self._max_temp = max(self._max_temp, s.temp_c)
        self._v_min = min(self._v_min, s.voltage_mv)
        self._v_max = max(self._v_max, s.voltage_mv)
        self._samples.append((t_s, s.voltage_mv, s.current_ma,
                               s.power_mw, s.temp_c10))

        if self._test_id:
            insert_reading(self._test_id, s.tick_ms, s.voltage_mv,
                           s.current_ma, s.power_mw, s.temp_c10)

        # SOC estimate: simple voltage-based linear map (36V system)
        # Replace with OCV lookup table for your chemistry later
        v_min_full, v_max_full = 30000, 42000
        soc = max(0, min(100, int(
            (s.voltage_mv - v_min_full) / (v_max_full - v_min_full) * 100)))

        # Update metric cards
        self._c_v.set_value(f"{s.voltage_v:.3f}")
        self._c_i.set_value(f"{s.current_a:.3f}")
        self._c_p.set_value(f"{s.power_w:.2f}")
        self._c_t.set_value(f"{s.temp_c:.1f}")
        self._c_soc.set_value(str(soc))
        self._c_ah.set_value(f"{self._total_ah:.3f}")
        self._c_wh.set_value(f"{self._total_wh:.2f}")
        self._c_time.set_value(f"{t_s:.0f}")

        # Update graphs
        self._t.append(t_s);         self._v.append(s.voltage_v)
        self._i.append(s.current_a); self._pw.append(s.power_w)
        self._tp.append(s.temp_c)

        tl = list(self._t)
        self._gv.listDataItems()[0].setData(tl, list(self._v))
        self._gi.listDataItems()[0].setData(tl, list(self._i))
        self._gp.listDataItems()[0].setData(tl, list(self._pw))
        self._gt.listDataItems()[0].setData(tl, list(self._tp))

    def _feed_orchestrator(self, s: OsbamsSample):
        if self._orch is None:
            return
        from services.protocol import (FLAG_OVERTEMP, FLAG_OVERCURRENT,
                                       FLAG_REVERSE_CURR, FLAG_LOAD_FAULT)
        # Firmware UNDERVOLT is its own protective stop; the orchestrator owns
        # the profile cutoff, so UNDERVOLT is not treated as a sensor fault.
        critical = FLAG_OVERTEMP | FLAG_OVERCURRENT | FLAG_REVERSE_CURR | FLAG_LOAD_FAULT
        fault = bool(s.flags & critical)
        self._orch.on_sample(Sample(s.time_s, s.voltage_v, s.current_a, s.temp_c, fault))
        self._show_phase()
        if self._orch.done and not self._stop_pending:
            self._stop_pending = True
            QTimer.singleShot(0, lambda: self._stop_test(force=True))

    @Slot(str)
    def _on_error(self, msg: str):
        QMessageBox.critical(self, "Serial Error", msg)
        self._stop_test()

    def _export_csv(self):
        if not self._samples: return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV",
            f"Battery_{self._battery_id:03d}.csv", "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time_s","voltage_mv","current_ma","power_mw","temp_c10"])
            w.writerows(self._samples)
        QMessageBox.information(self, "Exported", f"Saved: {path}")
